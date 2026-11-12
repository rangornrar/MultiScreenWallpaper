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
    {
        var target = new CanvasRenderTarget(Device, width, height, 96);
        using (var ds = target.CreateDrawingSession()) ds.Clear(background);

        foreach (var step in RenderPlan.Build(images))
        {
            cancel.ThrowIfCancellationRequested();
            var img = step.Image;
            var pixels = await ImageDecoder.DecodeAsync(img.Path);
            pixels = Filters.Apply(pixels, img.Brightness, img.Contrast, img.Saturation);
            if (img.Angle != 0) pixels = pixels.Rotate(img.Angle);
            var cropped = pixels.Crop(step.SourceLeft, step.SourceTop, step.SourceRight, step.SourceBottom);
            pixels = null!; // libère la pleine résolution avant l'envoi au GPU

            using var bitmap = CanvasBitmap.CreateFromBytes(Device, cropped.ToBgraPremultiplied(), cropped.Width, cropped.Height,
                DirectXPixelFormat.B8G8R8A8UIntNormalized);
            using var blur = img.Blur > 0
                ? new GaussianBlurEffect { Source = bitmap, BlurAmount = (float)img.Blur, BorderMode = EffectBorderMode.Hard, Optimization = EffectOptimization.Quality }
                : null;
            // Une session par image : le dessin est terminé avant de libérer l'image source.
            using var ds = target.CreateDrawingSession();
            ds.DrawImage((ICanvasImage?)blur ?? bitmap,
                new Rect(step.DestX, step.DestY, step.DestWidth, step.DestHeight),
                new Rect(0, 0, cropped.Width, cropped.Height),
                1f, CanvasImageInterpolation.HighQualityCubic);
        }
        return target;
    }

    /// <summary>Découpe la composition en une image par écran (taille native de l'écran) et l'enregistre en PNG.</summary>
    public static async Task<List<(MonitorInfo Monitor, string Path)>> SplitAsync(
        CanvasRenderTarget composite, IReadOnlyList<MonitorInfo> monitors, string outDir, string prefix)
    {
        var size = composite.SizeInPixels;
        var boxes = CompositionLayout.SplitBoxes(monitors, (int)size.Width, (int)size.Height);
        var results = new List<(MonitorInfo, string)>();
        for (int i = 0; i < monitors.Count; i++)
        {
            if (boxes[i] is not var (l, t, r, b)) continue;
            var m = monitors[i];
            bool sameSize = r - l == m.Width && b - t == m.Height;
            using var piece = new CanvasRenderTarget(Device, m.Width, m.Height, 96);
            using (var ds = piece.CreateDrawingSession())
            {
                ds.DrawImage(composite, new Rect(0, 0, m.Width, m.Height), new Rect(l, t, r - l, b - t), 1f,
                    sameSize ? CanvasImageInterpolation.NearestNeighbor : CanvasImageInterpolation.HighQualityCubic);
            }
            string path = Path.Combine(outDir, $"{prefix}_pos_{i:00}.png");
            await piece.SaveAsync(path, CanvasBitmapFileFormat.Png);
            results.Add((m, path));
        }
        return results;
    }

    /// <summary>Repli « Étendre » : une seule image à la géométrie du bureau Windows, reconstruite depuis les images par écran.</summary>
    public static async Task<string> BuildSpanAsync(IReadOnlyList<(MonitorInfo Monitor, string Path)> pieces, Windows.UI.Color background, string path)
    {
        int x0 = pieces.Min(p => p.Monitor.X), y0 = pieces.Min(p => p.Monitor.Y);
        int x1 = pieces.Max(p => p.Monitor.X + p.Monitor.Width), y1 = pieces.Max(p => p.Monitor.Y + p.Monitor.Height);
        using var span = new CanvasRenderTarget(Device, x1 - x0, y1 - y0, 96);
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
