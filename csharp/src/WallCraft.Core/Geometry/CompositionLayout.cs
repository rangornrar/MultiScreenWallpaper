using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using WallCraft.Core.Layout;

namespace WallCraft.Core.Geometry;

/// <summary>
/// Où se trouve chaque écran dans la composition (portage de display_geometry.py).
/// Mode « pixels » : la grille du bureau Windows. Mode « taille réelle » : chaque écran à sa taille
/// physique, voisins accolés avec l'espace des bordures, à l'échelle de l'écran le plus dense.
/// </summary>
public static class CompositionLayout
{
    /// <summary>Densité d'un écran 24″ 1080p, utilisée quand la taille physique est inconnue.</summary>
    public const double DefaultMmPerPx = 0.2715;

    private static (double W, double H) SizeMm(MonitorInfo m, PhysicalSettings settings, double fallbackDensity)
    {
        var o = settings.OverrideFor(m);
        double? w = NonZero(o?.WidthMm) ?? NonZero(m.WidthMm);
        double? h = NonZero(o?.HeightMm) ?? NonZero(m.HeightMm);
        if (w is null || h is null) return (m.Width * fallbackDensity, m.Height * fallbackDensity);
        return (w.Value, h.Value);

        static double? NonZero(double? v) => v is double d && d != 0 ? d : null;
    }

    /// <summary>Côté par lequel <paramref name="b"/> touche <paramref name="a"/> dans le bureau virtuel.</summary>
    internal static string? Neighbour(MonitorInfo a, MonitorInfo b)
    {
        int ax1 = a.X + a.Width, ay1 = a.Y + a.Height;
        int bx1 = b.X + b.Width, by1 = b.Y + b.Height;
        bool vOverlap = Math.Min(ay1, by1) - Math.Max(a.Y, b.Y) > 0;
        bool hOverlap = Math.Min(ax1, bx1) - Math.Max(a.X, b.X) > 0;
        if (vOverlap && Math.Abs(b.X - ax1) <= 2) return "right";
        if (vOverlap && Math.Abs(bx1 - a.X) <= 2) return "left";
        if (hOverlap && Math.Abs(b.Y - ay1) <= 2) return "below";
        if (hOverlap && Math.Abs(by1 - a.Y) <= 2) return "above";
        return null;
    }

    /// <summary>Position et taille (x, y, w, h) en mm de chaque écran (<c>physical_positions</c>).</summary>
    public static List<(double X, double Y, double W, double H)> PhysicalPositions(IReadOnlyList<MonitorInfo> monitors, PhysicalSettings settings)
    {
        var known = monitors.Where(m => m.WidthMm is double w && w != 0).Select(m => m.WidthMm!.Value / m.Width).OrderBy(v => v).ToList();
        double density = known.Count > 0 ? known[known.Count / 2] : DefaultMmPerPx;
        var sizes = monitors.Select(m => SizeMm(m, settings, density)).ToList();
        if (monitors.Count == 0) return [];

        var pos = new (double X, double Y)?[monitors.Count];
        int root = Enumerable.Range(0, monitors.Count).MinBy(i => ((long)Math.Abs(monitors[i].X) + Math.Abs(monitors[i].Y), i));
        pos[root] = (0.0, 0.0);
        var queue = new Queue<int>();
        queue.Enqueue(root);
        double gap = settings.BezelMm;
        while (queue.Count > 0)
        {
            int i = queue.Dequeue();
            var (ax, ay) = pos[i]!.Value;
            var (aw, ah) = sizes[i];
            for (int j = 0; j < monitors.Count; j++)
            {
                if (pos[j] is not null) continue;
                var side = Neighbour(monitors[i], monitors[j]);
                if (side is null) continue;
                var (bw, bh) = sizes[j];
                pos[j] = side switch
                {
                    "right" => (ax + aw + gap, ay + (ah - bh) / 2),
                    "left" => (ax - gap - bw, ay + (ah - bh) / 2),
                    "below" => (ax + (aw - bw) / 2, ay + ah + gap),
                    _ => (ax + (aw - bw) / 2, ay - gap - bh),
                };
                queue.Enqueue(j);
            }
        }
        // Écrans non contigus : position proportionnelle à celle du bureau virtuel
        for (int j = 0; j < monitors.Count; j++)
            pos[j] ??= ((monitors[j].X - monitors[root].X) * density, (monitors[j].Y - monitors[root].Y) * density);

        var result = new List<(double, double, double, double)>(monitors.Count);
        for (int j = 0; j < monitors.Count; j++)
        {
            var o = settings.OverrideFor(monitors[j]);
            result.Add((pos[j]!.Value.X + (o?.OffsetXMm ?? 0.0), pos[j]!.Value.Y + (o?.OffsetYMm ?? 0.0), sizes[j].W, sizes[j].H));
        }
        return result;
    }

