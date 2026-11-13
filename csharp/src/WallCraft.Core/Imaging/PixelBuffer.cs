namespace WallCraft.Core.Imaging;

/// <summary>Image en mémoire, 4 octets par pixel dans l'ordre R, V, B, A (alpha non prémultiplié), lignes contiguës.</summary>
public sealed class PixelBuffer
{
    public PixelBuffer(int width, int height, byte[]? data = null)
    {
        if (width <= 0 || height <= 0) throw new ArgumentOutOfRangeException(nameof(width), "taille nulle");
        Width = width;
        Height = height;
        Data = data ?? new byte[checked(width * height * 4)];
        if (Data.Length != width * height * 4) throw new ArgumentException("taille du tampon incohérente", nameof(data));
    }

    public int Width { get; }
    public int Height { get; }
    public byte[] Data { get; }

    public PixelBuffer Clone() => new(Width, Height, (byte[])Data.Clone());

    /// <summary>Niveaux de gris « L » de Pillow : (R×19595 + V×38470 + B×7471 + 0x8000) >> 16.</summary>
    public static byte Luma(byte r, byte g, byte b) => (byte)((r * 19595 + g * 38470 + b * 7471 + 0x8000) >> 16);

    public byte[] ToGray()
    {
        var gray = new byte[Width * Height];
        for (int i = 0, p = 0; i < gray.Length; i++, p += 4) gray[i] = Luma(Data[p], Data[p + 1], Data[p + 2]);
        return gray;
    }

    /// <summary>
    /// Rotation d'un multiple de 90° dans le sens trigonométrique, comme <c>Image.rotate(angle, expand=True)</c>
    /// de Pillow (l'angle des images WallCraft suit cette convention).
    /// </summary>
    public PixelBuffer Rotate(int angle)
    {
        angle = ((angle % 360) + 360) % 360;
        if (angle % 90 != 0) throw new ArgumentException("angle multiple de 90° attendu", nameof(angle));
        if (angle == 0) return Clone();
        int w = Width, h = Height;
        bool quarter = angle != 180;
        var dst = new PixelBuffer(quarter ? h : w, quarter ? w : h);
        var s = Data;
        var d = dst.Data;
        int dw = dst.Width;
        for (int y = 0; y < h; y++)
        {
            for (int x = 0; x < w; x++)
            {
                int nx, ny;
                switch (angle)
                {
                    case 90: nx = y; ny = w - 1 - x; break;          // anti-horaire
                    case 180: nx = w - 1 - x; ny = h - 1 - y; break;
                    default: nx = h - 1 - y; ny = x; break;           // 270 = horaire
                }
                Buffer.BlockCopy(s, (y * w + x) * 4, d, (ny * dw + nx) * 4, 4);
            }
        }
        return dst;
    }

    /// <summary>Morceau (gauche, haut, droite, bas) en pixels, borné à l'image.</summary>
    public PixelBuffer Crop(int left, int top, int right, int bottom)
    {
        left = Math.Clamp(left, 0, Width - 1); right = Math.Clamp(right, left + 1, Width);
        top = Math.Clamp(top, 0, Height - 1); bottom = Math.Clamp(bottom, top + 1, Height);
        var dst = new PixelBuffer(right - left, bottom - top);
        for (int y = 0; y < dst.Height; y++)
            Buffer.BlockCopy(Data, ((top + y) * Width + left) * 4, dst.Data, y * dst.Width * 4, dst.Width * 4);
        return dst;
    }

    /// <summary>Copie en B, V, R, A prémultiplié (format attendu par Direct2D / Win2D).</summary>
    public byte[] ToBgraPremultiplied()
    {
        var outData = new byte[Data.Length];
        for (int p = 0; p < Data.Length; p += 4)
        {
            int a = Data[p + 3];
            outData[p] = (byte)((Data[p + 2] * a + 127) / 255);
            outData[p + 1] = (byte)((Data[p + 1] * a + 127) / 255);
            outData[p + 2] = (byte)((Data[p] * a + 127) / 255);
            outData[p + 3] = (byte)a;
        }
        return outData;
    }
}
