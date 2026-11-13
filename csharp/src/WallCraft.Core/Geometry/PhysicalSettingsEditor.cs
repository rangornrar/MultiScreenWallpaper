using System.Globalization;

namespace WallCraft.Core.Geometry;

/// <summary>Une ligne du tableau « Taille réelle » : textes saisis pour un écran.</summary>
public sealed record PhysicalRowInput(MonitorInfo Monitor, string WidthMm, string HeightMm, string OffsetYMm);

/// <summary>
/// Logique du dialogue « Taille réelle des écrans » (<c>PhysicalDialog</c> Python) sans interface :
/// valeurs initiales, diagonale affichée et conversion des saisies en <see cref="PhysicalSettings"/>.
/// </summary>
public static class PhysicalSettingsEditor
{
    /// <summary>Clé des réglages d'un écran : identifiant matériel, sinon nom Windows.</summary>
    public static string KeyFor(MonitorInfo m) => string.IsNullOrEmpty(m.HwId) ? m.Name : m.HwId;

    /// <summary>Nombre saisi (virgule ou point) ; null si ce n'en est pas un.</summary>
    public static double? ParseNumber(string? text) =>
        double.TryParse((text ?? "").Replace(',', '.').Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out double d) && double.IsFinite(d)
            ? d : null;

    /// <summary>Format <c>{:g}</c> de Python pour les valeurs courantes (12.5 → « 12.5 », 0 → « 0 »).</summary>
    public static string FormatG(double value) => value.ToString("G6", CultureInfo.InvariantCulture);

    public static string FormatBezel(PhysicalSettings settings) => FormatG(settings.BezelMm);

    /// <summary>Textes initiaux (largeur, hauteur, décalage) : correction de l'utilisateur, sinon taille EDID.</summary>
    public static (string WidthMm, string HeightMm, string OffsetYMm) InitialRow(MonitorInfo m, PhysicalSettings settings)
    {
        var o = settings.Overrides.GetValueOrDefault(KeyFor(m));
        double? w = o?.WidthMm ?? m.WidthMm, h = o?.HeightMm ?? m.HeightMm;
        static string Mm(double? v) => v is double d && d != 0 ? d.ToString("F0", CultureInfo.InvariantCulture) : "";
        return (Mm(w), Mm(h), FormatG(o?.OffsetYMm ?? 0.0));
    }

    /// <summary>Diagonale « 23.8″ », ou null si largeur ou hauteur ne sont pas des nombres.</summary>
    public static string? DiagonalText(string widthText, string heightText)
    {
        if (ParseNumber(widthText) is not double w || ParseNumber(heightText) is not double h) return null;
        return Edid.DiagonalInches(w, h).ToString("F1", CultureInfo.InvariantCulture) + "″";
    }

    /// <summary>
    /// Nouveaux réglages (copie ; <paramref name="current"/> n'est pas modifié). Une taille n'est enregistrée que si elle
    /// est plausible (50 à 3000 mm) et diffère de celle lue dans l'écran ; décalage borné à ±1000 mm, espace à 0–200 mm.
    /// </summary>
    public static PhysicalSettings Apply(PhysicalSettings current, bool enabled, string bezelText, IEnumerable<PhysicalRowInput> rows)
    {
        var s = PhysicalSettings.FromJson(current.ToJson());
        s.Enabled = enabled;
        s.BezelMm = Math.Max(0.0, Math.Min(200.0, ParseNumber(bezelText) ?? 0.0));
        foreach (var row in rows)
        {
            var m = row.Monitor;
            var entry = new MonitorOverride();
            bool any = false;
            double? w = ParseNumber(row.WidthMm), h = ParseNumber(row.HeightMm);
            if (w is double wv && h is double hv && wv != 0 && hv != 0 && wv >= 50 && wv <= 3000 && hv >= 50 && hv <= 3000
                && (m.WidthMm is not double mw || mw == 0 || Math.Abs(wv - mw) > 0.5 || Math.Abs(hv - (m.HeightMm ?? 0)) > 0.5))
            {
                entry.WidthMm = wv;
                entry.HeightMm = hv;
                any = true;
            }
            double offset = ParseNumber(row.OffsetYMm) ?? 0.0;
            if (offset != 0)
            {
                entry.OffsetYMm = Math.Max(-1000.0, Math.Min(1000.0, offset));
                any = true;
            }
            string key = KeyFor(m);
            if (any) s.Overrides[key] = entry;
            else s.Overrides.Remove(key);
        }
        return s;
    }
}
