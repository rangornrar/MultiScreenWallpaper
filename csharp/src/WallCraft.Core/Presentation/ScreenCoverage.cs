using WallCraft.Core.Geometry;

namespace WallCraft.Core.Presentation;

/// <summary>Rectangle en coordonnées de composition (bords gauche, haut, droit, bas).</summary>
public readonly record struct CompositionCell(double Left, double Top, double Right, double Bottom);

/// <summary>Ce qui ne sera visible sur aucun écran (portage du calcul de <c>_dim_outside_screens</c>, ui_views.py).</summary>
public static class ScreenCoverage
{
    /// <summary>
    /// Découpe la composition selon les bords des écrans et renvoie les cases dont le centre n'est sur aucun écran
    /// (marges du bureau virtuel, espaces entre dalles en taille réelle). Ce sont les zones à assombrir.
    /// </summary>
    public static List<CompositionCell> OutsideCells(IReadOnlyList<IntRect> screens, double width, double height)
    {
        var xs = new SortedSet<double> { 0, width };
        var ys = new SortedSet<double> { 0, height };
        foreach (var r in screens)
        {
            xs.Add(r.X);
            xs.Add(r.Right);
            ys.Add(r.Y);
            ys.Add(r.Bottom);
        }
        var xl = xs.ToList();
        var yl = ys.ToList();
        var cells = new List<CompositionCell>();
        for (int i = 0; i + 1 < xl.Count; i++)
        {
            for (int j = 0; j + 1 < yl.Count; j++)
            {
                double x0 = xl[i], x1 = xl[i + 1], y0 = yl[j], y1 = yl[j + 1];
                double cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
                if (screens.Any(r => r.X <= cx && cx <= r.Right && r.Y <= cy && cy <= r.Bottom)) continue;
                cells.Add(new CompositionCell(x0, y0, x1, y1));
            }
        }
        return cells;
    }
}
