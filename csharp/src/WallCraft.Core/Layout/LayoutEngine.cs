using System.Diagnostics;
using System.Globalization;
using System.Text;
using WallCraft.Core.Model;

namespace WallCraft.Core.Layout;

/// <summary>Les six dispositions automatiques (mêmes identifiants que la version Python).</summary>
public static class LayoutModes
{
    public const string Mosaic = "layout_mosaic";
    public const string Lines = "layout_lines";
    public const string Grid = "layout_grid";
    public const string VerticalStrips = "layout_v_strip";
    public const string HorizontalStrips = "layout_h_strip";
    public const string Optimal = "layout_optimal";

    public static readonly IReadOnlyList<string> All = [Mosaic, Lines, Grid, VerticalStrips, HorizontalStrips, Optimal];

    internal static bool IsRegular(string mode) => mode is Grid or Lines or VerticalStrips or HorizontalStrips;
}

/// <summary>Placement d'une image calculé par le moteur, sans toucher à l'image elle-même.</summary>
public readonly record struct Placement(double X, double Y, double W, double H, CropBox Crop, int ZIndex);

/// <summary>
/// Portage fidèle de <c>AutoLayoutStrategy</c> (image_tools.py). Toutes les dispositions sont déterministes :
/// mêmes images, même taille et même numéro de variante donnent exactement le même résultat qu'en Python.
/// « Ajuster » : chaque image entière, sans déformation (bandes possibles). « Remplir » : chaque case est
/// couverte, l'image est recadrée autour de son point d'intérêt.
/// </summary>
public sealed class LayoutEngine
{
    /// <summary>Poids de l'équilibre des tailles dans le score du mode optimal.</summary>
    public const double OptimalBalanceWeight = 0.15;
    public const int VariantCount = 4;

    /// <summary>Garde-fou de durée du mode optimal, en secondes (le nombre d'essais s'arrête normalement avant).</summary>
    public double OptimalMaxTime { get; init; } = 2.0;

    /// <summary>Calcule le point d'intérêt d'une image qui n'en a pas encore (visages, zone détaillée…). Null = centre.</summary>
    public Func<CompositionImage, FocusPoint>? FocusProvider { get; init; }

    private delegate void PlaceFn(CompositionImage img, double x, double y, double w, double h);

    // --- Graine ---

    /// <summary>Chaîne hachée pour la graine : <c>repr((mode, round(tw), round(th), variant, [(path, round(aspect, 4)), …]))</c>.</summary>
    public static string SeedKey(string mode, double targetW, double targetH, IEnumerable<CompositionImage> images, int variant)
        => SeedKey(mode, targetW, targetH, variant, images.Select(i => (i.Path, i.VisibleAspect)));

    public static string SeedKey(string mode, double targetW, double targetH, int variant, IEnumerable<(string Path, double Aspect)> images)
    {
        var sb = new StringBuilder("(");
        sb.Append(PythonCompat.ReprString(mode)).Append(", ");
        sb.Append(PythonCompat.RoundToInt(targetW).ToString(CultureInfo.InvariantCulture)).Append(", ");
        sb.Append(PythonCompat.RoundToInt(targetH).ToString(CultureInfo.InvariantCulture)).Append(", ");
        sb.Append(variant.ToString(CultureInfo.InvariantCulture)).Append(", [");
        bool first = true;
        foreach (var (path, aspect) in images)
        {
            if (!first) sb.Append(", ");
            first = false;
            sb.Append('(').Append(PythonCompat.ReprString(path)).Append(", ")
              .Append(PythonCompat.ReprFloat(PythonCompat.Round(aspect, 4))).Append(')');
        }
        sb.Append("])");
        return sb.ToString();
    }

    public static long Seed(string mode, double targetW, double targetH, IEnumerable<CompositionImage> images, int variant)
        => PythonCompat.Sha1Prefix48(SeedKey(mode, targetW, targetH, images, variant));

    // --- Point d'entrée ---

