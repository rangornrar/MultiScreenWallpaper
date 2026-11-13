namespace WallCraft.Core.Services;

/// <summary>Dossiers de données, partagés avec la version Python (<c>%LOCALAPPDATA%\WallCraft</c>).</summary>
public static class AppPaths
{
    public static string DataDirectory()
    {
        string? baseDir = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        if (string.IsNullOrEmpty(baseDir))
            baseDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".local", "share");
        string path = Path.Combine(baseDir, "WallCraft");
        Directory.CreateDirectory(path);
        return path;
    }

    public static string SettingsFile() => Path.Combine(DataDirectory(), "settings.json");
}
