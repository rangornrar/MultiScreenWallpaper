using System.Text;
using WallCraft.Core.Geometry;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;
using WallCraft.Core.Persistence;
using WallCraft.Core.Services;
using WallCraft.Platform.Windows;

namespace WallCraft.App.Services;

/// <summary>
/// <c>WallCraft.exe --diagnostic [dossier] [images…]</c> : vérifie la couche Windows sur la vraie machine sans rien
/// changer (écrans, EDID, fonds actuels, visages, rendu HD et découpe dans le dossier). <c>--apply</c> applique en plus
/// le résultat comme fond d'écran. Écrit <c>diagnostic.txt</c> dans le dossier.
/// </summary>
public static class Diagnostic
{
    public static async Task<int> RunAsync(string[] args)
    {
        string outDir = args.FirstOrDefault(a => !a.StartsWith("--", StringComparison.Ordinal))
            ?? Path.Combine(Path.GetTempPath(), "WallCraft-diagnostic");
        Directory.CreateDirectory(outDir);
        var images = args.Skip(1).Where(a => !a.StartsWith("--", StringComparison.Ordinal) && File.Exists(a)).ToList();
        bool apply = args.Contains("--apply");
        var log = new StringBuilder();
        void Line(string s) => log.AppendLine(s);
        int code = 0;
        try
        {
            var monitors = Monitors.Enumerate();
            foreach (var m in monitors)
            {
                string mm = m.WidthMm is double w ? $"{w}×{m.HeightMm} mm ({Edid.DiagonalInches(w, m.HeightMm ?? 0):F1}″)" : "taille inconnue";
                Line($"ÉCRAN {m.Name} {m.HwId} {m.Width}×{m.Height} @({m.X},{m.Y}) {(m.IsPrimary ? "principal " : "")}{mm}");
            }
            Line("NOMS " + string.Join(" | ", MonitorNames.Labels(monitors, PositionWords.French)));
            Line("EMPREINTE " + CompositionLayout.Signature(monitors));
            var pixels = CompositionLayout.Apply(monitors);
            Line($"COMPOSITION pixels {pixels.Width}×{pixels.Height}");
            var physical = new PhysicalSettings { Enabled = true };
            var phys = CompositionLayout.Apply(monitors.Select(m => m.Clone()).ToList(), physical);
            Line($"COMPOSITION taille réelle {phys.Width}×{phys.Height}");
            CompositionLayout.Apply(monitors);

            foreach (var c in DesktopWallpaper.Current())
                Line($"FOND ACTUEL {c.Monitor.Left},{c.Monitor.Top},{c.Monitor.Right},{c.Monitor.Bottom} = {c.Path}");
            Line($"DÉMARRAGE AUTO {Autostart.IsEnabled()}");

            var loaded = new List<CompositionImage>();
            foreach (var path in images)
            {
                var (w, h) = await ImageDecoder.ReadSizeAsync(path);
                var proxy = await ImageDecoder.DecodeAsync(path, ImageDecoder.ProxyMaxSize);
                var focus = await FaceFocus.FindAsync(proxy);
                Line($"IMAGE {Path.GetFileName(path)} {w}×{h} vignette {proxy.Width}×{proxy.Height} point d'intérêt ({focus.X:F3}, {focus.Y:F3})");
                loaded.Add(new CompositionImage(path, w, h) { Focus = focus });
            }
            if (loaded.Count > 0)
            {
                new LayoutEngine().Apply(LayoutModes.Optimal, pixels.Width, pixels.Height, loaded, fill: true);
                var store = new WallpaperStore(Path.Combine(outDir, "configs"));
                var clock = System.Diagnostics.Stopwatch.StartNew();
                if (apply)
                {
                    var outcome = await WallpaperApplier.RenderAndApplyAsync(loaded, pixels.Width, pixels.Height, monitors, Windows.UI.Color.FromArgb(255, 0, 0, 0), store);
                    Line($"APPLICATION {outcome.Status} en {clock.Elapsed.TotalSeconds:F1} s {string.Join(" ; ", outcome.Errors)}");
                    foreach (var (m, p) in outcome.Pieces) Line($"  {m.Name} ← {p}");
                }
                else
                {
                    var background = Windows.UI.Color.FromArgb(255, 0, 0, 0);
                    var pieces = await HdRenderer.SplitAsync(loaded, pixels.Width, pixels.Height, monitors, background, outDir, "ecran");
                    Line($"RENDU {pieces.Count} écran(s) en {clock.Elapsed.TotalSeconds:F1} s, sans application");
                    using var composite = await HdRenderer.ComposeAsync(loaded, pixels.Width, pixels.Height, background);
                    await composite.SaveAsync(Path.Combine(outDir, "composition.png"));
                }
            }
            Line("TERMINÉ");
        }
        catch (Exception e)
        {
            Line("ERREUR " + e);
            code = 1;
        }
        await File.WriteAllTextAsync(Path.Combine(outDir, "diagnostic.txt"), log.ToString());
        return code;
    }
}