    /// <summary>Applique une disposition : remet rotation, ordre et rognage à zéro puis place les images.</summary>
    public void Apply(string mode, double targetW, double targetH, IList<CompositionImage> images, bool fill = false, int variant = 0)
    {
        if (images.Count == 0) return;
        for (int idx = 0; idx < images.Count; idx++)
        {
            images[idx].Angle = 0;
            images[idx].ZIndex = idx;
            images[idx].Crop = CropBox.Full;
        }

        var rng = new PythonRandom(Seed(mode, targetW, targetH, images, variant));
        PlaceFn place = fill ? CropCover : FitInside;
        IList<CompositionImage> ordered = LayoutModes.IsRegular(mode) ? Ordered(images, variant) : images;

        switch (mode)
        {
            case LayoutModes.Grid: GridFit(targetW, targetH, ordered, place); break;
            case LayoutModes.Lines: JustifiedFit(targetW, targetH, ordered, place, fill); break;
            case LayoutModes.VerticalStrips: VerticalStrip(targetW, targetH, ordered, place); break;
            case LayoutModes.HorizontalStrips: HorizontalStrip(targetW, targetH, ordered, place); break;
            case LayoutModes.Optimal: OptimalFit(targetW, targetH, images, rng, variant, fill); break;
            default: PerfectMosaic(targetW, targetH, images, rng, place); break;
        }
    }

    /// <summary>Ordres déterministes pour les dispositions régulières : variante 0 = ordre d'import.</summary>
    internal static List<CompositionImage> Ordered(IList<CompositionImage> images, int variant) => (variant % 4) switch
    {
        0 => [.. images],
        1 => [.. images.Reverse()],
        2 => [.. images.OrderBy(i => -i.VisibleAspect)],
        _ => [.. images.OrderBy(i => i.VisibleAspect)],
    };

    /// <summary>Une image par écran (rects = rectangles de composition des écrans).</summary>
    public void PlaceOnScreens(IList<CompositionImage> images, IReadOnlyList<(double X, double Y, double W, double H)> rects, bool fill = false)
    {
        PlaceFn place = fill ? CropCover : FitInside;
        for (int idx = 0; idx < Math.Min(images.Count, rects.Count); idx++)
        {
            var img = images[idx];
            img.Angle = 0;
            img.ZIndex = idx;
            img.Crop = CropBox.Full;
            var (x, y, w, h) = rects[idx];
            place(img, x, y, w, h);
        }
    }

    /// <summary>Jusqu'à <paramref name="count"/> variantes distinctes, calculées sur des copies (les images ne bougent pas).</summary>
    public List<List<Placement>> Variants(string mode, double targetW, double targetH, IList<CompositionImage> images, bool fill = false, int? count = null)
    {
        int wanted = count ?? VariantCount;
        var results = new List<List<Placement>>();
        var seen = new HashSet<string>();
        for (int variant = 0; variant < wanted * 3; variant++)
        {
            var clones = images.Select(i => i.Clone()).ToList();
            Apply(mode, targetW, targetH, clones, fill, variant);
            var placement = clones.Select(c => new Placement(c.X, c.Y, c.W ?? 0, c.H ?? 0, c.Crop, c.ZIndex)).ToList();
            var key = string.Join(";", placement.Select(p =>
                $"{RoundQuarter(p.X)},{RoundQuarter(p.Y)},{RoundQuarter(p.W)},{RoundQuarter(p.H)}"));
            if (!seen.Add(key)) continue;
            results.Add(placement);
            if (results.Count == wanted) break;
        }
        return results;

        static string RoundQuarter(double v) => PythonCompat.RoundToInt(v / 4).ToString(CultureInfo.InvariantCulture);
    }

    public static void ApplyPlacement(IList<CompositionImage> images, IReadOnlyList<Placement> placement)
    {
        for (int i = 0; i < Math.Min(images.Count, placement.Count); i++)
        {
            var p = placement[i];
            var img = images[i];
            img.Angle = 0;
            img.X = p.X; img.Y = p.Y; img.W = p.W; img.H = p.H;
            img.Crop = p.Crop;
            img.ZIndex = p.ZIndex;
        }
    }

    // --- Placement dans une case ---

    /// <summary>Place la zone visible de l'image dans la case, sans déformation (bandes si besoin).</summary>
    public static void FitInside(CompositionImage img, double boxX, double boxY, double boxW, double boxH)
    {
        if (boxW <= 0 || boxH <= 0) return;
        double imgRatio = img.VisibleAspect, boxRatio = boxW / boxH;
        double newW, newH;
        if (imgRatio > boxRatio) { newW = boxW; newH = boxW / imgRatio; }
        else { newH = boxH; newW = boxH * imgRatio; }
        img.X = boxX + (boxW - newW) / 2;
        img.Y = boxY + (boxH - newH) / 2;
        img.W = Math.Truncate(newW);
        img.H = Math.Truncate(newH);
    }

