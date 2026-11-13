using System.Runtime.InteropServices;
using Microsoft.Win32;
using WallCraft.Core.Geometry;

namespace WallCraft.Platform.Windows;

/// <summary>Écrans branchés, en pixels physiques, avec leur taille réelle lue dans l'EDID.</summary>
public static unsafe class Monitors
{
    /// <summary>
    /// Écrans triés de gauche à droite puis de haut en bas. Le processus doit être « Per-Monitor V2 »
    /// (manifeste de l'application) pour obtenir des pixels physiques.
    /// </summary>
    public static List<MonitorInfo> Enumerate()
    {
        var handles = new List<nint>();
        var gc = GCHandle.Alloc(handles);
        try
        {
            Native.EnumDisplayMonitors(0, 0, &Collect, GCHandle.ToIntPtr(gc));
        }
        finally
        {
            gc.Free();
        }

        var result = new List<MonitorInfo>();
        foreach (var h in handles)
        {
            var info = new MonitorInfoEx { cbSize = sizeof(MonitorInfoEx) };
            if (!Native.GetMonitorInfo(h, ref info)) continue;
            var r = info.rcMonitor;
            string name = Native.ReadFixed(info.szDevice, 32);
            var m = new MonitorInfo
            {
                Name = name,
                X = r.Left, Y = r.Top, Width = r.Right - r.Left, Height = r.Bottom - r.Top,
                IsPrimary = (info.dwFlags & Native.MonitorInfoPrimary) != 0,
                HwId = name,
            };
            EnrichWithEdid(m);
            result.Add(m);
        }
        return result.OrderBy(m => m.X).ThenBy(m => m.Y).ToList();
    }

    [UnmanagedCallersOnly(CallConvs = [typeof(System.Runtime.CompilerServices.CallConvStdcall)])]
    private static int Collect(nint hMonitor, nint hdc, Rect* rect, nint data)
    {
        if (GCHandle.FromIntPtr(data).Target is List<nint> list) list.Add(hMonitor);
        return 1;
    }

    /// <summary>Identifiant matériel stable et taille physique (EDID dans le registre) de l'écran branché sur une sortie.</summary>
    private static void EnrichWithEdid(MonitorInfo m)
    {
        try
        {
            var dev = new DisplayDevice { cb = sizeof(DisplayDevice) };
            if (!Native.EnumDisplayDevices(m.Name, 0, ref dev, Native.EddGetDeviceInterfaceName)) return;
            // \\?\DISPLAY#GSM5B7F#5&2f3b8a6&0&UID4352#{e6f07b5f-…}
            string deviceId = Native.ReadFixed(dev.DeviceID, 128);
            var parts = deviceId.Split('#');
            if (parts.Length < 3) return;
            string model = parts[1], instance = parts[2];
            m.HwId = $"{model}#{instance}";
            using var key = Registry.LocalMachine.OpenSubKey($@"SYSTEM\CurrentControlSet\Enum\DISPLAY\{model}\{instance}\Device Parameters");
            if (key?.GetValue("EDID") is byte[] edid)
                Edid.ApplySize(m, Edid.ParseSizeMm(edid));
        }
        catch (Exception e) when (e is System.Security.SecurityException or UnauthorizedAccessException or IOException)
        {
            // Taille inconnue : la composition utilisera une densité par défaut.
        }
    }
}
