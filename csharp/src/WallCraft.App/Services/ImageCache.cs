using Microsoft.Graphics.Canvas;
using Windows.Graphics.DirectX;
using WallCraft.Core.Imaging;
using WallCraft.Core.Model;

namespace WallCraft.App.Services;

/// <summary>
/// Vignettes de travail (<see cref="ImageDecoder.ProxyMaxSize"/> px de côté) des images de la composition, leur point
/// d'intérêt et leurs versions GPU (Win2D) retouchées et tournées. Toutes les méthodes s'appellent depuis le fil de
/// l'interface ; le décodage et la détection de visages tournent en arrière-plan.
/// </summary>
public sealed class ImageCache
{
    private readonly Dictionary<string, Task<Proxy>> _loads = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, Proxy> _proxies = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, Task<FocusPoint>> _focus = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, CanvasBitmap> _bitmaps = new(StringComparer.Ordinal);
    private readonly HashSet<string> _usedThisFrame = new(StringComparer.Ordinal);

    /// <summary>Taille de l'image d'origine (redressée selon l'EXIF) et vignette de travail.</summary>
    public sealed record Proxy(int Width, int Height, PixelBuffer Pixels);

    /// <summary>Une vignette vient d'être chargée : redessiner.</summary>
    public event EventHandler<string>? ProxyLoaded;

    /// <summary>
    /// Charge la taille et la vignette d'une image (une seule fois par chemin), puis lance le calcul de son point d'intérêt.
    /// Lève une exception si l'image est illisible.
    /// </summary>
    public Task<Proxy> LoadAsync(string path)
    {
        if (_loads.TryGetValue(path, out var existing) && !existing.IsFaulted) return existing;
        var task = LoadCoreAsync(path);
        _loads[path] = task;
        return task;
    }

    private async Task<Proxy> LoadCoreAsync(string path)
    {
        var proxy = await Task.Run(async () =>
        {
            var (w, h) = await ImageDecoder.ReadSizeAsync(path);
            var pixels = await ImageDecoder.DecodeAsync(path, ImageDecoder.ProxyMaxSize);
            return new Proxy(w, h, pixels);
        });
        _proxies[path] = proxy;
        if (!_focus.ContainsKey(path)) _focus[path] = Task.Run(() => FaceFocus.FindAsync(proxy.Pixels));
        ProxyLoaded?.Invoke(this, path);
        return proxy;
    }

    public PixelBuffer? ProxyPixels(string path) => _proxies.TryGetValue(path, out var p) ? p.Pixels : null;

    /// <summary>Point d'intérêt déjà calculé, ou null s'il est encore en cours (ou si l'image n'est pas chargée).</summary>
    public FocusPoint? CompletedFocus(string path)
        => _focus.TryGetValue(path, out var t) && t.IsCompletedSuccessfully ? t.Result : null;

    /// <summary>
    /// Donne à chaque image sans point d'intérêt celui de sa vignette (calculé en arrière-plan), avant une disposition en
    /// mode Remplir. Une image dont la détection échoue garde le centre.
    /// </summary>
    public async Task EnsureFocusAsync(IEnumerable<CompositionImage> images)
    {
        foreach (var img in images.Where(i => i.Focus is null).ToList())
        {
            try
            {
                await LoadAsync(img.Path);
                img.Focus = await _focus[img.Path];
            }
            catch (Exception)
            {
                img.Focus = FocusPoint.Center;
            }
        }
    }

    /// <summary>
    /// Vignette GPU retouchée (luminosité, contraste, saturation) et tournée comme l'image ; le rognage et le flou sont
    /// appliqués au dessin. Null tant que la vignette n'est pas chargée. Les versions non utilisées pendant un dessin
    /// sont libérées par <see cref="EndFrame"/>.
    /// </summary>
    public CanvasBitmap? Bitmap(ICanvasResourceCreator device, CompositionImage img)
    {
        if (!_proxies.TryGetValue(img.Path, out var proxy)) return null;
        string key = FormattableString.Invariant($"{img.Path}|{img.Angle}|{img.Brightness:R}|{img.Contrast:R}|{img.Saturation:R}");
        _usedThisFrame.Add(key);
        if (_bitmaps.TryGetValue(key, out var cached)) return cached;
        var pixels = Filters.Apply(proxy.Pixels, img.Brightness, img.Contrast, img.Saturation);
        if (img.Angle != 0) pixels = pixels.Rotate(img.Angle);
        var bitmap = CanvasBitmap.CreateFromBytes(device, pixels.ToBgraPremultiplied(), pixels.Width, pixels.Height,
            DirectXPixelFormat.B8G8R8A8UIntNormalized);
        _bitmaps[key] = bitmap;
        return bitmap;
    }

    /// <summary>Fin d'un dessin : libère les versions GPU qui n'ont pas servi (retouches changées, image supprimée…).</summary>
    public void EndFrame()
    {
        foreach (var key in _bitmaps.Keys.Where(k => !_usedThisFrame.Contains(k)).ToList())
        {
            _bitmaps[key].Dispose();
            _bitmaps.Remove(key);
        }
        _usedThisFrame.Clear();
    }

    /// <summary>Périphérique graphique perdu ou recréé (<c>CreateResources</c> de Win2D) : les bitmaps GPU seront recréés.</summary>
    public void ResetDevice()
    {
        foreach (var b in _bitmaps.Values) b.Dispose();
        _bitmaps.Clear();
        _usedThisFrame.Clear();
    }

    /// <summary>Oublie les images qui ne sont plus dans la composition ni dans l'historique (nouveau projet).</summary>
    public void Trim(IEnumerable<string> keep)
    {
        var set = new HashSet<string>(keep, StringComparer.OrdinalIgnoreCase);
        foreach (var path in _proxies.Keys.Where(p => !set.Contains(p)).ToList())
        {
            _proxies.Remove(path);
            _loads.Remove(path);
            _focus.Remove(path);
        }
    }
}