    /// <summary>Couvre toute la case : recadrage au ratio de la case, centré sur le point d'intérêt et maintenu dans l'image.</summary>
    public void CropCover(CompositionImage img, double boxX, double boxY, double boxW, double boxH)
    {
        if (boxW <= 0 || boxH <= 0) return;
        img.X = boxX; img.Y = boxY;
        img.W = Math.Max(1, PythonCompat.RoundToInt(boxW));
        img.H = Math.Max(1, PythonCompat.RoundToInt(boxH));
        double boxRatio = boxW / boxH;
        double imgRatio = img.CurrentAspect;
        img.Focus ??= FocusProvider?.Invoke(img);
        var (fx, fy) = img.Focus ?? FocusPoint.Center;
        if (imgRatio > boxRatio)
        {
            double frac = boxRatio / imgRatio;
            double left = Math.Min(Math.Max(fx - frac / 2, 0.0), 1.0 - frac);
            img.Crop = new CropBox(left, 0.0, left + frac, 1.0);
        }
        else
        {
            double frac = imgRatio / boxRatio;
            double top = Math.Min(Math.Max(fy - frac / 2, 0.0), 1.0 - frac);
            img.Crop = new CropBox(0.0, top, 1.0, top + frac);
        }
    }

    // --- Dispositions ---

    private static void GridFit(double tw, double th, IList<CompositionImage> images, PlaceFn place)
    {
        int count = images.Count;
        if (count == 0) return;
        int cols = (int)Math.Ceiling(Math.Sqrt(count));
        int rows = (int)Math.Ceiling((double)count / cols);
        double cw = tw / cols, ch = th / rows;
        for (int i = 0; i < count; i++)
        {
            int col = i % cols, row = i / cols;
            int itemsInRow = count - row * cols;
            if (row == rows - 1 && itemsInRow < cols)
            {
                double specialW = tw / itemsInRow;
                place(images[i], col * specialW, row * ch, specialW, ch);
            }
            else
            {
                place(images[i], col * cw, row * ch, cw, ch);
            }
        }
    }

    private static void HorizontalStrip(double tw, double th, IList<CompositionImage> images, PlaceFn place)
    {
        int count = images.Count;
        if (count == 0) return;
        double ch = th / count;
        for (int i = 0; i < count; i++) place(images[i], 0, i * ch, tw, ch);
    }

    private static void VerticalStrip(double tw, double th, IList<CompositionImage> images, PlaceFn place)
    {
        int count = images.Count;
        if (count == 0) return;
        double cw = tw / count;
        for (int i = 0; i < count; i++) place(images[i], i * cw, 0, cw, th);
    }

