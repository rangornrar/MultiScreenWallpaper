using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Graphics.Imaging;
using Windows.Media.FaceAnalysis;
using WallCraft.Core.Imaging;
using WallCraft.Core.Model;

namespace WallCraft.App.Services;

/// <summary>
/// Point d'intérêt d'une image pour le mode « Remplir » : visages détectés par Windows (FaceDetector),
/// sinon zone la plus détaillée. Remplace OpenCV de la version Python.
/// </summary>
public static class FaceFocus
{
    private static readonly SemaphoreSlim Gate = new(1, 1);
    private static FaceDetector? _detector;
    private static bool _unavailable;

    private static async Task<FaceDetector?> DetectorAsync()
    {
        if (_detector is not null || _unavailable) return _detector;
        try
        {
            if (!FaceDetector.IsSupported) { _unavailable = true; return null; }
            _detector = await FaceDetector.CreateAsync();
        }
        catch (Exception)
        {
            _unavailable = true;
        }
        return _detector;
    }

    /// <summary>Calcule le point d'intérêt sur la vignette de travail (orientation d'origine, déjà redressée).</summary>
    public static async Task<FocusPoint> FindAsync(PixelBuffer proxy)
    {
        var gray = proxy.ToGray();
        await Gate.WaitAsync();
        try
        {
            var detector = await DetectorAsync();
            if (detector is not null)
            {
                try
                {
                    uint minSide = (uint)Math.Max(24, Math.Min(proxy.Width, proxy.Height) * 0.06);
                    try { detector.MinDetectableFaceSize = new BitmapSize { Width = minSide, Height = minSide }; }
                    catch (ArgumentException) { /* hors des bornes du détecteur : on garde sa valeur */ }
                    using var bitmap = new SoftwareBitmap(BitmapPixelFormat.Gray8, proxy.Width, proxy.Height);
                    bitmap.CopyFromBuffer(gray.AsBuffer());
                    var faces = await detector.DetectFacesAsync(bitmap);
                    var boxes = faces.Select(f => new FaceBox(f.FaceBox.X, f.FaceBox.Y, f.FaceBox.Width, f.FaceBox.Height)).ToList();
                    if (FocusFinder.FromFaces(boxes, proxy.Width, proxy.Height) is FocusPoint p) return p;
                }
                catch (Exception)
                {
                    // Détection impossible sur cette image : repli sur les contours.
                }
            }
        }
        finally
        {
            Gate.Release();
        }
        return FocusFinder.FromDetail(gray, proxy.Width, proxy.Height);
    }
}
