using WallCraft.Core.Geometry;
using WallCraft.Core.Model;

namespace WallCraft.Core.Layout;

/// <summary>Mise en page automatique sans interface (<c>_apply_auto_layout</c>), utilisée aussi par la rotation.</summary>
public static class AutoLayout
{
    /// <summary>
    /// Mosaïque avec au plus une image par écran : chaque image va sur son écran (écrans triés par position dans la
    /// composition) ; sinon disposition <paramref name="mode"/> sur toute la composition.
    /// Les écrans doivent avoir leur <see cref="MonitorInfo.Canvas"/> (après <see cref="CompositionLayout.Apply"/>).
    /// </summary>
    public static void Apply(LayoutEngine engine, string mode, int targetW, int targetH, IReadOnlyList<MonitorInfo> monitors,
        IList<CompositionImage> images, bool fill, int variant = 0)
    {
        if (mode == LayoutModes.Mosaic && monitors.Count > 0 && images.Count <= monitors.Count && monitors.All(m => m.Canvas is not null))
        {
            var rects = monitors.Select(m => m.Canvas!.Value)
                .OrderBy(r => r.X).ThenBy(r => r.Y)
                .Select(r => ((double)r.X, (double)r.Y, (double)r.Width, (double)r.Height))
                .ToList();
            engine.PlaceOnScreens(images, rects, fill);
        }
        else
        {
            engine.Apply(mode, targetW, targetH, images, fill, variant);
        }
    }
}
