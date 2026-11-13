using Microsoft.Graphics.Canvas;
using System.Text.Json;
using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Model;
using WallCraft.Core.Services;
using WallCraft.Platform.Windows;

namespace WallCraft.App.Services;

/// <summary>
/// <c>WallCraft.exe --selftest rapport.json</c> vérifie le rendu, l'application du fond et la tâche de démarrage.
/// L'option <c>--render-only</c> limite le contrôle au rendu, sans modifier les paramètres de Windows.
/// </summary>
public static class StoreSelfTest
{
    public static async Task<int> RunAsync(string? reportPath, bool renderOnly = false)
    {
        reportPath ??= Path.Combine(Path.GetTempPath(), "wallcraft-selftest.json");
        var report = new JsonObject
        {
            ["packaged"] = StoreStartup.IsPackaged,
            ["family"] = AppPaths.PackageFamilyName,
        };
        int code = 0;
        try
        {
            string folder = renderOnly
                ? Path.Combine(Path.GetDirectoryName(Path.GetFullPath(reportPath))!, "wallcraft-render-" + Guid.NewGuid().ToString("N"))
                : AppPaths.DataDirectory();
            Directory.CreateDirectory(folder);
            report["data_dir"] = folder;
            string image = Path.Combine(folder, "selftest.png");
            await File.WriteAllBytesAsync(image, SolidPng(64, 36, 40, 90, 160));
            string secondImage = Path.Combine(folder, "selftest-second.png");
            await File.WriteAllBytesAsync(secondImage, SolidPng(64, 36, 160, 90, 40));
            var background = Windows.UI.Color.FromArgb(255, 0, 0, 0);
            int limit = CanvasDevice.GetSharedDevice().MaximumBitmapSizeInPixels;
            var simulated = new[]
            {
                new MonitorInfo { Width = 64, Height = 36, Canvas = new IntRect(0, 0, 64, 36) },
                new MonitorInfo { Width = 64, Height = 36, Canvas = new IntRect(limit, 0, 64, 36) },
            };
            var wide = await HdRenderer.SplitAsync([new(image, 64, 36), new(secondImage, 64, 36) { X = limit }],
                limit + 64, 36, simulated, background, folder, "selftest-wide");
            report["wide_render"] = wide.Count == 2;
            if (wide.Count == 2)
            {
                var left = await ImageDecoder.DecodeAsync(wide[0].Path);
                var right = await ImageDecoder.DecodeAsync(wide[1].Path);
                report["wide_render"] = left.Width == 64 && left.Height == 36 && left.Data[0] == 40
                    && right.Width == 64 && right.Height == 36 && right.Data[0] == 160;
            }

            if (!renderOnly)
            {
                var monitors = Monitors.Enumerate();
                var (width, height) = CompositionLayout.Apply(monitors);
                var images = monitors.Select((monitor, i) =>
                {
                    var area = monitor.Canvas!.Value;
                    return new CompositionImage(i % 2 == 0 ? image : secondImage, 64, 36)
                    {
                        X = area.X, Y = area.Y, W = area.Width, H = area.Height,
                    };
                }).ToList();
                var store = new WallpaperStore(Path.Combine(folder, "selftest-configs"));
                var outcome = await WallpaperApplier.RenderAndApplyAsync(images, width, height, monitors, background, store);
                report["native_status"] = outcome.Status.ToString();
                report["native_errors"] = new JsonArray(outcome.Errors.Select(error => (JsonNode?)error).ToArray());
                var current = DesktopWallpaper.Current();
                report["native_applied"] = outcome.Pieces.Count(piece => current.Any(w =>
                    w.Monitor.Left == piece.Monitor.X && w.Monitor.Top == piece.Monitor.Y
                    && string.Equals(w.Path, piece.Path, StringComparison.OrdinalIgnoreCase)));
                report["native_expected"] = monitors.Count;
                report["wallpaper_set"] = DesktopWallpaper.ApplySpan(image);
                report["wallpaper_now"] = new JsonArray(DesktopWallpaper.Current().Select(c => (JsonNode?)c.Path).ToArray());
                report["launched_at_startup"] = StoreStartup.LaunchedAtStartup();
                report["startup_before"] = StoreStartup.IsEnabled();
                report["startup_enable"] = StoreStartup.Set(true);
                report["startup_after_enable"] = StoreStartup.IsEnabled();
                StoreStartup.Set(false);
                report["startup_after_disable"] = StoreStartup.IsEnabled();
            }
            if (!(report["wide_render"]?.GetValue<bool>() ?? false)) code = 1;
        }
        catch (Exception e)
        {
            report["error"] = e.ToString();
            code = 1;
        }
        await File.WriteAllTextAsync(reportPath, report.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        return code;
    }

    /// <summary>Image source aux couleurs connues pour vérifier les pixels produits par le rendu.</summary>
    private static byte[] SolidPng(int width, int height, byte r, byte g, byte b)
    {
        var raw = new MemoryStream();
        for (int y = 0; y < height; y++)
        {
            raw.WriteByte(0); // filtre « None »
            for (int x = 0; x < width; x++) { raw.WriteByte(r); raw.WriteByte(g); raw.WriteByte(b); }
        }
        var idat = new MemoryStream();
        using (var z = new System.IO.Compression.ZLibStream(idat, System.IO.Compression.CompressionLevel.Optimal, leaveOpen: true))
            raw.WriteTo(z);
        var png = new MemoryStream();
        png.Write([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
        var ihdr = new byte[13];
        System.Buffers.Binary.BinaryPrimitives.WriteInt32BigEndian(ihdr, width);
        System.Buffers.Binary.BinaryPrimitives.WriteInt32BigEndian(ihdr.AsSpan(4), height);
        ihdr[8] = 8; ihdr[9] = 2; // 8 bits, RGB
        Chunk(png, "IHDR", ihdr);
        Chunk(png, "IDAT", idat.ToArray());
        Chunk(png, "IEND", []);
        return png.ToArray();
    }

    private static void Chunk(Stream s, string type, byte[] data)
    {
        Span<byte> buf = stackalloc byte[4];
        System.Buffers.Binary.BinaryPrimitives.WriteInt32BigEndian(buf, data.Length);
        s.Write(buf);
        byte[] typeBytes = System.Text.Encoding.ASCII.GetBytes(type);
        s.Write(typeBytes);
        s.Write(data);
        uint crc = Crc32(typeBytes.Concat(data));
        System.Buffers.Binary.BinaryPrimitives.WriteUInt32BigEndian(buf, crc);
        s.Write(buf);
    }

    private static uint Crc32(IEnumerable<byte> bytes)
    {
        uint c = 0xFFFFFFFF;
        foreach (byte v in bytes)
        {
            c ^= v;
            for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320 ^ (c >> 1) : c >> 1;
        }
        return c ^ 0xFFFFFFFF;
    }
}
