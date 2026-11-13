namespace WallCraft.Core.Imaging;

/// <summary>Miniatures de la bibliothèque, calculées depuis la vignette de travail.</summary>
public static class Thumbnail
{
    /// <summary>
    /// Réduit l'image pour qu'elle tienne dans <paramref name="maxWidth"/> × <paramref name="maxHeight"/> sans la déformer
    /// (comme <c>Image.thumbnail</c> : jamais agrandie). Chaque pixel est la moyenne de la zone source qu'il couvre.
    /// </summary>
    public static PixelBuffer Fit(PixelBuffer source, int maxWidth, int maxHeight)
    {
        double scale = Math.Min(1.0, Math.Min((double)maxWidth / source.Width, (double)maxHeight / source.Height));
        int w = Math.Max(1, (int)Math.Round(source.Width * scale));
        int h = Math.Max(1, (int)Math.Round(source.Height * scale));
        if (w == source.Width && h == source.Height) return source.Clone();

        var dst = new PixelBuffer(w, h);
        var s = source.Data;
        var d = dst.Data;
        for (int y = 0; y < h; y++)
        {
            int sy0 = y * source.Height / h, sy1 = Math.Max(sy0 + 1, (y + 1) * source.Height / h);
            for (int x = 0; x < w; x++)
            {
                int sx0 = x * source.Width / w, sx1 = Math.Max(sx0 + 1, (x + 1) * source.Width / w);
                long r = 0, g = 0, b = 0, a = 0;
                for (int yy = sy0; yy < sy1; yy++)
                {
                    int p = (yy * source.Width + sx0) * 4;
                    for (int xx = sx0; xx < sx1; xx++, p += 4)
                    {
                        // Moyenne pondérée par l'alpha : pas de liseré sombre autour des zones transparentes.
                        int alpha = s[p + 3];
                        r += s[p] * alpha;
                        g += s[p + 1] * alpha;
                        b += s[p + 2] * alpha;
                        a += alpha;
                    }
                }
                int count = (sy1 - sy0) * (sx1 - sx0);
                int o = (y * w + x) * 4;
                if (a > 0)
                {
                    d[o] = (byte)((r + a / 2) / a);
                    d[o + 1] = (byte)((g + a / 2) / a);
                    d[o + 2] = (byte)((b + a / 2) / a);
                }
                d[o + 3] = (byte)((a + count / 2) / count);
            }
        }
        return dst;
    }
}
