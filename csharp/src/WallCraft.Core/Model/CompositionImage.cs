namespace WallCraft.Core.Model;

/// <summary>Zone visible d'une image, en fractions de l'image tournée (gauche, haut, droite, bas).</summary>
public readonly record struct CropBox(double Left, double Top, double Right, double Bottom)
{
    public static readonly CropBox Full = new(0.0, 0.0, 1.0, 1.0);
    public double Width => Right - Left;
    public double Height => Bottom - Top;
}

/// <summary>Point d'intérêt normalisé (0..1) sur lequel le mode Remplir centre le recadrage.</summary>
public readonly record struct FocusPoint(double X, double Y)
{
    public static readonly FocusPoint Center = new(0.5, 0.5);
}

/// <summary>
/// Une image placée dans la composition (équivalent de <c>LoadedImage</c> côté Python, sans les pixels).
/// Coordonnées dans l'espace de composition (pixels virtuels, ou millimètres mis à l'échelle en mode taille réelle).
/// </summary>
public sealed class CompositionImage
{
    public CompositionImage(string path, int originalWidth, int originalHeight)
    {
        Path = path;
        OriginalWidth = originalWidth;
        OriginalHeight = originalHeight;
    }

    public string Path { get; }
    public int OriginalWidth { get; }
    public int OriginalHeight { get; }

    public double X { get; set; }
    public double Y { get; set; }
    /// <summary>Largeur affichée ; null tant que l'image n'a pas été placée.</summary>
    public double? W { get; set; }
    public double? H { get; set; }

    /// <summary>Rotation en degrés (0, 90, 180, 270), sens trigonométrique comme Pillow.</summary>
    public int Angle { get; set; }
    public int ZIndex { get; set; }
    public CropBox Crop { get; set; } = CropBox.Full;
    /// <summary>Point d'intérêt ; null = pas encore calculé (le moteur demande alors au fournisseur de point d'intérêt).</summary>
    public FocusPoint? Focus { get; set; }

    public double Brightness { get; set; } = 1.0;
    public double Contrast { get; set; } = 1.0;
    public double Saturation { get; set; } = 1.0;
    public double Blur { get; set; }

    /// <summary>Ratio largeur/hauteur de l'image d'origine.</summary>
    public double Aspect => OriginalHeight != 0 ? (double)OriginalWidth / OriginalHeight : 1.0;

    /// <summary>Ratio de l'image entière après rotation (<c>current_aspect</c>).</summary>
    public double CurrentAspect => (Angle % 180) == 90 ? 1.0 / Aspect : Aspect;

    /// <summary>Ratio de la zone réellement affichée, après rotation et rognage (<c>visible_aspect</c>).</summary>
    public double VisibleAspect => CurrentAspect * Math.Max(1e-6, Crop.Width) / Math.Max(1e-6, Crop.Height);

    /// <summary>Rotation d'un quart de tour dans le sens horaire (<c>rotate_cw</c>).</summary>
    public void RotateClockwise() => Angle = ((Angle - 90) % 360 + 360) % 360;

    public CompositionImage Clone() => new(Path, OriginalWidth, OriginalHeight)
    {
        X = X, Y = Y, W = W, H = H, Angle = Angle, ZIndex = ZIndex, Crop = Crop, Focus = Focus,
        Brightness = Brightness, Contrast = Contrast, Saturation = Saturation, Blur = Blur,
    };

    public override string ToString() => $"{System.IO.Path.GetFileName(Path)} ({X:0.##}, {Y:0.##}, {W:0.##}×{H:0.##})";
}
