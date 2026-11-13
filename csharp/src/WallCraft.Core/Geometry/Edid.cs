namespace WallCraft.Core.Geometry;

/// <summary>Lecture de la taille physique d'un écran dans son bloc EDID.</summary>
public static class Edid
{
    private static readonly byte[] Header = [0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00];

    /// <summary>
    /// Taille de la zone d'affichage en mm : premier descripteur de timing détaillé, sinon octets 21-22 (en cm).
    /// Null si le bloc est invalide ou ne donne pas de taille.
    /// </summary>
    public static (double WidthMm, double HeightMm)? ParseSizeMm(ReadOnlySpan<byte> edid)
    {
        if (edid.Length < 128 || !edid[..8].SequenceEqual(Header)) return null;
        var d = edid.Slice(54, 18);
        if (d[0] != 0 || d[1] != 0)
        {
            int w = d[12] | ((d[14] & 0xF0) << 4);
            int h = d[13] | ((d[14] & 0x0F) << 8);
            if (w > 50 && h > 50) return (w, h);
        }
        if (edid[21] != 0 && edid[22] != 0) return (edid[21] * 10.0, edid[22] * 10.0);
        return null;
    }

    /// <summary>Diagonale en pouces.</summary>
    public static double DiagonalInches(double widthMm, double heightMm) => Math.Sqrt(widthMm * widthMm + heightMm * heightMm) / 25.4;

    /// <summary>
    /// Applique une taille EDID à un écran : l'EDID décrit la dalle en paysage, on suit l'orientation réelle.
    /// </summary>
    public static void ApplySize(MonitorInfo m, (double WidthMm, double HeightMm)? size)
    {
        if (size is null) return;
        var (w, h) = size.Value;
        if ((m.Width < m.Height) != (w < h)) (w, h) = (h, w);
        m.WidthMm = w;
        m.HeightMm = h;
    }
}
