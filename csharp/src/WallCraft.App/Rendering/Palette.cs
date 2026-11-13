using Windows.UI;

namespace WallCraft.App.Rendering;

/// <summary>Couleurs des zones dessinées, reprises de la version Python (<c>self.colors</c> de ui.py et ui_views.py).</summary>
internal static class Palette
{
    public static Color Rgb(byte r, byte g, byte b, byte a = 255) => Color.FromArgb(a, r, g, b);

    public static Color Hex(uint rgb, byte a = 255) => Color.FromArgb(a, (byte)(rgb >> 16), (byte)(rgb >> 8), (byte)rgb);

    public static readonly Color CanvasBackground = Hex(0x09111f);
    public static readonly Color StageShadow = Hex(0x0c1422, 64);   // stipple gray25
    public static readonly Color Stage = Hex(0x0d1626);
    public static readonly Color Grid = Hex(0x1b2536);
    public static readonly Color Border = Hex(0x314056);
    public static readonly Color ImageShadow = Hex(0x04070d, 128);  // stipple gray50
    public static readonly Color Placeholder = Hex(0x1e2940);
    public static readonly Color Accent = Hex(0x8ab4f8);
    public static readonly Color AccentLine = Hex(0xd9e7ff);
    public static readonly Color Monitor = Hex(0x9ecbff);
    public static readonly Color MonitorChip = Hex(0x0e2236);
    public static readonly Color Warning = Hex(0xffc46e);
    public static readonly Color WarningChip = Hex(0x3a2a10);
    public static readonly Color TextMuted = Hex(0x9aa9bf);
    /// <summary>Voile des zones vues par aucun écran : (4, 7, 14, 175).</summary>
    public static readonly Color OutsideScreens = Rgb(4, 7, 14, 175);

    // Aperçu sur les écrans
    public static readonly Color DeskLine = Hex(0x485262);
    public static readonly Color Desk = Hex(0x121821);
    public static readonly Color DeskHighlight = Hex(0x2c3748);
    public static readonly Color DeskEdge = Hex(0x0c1118);
    public static readonly Color MonitorShadow = Hex(0x05070b, 128);
    public static readonly Color MonitorCase = Hex(0x151920);
    public static readonly Color MonitorCaseLine = Hex(0x262d37);
    public static readonly Color MonitorBezel = Hex(0x1e242d);
    public static readonly Color MonitorBezelLine = Hex(0x3a4554);
    public static readonly Color Panel = Hex(0x030405);
    public static readonly Color PanelGlare = Hex(0x5f6979);
    public static readonly Color PanelLine = Hex(0x0b0e13);
    public static readonly Color PreviewChip = Hex(0x232b36);
    public static readonly Color PreviewChipText = Hex(0xcfd6e0);
    public static readonly Color Stand = Hex(0x171b22);
    public static readonly Color StandLine = Hex(0x0c0f14);
    public static readonly Color StandFoot = Hex(0x11151b);
    public static readonly Color StandFootLine = Hex(0x2a313c);
    public static readonly Color StandShadow = Hex(0x090c11, 128);
}
