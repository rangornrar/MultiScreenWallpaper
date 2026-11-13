using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Imaging;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;
using WallCraft.Core.Persistence;
using WallCraft.Core.Services;

namespace WallCraft.Core.Tests;

public class AutomationTests
{
    private static AppSettings TempSettings(string? json = null)
    {
        string path = Path.Combine(Path.GetTempPath(), $"wallcraft-test-{Guid.NewGuid():N}.json");
        if (json is not null) File.WriteAllText(path, json);
        var s = AppSettings.Load(path);
        File.Delete(path);
        return s;
    }

    [Test]
    public void PrefsDefaultsLikePython()
    {
        var p = AutomationPrefs.Read(TempSettings());
        Assert.True(p.KeepWallpaper);
        Assert.True(p.Tray);
        Assert.True(!p.Rotation.Enabled);
        Assert.Equal("", p.Rotation.Folder);
        Assert.Equal(60, p.Rotation.Minutes);
        Assert.Equal<int?>(null, p.Rotation.Count);
        Assert.Equal(3, p.Rotation.EffectiveCount(3));
    }

    [Test]
    public void PrefsReadPythonFile()
    {
        var s = TempSettings("""{"keep_wallpaper": false, "tray": 0, "rotation": {"enabled": true, "folder": "C:\\Images", "minutes": "15", "count": 2}, "fill": true}""");
        var p = AutomationPrefs.Read(s, autostart: true);
        Assert.True(!p.KeepWallpaper);
        Assert.True(!p.Tray);
        Assert.True(p.Autostart);
        Assert.True(p.Rotation.Enabled);
        Assert.Equal(@"C:\Images", p.Rotation.Folder);
        Assert.Equal(15, p.Rotation.Minutes);
        Assert.Equal<int?>(2, p.Rotation.Count);
    }

    [Test]
    public void PrefsWriteSameKeysAsPython()
    {
        var s = TempSettings("""{"fill": true, "rotation": {"old": 1}}""");
        var p = new AutomationPrefs
        {
            KeepWallpaper = false, Tray = true, Autostart = true,
            Rotation = new RotationPrefs { Enabled = true, Folder = "D:/x", Minutes = 30, Count = 4 },
        };
        p.WriteTo(s);
        Assert.Equal(false, s["keep_wallpaper"]!.GetValue<bool>());
        Assert.Equal(true, s["tray"]!.GetValue<bool>());
        Assert.True(s["autostart"] is null, "autostart reste dans le registre");
        var rot = (JsonObject)s["rotation"]!;
        Assert.SequenceEqual(["enabled", "folder", "minutes", "count"], rot.Select(kv => kv.Key));
        Assert.Equal(30, rot["minutes"]!.GetValue<int>());
        Assert.True(s.Fill, "les autres réglages sont conservés");
        Assert.Equal(p with { Autostart = false }, AutomationPrefs.Read(s));
    }

    [Test]
    public void ParseClampedLikeAsInt()
    {
        Assert.Equal(15, AutomationPrefs.ParseClamped("15", 60, 1, 1440));
        Assert.Equal(12, AutomationPrefs.ParseClamped(" 12.9 ", 60, 1, 1440));
        Assert.Equal(1, AutomationPrefs.ParseClamped("0", 60, 1, 1440));
        Assert.Equal(1440, AutomationPrefs.ParseClamped("1e9", 60, 1, 1440));
        Assert.Equal(60, AutomationPrefs.ParseClamped("abc", 60, 1, 1440));
        Assert.Equal(3, AutomationPrefs.ParseClamped("", 3, 1, 30));
        Assert.Equal(1, AutomationPrefs.ParseClamped("-0.5", 3, 1, 30));
    }

    [Test]
    public void RotationScheduleRules()
    {
        var now = new DateTimeOffset(2026, 11, 13, 10, 0, 0, TimeSpan.Zero);
        var on = new RotationPrefs { Enabled = true, Folder = "C:/img", Minutes = 15 };
        Assert.Equal<DateTimeOffset?>(null, RotationSchedule.Next(on with { Enabled = false }, now, now, false));
        Assert.Equal<DateTimeOffset?>(null, RotationSchedule.Next(on with { Folder = "" }, now, null, true));
        Assert.Equal<DateTimeOffset?>(now.AddMinutes(15), RotationSchedule.Next(on, now, null, false));
        var existing = now.AddMinutes(3);
        Assert.Equal<DateTimeOffset?>(existing, RotationSchedule.Next(on, now, existing, false));
        Assert.Equal<DateTimeOffset?>(now.AddMinutes(15), RotationSchedule.Next(on, now, existing, true));
        Assert.Equal<DateTimeOffset?>(now.AddMinutes(1), RotationSchedule.Next(on with { Minutes = 0 }, now, null, true));
        Assert.True(RotationSchedule.IsDue(now, now));
        Assert.True(!RotationSchedule.IsDue(existing, now));
        Assert.True(!RotationSchedule.IsDue(null, now));
    }

    private static MonitorInfo Screen(string hw, int x, int w, int h, double? wmm, double? hmm) =>
        new() { Name = $@"\\.\DISPLAY{x}", X = x, Y = 0, Width = w, Height = h, HwId = hw, WidthMm = wmm, HeightMm = hmm };