    /// <summary>Lignes justifiées sur la largeur, réduites si besoin pour tenir en hauteur (étirées en mode Remplir).</summary>
    private static void JustifiedFit(double tw, double th, IList<CompositionImage> images, PlaceFn place, bool fill)
    {
        if (images.Count == 0) return;
        var ratios = images.Select(i => i.VisibleAspect).ToList();
        double totalRatio = PythonCompat.Sum(ratios);
        double screenRatio = tw / th;

        long idealRows = Math.Max(1, Math.Min(images.Count, PythonCompat.RoundToInt(totalRatio / screenRatio)));
        var rows = new List<(List<CompositionImage> Images, double Ratio)>();
        var currentRow = new List<CompositionImage>();
        double currentRowRatio = 0.0;
        double avgTargetRowRatio = totalRatio / idealRows;

        for (int i = 0; i < images.Count; i++)
        {
            currentRow.Add(images[i]);
            currentRowRatio += ratios[i];
            if (currentRowRatio >= avgTargetRowRatio && rows.Count < idealRows - 1)
            {
                rows.Add((currentRow, currentRowRatio));
                currentRow = [];
                currentRowRatio = 0.0;
            }
        }
        if (currentRow.Count > 0) rows.Add((currentRow, currentRowRatio));

        // Comme en Python : les lignes de ratio nul sont absentes de row_heights, et zip s'arrête au plus court.
        var rowHeights = rows.Where(r => r.Ratio > 0).Select(r => tw / r.Ratio).ToList();
        double totalUsedHeight = PythonCompat.Sum(rowHeights);
        int pairs = Math.Min(rows.Count, rowHeights.Count);

        if (fill)
        {
            double yScale = totalUsedHeight > 0 ? th / totalUsedHeight : 1.0;
            double currentY = 0.0;
            for (int r = 0; r < pairs; r++)
            {
                var (rowImages, rowRatio) = rows[r];
                double rowH = rowHeights[r] * yScale;
                double currentX = 0.0;
                foreach (var img in rowImages)
                {
                    double w = tw * img.VisibleAspect / rowRatio;
                    place(img, currentX, currentY, w, rowH);
                    currentX += w;
                }
                currentY += rowH;
            }
            return;
        }

        double scaleFactor = totalUsedHeight > 0 ? Math.Min(1.0, th / totalUsedHeight) : 1.0;
        double y = (th - totalUsedHeight * scaleFactor) / 2;
        for (int r = 0; r < pairs; r++)
        {
            var (rowImages, _) = rows[r];
            double finalH = rowHeights[r] * scaleFactor;
            double currentX = (tw - tw * scaleFactor) / 2;
            foreach (var img in rowImages)
            {
                double w = finalH * img.VisibleAspect;
                place(img, currentX, y, w, finalH);
                currentX += w;
            }
            y += finalH;
        }
    }

    /// <summary>Patchwork : découpage binaire de l'espace, avec un aléa reproductible.</summary>
    private static void PerfectMosaic(double tw, double th, IList<CompositionImage> images, PythonRandom rng, PlaceFn place)
    {
        if (images.Count == 0) return;
        var shuffled = images.ToList();
        rng.Shuffle(shuffled);
        RecursiveBsp(0, 0, tw, th, shuffled, rng, place);
    }

    private static readonly bool[] TrueFalse = [true, false];

    private static void RecursiveBsp(double x, double y, double w, double h, List<CompositionImage> images, PythonRandom rng, PlaceFn place)
    {
        int n = images.Count;
        if (n == 0) return;
        if (n == 1) { place(images[0], x, y, w, h); return; }

        bool splitVertical;
        if (w > h * 1.5) splitVertical = true;
        else if (h > w * 1.5) splitVertical = false;
        else splitVertical = rng.Choice(TrueFalse);

        int splitIdx = n == 2 ? 1 : rng.RandInt(1, n - 1);
        var groupA = images.GetRange(0, splitIdx);
        var groupB = images.GetRange(splitIdx, n - splitIdx);

        double baseRatio = (double)groupA.Count / n;
        double jitter = rng.Uniform(-0.1, 0.1);
        double finalRatio = Math.Max(0.2, Math.Min(0.8, baseRatio + jitter));

        if (splitVertical)
        {
            double wA = w * finalRatio;
            RecursiveBsp(x, y, wA, h, groupA, rng, place);
            RecursiveBsp(x + wA, y, w - wA, h, groupB, rng, place);
        }
        else
        {
            double hA = h * finalRatio;
            RecursiveBsp(x, y, w, hA, groupA, rng, place);
            RecursiveBsp(x, y + hA, w, h - hA, groupB, rng, place);
        }
    }

    // --- Mode optimal : arbre de découpage (« slicing floorplan ») ---

    private sealed class Node
    {
        public required char Type;            // 'L' feuille, 'H' côte à côte, 'V' empilées
        public CompositionImage? Image;
        public Node? Left, Right;
        public required double R;             // ratio largeur/hauteur du nœud
        public required List<double> Areas;   // aires des feuilles pour une hauteur de 1
        public required string Key;           // structure de l'arbre (pour reconnaître les doublons)
    }

    /// <summary>Nombre d'essais selon le nombre d'images (identique à Python).</summary>
    public static int OptimalIterations(int imageCount) => imageCount <= 6 ? 60000 : imageCount <= 12 ? 30000 : 15000;

