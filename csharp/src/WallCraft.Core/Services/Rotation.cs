using WallCraft.Core.Layout;

namespace WallCraft.Core.Services;

/// <summary>Rotation automatique des fonds à partir d'un dossier d'images.</summary>
public static class Rotation
{
    public static readonly IReadOnlySet<string> ImageExtensions =
        new HashSet<string>([".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"], StringComparer.OrdinalIgnoreCase);

    public static List<string> ListImages(string? folder)
    {
        if (string.IsNullOrEmpty(folder) || !Directory.Exists(folder)) return [];
        return Directory.EnumerateFiles(folder)
            .Where(f => ImageExtensions.Contains(Path.GetExtension(f)))
            .Order(StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>Tire <paramref name="count"/> images en évitant celles de la rotation précédente quand c'est possible.</summary>
    public static List<string> Pick(IReadOnlyList<string> files, int count, IEnumerable<string>? previous = null, PythonRandom? rng = null)
    {
        rng ??= new PythonRandom(Random.Shared.NextInt64());
        var prev = new HashSet<string>(previous ?? [], StringComparer.Ordinal);
        var pool = files.Where(f => !prev.Contains(f)).ToList();
        if (pool.Count < count) pool = files.ToList();
        return rng.Sample(pool, Math.Min(count, pool.Count));
    }
}
