namespace WallCraft.Core.Imaging;

/// <summary>
/// Retouches identiques à <c>PIL.ImageEnhance</c> (Brightness, Contrast, Color) : même image dégénérée,
/// même mélange <c>Image.blend</c> en flottant 32 bits avec troncature, l'alpha est conservé.
/// Le flou est laissé au moteur de rendu (Win2D).
/// </summary>
public static class Filters
{
    /// <summary>Applique dans l'ordre de la version Python : luminosité, contraste, saturation. Ne modifie pas <paramref name="source"/>.</summary>
    public static PixelBuffer Apply(PixelBuffer source, double brightness, double contrast, double saturation)
    {
        var img = source;
        if (brightness != 1.0) img = Brightness(img, brightness);
        if (contrast != 1.0) img = Contrast(img, contrast);
        if (saturation != 1.0) img = Color(img, saturation);
        return ReferenceEquals(img, source) ? source.Clone() : img;
    }

    public static PixelBuffer Brightness(PixelBuffer img, double factor)
    {
        var d = img.Data;
        var degenerate = new byte[d.Length];
        for (int p = 3; p < d.Length; p += 4) degenerate[p] = d[p]; // noir, alpha de l'image
        return Blend(img, degenerate, factor);
    }

    public static PixelBuffer Contrast(PixelBuffer img, double factor)
    {
        var gray = img.ToGray();
        long sum = 0;
        foreach (var v in gray) sum += v;
        double mean = (double)sum / gray.Length;
        byte m = (byte)(int)(mean + 0.5);
        var d = img.Data;
        var degenerate = new byte[d.Length];
        for (int p = 0; p < d.Length; p += 4)
        {
            degenerate[p] = degenerate[p + 1] = degenerate[p + 2] = m;
            degenerate[p + 3] = d[p + 3];
        }
        return Blend(img, degenerate, factor);
    }

    public static PixelBuffer Color(PixelBuffer img, double factor)
    {
        var d = img.Data;
        var degenerate = new byte[d.Length];
        for (int p = 0; p < d.Length; p += 4)
        {
            byte l = PixelBuffer.Luma(d[p], d[p + 1], d[p + 2]);
            degenerate[p] = degenerate[p + 1] = degenerate[p + 2] = l;
            degenerate[p + 3] = d[p + 3];
        }
        return Blend(img, degenerate, factor);
    }

    /// <summary><c>Image.blend(degenerate, image, alpha)</c> de Pillow (Blend.c).</summary>
    private static PixelBuffer Blend(PixelBuffer img, byte[] degenerate, double factor)
    {
        float alpha = (float)factor;
        var src = img.Data;
        var outData = new byte[src.Length];
        if (alpha >= 0 && alpha <= 1.0f)
        {
            for (int i = 0; i < src.Length; i++)
                outData[i] = (byte)(int)(degenerate[i] + alpha * (src[i] - degenerate[i]));
        }
        else
        {
            for (int i = 0; i < src.Length; i++)
            {
                float temp = degenerate[i] + alpha * (src[i] - degenerate[i]);
                outData[i] = temp <= 0.0f ? (byte)0 : temp >= 255.0f ? (byte)255 : (byte)temp;
            }
        }
        return new PixelBuffer(img.Width, img.Height, outData);
    }
}