    private void OptimalFit(double tw, double th, IList<CompositionImage> images, PythonRandom rng, int variant, bool fill, int? iterations = null)
    {
        int n = images.Count;
        if (n == 0) return;
        PlaceFn place = fill ? CropCover : FitInside;
        if (n == 1) { place(images[0], 0, 0, tw, th); return; }

        double targetRatio = tw / th;
        int iters = iterations ?? OptimalIterations(n);
        int keep = variant + 1;
        var ids = new Dictionary<CompositionImage, int>(ReferenceEqualityComparer.Instance);
        for (int i = 0; i < n; i++) ids[images[i]] = i;

        Node MakeRandomTree(List<CompositionImage> slice, int start, int count)
        {
            if (count == 1)
            {
                var img = slice[start];
                double r = img.VisibleAspect;
                return new Node { Type = 'L', Image = img, R = r, Areas = [r], Key = ids[img].ToString(CultureInfo.InvariantCulture) };
            }

            int splitIdx = rng.RandInt(1, count - 1);
            var left = MakeRandomTree(slice, start, splitIdx);
            var right = MakeRandomTree(slice, start + splitIdx, count - splitIdx);

            if (rng.Random() < 0.5)
            {
                var areasH = new List<double>(left.Areas.Count + right.Areas.Count);
                areasH.AddRange(left.Areas);
                areasH.AddRange(right.Areas);
                return new Node { Type = 'H', Left = left, Right = right, R = left.R + right.R, Areas = areasH, Key = $"H({left.Key},{right.Key})" };
            }

            double rv = 1.0 / (1.0 / left.R + 1.0 / right.R);
            double kl = Math.Pow(rv / left.R, 2), kr = Math.Pow(rv / right.R, 2);
            var areasV = new List<double>(left.Areas.Count + right.Areas.Count);
            foreach (var a in left.Areas) areasV.Add(a * kl);
            foreach (var a in right.Areas) areasV.Add(a * kr);
            return new Node { Type = 'V', Left = left, Right = right, R = rv, Areas = areasV, Key = $"V({left.Key},{right.Key})" };
        }

        double Score(Node tree)
        {
            double tr = tree.R;
            double fillRatio = tr >= targetRatio ? targetRatio / tr : tr / targetRatio;
            return fillRatio * Math.Pow(tree.Areas.Min() / tree.Areas.Max(), OptimalBalanceWeight);
        }

        var best = new List<(double Score, int It, Node Tree)>();
        var keys = new HashSet<string>(StringComparer.Ordinal);
        var clock = Stopwatch.StartNew();
        var imgsCopy = images.ToList();
        for (int it = 0; it < iters; it++)
        {
            if (it % 2000 == 0 && it != 0 && clock.Elapsed.TotalSeconds > OptimalMaxTime) break;
            rng.Shuffle(imgsCopy);
            var tree = MakeRandomTree(imgsCopy, 0, imgsCopy.Count);
            if (keys.Contains(tree.Key)) continue;
            double s = Score(tree);
            if (best.Count < keep || s > best[^1].Score)
            {
                keys.Add(tree.Key);
                best.Add((s, it, tree));
                best.Sort((a, b) => a.Score != b.Score ? b.Score.CompareTo(a.Score) : a.It.CompareTo(b.It));
                if (best.Count > keep)
                {
                    keys.Remove(best[^1].Tree.Key);
                    best.RemoveAt(best.Count - 1);
                }
            }
        }
        var bestTree = best[Math.Min(variant, best.Count - 1)].Tree;

        double rTotal = bestTree.R;
        double globalW, globalH;
        if (fill) { globalW = tw; globalH = th; }
        else if (rTotal >= targetRatio) { globalW = tw; globalH = tw / rTotal; }
        else { globalH = th; globalW = th * rTotal; }

        void PlaceTree(Node node, double x, double y, double w, double h)
        {
            if (node.Type == 'L') { place(node.Image!, x, y, w, h); return; }
            var left = node.Left!;
            var right = node.Right!;
            if (node.Type == 'H')
            {
                double wLeft = w * (left.R / node.R);
                PlaceTree(left, x, y, wLeft, h);
                PlaceTree(right, x + wLeft, y, w - wLeft, h);
            }
            else
            {
                double invL = 1.0 / left.R, invR = 1.0 / right.R;
                double hLeft = h * (invL / (invL + invR));
                PlaceTree(left, x, y, w, hLeft);
                PlaceTree(right, x, y + hLeft, w, h - hLeft);
            }
        }

        PlaceTree(bestTree, (tw - globalW) / 2, (th - globalH) / 2, globalW, globalH);
    }
}
