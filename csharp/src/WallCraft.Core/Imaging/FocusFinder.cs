using WallCraft.Core.Model;

namespace WallCraft.Core.Imaging;

/// <summary>Rectangle d'un visage détecté, en pixels de l'image analysée.</summary>
public readonly record struct FaceBox(double X, double Y, double Width, double Height);

/// <summary>
/// Point d'intérêt pour le mode « Remplir » (portage de facefocus.py) : centre des visages pondéré par leur
/// taille, visé un peu au-dessus ; sinon centre de gravité des contours ramené vers le centre.
/// La détection des visages elle-même est fournie par la plateforme (FaceDetector de Windows).
/// </summary>
public static class FocusFinder
{
    public static FocusPoint? FromFaces(IReadOnlyCollection<FaceBox> faces, int width, int height)
    {
        if (faces.Count == 0) return null;
        double total = faces.Sum(f => f.Width * f.Height);
        if (total <= 0) return null;
        double cx = faces.Sum(f => (f.X + f.Width / 2) * f.Width * f.Height) / total;
        // Viser un peu au-dessus du centre des visages laisse de la place au-dessus des têtes.
        double cy = faces.Sum(f => (f.Y + f.Height * 0.4) * f.Width * f.Height) / total;
        return new FocusPoint(Math.Clamp(cx / width, 0.0, 1.0), Math.Clamp(cy / height, 0.0, 1.0));
    }

    /// <summary>
    /// Repli sans visage : contours d'une vignette de 160 px au plus, adoucis, puis centre de gravité rapproché
    /// du centre de 40 %. Proche de la version Python (le redimensionnement et le flou de Pillow ne sont pas
    /// reproduits au pixel près, l’écart reste sous 5 % de la largeur).
    /// </summary>
    public static FocusPoint FromDetail(byte[] gray, int width, int height)
    {
        var (small, w, h) = Downscale(gray, width, height, 160);
        var edges = FindEdges(small, w, h);
        var blurred = GaussianBlur(edges, w, h, 2.0);
        double total = 0, sx = 0, sy = 0;
        for (int i = 0; i < blurred.Length; i++)
        {
            byte v = blurred[i];
            if (v == 0) continue;
            total += v;
            sx += (i % w) * v;
            sy += (i / w) * v;
        }
        if (total <= 0) return FocusPoint.Center;
        double cx = sx / total / Math.Max(1, w - 1), cy = sy / total / Math.Max(1, h - 1);
        return new FocusPoint(0.5 + (cx - 0.5) * 0.6, 0.5 + (cy - 0.5) * 0.6);
    }

    /// <summary>Réduction par moyenne de zones, en gardant les proportions (comme <c>thumbnail</c>).</summary>
    internal static (byte[] Data, int Width, int Height) Downscale(byte[] gray, int width, int height, int maxSide)
    {
        if (width <= maxSide && height <= maxSide) return ((byte[])gray.Clone(), width, height);
        double scale = Math.Min((double)maxSide / width, (double)maxSide / height);
        int w = Math.Max(1, (int)Math.Round(width * scale)), h = Math.Max(1, (int)Math.Round(height * scale));
        var result = new byte[w * h];
        for (int y = 0; y < h; y++)
        {
            int y0 = y * height / h, y1 = Math.Max(y0 + 1, (y + 1) * height / h);
            for (int x = 0; x < w; x++)
            {
                int x0 = x * width / w, x1 = Math.Max(x0 + 1, (x + 1) * width / w);
                long sum = 0;
                for (int yy = y0; yy < y1; yy++)
                    for (int xx = x0; xx < x1; xx++) sum += gray[yy * width + xx];
                result[y * w + x] = (byte)((sum + (x1 - x0) * (y1 - y0) / 2) / ((x1 - x0) * (y1 - y0)));
            }
        }
        return (result, w, h);
    }

    /// <summary>Filtre FIND_EDGES de Pillow (noyau 3×3 : 8 au centre, −1 autour), bords recopiés.</summary>
    internal static byte[] FindEdges(byte[] src, int w, int h)
    {
        var dst = (byte[])src.Clone();
        for (int y = 1; y < h - 1; y++)
        {
            for (int x = 1; x < w - 1; x++)
            {
                int sum = 8 * src[y * w + x];
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                        if (dx != 0 || dy != 0) sum -= src[(y + dy) * w + x + dx];
                dst[y * w + x] = (byte)Math.Clamp(sum, 0, 255);
            }
        }
        return dst;
    }

    /// <summary>Flou gaussien séparable (écart type = rayon), bords prolongés.</summary>
    internal static byte[] GaussianBlur(byte[] src, int w, int h, double sigma)
    {
        int radius = (int)Math.Ceiling(sigma * 3);
        var kernel = new double[radius * 2 + 1];
        double norm = 0;
        for (int i = -radius; i <= radius; i++) norm += kernel[i + radius] = Math.Exp(-(i * i) / (2 * sigma * sigma));
        for (int i = 0; i < kernel.Length; i++) kernel[i] /= norm;

        var tmp = new double[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                double acc = 0;
                for (int k = -radius; k <= radius; k++) acc += kernel[k + radius] * src[y * w + Math.Clamp(x + k, 0, w - 1)];
                tmp[y * w + x] = acc;
            }
        var dst = new byte[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                double acc = 0;
                for (int k = -radius; k <= radius; k++) acc += kernel[k + radius] * tmp[Math.Clamp(y + k, 0, h - 1) * w + x];
                dst[y * w + x] = (byte)Math.Clamp((int)Math.Round(acc), 0, 255);
            }
        return dst;
    }
}
