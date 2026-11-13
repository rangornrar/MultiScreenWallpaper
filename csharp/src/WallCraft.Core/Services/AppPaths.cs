namespace WallCraft.Core.Services;

/// <summary>
/// Dossiers de données, partagés avec la version Python (<c>%LOCALAPPDATA%\WallCraft</c>).
/// Dans le paquet du Microsoft Store, Windows redirige les écritures dans %LOCALAPPDATA% vers un dossier privé
/// que l'Explorateur ne voit pas : on écrit alors directement dans ce dossier réel
/// (<c>Packages\&lt;famille&gt;\LocalCache\Local\WallCraft</c>), pour que les fonds appliqués s'affichent.
/// </summary>
public static class AppPaths
{
    /// <summary>Nom de famille du paquet MSIX (version Store), ou null hors paquet. Renseigné au démarrage de l'application.</summary>
    public static string? PackageFamilyName { get; set; }

    private static bool _settingsImported;

    internal static string LegacyDataDirectory() => Path.Combine(LocalAppData(), "WallCraft");

    public static string LocalAppData()
    {
        string? baseDir = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        if (string.IsNullOrEmpty(baseDir))
            baseDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".local", "share");
        return baseDir;
    }

    /// <summary>Dossier qui contient « WallCraft » : %LOCALAPPDATA%, ou son équivalent réel dans le paquet.</summary>
    public static string DataRoot(string localAppData, string? packageFamilyName) =>
        string.IsNullOrEmpty(packageFamilyName)
            ? localAppData
            : Path.Combine(localAppData, "Packages", packageFamilyName, "LocalCache", "Local");

    public static string DataDirectory()
    {
        string path = Path.Combine(DataRoot(LocalAppData(), PackageFamilyName), "WallCraft");
        Directory.CreateDirectory(path);
        if (!string.IsNullOrEmpty(PackageFamilyName) && !_settingsImported)
        {
            _settingsImported = true;
            ImportSettingsOnce(Path.Combine(LegacyDataDirectory(), "settings.json"), Path.Combine(path, "settings.json"));
        }
        return path;
    }

    /// <summary>Première ouverture de la version Store : reprend les réglages de l'exe GitHub s'ils existent.</summary>
    public static void ImportSettingsOnce(string source, string target)
    {
        if (File.Exists(target) || string.Equals(Path.GetFullPath(source), Path.GetFullPath(target), StringComparison.OrdinalIgnoreCase))
            return;
        try { File.Copy(source, target); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
    }

    public static string SettingsFile() => Path.Combine(DataDirectory(), "settings.json");
}
