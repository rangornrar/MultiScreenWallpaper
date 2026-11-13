using System.Runtime.InteropServices;

namespace WallCraft.Platform.Windows;

/// <summary>Paquet MSIX en cours (version Microsoft Store), ou aucun (exe GitHub).</summary>
public static unsafe partial class PackageInfo
{
    private const int ErrorInsufficientBuffer = 122;

    /// <summary>Nom de famille du paquet, ou null hors paquet.</summary>
    public static string? FamilyName()
    {
        try
        {
            uint length = 0;
            if (GetCurrentPackageFamilyName(ref length, null) != ErrorInsufficientBuffer) return null;
            var buffer = new char[length];
            fixed (char* p = buffer)
            {
                if (GetCurrentPackageFamilyName(ref length, p) != 0) return null;
            }
            string name = new string(buffer, 0, (int)Math.Max(0, length - 1));
            return name.Length > 0 ? name : null;
        }
        catch (EntryPointNotFoundException)
        {
            return null;
        }
    }

    [LibraryImport("kernel32.dll")]
    private static partial int GetCurrentPackageFamilyName(ref uint length, char* name);
}
