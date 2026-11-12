using System.Runtime.InteropServices;
using System.Runtime.InteropServices.Marshalling;

namespace WallCraft.Platform.Windows;

[StructLayout(LayoutKind.Sequential)]
internal struct Rect
{
    public int Left, Top, Right, Bottom;
}

internal enum DesktopWallpaperPosition
{
    Center = 0, Tile = 1, Stretch = 2, Fit = 3, Fill = 4, Span = 5,
}

/// <summary>Interface COM <c>IDesktopWallpaper</c> (shobjidl_core.h), dans l'ordre exact de la vtable.</summary>
[GeneratedComInterface(StringMarshalling = StringMarshalling.Utf16)]
[Guid("B92B56A9-8B55-4E14-9A89-0199BBB6F93B")]
internal partial interface IDesktopWallpaper
{
    [PreserveSig] int SetWallpaper(string? monitorId, string wallpaper);
    [PreserveSig] int GetWallpaper(string? monitorId, out nint wallpaper);           // LPWSTR à libérer par CoTaskMemFree
    [PreserveSig] int GetMonitorDevicePathAt(uint monitorIndex, out nint monitorId); // idem
    [PreserveSig] int GetMonitorDevicePathCount(out uint count);
    [PreserveSig] int GetMonitorRECT(string monitorId, out Rect displayRect);
    [PreserveSig] int SetBackgroundColor(uint color);
    [PreserveSig] int GetBackgroundColor(out uint color);
    [PreserveSig] int SetPosition(DesktopWallpaperPosition position);
    [PreserveSig] int GetPosition(out DesktopWallpaperPosition position);
    // SetSlideshow, GetSlideshow, SetSlideshowOptions, GetSlideshowOptions, AdvanceSlideshow, GetStatus, Enable : non utilisés.
}

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
internal unsafe struct DisplayDevice
{
    public int cb;
    public fixed char DeviceName[32];
    public fixed char DeviceString[128];
    public int StateFlags;
    public fixed char DeviceID[128];
    public fixed char DeviceKey[128];
}

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
internal unsafe struct MonitorInfoEx
{
    public int cbSize;
    public Rect rcMonitor;
    public Rect rcWork;
    public uint dwFlags;
    public fixed char szDevice[32];
}

internal static unsafe partial class Native
{
    public static readonly Guid ClsidDesktopWallpaper = new("C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD");
    public static readonly Guid IidDesktopWallpaper = new("B92B56A9-8B55-4E14-9A89-0199BBB6F93B");
    public const uint ClsctxLocalServer = 4;
    public const uint MonitorInfoPrimary = 1;
    public const uint EddGetDeviceInterfaceName = 1;
    public const uint SpiSetDeskWallpaper = 20;
    public const uint SpifUpdateIniFileAndSendChange = 3;

    [LibraryImport("ole32.dll")]
    public static partial int CoCreateInstance(in Guid rclsid, nint pUnkOuter, uint dwClsContext, in Guid riid, out nint ppv);

    [LibraryImport("ole32.dll")]
    public static partial int CoInitializeEx(nint reserved, uint coInit);

    [LibraryImport("ole32.dll")]
    public static partial void CoUninitialize();

    [LibraryImport("ole32.dll")]
    public static partial void CoTaskMemFree(nint pv);

    public delegate int MonitorEnumProc(nint hMonitor, nint hdc, Rect* rect, nint data);

    [LibraryImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool EnumDisplayMonitors(nint hdc, nint clip, delegate* unmanaged[Stdcall]<nint, nint, Rect*, nint, int> callback, nint data);

    [LibraryImport("user32.dll", EntryPoint = "GetMonitorInfoW")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool GetMonitorInfo(nint hMonitor, ref MonitorInfoEx info);

    [LibraryImport("user32.dll", EntryPoint = "EnumDisplayDevicesW", StringMarshalling = StringMarshalling.Utf16)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool EnumDisplayDevices(string? device, uint devNum, ref DisplayDevice displayDevice, uint flags);

    [LibraryImport("user32.dll", EntryPoint = "SystemParametersInfoW", StringMarshalling = StringMarshalling.Utf16)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool SystemParametersInfo(uint action, uint param, string? value, uint winIni);

    public static string ReadFixed(char* buffer, int max)
    {
        int len = 0;
        while (len < max && buffer[len] != '\0') len++;
        return new string(buffer, 0, len);
    }

    public static string TakeCoTaskString(nint ptr)
    {
        if (ptr == 0) return "";
        try { return Marshal.PtrToStringUni(ptr) ?? ""; }
        finally { CoTaskMemFree(ptr); }
    }
}
