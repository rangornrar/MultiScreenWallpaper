using Microsoft.Win32;

namespace WallCraft.Platform.Windows;

/// <summary>Lancement avec Windows (<c>HKCU\…\Run</c>), dans la zone de notification (<c>--tray</c>).</summary>
public static class Autostart
{
    private const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
    private const string AppName = "WallCraft";

    public static string Command(string executablePath) => $"\"{executablePath}\" --tray";

    public static bool IsEnabled()
    {
        using var key = Registry.CurrentUser.OpenSubKey(RunKey);
        return key?.GetValue(AppName) is not null;
    }

    public static void Set(bool enabled, string executablePath)
    {
        using var key = Registry.CurrentUser.OpenSubKey(RunKey, writable: true) ?? Registry.CurrentUser.CreateSubKey(RunKey);
        if (enabled) key.SetValue(AppName, Command(executablePath), RegistryValueKind.String);
        else key.DeleteValue(AppName, throwOnMissingValue: false);
    }
}
