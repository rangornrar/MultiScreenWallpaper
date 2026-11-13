using WallCraft.Core.Geometry;
using WallCraft.Core.Model;
using WallCraft.Core.Services;
using WallCraft.Platform.Windows;

namespace WallCraft.App.Services;

public enum ApplyStatus { Ok, Partial, Span, Failed, NoMonitors }

public sealed record ApplyOutcome(ApplyStatus Status, List<string> Errors, List<(MonitorInfo Monitor, string Path)> Pieces);

/// <summary>
/// Rendu HD, découpe par écran, application Windows puis mémorisation pour cette configuration d'écrans
/// (portage de services.render_and_apply). À appeler hors du fil de l'interface.
/// </summary>
public static class WallpaperApplier
{
    public static async Task<ApplyOutcome> RenderAndApplyAsync(
        IReadOnlyList<CompositionImage> images, int width, int height, IReadOnlyList<MonitorInfo> monitors,
        Windows.UI.Color background, WallpaperStore store, CancellationToken cancel = default)
    {
        string outDir = store.DirectoryFor(monitors);
        // Nom unique à chaque application : Windows ne garde pas en cache une ancienne version.
        string prefix = "wallcraft_" + Guid.NewGuid().ToString("N");
        var pieces = await HdRenderer.SplitAsync(images, width, height, monitors, background, outDir, prefix, cancel);
        if (pieces.Count == 0) return new ApplyOutcome(ApplyStatus.NoMonitors, [], pieces);
        return await ApplyPiecesAsync(pieces, monitors, background, store, prefix, outDir);
    }

    /// <summary>Applique des images déjà découpées (nouveau rendu ou fond mémorisé) et met à jour la mémoire.</summary>
    public static async Task<ApplyOutcome> ApplyPiecesAsync(
        List<(MonitorInfo Monitor, string Path)> pieces, IReadOnlyList<MonitorInfo> monitors, Windows.UI.Color background,
        WallpaperStore store, string prefix, string outDir)
    {
        var result = await Task.Run(() => DesktopWallpaper.Apply(pieces, (background.R, background.G, background.B)));
        if (result.Success)
        {
            store.Save(monitors.ToList(), pieces, prefix); // supprime les anciens fichiers seulement après succès
            return new ApplyOutcome(ApplyStatus.Ok, [], pieces);
        }
        if (result.Applied > 0) return new ApplyOutcome(ApplyStatus.Partial, result.Errors, pieces);

        string spanPath = await HdRenderer.BuildSpanAsync(pieces, background, Path.Combine(outDir, prefix + "_span.png"));
        if (await Task.Run(() => DesktopWallpaper.ApplySpan(spanPath)))
        {
            store.Save(monitors.ToList(), pieces, prefix);
            return new ApplyOutcome(ApplyStatus.Span, result.Errors, pieces);
        }
        return new ApplyOutcome(ApplyStatus.Failed, result.Errors, pieces);
    }
}
