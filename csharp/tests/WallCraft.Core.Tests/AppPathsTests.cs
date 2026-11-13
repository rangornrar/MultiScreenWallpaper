using WallCraft.Core.Geometry;
using WallCraft.Core.Services;

namespace WallCraft.Core.Tests;

/// <summary>Version Microsoft Store : dossier réel du paquet et reprise des réglages de l'exe.</summary>
public class AppPathsTests
{
    [Test]
    public void HorsPaquetDossierHabituel() =>
        Assert.Equal("/home/p/AppData", AppPaths.DataRoot("/home/p/AppData", null));

    [Test]
    public void DansUnPaquetCheminReelDuDossierRedirige() =>
        Assert.Equal(Path.Combine("/home/p/AppData", "Packages", "Fam_x", "LocalCache", "Local"),
                     AppPaths.DataRoot("/home/p/AppData", "Fam_x"));

    [Test]
    public void ReglagesDeLExeReprisUneSeuleFois()
    {
        string dir = Path.Combine(Path.GetTempPath(), "wallcraft-paths-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        try
        {
            string source = Path.Combine(dir, "exe.json"), target = Path.Combine(dir, "store.json");
            File.WriteAllText(source, "{\"lang\": \"de\"}");
            AppPaths.ImportSettingsOnce(source, target);
            Assert.Equal("{\"lang\": \"de\"}", File.ReadAllText(target));
            File.WriteAllText(target, "{\"lang\": \"fr\"}");
            AppPaths.ImportSettingsOnce(source, target);
            Assert.Equal("{\"lang\": \"fr\"}", File.ReadAllText(target), "les réglages de la version Store ne sont pas écrasés");
        }
        finally { Directory.Delete(dir, true); }
    }

    [Test]
    public void ReprendLeFondPythonEtSonPanoramaSansEcraserLeStore()
    {
        string dir = Path.Combine(Path.GetTempPath(), "wallcraft-configs-" + Guid.NewGuid().ToString("N"));
        MonitorInfo[] monitors = [new() { Name = "Display", Width = 1920, Height = 1080 }];
        try
        {
            var legacy = new WallpaperStore(Path.Combine(dir, "legacy"));
            var store = new WallpaperStore(Path.Combine(dir, "store"), legacy.Root);
            string source = legacy.DirectoryFor(monitors);
            const string prefix = "wallcraft_20261113-120000";
            string file = Path.Combine(source, prefix + "_pos_00.png");
            string span = Path.Combine(source, prefix + "_span.png");
            File.WriteAllText(file, "image Python");
            File.WriteAllText(span, "panorama Python");
            legacy.Save(monitors, [(monitors[0], file)], prefix);
            legacy.Release(monitors);

            Assert.True(store.IsReleased(monitors));
            var saved = store.Load(monitors);
            string imported = saved.Single().Path;
            string importedSpan = WallpaperStore.SpanPath(imported)!;
            Assert.Equal("image Python", File.ReadAllText(imported));
            Assert.Equal("panorama Python", File.ReadAllText(importedSpan));
            Assert.Equal(WallpaperChange.None, WallpaperWatch.Detect(store.ExpectedPaths(saved), [span]));
            Assert.Equal(WallpaperChange.None, WallpaperWatch.Detect(store.ExpectedPaths(saved), [importedSpan]));
            Assert.Equal(WallpaperChange.User, WallpaperWatch.Detect(store.ExpectedPaths(saved), [Path.Combine(dir, "custom.png")]));

            store.SetReleased(monitors, false);
            File.WriteAllText(file, "nouvelle image Python");
            Assert.Equal("image Python", File.ReadAllText(store.Load(monitors).Single().Path));
            Assert.True(!store.IsReleased(monitors));
            Assert.True(legacy.IsReleased(monitors));
        }
        finally { Directory.Delete(dir, true); }
    }

    [Test]
    public void UneConfigurationIncomplètePeutEtreReprisePlusTard()
    {
        string dir = Path.Combine(Path.GetTempPath(), "wallcraft-configs-" + Guid.NewGuid().ToString("N"));
        MonitorInfo[] monitors = [new() { Width = 1920, Height = 1080 }];
        try
        {
            var legacy = new WallpaperStore(Path.Combine(dir, "legacy"));
            var store = new WallpaperStore(Path.Combine(dir, "store"), legacy.Root);
            const string prefix = "wallcraft_20261113-120000";
            string sourceFile = Path.Combine(legacy.DirectoryFor(monitors), prefix + "_pos_00.png");
            legacy.Save(monitors, [(monitors[0], sourceFile)], prefix);
            string folder = store.DirectoryFor(monitors);
            Assert.Equal(0, store.Load(monitors).Count);
            Assert.Equal(0, Directory.EnumerateFiles(folder).Count());

            File.WriteAllText(sourceFile, "image encore disponible");
            Assert.Equal("image encore disponible", File.ReadAllText(store.Load(monitors).Single().Path));
            Assert.Equal(1, Directory.EnumerateFileSystemEntries(store.Root).Count());
        }
        finally { Directory.Delete(dir, true); }
    }
}
