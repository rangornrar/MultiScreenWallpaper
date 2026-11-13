using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Graphics.Imaging;
using Windows.Storage;
using Windows.Storage.Streams;
using WallCraft.Core.Imaging;

namespace WallCraft.App.Services;

/// <summary>Lecture des images (JPG, PNG, WebP, BMP, TIFF…) par WIC, redressées selon l'EXIF et converties en sRGB.</summary>
public static class ImageDecoder
{
    /// <summary>Taille d'affichage de la vignette de travail (même valeur que PROXY_MAX_SIZE en Python).</summary>
    public const int ProxyMaxSize = 1024;

    private static async Task<IRandomAccessStream> OpenAsync(string path) =>
        await FileRandomAccessStream.OpenAsync(path, FileAccessMode.Read);

    /// <summary>Taille de l'image une fois redressée (largeur, hauteur).</summary>
    public static async Task<(int Width, int Height)> ReadSizeAsync(string path)
    {
        using var stream = await OpenAsync(path);
        var decoder = await BitmapDecoder.CreateAsync(stream);
        return ((int)decoder.OrientedPixelWidth, (int)decoder.OrientedPixelHeight);
    }

    /// <summary>Pixels RVBA redressés ; <paramref name="maxSide"/> réduit l'image (vignette de travail) sans la déformer.</summary>
    public static async Task<PixelBuffer> DecodeAsync(string path, int? maxSide = null)
    {
        using var stream = await OpenAsync(path);
        var decoder = await BitmapDecoder.CreateAsync(stream);
        var transform = new BitmapTransform();
        uint longest = Math.Max(decoder.PixelWidth, decoder.PixelHeight);
        if (maxSide is int max && longest > max)
        {
            // L'échelle s'applique à l'image avant redressement EXIF.
            double s = (double)max / longest;
            transform.ScaledWidth = (uint)Math.Max(1, Math.Round(decoder.PixelWidth * s));
            transform.ScaledHeight = (uint)Math.Max(1, Math.Round(decoder.PixelHeight * s));
            transform.InterpolationMode = BitmapInterpolationMode.Fant;
        }
        using var bitmap = await decoder.GetSoftwareBitmapAsync(
            BitmapPixelFormat.Rgba8, BitmapAlphaMode.Straight, transform,
            ExifOrientationMode.RespectExifOrientation, ColorManagementMode.ColorManageToSRgb);
        var bytes = new byte[bitmap.PixelWidth * bitmap.PixelHeight * 4];
        bitmap.CopyToBuffer(bytes.AsBuffer());
        return new PixelBuffer(bitmap.PixelWidth, bitmap.PixelHeight, bytes);
    }
}
