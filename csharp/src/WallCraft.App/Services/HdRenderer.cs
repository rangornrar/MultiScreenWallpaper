using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Effects;
using Windows.Foundation;
using Windows.Graphics.DirectX;
using WallCraft.Core.Geometry;
using WallCraft.Core.Imaging;
using WallCraft.Core.Model;

namespace WallCraft.App.Services;

/// <summary>
/// Rendu HD à partir des fichiers originaux (portage de compose_wallpaper_contain et de la découpe par écran),
/// avec Win2D. Chaque image est décodée, retouchée, tournée, rognée puis redimensionnée en bicubique haute qualité.
/// </summary>
public static class HdRenderer
{
    private static CanvasDevice Device => CanvasDevice.GetSharedDevice();

    public static async Task<CanvasRenderTarget> ComposeAsync(
        IReadOnlyList<CompositionImage> images, int width, int height, Windows.UI.Color background, CancellationToken cancel = default)
        => await RenderAsync(RenderPlan.Build(images), new IntRect(0, 0, width, height), width, height, background, cancel);

    private static async Task<CanvasRenderTarget> RenderAsync(
        IReadOnlyList<RenderStep> steps, IntRect area, int width, int height, Windows.UI.Color background, CancellationToken cancel)
    {
        var device = Device;
        int limit = device.MaximumBitmapSizeInPixels;
        var target = CreateTarget(device, width, height, limit);
        try
        {
            using (var ds = target.CreateDrawingSession()) ds.Clear(background);
            double sx = (double)width / area.Width, sy = (double)height / area.Height;
            foreach (var step in steps)
            {
                cancel.ThrowIfCancellationRequested();
                if (step.DestX >= area.Right || step.DestY >= area.Bottom ||
                    (long)step.DestX + step.DestWidth <= area.X || (long)step.DestY + step.DestHeight <= area.Y) continue;

                var img = step.Image;
                var pixels = await ImageDecoder.DecodeAsync(img.Path);
                pixels = Filters.Apply(pixels, img.Brightness, img.Contrast, img.Saturation);
                if (img.Angle != 0) pixels = pixels.Rotate(img.Angle);
                var cropped = pixels.Crop(step.SourceLeft, step.SourceTop, step.SourceRight, step.SourceBottom);
                double blurScale = 1;
                if (cropped.Width > limit || cropped.Height > limit)
                {
                    blurScale = (double)limit / Math.Max(cropped.Width, cropped.Height);
                    cropped = Thumbnail.Fit(cropped, limit, limit);
                }
                using var bitmap = CanvasBitmap.CreateFromBytes(device, cropped.ToBgraPremultiplied(), cropped.Width, cropped.Height,
                    DirectXPixelFormat.B8G8R8A8UIntNormalized);
                using var blur = img.Blur > 0
                    ? new GaussianBlurEffect { Source = bitmap, BlurAmount = (float)(img.Blur * blurScale), BorderMode = EffectBorderMode.Hard, Optimization = EffectOptimization.Quality }
                    : null;
                // La surface de sortie découpe l'image sans modifier son placement dans la composition.
                using var ds = target.CreateDrawingSession();
                ds.DrawImage((ICanvasImage?)blur ?? bitmap,
                    new Rect((step.DestX - (double)area.X) * sx, (step.DestY - (double)area.Y) * sy,
                        step.DestWidth * sx, step.DestHeight * sy),
                    new Rect(0, 0, cropped.Width, cropped.Height), 1f, CanvasImageInterpolation.HighQualityCubic);
            }
            return target;
        }
        catch
        {
            target.Dispose();
            throw;
        }
    }

    /// <summary>Enregistre une image PNG à la taille native de chaque écran.</summary>
    public static async Task<List<(MonitorInfo Monitor, string Path)>> SplitAsync(
        IReadOnlyList<CompositionImage> images, int width, int height, IReadOnlyList<MonitorInfo> monitors,
        Windows.UI.Color background, string outDir, string prefix, CancellationToken cancel = default)
    {
        if (monitors.Count == 0) return [];
        var boxes = CompositionLayout.SplitBoxes(monitors, width, height);
        int limit = Device.MaximumBitmapSizeInPixels;
        var steps = RenderPlan.Build(images);
        using var composite = width <= limit && height <= limit
            ? await RenderAsync(steps, new IntRect(0, 0, width, height), width, height, background, cancel)
            : null;
        var results = new List<(MonitorInfo, string)>();
        for (int i = 0; i < monitors.Count; i++)
        {
            cancel.ThrowIfCancellationRequested();
            if (boxes[i] is not var (l, t, r, b)) continue;
            var m = monitors[i];
            var area = new IntRect(l, t, r - l, b - t);
            using var piece = composite is null
                ? await RenderAsync(steps, area, m.Width, m.Height, background, cancel)
                : ExtractScreen(composite, area, m.Width, m.Height, limit);
            string path = Path.Combine(outDir, $"{prefix}_pos_{i:00}.png");
            await piece.SaveAsync(path, CanvasBitmapFileFormat.Png);
            results.Add((m, path));
        }
        return results;
    }

    private static CanvasRenderTarget ExtractScreen(CanvasRenderTarget composite, IntRect area, int width, int height, int limit)
    {
        var piece = CreateTarget(Device, width, height, limit);
        try
        {
            using var ds = piece.CreateDrawingSession();
            ds.DrawImage(composite, new Rect(0, 0, width, height), new Rect(area.X, area.Y, area.Width, area.Height), 1f,
                area.Width == width && area.Height == height ? CanvasImageInterpolation.NearestNeighbor : CanvasImageInterpolation.HighQualityCubic);
            return piece;
        }
        catch
        {
            piece.Dispose();
            throw;
        }
    }

    private static CanvasRenderTarget CreateTarget(CanvasDevice device, int width, int height, int limit)
    {
        if (width > limit || height > limit)
            throw new InvalidOperationException(Localizer.Current.Format("msg_render_too_large", width, height, limit));
        return new CanvasRenderTarget(device, width, height, 96);
    }

    /// <summary>Repli « Étendre » : une seule image à la géométrie du bureau Windows, reconstruite depuis les images par écran.</summary>
    public static async Task<string> BuildSpanAsync(IReadOnlyList<(MonitorInfo Monitor, string Path)> pieces, Windows.UI.Color background, string path)
    {
        int x0 = pieces.Min(p => p.Monitor.X), y0 = pieces.Min(p => p.Monitor.Y);
        int x1 = pieces.Max(p => p.Monitor.X + p.Monitor.Width), y1 = pieces.Max(p => p.Monitor.Y + p.Monitor.Height);
        var device = Device;
        using var span = CreateTarget(device, x1 - x0, y1 - y0, device.MaximumBitmapSizeInPixels);
        using (var ds = span.CreateDrawingSession()) ds.Clear(background);
        foreach (var (m, file) in pieces)
        {
            using var bitmap = await CanvasBitmap.LoadAsync(Device, file, 96);
            using var ds = span.CreateDrawingSession();
            ds.DrawImage(bitmap, new Rect(m.X - x0, m.Y - y0, m.Width, m.Height), bitmap.Bounds, 1f, CanvasImageInterpolation.NearestNeighbor);
        }
        await span.SaveAsync(path, CanvasBitmapFileFormat.Png);
        return path;
    }
}
