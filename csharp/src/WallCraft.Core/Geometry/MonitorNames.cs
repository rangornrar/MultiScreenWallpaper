using System.Globalization;
using WallCraft.Core.Layout;

namespace WallCraft.Core.Geometry;

/// <summary>Mots utilisés pour nommer les écrans, dans la langue de l'interface.</summary>
public sealed record PositionWords(string Left, string Center, string Right, string Top, string Bottom, string ScreenFormat)
{
    public static readonly PositionWords French = new("Gauche", "Centre", "Droite", "Haut", "Bas", "Écran {0}");
    public static readonly PositionWords English = new("Left", "Center", "Right", "Top", "Bottom", "Screen {0}");
}

/// <summary>Noms lisibles des écrans : « Gauche · Philips 23″ » plutôt que <c>\\.\DISPLAY2</c>.</summary>
public static class MonitorNames
{
    /// <summary>Codes fabricant PNP (3 lettres en tête de l'identifiant matériel) les plus courants.</summary>
    public static readonly IReadOnlyDictionary<string, string> Vendors = new Dictionary<string, string>
    {
        ["ACR"] = "Acer", ["AOC"] = "AOC", ["APP"] = "Apple", ["AUO"] = "AUO", ["AUS"] = "ASUS", ["BNQ"] = "BenQ", ["BOE"] = "BOE",
        ["CMN"] = "Innolux", ["DEL"] = "Dell", ["EIZ"] = "EIZO", ["ENC"] = "EIZO", ["GBT"] = "Gigabyte", ["GSM"] = "LG", ["HKC"] = "HKC",
        ["HPN"] = "HP", ["HWP"] = "HP", ["IVM"] = "iiyama", ["KOS"] = "KOORUI", ["LEN"] = "Lenovo", ["LGD"] = "LG", ["MEI"] = "Panasonic",
        ["MSI"] = "MSI", ["NEC"] = "NEC", ["PHL"] = "Philips", ["SAM"] = "Samsung", ["SDC"] = "Samsung", ["SHP"] = "Sharp",
        ["SNY"] = "Sony", ["VSC"] = "ViewSonic", ["XMI"] = "Xiaomi",
    };

    public static string Vendor(MonitorInfo m)
    {
        string hw = m.HwId ?? "";
        string code = hw.Contains('#') && hw.Length >= 3 ? hw[..3].ToUpperInvariant() : "";
        if (code.Length == 0 || !code.All(char.IsLetter)) return "";
        return Vendors.GetValueOrDefault(code, code);
    }

    public static string FormatInches(double widthMm, double heightMm, string decimalSeparator = ",")
    {
        double d = PythonCompat.Round(Edid.DiagonalInches(widthMm, heightMm), 1);
        string text = d == Math.Truncate(d)
            ? d.ToString("F0", CultureInfo.InvariantCulture)
            : d.ToString("F1", CultureInfo.InvariantCulture).Replace(".", decimalSeparator);
        return text + "″";
    }

    /// <summary>
    /// Noms dans l'ordre de <paramref name="monitors"/>. Les écrans en ligne (2 ou 3) sont nommés
    /// Gauche/Centre/Droite, deux écrans empilés Haut/Bas, sinon numérotés de gauche à droite.
    /// </summary>
    public static List<string> Labels(IReadOnlyList<MonitorInfo> monitors, PositionWords words, string decimalSeparator = ",")
    {
        IntRect Rect(MonitorInfo m) => m.Canvas ?? m.DesktopRect;
        int n = monitors.Count;
        var order = Enumerable.Range(0, n).OrderBy(i => Rect(monitors[i]).X).ThenBy(i => Rect(monitors[i]).Y).ToList();
        var rects = order.Select(i => Rect(monitors[i])).ToList();
        bool inRow = Enumerable.Range(0, Math.Max(0, n - 1)).All(k => rects[k].X + rects[k].Width <= rects[k + 1].X + 1);
        var orderV = Enumerable.Range(0, n).OrderBy(i => Rect(monitors[i]).Y).ThenBy(i => Rect(monitors[i]).X).ToList();
        var rectsV = orderV.Select(i => Rect(monitors[i])).ToList();
        bool inCol = Enumerable.Range(0, Math.Max(0, n - 1)).All(k => rectsV[k].Y + rectsV[k].Height <= rectsV[k + 1].Y + 1);

        var positions = new Dictionary<int, string>();
        if (n >= 2 && n <= 3 && inRow)
        {
            string[] names = n == 2 ? [words.Left, words.Right] : [words.Left, words.Center, words.Right];
            for (int k = 0; k < n; k++) positions[order[k]] = names[k];
        }
        else if (n == 2 && inCol)
        {
            positions[orderV[0]] = words.Top;
            positions[orderV[1]] = words.Bottom;
        }
        else if (n > 1)
        {
            for (int k = 0; k < n; k++) positions[order[k]] = string.Format(CultureInfo.InvariantCulture, words.ScreenFormat, k + 1);
        }

        var labels = new List<string>(n);
        for (int i = 0; i < n; i++)
        {
            var m = monitors[i];
            string vendor = Vendor(m);
            string size = m.WidthMm is double w && w != 0 && m.HeightMm is double h && h != 0 ? FormatInches(w, h, decimalSeparator) : "";
            string detail = string.Join(" ", new[] { vendor, size }.Where(p => p.Length > 0));
            if (detail.Length == 0) detail = $"{m.Width} × {m.Height}";
            labels.Add(positions.TryGetValue(i, out var pos) ? $"{pos} · {detail}" : detail);
        }
        return labels;
    }
}
