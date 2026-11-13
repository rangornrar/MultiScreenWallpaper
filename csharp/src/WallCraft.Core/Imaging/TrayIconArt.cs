namespace WallCraft.Core.Imaging;

/// <summary>
/// Icône de la zone de notification (<c>tray_icon_image</c> Python) : trois écrans colorés sur un pied, dessinés
/// en code avec lissage, puis encodés en fichier .ico (images 32 bits non compressées).
/// </summary>
public static class TrayIconArt
{
    public static readonly int[] Sizes = [16, 20, 24, 32, 48, 64];

    private static readonly (byte R, byte G, byte B)[] ScreenColors = [(138, 180, 248), (120, 212, 160), (255, 196, 110)];
    private static readonly (byte R, byte G, byte B) StandColor = (200, 210, 225);

    /// <summary>Formes du dessin de référence en 64 px : (x0, y0, x1, y1, rayon, couleur).</summary>
    private static IEnumerable<(double X0, double Y0, double X1, double Y1, double Radius, (byte R, byte G, byte B) Color)> Shapes()
    {
        for (int i = 0; i < ScreenColors.Length; i++)
        {
            double x0 = 4 + i * 19;
            yield return (x0, 18, x0 + 17, 40, 3, ScreenColors[i]);
        }
        yield return (28, 42, 36, 50, 0, StandColor);
        yield return (20, 50, 44, 54, 0, StandColor);
    }

    private static bool Inside(double px, double py, (double X0, double Y0, double X1, double Y1, double Radius, (byte, byte, byte) _) s)
    {
        if (px < s.X0 || px > s.X1 || py < s.Y0 || py > s.Y1) return false;
        double r = s.Radius;
        if (r <= 0) return true;
        double cx = Math.Clamp(px, s.X0 + r, s.X1 - r), cy = Math.Clamp(py, s.Y0 + r, s.Y1 - r);
        double dx = px - cx, dy = py - cy;
        return dx * dx + dy * dy <= r * r;
    }

    /// <summary>Pixels RVBA (non prémultipliés) de l'icône en <paramref name="size"/>×<paramref name="size"/>, lissés par suréchantillonnage 4×4.</summary>
    public static PixelBuffer Render(int size)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(size, 1);
        const int ss = 4;
        var shapes = Shapes().ToList();
        var data = new byte[size * size * 4];
        double unit = 64.0 / size;
        for (int y = 0; y < size; y++)
        {
            for (int x = 0; x < size; x++)
            {
                double r = 0, g = 0, b = 0;
                int hits = 0;
                for (int sy = 0; sy < ss; sy++)
                {
                    for (int sx = 0; sx < ss; sx++)
                    {
                        double px = (x + (sx + 0.5) / ss) * unit, py = (y + (sy + 0.5) / ss) * unit;
                        foreach (var s in shapes)
                        {
                            if (!Inside(px, py, s)) continue;
                            r += s.Color.R; g += s.Color.G; b += s.Color.B;
                            hits++;
                            break;
                        }
                    }
                }
                int o = (y * size + x) * 4;
                if (hits == 0) continue;
                data[o] = (byte)Math.Round(r / hits);
                data[o + 1] = (byte)Math.Round(g / hits);
                data[o + 2] = (byte)Math.Round(b / hits);
                data[o + 3] = (byte)Math.Round(255.0 * hits / (ss * ss));
            }
        }
        return new PixelBuffer(size, size, data);
    }

    /// <summary>Fichier .ico complet (une image BMP 32 bits par taille de <see cref="Sizes"/>).</summary>
    public static byte[] CreateIco(IReadOnlyList<int>? sizes = null)
    {
        sizes ??= Sizes;
        var images = sizes.Select(s => EncodeDib(Render(s))).ToList();
        using var ms = new MemoryStream();
        using var w = new BinaryWriter(ms);
        w.Write((ushort)0);            // réservé
        w.Write((ushort)1);            // type : icône
        w.Write((ushort)sizes.Count);
        int offset = 6 + 16 * sizes.Count;
        for (int i = 0; i < sizes.Count; i++)
        {
            int s = sizes[i];
            w.Write((byte)(s >= 256 ? 0 : s));
            w.Write((byte)(s >= 256 ? 0 : s));
            w.Write((byte)0);          // pas de palette
            w.Write((byte)0);
            w.Write((ushort)1);        // plans
            w.Write((ushort)32);       // bits par pixel
            w.Write(images[i].Length);
            w.Write(offset);
            offset += images[i].Length;
        }
        foreach (var img in images) w.Write(img);
        w.Flush();
        return ms.ToArray();
    }

    /// <summary>Image d'icône au format DIB : en-tête BITMAPINFOHEADER (hauteur doublée), pixels BGRA de bas en haut, masque ET.</summary>
    private static byte[] EncodeDib(PixelBuffer p)
    {
        int size = p.Width;
        int maskStride = ((size + 31) / 32) * 4;
        using var ms = new MemoryStream();
        using var w = new BinaryWriter(ms);
        w.Write(40);                   // taille de l'en-tête
        w.Write(size);
        w.Write(size * 2);             // couleur + masque
        w.Write((ushort)1);
        w.Write((ushort)32);
        w.Write(0);                    // BI_RGB
        w.Write(size * size * 4 + maskStride * size);
        w.Write(0); w.Write(0); w.Write(0); w.Write(0);
        var rgba = p.Data;
        for (int y = size - 1; y >= 0; y--)
        {
            for (int x = 0; x < size; x++)
            {
                int o = (y * size + x) * 4;
                w.Write(rgba[o + 2]); w.Write(rgba[o + 1]); w.Write(rgba[o]); w.Write(rgba[o + 3]);
            }
        }
        // Masque ET : 1 = transparent (utilisé seulement par les anciens affichages sans alpha).
        for (int y = size - 1; y >= 0; y--)
        {
            var row = new byte[maskStride];
            for (int x = 0; x < size; x++)
                if (rgba[(y * size + x) * 4 + 3] == 0) row[x / 8] |= (byte)(0x80 >> (x % 8));
            w.Write(row);
        }
        w.Flush();
        return ms.ToArray();
    }
}
