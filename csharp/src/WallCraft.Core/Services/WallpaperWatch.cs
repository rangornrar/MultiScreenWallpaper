namespace WallCraft.Core.Services;

/// <summary>Ce qui est arrivé au fond appliqué par WallCraft.</summary>
public enum WallpaperChange
{
    /// <summary>Rien n'a changé.</summary>
    None,
    /// <summary>Windows a remis un thème (synchronisation du compte, mise à jour) : il faut réappliquer.</summary>
    Theme,
    /// <summary>L'utilisateur a choisi un autre fond : ne plus y toucher.</summary>
    User,
}

public static class WallpaperWatch
{
    private static readonly string[] ThemeMarkers =
    [
        "/microsoft/windows/themes/",           // thèmes et synchronisation du compte
        "transcodedwallpaper",
        "/windows/web/",                        // fonds fournis par Windows
        "spotlight", "contentdeliverymanager",  // Windows à la une
    ];

    /// <summary>True si le fichier vient d'un thème Windows (et non d'un choix de l'utilisateur).</summary>
    public static bool IsThemeWallpaper(string? path)
    {
        if (string.IsNullOrEmpty(path)) return true;
        string low = path.Replace('\\', '/').ToLowerInvariant();
        return ThemeMarkers.Any(low.Contains);
    }

    /// <summary>Compare les fonds actuels (un chemin par écran) à ceux que WallCraft a appliqués.</summary>
    public static WallpaperChange Detect(IReadOnlyCollection<string> expectedPaths, IReadOnlyCollection<string?> currentPaths)
    {
        if (expectedPaths.Count == 0 || currentPaths.Count == 0) return WallpaperChange.None;
        var expected = new HashSet<string>(expectedPaths.Select(Normalize), StringComparer.Ordinal);
        var replaced = currentPaths.Where(p => !expected.Contains(Normalize(p ?? ""))).ToList();
        if (replaced.Count == 0) return WallpaperChange.None;
        return replaced.All(IsThemeWallpaper) ? WallpaperChange.Theme : WallpaperChange.User;
    }

    /// <summary>Équivalent de <c>os.path.normcase(os.path.abspath(p))</c> sous Windows.</summary>
    internal static string Normalize(string path)
    {
        if (path.Length == 0) return Path.GetFullPath(".").ToLowerInvariant();
        string full = Path.GetFullPath(path);
        return OperatingSystem.IsWindows() ? full.Replace('/', '\\').ToLowerInvariant() : full;
    }
}
