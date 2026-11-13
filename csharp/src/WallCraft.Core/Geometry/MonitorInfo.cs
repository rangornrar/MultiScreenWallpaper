namespace WallCraft.Core.Geometry;

/// <summary>Rectangle entier (pixels de composition ou du bureau Windows).</summary>
public readonly record struct IntRect(int X, int Y, int Width, int Height)
{
    public int Right => X + Width;
    public int Bottom => Y + Height;
}

/// <summary>
/// Un écran tel que Windows le décrit, enrichi de sa taille physique (EDID) et, après
/// <see cref="CompositionLayout.Apply"/>, de son rectangle dans la composition.
/// </summary>
public sealed class MonitorInfo
{
    /// <summary>Nom Windows de la sortie, ex. <c>\\.\DISPLAY1</c>.</summary>
    public string Name { get; init; } = "";
    public int X { get; init; }
    public int Y { get; init; }
    public int Width { get; init; }
    public int Height { get; init; }
    /// <summary>Taille de la dalle en mm (EDID), dans l'orientation réelle de l'écran.</summary>
    public double? WidthMm { get; set; }
    public double? HeightMm { get; set; }
    /// <summary>Identifiant matériel stable (« PHLC069#5&amp;24d6a99a&amp;0&amp;UID45316 »), clé des réglages par écran.</summary>
    public string HwId { get; set; } = "";
    public bool IsPrimary { get; init; }
    /// <summary>Rectangle dans la composition ; null tant que la disposition n'a pas été calculée.</summary>
    public IntRect? Canvas { get; set; }

    public IntRect DesktopRect => new(X, Y, Width, Height);

    public MonitorInfo Clone() => (MonitorInfo)MemberwiseClone();

    public override string ToString() => $"{Name} {Width}×{Height} @({X},{Y})";
}
