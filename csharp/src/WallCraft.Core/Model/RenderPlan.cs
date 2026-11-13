namespace WallCraft.Core.Model;

/// <summary>
/// Ce qu'il faut dessiner pour une image dans le rendu HD (portage de <c>compose_wallpaper_contain</c>) :
/// la zone à prendre dans l'image tournée (en pixels) et le rectangle de destination (en pixels entiers).
/// </summary>
public readonly record struct RenderStep(
    CompositionImage Image,
    int RotatedWidth, int RotatedHeight,
    int SourceLeft, int SourceTop, int SourceRight, int SourceBottom,
    int DestX, int DestY, int DestWidth, int DestHeight);

public static class RenderPlan
{
    /// <summary>
    /// Étapes dans l'ordre des calques (du dessous vers le dessus). Les bords sont arrondis séparément :
    /// deux images voisines se touchent sans liseré d'un pixel.
    /// </summary>
    public static List<RenderStep> Build(IEnumerable<CompositionImage> images)
    {
        var steps = new List<RenderStep>();
        foreach (var img in images.OrderBy(i => i.ZIndex)) // OrderBy est stable, comme sorted() en Python
        {
            bool quarter = img.Angle % 180 == 90;
            int sw = quarter ? img.OriginalHeight : img.OriginalWidth;
            int sh = quarter ? img.OriginalWidth : img.OriginalHeight;
            var c = img.Crop;
            int l = (int)(c.Left * sw), t = (int)(c.Top * sh), r = (int)(c.Right * sw), b = (int)(c.Bottom * sh);
            int x0 = (int)Layout.PythonCompat.RoundToInt(img.X), y0 = (int)Layout.PythonCompat.RoundToInt(img.Y);
            int w = r - l, h = b - t;
            if (img.W is double iw && iw != 0 && img.H is double ih && ih != 0)
            {
                int x1 = (int)Layout.PythonCompat.RoundToInt(img.X + iw), y1 = (int)Layout.PythonCompat.RoundToInt(img.Y + ih);
                w = Math.Max(1, x1 - x0);
                h = Math.Max(1, y1 - y0);
            }
            steps.Add(new RenderStep(img, sw, sh, l, t, r, b, x0, y0, w, h));
        }
        return steps;
    }
}
