using System.Text.Json;
using System.Text.Json.Nodes;
using WallCraft.Core.Services;
using WallCraft.Platform.Windows;

namespace WallCraft.App.Services;

/// <summary>
/// <c>WallCraft.exe --selftest rapport.json</c>, lancé par la CI dans le paquet MSIX installé : vérifie le dossier réel,
/// l'application d'un fond depuis ce dossier et la tâche de démarrage, puis écrit le résultat en JSON.
/// </summary>
public static class StoreSelfTest
{
    public static async Task<int> RunAsync(string? reportPath)
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
            string folder = AppPaths.DataDirectory();
            report["data_dir"] = folder;
            string image = Path.Combine(folder, "selftest.png");
            await File.WriteAllBytesAsync(image, SolidPng(64, 36, 40, 90, 160));
            report["wallpaper_set"] = DesktopWallpaper.ApplySpan(image);
            report["wallpaper_now"] = new JsonArray(DesktopWallpaper.Current().Select(c => (JsonNode?)c.Path).ToArray());
            report["launched_at_startup"] = StoreStartup.LaunchedAtStartup();
            report["startup_before"] = StoreStartup.IsEnabled();
            report["startup_enable"] = StoreStartup.Set(true);
            report["startup_after_enable"] = StoreStartup.IsEnabled();
            StoreStartup.Set(false);
            report["startup_after_disable"] = StoreStartup.IsEnabled();
        }
        catch (Exception e)
        {
            report["error"] = e.ToString();
            code = 1;
        }
        await File.WriteAllTextAsync(reportPath, report.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        return code;
    }

    /// <summary>PNG uni RGB, écrit à la main (pas de dépendance au GPU sur le runner).</summary>
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
