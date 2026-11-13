namespace WallCraft.Core.Geometry;

/// <summary>Un écran tel que l'API de fond d'écran de Windows le connaît : identifiant et rectangle (gauche, haut, droite, bas).</summary>
public sealed record WindowsMonitor(string Id, int Left, int Top, int Right, int Bottom);

public static class MonitorMatching
{
    /// <summary>
    /// Associe chaque image découpée à un écran Windows par recouvrement de rectangles (<c>match_monitors</c>).
    /// Retourne les paires (identifiant Windows, fichier) et les fichiers sans écran.
    /// </summary>
    public static (List<(string MonitorId, string Path)> Pairs, List<string> Unmatched) Match(
        IEnumerable<(MonitorInfo Monitor, string Path)> splitResults, IEnumerable<WindowsMonitor> windowsMonitors)
    {
        var pairs = new List<(string, string)>();
        var unmatched = new List<string>();
        var free = windowsMonitors.ToList();
        foreach (var (m, path) in splitResults)
        {
            var rect = (L: m.X, T: m.Y, R: m.X + m.Width, B: m.Y + m.Height);
            WindowsMonitor? best = null;
            long bestOverlap = -1;
            foreach (var wm in free) // max() de Python : le premier des ex æquo l'emporte
            {
                long o = Overlap(rect, wm);
                if (o > bestOverlap) { best = wm; bestOverlap = o; }
            }
            if (best is null || bestOverlap == 0)
            {
                unmatched.Add(path);
                continue;
            }
            free.Remove(best);
            pairs.Add((best.Id, path));
        }
        return (pairs, unmatched);

        static long Overlap((int L, int T, int R, int B) a, WindowsMonitor b)
        {
            long w = Math.Min(a.R, b.Right) - Math.Max(a.L, b.Left);
            long h = Math.Min(a.B, b.Bottom) - Math.Max(a.T, b.Top);
            return Math.Max(0, w) * Math.Max(0, h);
        }
    }
}
