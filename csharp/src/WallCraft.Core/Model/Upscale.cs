namespace WallCraft.Core.Model;

public static class Upscale
{
    /// <summary>Seuil au-delà duquel l'image est visiblement floue sur l'écran.</summary>
    public const double LowResolutionThreshold = 1.3;

    /// <summary>Agrandissement subi par l'image dans la composition : 1 = pixel pour pixel, 2,5 = étirée 2,5 fois.</summary>
    public static double Factor(CompositionImage img)
    {
        double ow = img.OriginalWidth, oh = img.OriginalHeight;
        if (img.Angle % 180 == 90) (ow, oh) = (oh, ow);
        double srcW = Math.Max(1.0, ow * img.Crop.Width), srcH = Math.Max(1.0, oh * img.Crop.Height);
        return Math.Max((img.W ?? 0) / srcW, (img.H ?? 0) / srcH);
    }
}