    [Test]
    public void PhysicalEditorInitialValues()
    {
        var a = Screen("PHL#1", 0, 1920, 1080, 509.2, 286.4);
        var b = Screen("", 1920, 1920, 1080, null, null);
        var s = new PhysicalSettings { BezelMm = 12.5 };
        s.Overrides["PHL#1"] = new MonitorOverride { OffsetYMm = -20 };
        Assert.Equal("12.5", PhysicalSettingsEditor.FormatBezel(s));
        Assert.Equal(("509", "286", "-20"), PhysicalSettingsEditor.InitialRow(a, s));
        Assert.Equal(("", "", "0"), PhysicalSettingsEditor.InitialRow(b, s));
        Assert.Equal(b.Name, PhysicalSettingsEditor.KeyFor(b));
        Assert.Equal("23.0″", PhysicalSettingsEditor.DiagonalText("509", "286,4"));
        Assert.Equal<string?>(null, PhysicalSettingsEditor.DiagonalText("", "286"));
    }

    [Test]
    public void PhysicalEditorApplyLikePython()
    {
        var a = Screen("PHL#1", 0, 1920, 1080, 509, 286);
        var b = Screen("DEL#2", 1920, 2560, 1440, null, null);
        var c = Screen("SAM#3", 4480, 1920, 1080, 600, 340);
        var current = new PhysicalSettings();
        current.Overrides["SAM#3"] = new MonitorOverride { WidthMm = 610, HeightMm = 345 };
        var result = PhysicalSettingsEditor.Apply(current, true, "500", [
            new PhysicalRowInput(a, "509,3", "286", "15"),   // même taille que l'EDID : seul le décalage est gardé
            new PhysicalRowInput(b, "597", "336", "abc"),    // pas d'EDID : taille enregistrée
            new PhysicalRowInput(c, "600", "340", "0"),      // revenu à l'EDID : la correction disparaît
        ]);
        Assert.True(result.Enabled);
        Assert.Equal(200.0, result.BezelMm);
        Assert.Equal<double?>(null, result.Overrides["PHL#1"].WidthMm);
        Assert.Equal(15.0, result.Overrides["PHL#1"].OffsetYMm);
        Assert.Equal<double?>(597, result.Overrides["DEL#2"].WidthMm);
        Assert.Equal(0.0, result.Overrides["DEL#2"].OffsetYMm);
        Assert.True(!result.Overrides.ContainsKey("SAM#3"));
        Assert.True(current.Overrides.ContainsKey("SAM#3"), "l'original n'est pas modifié");

        var clamped = PhysicalSettingsEditor.Apply(current, false, "-3", [new PhysicalRowInput(b, "20", "3500", "-5000")]);
        Assert.Equal(0.0, clamped.BezelMm);
        Assert.Equal<double?>(null, clamped.Overrides["DEL#2"].WidthMm);
        Assert.Equal(-1000.0, clamped.Overrides["DEL#2"].OffsetYMm);
    }

    [Test]
    public void AutoLayoutPutsOneImagePerScreen()
    {
        var monitors = new List<MonitorInfo> { Screen("B#2", 1920, 1920, 1080, null, null), Screen("A#1", 0, 1920, 1080, null, null) };
        var (w, h) = CompositionLayout.Apply(monitors);
        var images = new List<CompositionImage> { new("a.jpg", 1920, 1080), new("b.jpg", 1920, 1080) };
        AutoLayout.Apply(new LayoutEngine(), LayoutModes.Mosaic, w, h, monitors, images, fill: true);
        Assert.Near(0, images[0].X);
        Assert.Near(1920, images[1].X);
        Assert.Near(1920, images[1].W ?? 0);
    }

    [Test]
    public void TrayIconIsValidIco()
    {
        byte[] ico = TrayIconArt.CreateIco();
        Assert.Equal((ushort)1, BitConverter.ToUInt16(ico, 2));
        Assert.Equal((ushort)TrayIconArt.Sizes.Length, BitConverter.ToUInt16(ico, 4));
        for (int i = 0; i < TrayIconArt.Sizes.Length; i++)
        {
            int entry = 6 + 16 * i, size = TrayIconArt.Sizes[i];
            Assert.Equal((byte)size, ico[entry]);
            int length = BitConverter.ToInt32(ico, entry + 8), offset = BitConverter.ToInt32(ico, entry + 12);
            Assert.True(offset + length <= ico.Length);
            Assert.Equal(40, BitConverter.ToInt32(ico, offset));
            Assert.Equal(size * 2, BitConverter.ToInt32(ico, offset + 8));
        }

        var p = TrayIconArt.Render(64);
        byte[] Px(int x, int y) => p.Data.AsSpan((y * 64 + x) * 4, 4).ToArray();
        Assert.SequenceEqual(new byte[] { 138, 180, 248, 255 }, Px(12, 28), "écran gauche bleu");
        Assert.SequenceEqual(new byte[] { 120, 212, 160, 255 }, Px(31, 28), "écran central vert");
        Assert.SequenceEqual(new byte[] { 255, 196, 110, 255 }, Px(50, 28), "écran droit orange");
        Assert.Equal((byte)0, Px(2, 2)[3], "coin transparent");
        Assert.Equal((byte)255, Px(32, 52)[3], "pied opaque");
    }
}
