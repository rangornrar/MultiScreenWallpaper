using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Effects;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using Windows.UI;
using WallCraft.App.Services;
using WallCraft.Core.Model;

namespace WallCraft.App.Rendering;

/// <summary>Éléments communs aux deux vues : étiquettes et dessin d'une partie d'image depuis sa vignette.</summary>
internal static class DrawingHelpers
{
    private static CanvasTextFormat ChipFormat() => new()
    {
        FontFamily = "Segoe UI",
        FontSize = 11,
        FontWeight = new Windows.UI.Text.FontWeight { Weight = 700 },
        WordWrapping = CanvasWordWrapping.NoWrap,
    };

    private static Size Measure(ICanvasResourceCreator creator, string text, CanvasTextFormat format)
    {
        using var layout = new CanvasTextLayout(creator, text, format, 10000, 1000);
        return new Size(layout.LayoutBounds.Width, layout.LayoutBounds.Height);
    }

    /// <summary>
    /// Étiquette arrondie à la taille de son texte (<c>_draw_chip</c>) : tronquée par la fin si elle dépasse
    /// <paramref name="maxWidth"/>, omise si la place est inférieure à 40 px. <paramref name="anchorBottom"/> : (x, y) est
    /// le coin bas gauche.
    /// </summary>
    public static void Chip(CanvasDrawingSession ds, double x, double y, string text, Color background, Color foreground,
                            bool anchorBottom = false, double? maxWidth = null)
    {
        using var format = ChipFormat();
        var size = Measure(ds, text, format);
        double w = size.Width + 12, h = size.Height + 6;
        if (maxWidth is double max && w > max)
        {
            if (max < 40) return;
            while (text.Length > 3 && w > max)
            {
                text = text[..^2] + "…";
                w = Measure(ds, text, format).Width + 12;
            }
        }
        if (anchorBottom) y -= h;
        ds.FillRoundedRectangle(new Rect(x, y, w, h), 4, 4, background);
        format.VerticalAlignment = CanvasVerticalAlignment.Center;
        ds.DrawText(text, new Rect(x + 6, y, Math.Max(1, w - 6), h), foreground, format);
    }

    /// <summary>
    /// Dessine la partie (<paramref name="left"/>, <paramref name="top"/>) – (<paramref name="right"/>, <paramref name="bottom"/>)
    /// de l'image, en unités de composition relatives à son coin (0..W, 0..H), dans <paramref name="dest"/>. Le rognage,
    /// la rotation, les retouches et le flou de l'image sont appliqués ; rien n'est dessiné tant que la vignette se charge.
    /// </summary>
    public static bool DrawImagePart(CanvasDrawingSession ds, ImageCache cache, CompositionImage img, Rect dest,
                                     double left, double top, double right, double bottom)
    {
        double w = img.W ?? 0, h = img.H ?? 0;
        if (w <= 0 || h <= 0 || dest.Width <= 0 || dest.Height <= 0) return false;
        var bitmap = cache.Bitmap(ds, img);
        return DrawBitmapPart(ds, bitmap, img, dest, left, top, right, bottom);
    }

    /// <summary>Comme <see cref="DrawImagePart"/>, avec la vignette GPU déjà obtenue (null : cadre vide).</summary>
    public static bool DrawBitmapPart(CanvasDrawingSession ds, CanvasBitmap? bitmap, CompositionImage img, Rect dest,
                                      double left, double top, double right, double bottom)
    {
        double w = img.W ?? 0, h = img.H ?? 0;
        if (w <= 0 || h <= 0 || dest.Width <= 0 || dest.Height <= 0) return false;
        if (bitmap is null)
        {
            ds.FillRectangle(dest, Palette.Placeholder);
            return false;
        }
        var bounds = bitmap.SizeInPixels;
        double bw = bounds.Width, bh = bounds.Height;
        var crop = img.Crop;
        // Unités de l'image → pixels de la vignette tournée, à l'intérieur de la zone visible
        double fx = bw * crop.Width / w, fy = bh * crop.Height / h;
        var source = new Rect(crop.Left * bw + left * fx, crop.Top * bh + top * fy,
                              Math.Max(0.5, (right - left) * fx), Math.Max(0.5, (bottom - top) * fy));
        ICanvasImage image = bitmap;
        GaussianBlurEffect? blur = null;
        if (img.Blur > 0)
        {
            // Le flou est exprimé en pixels de l'image d'origine : ramené à l'échelle de la vignette.
            bool quarter = img.Angle % 180 == 90;
            double originalWidth = quarter ? img.OriginalHeight : img.OriginalWidth;
            blur = new GaussianBlurEffect
            {
                Source = bitmap,
                BlurAmount = (float)(img.Blur * bw / Math.Max(1, originalWidth)),
                BorderMode = EffectBorderMode.Hard,
            };
            image = blur;
        }
        ds.DrawImage(image, dest, source, 1f, CanvasImageInterpolation.HighQualityCubic);
        blur?.Dispose();
        return true;
    }
}
