using System.Runtime.InteropServices.WindowsRuntime;
using CommunityToolkit.Mvvm.ComponentModel;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Imaging;
using WallCraft.App.Services;
using WallCraft.Core.Imaging;
using WallCraft.Core.Model;
using WallCraft.Core.Presentation;

namespace WallCraft.App.ViewModels;

/// <summary>Une ligne de la bibliothèque : miniature, nom tronqué au milieu, résolution et alerte basse résolution.</summary>
public sealed partial class LibraryItemViewModel : ObservableObject
{
    /// <summary>Taille de la miniature affichée (76 × 48 comme en Python), calculée au double pour les écrans à haute densité.</summary>
    public const int ThumbWidth = 76, ThumbHeight = 48;

    private string _thumbKey = "";
    private ImageSource? _thumbnail;
    private string _lowResText = "";

    public LibraryItemViewModel(CompositionImage image, int index)
    {
        Image = image;
        Index = index;
        Name = DisplayText.MiddleTruncate(Path.GetFileName(image.Path));
        Resolution = $"{image.OriginalWidth} × {image.OriginalHeight}";
        FullPath = image.Path;
    }

    /// <summary>Image du document (remplacée après annuler/rétablir : <see cref="Update"/>).</summary>
    public CompositionImage Image { get; private set; }

    /// <summary>Position dans la liste des calques du document.</summary>
    public int Index { get; }

    public string Name { get; }
    public string FullPath { get; }
    public string Resolution { get; }

    public ImageSource? Thumbnail
    {
        get => _thumbnail;
        private set => SetProperty(ref _thumbnail, value);
    }

    /// <summary>« ⚠ Basse résolution ×2,5 », ou vide.</summary>
    public string LowResText
    {
        get => _lowResText;
        private set
        {
            if (SetProperty(ref _lowResText, value)) OnPropertyChanged(nameof(LowResVisibility));
        }
    }

    public Visibility LowResVisibility => _lowResText.Length > 0 ? Visibility.Visible : Visibility.Collapsed;

    /// <summary>Met à jour l'alerte et la miniature (si la rotation, le rognage ou les retouches ont changé).</summary>
    public void Update(CompositionImage image, ImageCache cache, Localizer loc)
    {
        Image = image;
        LowResText = DisplayText.LowResolution(image, loc.DecimalSeparator) is { } low ? "⚠ " + loc.Format("lowres_badge", low) : "";
        var proxy = cache.ProxyPixels(image.Path);
        if (proxy is null) return;
        string key = FormattableString.Invariant(
            $"{image.Angle}|{image.Crop}|{image.Brightness:R}|{image.Contrast:R}|{image.Saturation:R}");
        if (key == _thumbKey && _thumbnail is not null) return;
        _thumbKey = key;
        Thumbnail = MakeThumbnail(proxy, image);
    }

    /// <summary>Miniature « contenue » de la partie visible de l'image (<c>_make_contained_preview</c>).</summary>
    private static WriteableBitmap MakeThumbnail(PixelBuffer proxy, CompositionImage img)
    {
        var rotated = img.Angle != 0 ? proxy.Rotate(img.Angle) : proxy;
        var c = img.Crop;
        int rw = rotated.Width, rh = rotated.Height;
        int l = (int)(c.Left * rw), t = (int)(c.Top * rh);
        int r = Math.Max(l + 1, (int)(c.Right * rw)), b = Math.Max(t + 1, (int)(c.Bottom * rh));
        var small = Core.Imaging.Thumbnail.Fit(rotated.Crop(l, t, r, b), ThumbWidth * 2, ThumbHeight * 2);
        small = Filters.Apply(small, img.Brightness, img.Contrast, img.Saturation);
        var bitmap = new WriteableBitmap(small.Width, small.Height);
        byte[] bgra = small.ToBgraPremultiplied();
        using (var stream = bitmap.PixelBuffer.AsStream()) stream.Write(bgra, 0, bgra.Length);
        bitmap.Invalidate();
        return bitmap;
    }
}
