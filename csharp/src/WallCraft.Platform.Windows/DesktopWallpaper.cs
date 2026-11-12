using System.Runtime.InteropServices;
using System.Runtime.InteropServices.Marshalling;
using Microsoft.Win32;
using WallCraft.Core.Geometry;

namespace WallCraft.Platform.Windows;

/// <summary>Fond actuel d'un écran actif.</summary>
public sealed record CurrentWallpaper(WindowsMonitor Monitor, string Path);

/// <summary>Résultat d'une application : tout s'est bien passé si <see cref="Errors"/> est vide.</summary>
public sealed record ApplyResult(int Applied, List<string> Errors)
{
    public bool Success => Applied > 0 && Errors.Count == 0;
}

/// <summary>Fond d'écran par écran via <c>IDesktopWallpaper</c> (Windows 8 et plus), avec repli « Étendre ».</summary>
public static class DesktopWallpaper
{
    private static readonly StrategyBasedComWrappers ComWrappers = new();

    /// <summary>Exécute <paramref name="action"/> avec l'objet COM, dans un appartement initialisé et libéré proprement.</summary>
    private static T With<T>(Func<IDesktopWallpaper, T> action, Func<string, T> onError)
    {
        int hrInit = Native.CoInitializeEx(0, 0x2); // COINIT_APARTMENTTHREADED
        try
        {
            int hr = Native.CoCreateInstance(Native.ClsidDesktopWallpaper, 0, Native.ClsctxLocalServer, Native.IidDesktopWallpaper, out nint ptr);
            if (hr != 0 || ptr == 0) return onError($"CoCreateInstance a échoué (0x{hr:X8}).");
            try
            {
                var wallpaper = (IDesktopWallpaper)ComWrappers.GetOrCreateObjectForComInstance(ptr, CreateObjectFlags.UniqueInstance);
                return action(wallpaper);
            }
            finally
            {
                Marshal.Release(ptr);
            }
        }
        finally
        {
            if (hrInit is 0 or 1) Native.CoUninitialize(); // S_OK ou S_FALSE : à équilibrer
        }
    }

    /// <summary>Écrans actifs connus de l'API ; ceux dont le rectangle est illisible sont inactifs et ignorés.</summary>
    private static List<WindowsMonitor> ActiveMonitors(IDesktopWallpaper w)
    {
        var list = new List<WindowsMonitor>();
        if (w.GetMonitorDevicePathCount(out uint count) != 0) return list;
        for (uint i = 0; i < count; i++)
        {
            if (w.GetMonitorDevicePathAt(i, out nint raw) != 0 || raw == 0) continue;
            string id = Native.TakeCoTaskString(raw);
            if (w.GetMonitorRECT(id, out Rect r) != 0) continue;
            list.Add(new WindowsMonitor(id, r.Left, r.Top, r.Right, r.Bottom));
        }
        return list;
    }

    /// <summary>
    /// Applique une image par écran. Les images sont associées aux écrans Windows par recouvrement de rectangles.
    /// <paramref name="background"/> = couleur de fond (R, G, B) assortie à la composition.
    /// </summary>
    public static ApplyResult Apply(IEnumerable<(MonitorInfo Monitor, string Path)> splitResults, (byte R, byte G, byte B) background)
    {
        var results = splitResults.ToList();
        return With(w =>
        {
            var errors = new List<string>();
            var monitors = ActiveMonitors(w);
            if (monitors.Count == 0) return new ApplyResult(0, ["Windows ne signale aucun écran actif."]);

            // Remplissage exact (évite d'hériter d'un mode « Étendre » précédent) et fond assorti.
            w.SetBackgroundColor((uint)(background.R | (background.G << 8) | (background.B << 16)));
            int hrPos = w.SetPosition(DesktopWallpaperPosition.Fill);
            if (hrPos != 0) errors.Add($"SetPosition a échoué (0x{hrPos:X8}).");

            var (pairs, unmatched) = MonitorMatching.Match(results, monitors);
            errors.AddRange(unmatched.Select(p => $"Aucun écran Windows ne correspond à {Path.GetFileName(p)}."));
            int applied = 0;
            foreach (var (id, path) in pairs)
            {
                int hr = w.SetWallpaper(id, Path.GetFullPath(path));
                if (hr != 0) errors.Add($"SetWallpaper a échoué pour {Path.GetFileName(path)} (0x{hr:X8}).");
                else applied++;
            }
            return new ApplyResult(applied, errors);
        }, message => new ApplyResult(0, [message]));
    }

    /// <summary>Fond actuel de chaque écran actif (pour détecter qu'un thème Windows a remplacé celui de WallCraft).</summary>
    public static List<CurrentWallpaper> Current() => With(w =>
    {
        var list = new List<CurrentWallpaper>();
        foreach (var m in ActiveMonitors(w))
        {
            string path = w.GetWallpaper(m.Id, out nint raw) == 0 ? Native.TakeCoTaskString(raw) : "";
            list.Add(new CurrentWallpaper(m, path));
        }
        return list;
    }, _ => []);

    /// <summary>Mode de secours : une seule image étirée sur tout le bureau (« Étendre »).</summary>
    public static bool ApplySpan(string imagePath)
    {
        try
        {
            using (var key = Registry.CurrentUser.OpenSubKey(@"Control Panel\Desktop", writable: true))
            {
                if (key is null) return false;
                key.SetValue("WallpaperStyle", "22", RegistryValueKind.String);
                key.SetValue("TileWallpaper", "0", RegistryValueKind.String);
            }
            return Native.SystemParametersInfo(Native.SpiSetDeskWallpaper, 0, Path.GetFullPath(imagePath), Native.SpifUpdateIniFileAndSendChange);
        }
        catch (Exception e) when (e is UnauthorizedAccessException or System.Security.SecurityException or IOException)
        {
            return false;
        }
    }
}