    /// <summary>
    /// Calcule <see cref="MonitorInfo.Canvas"/> pour chaque écran et retourne la taille de la composition (<c>apply_layout</c>).
    /// </summary>
    public static (int Width, int Height) Apply(IReadOnlyList<MonitorInfo> monitors, PhysicalSettings? settings = null)
    {
        if (monitors.Count == 0) return (1920, 1080);
        settings ??= new PhysicalSettings();
        if (!settings.Enabled)
        {
            int x0 = monitors.Min(m => m.X), y0 = monitors.Min(m => m.Y);
            int x1 = monitors.Max(m => m.X + m.Width), y1 = monitors.Max(m => m.Y + m.Height);
            foreach (var m in monitors) m.Canvas = new IntRect(m.X - x0, m.Y - y0, m.Width, m.Height);
            return (x1 - x0, y1 - y0);
        }

        var rects = PhysicalPositions(monitors, settings);
        double scale = monitors.Zip(rects).Max(p => p.First.Width / p.Second.W); // px de composition par mm
        double mx0 = rects.Min(r => r.X), my0 = rects.Min(r => r.Y);
        double mx1 = rects.Max(r => r.X + r.W), my1 = rects.Max(r => r.Y + r.H);
        for (int i = 0; i < monitors.Count; i++)
        {
            var (x, y, w, h) = rects[i];
            int cx = (int)PythonCompat.RoundToInt((x - mx0) * scale), cy = (int)PythonCompat.RoundToInt((y - my0) * scale);
            monitors[i].Canvas = new IntRect(cx, cy,
                (int)PythonCompat.RoundToInt((x + w - mx0) * scale) - cx,
                (int)PythonCompat.RoundToInt((y + h - my0) * scale) - cy);
        }
        return ((int)Math.Ceiling((mx1 - mx0) * scale), (int)Math.Ceiling((my1 - my0) * scale));
    }

    /// <summary>
    /// Empreinte d'une configuration d'écrans (<c>layout_signature</c>) : identique à celle de Python, donc les fonds
    /// mémorisés par la version Python sont retrouvés.
    /// </summary>
    public static string Signature(IEnumerable<MonitorInfo> monitors)
    {
        var items = monitors.Select(m => (m.Name, m.X, m.Y, m.Width, m.Height))
            .OrderBy(t => t.Name, CodePointComparer.Instance).ThenBy(t => t.X).ThenBy(t => t.Y).ThenBy(t => t.Width).ThenBy(t => t.Height);
        var sb = new StringBuilder("[");
        bool first = true;
        foreach (var t in items)
        {
            if (!first) sb.Append(", ");
            first = false;
            sb.Append('[').Append(Json.PythonDumpsString(t.Name)).Append(", ")
              .Append(t.X.ToString(CultureInfo.InvariantCulture)).Append(", ")
              .Append(t.Y.ToString(CultureInfo.InvariantCulture)).Append(", ")
              .Append(t.Width.ToString(CultureInfo.InvariantCulture)).Append(", ")
              .Append(t.Height.ToString(CultureInfo.InvariantCulture)).Append(']');
        }
        sb.Append(']');
        return Convert.ToHexStringLower(SHA1.HashData(Encoding.UTF8.GetBytes(sb.ToString())))[..16];
    }

    /// <summary>
    /// Rectangle (gauche, haut, droite, bas) à découper dans l'image composée pour chaque écran
    /// (<c>split_wallpaper_by_monitors</c>), borné à l'image. Null si l'écran ne reçoit rien.
    /// </summary>
    public static List<(int Left, int Top, int Right, int Bottom)?> SplitBoxes(IReadOnlyList<MonitorInfo> monitors, int imageWidth, int imageHeight)
    {
        if (monitors.Count == 0) throw new InvalidOperationException("Aucun moniteur détecté.");
        List<IntRect> rects;
        int compW, compH;
        if (monitors.All(m => m.Canvas is not null))
        {
            rects = monitors.Select(m => m.Canvas!.Value).ToList();
            compW = rects.Max(r => r.Right);
            compH = rects.Max(r => r.Bottom);
        }
        else
        {
            int x0 = monitors.Min(m => m.X), y0 = monitors.Min(m => m.Y);
            rects = monitors.Select(m => new IntRect(m.X - x0, m.Y - y0, m.Width, m.Height)).ToList();
            compW = monitors.Max(m => m.X + m.Width) - x0;
            compH = monitors.Max(m => m.Y + m.Height) - y0;
        }
        double rx = (double)imageWidth / compW, ry = (double)imageHeight / compH;
        var boxes = new List<(int, int, int, int)?>(monitors.Count);
        foreach (var r in rects)
        {
            int l = Clamp(PythonCompat.RoundToInt(r.X * rx), imageWidth), t = Clamp(PythonCompat.RoundToInt(r.Y * ry), imageHeight);
            int rr = Clamp(PythonCompat.RoundToInt(r.Right * rx), imageWidth), b = Clamp(PythonCompat.RoundToInt(r.Bottom * ry), imageHeight);
            boxes.Add(rr <= l || b <= t ? null : (l, t, rr, b));
        }
        return boxes;

        static int Clamp(long v, int max) => (int)Math.Max(0, Math.Min(v, max));
    }
}

/// <summary>Comparaison par point de code Unicode, comme les chaînes Python (et non par unité UTF-16).</summary>
internal sealed class CodePointComparer : IComparer<string>
{
    public static readonly CodePointComparer Instance = new();

    public int Compare(string? x, string? y)
    {
        if (ReferenceEquals(x, y)) return 0;
        if (x is null) return -1;
        if (y is null) return 1;
        var ex = x.EnumerateRunes();
        var ey = y.EnumerateRunes();
        while (true)
        {
            bool hx = ex.MoveNext(), hy = ey.MoveNext();
            if (!hx || !hy) return hx == hy ? 0 : hx ? 1 : -1;
            int c = ex.Current.Value.CompareTo(ey.Current.Value);
            if (c != 0) return c;
        }
    }
}
