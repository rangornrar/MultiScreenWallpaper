using WallCraft.Core.Geometry;
using WallCraft.Core.Model;

namespace WallCraft.Core.Presentation;

/// <summary>
/// Un écran de l'aperçu : <see cref="Index"/> dans la liste des écrans, rectangle du moniteur dessiné (en pixels de la zone)
/// et rectangle de la composition qu'il affiche.
/// </summary>
public readonly record struct PreviewScreen(int Index, double X, double Y, double Width, double Height, IntRect Canvas)
{
    /// <summary>Marge entre le bord du moniteur dessiné et la dalle (cadre de 4 px).</summary>
    public const double Bezel = 4;

    public double InnerLeft => X + Bezel;
    public double InnerTop => Y + Bezel;
    public double InnerRight => X + Width - Bezel;
    public double InnerBottom => Y + Height - Bezel;
}

/// <summary>
/// Morceau d'image visible sur un écran de l'aperçu : partie de l'image en unités de composition relatives à son coin
/// (0..W, 0..H), et rectangle de destination en pixels de la zone.
/// </summary>
public readonly record struct PreviewSlice(
    CompositionImage Image,
    double SourceLeft, double SourceTop, double SourceRight, double SourceBottom,
    double X, double Y, double Width, double Height);

/// <summary>Géométrie de l'aperçu « vue réelle » des écrans (portage de <c>_refresh_sim_view</c>, ui_views.py).</summary>
public static class PreviewLayout
{
    /// <summary>Espace ajouté entre deux écrans de l'aperçu en mode pixels, en unités de composition.</summary>
    public const double GapUnits = 180;
    public const double PaddingX = 28;
    public const double PaddingTop = 16;

    /// <summary>Hauteur du plan du bureau (80 % de la zone).</summary>
    public static double DeskY(double viewportHeight) => viewportHeight * 0.8;

    /// <summary>
    /// Place les écrans dans la zone (<paramref name="viewportWidth"/> × <paramref name="viewportHeight"/>), dans l'ordre de
    /// <paramref name="canvases"/>. En mode pixels, un espace sépare les écrans (classés de gauche à droite) ; en taille
    /// réelle, les espaces entre dalles sont déjà dans la composition.
    /// </summary>
    public static List<PreviewScreen> Screens(IReadOnlyList<IntRect> canvases, double compositionWidth, double compositionHeight,
                                              bool physical, double viewportWidth, double viewportHeight)
    {
        var result = new List<PreviewScreen>(canvases.Count);
        if (canvases.Count == 0) return result;
        double deskY = DeskY(viewportHeight);
        double gap = physical ? 0 : GapUnits;
        // Rang de gauche à droite (tri stable sur (x, y), comme sorted() en Python)
        var rank = new int[canvases.Count];
        var order = Enumerable.Range(0, canvases.Count).OrderBy(i => canvases[i].X).ThenBy(i => canvases[i].Y).ToList();
        for (int k = 0; k < order.Count; k++) rank[order[k]] = k;

        double span = compositionWidth + Math.Max(0, canvases.Count - 1) * gap;
        double usableH = Math.Max(80, deskY - PaddingTop - 26);
        double scale = Math.Min((viewportWidth - PaddingX * 2) / Math.Max(1, span), usableH / Math.Max(1, compositionHeight));
        double ox = (viewportWidth - span * scale) / 2;
        double oy = PaddingTop + (usableH - compositionHeight * scale) / 2;

        for (int i = 0; i < canvases.Count; i++)
        {
            var c = canvases[i];
            double offset = rank[i] * gap;
            result.Add(new PreviewScreen(i, (c.X + offset) * scale + ox, c.Y * scale + oy, c.Width * scale, c.Height * scale, c));
        }
        return result;
    }

    /// <summary>Morceaux des images visibles sur un écran, du calque du dessous vers celui du dessus.</summary>
    public static List<PreviewSlice> Slices(PreviewScreen screen, IEnumerable<CompositionImage> images)
    {
        var slices = new List<PreviewSlice>();
        var c = screen.Canvas;
        double mx0 = c.X, my0 = c.Y, mx1 = c.X + c.Width, my1 = c.Y + c.Height;
        // Échelle de la dalle (cadre retiré) : l'image ne déborde pas sur le bord de l'écran.
        double kx = (screen.InnerRight - screen.InnerLeft) / Math.Max(1, c.Width);
        double ky = (screen.InnerBottom - screen.InnerTop) / Math.Max(1, c.Height);
        foreach (var img in images.OrderBy(i => i.ZIndex))
        {
            double w = img.W ?? 0, h = img.H ?? 0;
            double ix0 = img.X, iy0 = img.Y, ix1 = img.X + w, iy1 = img.Y + h;
            if (!(ix0 < mx1 && ix1 > mx0 && iy0 < my1 && iy1 > my0)) continue;
            double cx0 = Math.Max(0, mx0 - ix0), cy0 = Math.Max(0, my0 - iy0);
            double cx1 = Math.Min(w, mx1 - ix0), cy1 = Math.Min(h, my1 - iy0);
            double tx = screen.InnerLeft + Math.Max(0, ix0 - mx0) * kx;
            double ty = screen.InnerTop + Math.Max(0, iy0 - my0) * ky;
            slices.Add(new PreviewSlice(img, cx0, cy0, cx1, cy1, tx, ty, (cx1 - cx0) * kx, (cy1 - cy0) * ky));
        }
        return slices;
    }
}
