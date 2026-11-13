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
}
