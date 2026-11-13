using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Imaging;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;
using WallCraft.Core.Persistence;
using WallCraft.Core.Presentation;

namespace WallCraft.Core.Tests;

/// <summary>Logique d'affichage de la fenêtre principale : textes, zones hors écran, aperçu, métadonnées du projet.</summary>
public class PresentationTests
{
    [Test]
    public void MiddleTruncateKeepsBothEnds()
    {
        Assert.Equal("court.jpg", DisplayText.MiddleTruncate("court.jpg"));
        string name = "vacances_ete_2026_plage_coucher.jpg"; // 35 caractères
        // Python : name[:11] + "…" + name[-11:]
        Assert.Equal("vacances_et…coucher.jpg", DisplayText.MiddleTruncate(name));
        Assert.Equal(24, DisplayText.MiddleTruncate(new string('a', 24)).Length);
    }

    [Test]
    public void SelectionNameShortensLongNames()
    {
        Assert.Equal("photo.png", DisplayText.SelectionName("photo.png"));
        string name = "0123456789abcdefghijklmnopqrstuvwxyz.png"; // 40 caractères
        Assert.Equal("0123456789abcdef…stuvwxyz.png", DisplayText.SelectionName(name));
    }

    [Test]
    public void LowResolutionTextUsesThresholdAndSeparator()
    {
        var img = new CompositionImage("a.jpg", 1000, 500) { W = 1000, H = 500 };
        Assert.Equal(null, DisplayText.LowResolution(img, ","));
        img.W = 2500; img.H = 1250;
        Assert.Equal("2,5", DisplayText.LowResolution(img, ","));
        Assert.Equal("2.5", DisplayText.LowResolution(img, "."));
        img.W = 1300; img.H = 650; // exactement le seuil : alerte
        Assert.Equal("1,3", DisplayText.LowResolution(img, ","));
    }

    [Test]
    public void PluralAndCropPercent()
    {
        Assert.Equal("_One", DisplayText.PluralSuffix(1));
        Assert.Equal("_Other", DisplayText.PluralSuffix(0));
        Assert.Equal("_Other", DisplayText.PluralSuffix(3));
        var img = new CompositionImage("a.jpg", 100, 100) { Crop = new CropBox(0.1, 0, 0.675, 1) };
        Assert.Equal(57, DisplayText.CropPercent(img));
    }

    [Test]
    public void FormatErrorsLimitsTheList()
    {
        var errors = Enumerable.Range(1, 10).Select(i => $"e{i}").ToList();
        string text = DisplayText.FormatErrors(errors);
        var lines = text.Split('\n');
        Assert.Equal(9, lines.Length);
        Assert.Equal("• e1", lines[0]);
        Assert.Equal("• … (+2)", lines[8]);
        string load = DisplayText.FormatErrors([new ProjectLoadError(Path.Combine("dossier", "x.jpg"), "fichier introuvable")]);
        Assert.Equal("• x.jpg : fichier introuvable", load);
    }

    [Test]
    public void OutsideCellsCoverMarginsAndGaps()
    {
        // Deux écrans 100×100 côte à côte avec 20 d'espace, le second décalé de 10 vers le bas : composition 220×110.
        IntRect[] screens = [new(0, 0, 100, 100), new(120, 10, 100, 100)];
        var cells = ScreenCoverage.OutsideCells(screens, 220, 110);
        double area = cells.Sum(c => (c.Right - c.Left) * (c.Bottom - c.Top));
        Assert.Near(220 * 110 - 2 * 100 * 100, area);
        Assert.True(cells.Contains(new CompositionCell(100, 0, 120, 10)), "espace entre les dalles");
        Assert.True(cells.Contains(new CompositionCell(0, 100, 100, 110)), "sous l'écran de gauche");
        Assert.True(cells.Contains(new CompositionCell(120, 0, 220, 10)), "au-dessus de l'écran de droite");
        // Écrans qui couvrent tout : rien à assombrir
        Assert.Equal(0, ScreenCoverage.OutsideCells([new IntRect(0, 0, 50, 50), new IntRect(50, 0, 50, 50)], 100, 50).Count);
    }

    [Test]
    public void PreviewScreensMatchPython()
    {
        // Valeurs calculées à la main avec la formule de _refresh_sim_view (mode pixels, deux écrans 1920×1080).
        IntRect[] canvases = [new(1920, 0, 1920, 1080), new(0, 0, 1920, 1080)];
        var screens = PreviewLayout.Screens(canvases, 3840, 1080, physical: false, 1000, 600);
        double span = 3840 + 180;
        double usable = Math.Max(80, 600 * 0.8 - 16 - 26);
        double scale = Math.Min((1000 - 56) / span, usable / 1080);
        double ox = (1000 - span * scale) / 2, oy = 16 + (usable - 1080 * scale) / 2;
        // Le premier écran de la liste est à droite : il a le rang 1 et reçoit l'espace.
        Assert.Near((1920 + 180) * scale + ox, screens[0].X);
        Assert.Near(ox, screens[1].X);
        Assert.Near(oy, screens[0].Y);
        Assert.Near(1920 * scale, screens[0].Width);
        Assert.Equal(0, screens[0].Index);

        var physical = PreviewLayout.Screens(canvases, 3840, 1080, physical: true, 1000, 600);
        Assert.Near(physical[1].X + physical[1].Width, physical[0].X, 1e-9, "taille réelle : pas d'espace ajouté");
        Assert.Equal(0, PreviewLayout.Screens([], 100, 100, false, 1000, 600).Count);
    }

    [Test]
    public void PreviewSlicesClipImagesToEachScreen()
    {
        var screen = new PreviewScreen(0, 100, 50, 208, 108, new IntRect(1000, 0, 1000, 500));
        var under = new CompositionImage("a.jpg", 10, 10) { X = 500, Y = -100, W = 1000, H = 400, ZIndex = 0 };
        var over = new CompositionImage("b.jpg", 10, 10) { X = 1900, Y = 400, W = 300, H = 300, ZIndex = 1 };
        var outside = new CompositionImage("c.jpg", 10, 10) { X = 0, Y = 0, W = 1000, H = 500, ZIndex = 2 };
        var slices = PreviewLayout.Slices(screen, [over, outside, under]);
        Assert.Equal(2, slices.Count);
        Assert.True(ReferenceEquals(under, slices[0].Image), "ordre des calques");
        double k = 200.0 / 1000; // dalle de 200 px pour 1000 unités (cadre de 4 px retiré)
        var s = slices[0];
        Assert.Near(500, s.SourceLeft); Assert.Near(100, s.SourceTop); Assert.Near(1000, s.SourceRight); Assert.Near(400, s.SourceBottom);
        Assert.Near(104, s.X); Assert.Near(54, s.Y); Assert.Near(500 * k, s.Width); Assert.Near(300 * (100.0 / 500), s.Height);
        var t = slices[1];
        Assert.Near(0, t.SourceLeft); Assert.Near(100, t.SourceRight); Assert.Near(100, t.SourceBottom);
        Assert.Near(104 + 900 * k, t.X); Assert.Near(54 + 400 * (100.0 / 500), t.Y);
    }

    [Test]
    public void ProjectMetaIsCompatibleWithPython()
    {
        var m = new MonitorInfo { Name = @"\\.\DISPLAY1", X = 0, Y = 0, Width = 1920, Height = 1080, WidthMm = 527, HeightMm = 296, HwId = "PHL#1" };
        m.Canvas = new IntRect(0, 0, 1920, 1080);
        var meta = ProjectMeta.Build(1920, 1080, LayoutModes.Grid, fill: true, physical: false, [m]);
        Assert.Equal("[1920,1080]", meta["target"]!.ToJsonString());
        var mon = (JsonObject)((JsonArray)meta["monitors"]!)[0]!;
        Assert.Equal(@"\\.\DISPLAY1", mon["device_id"]!.GetValue<string>());
        Assert.Equal("[0,0,1920,1080]", mon["canvas"]!.ToJsonString());
        Assert.Equal(LayoutModes.Grid, ProjectMeta.Layout(meta));
        Assert.Equal(true, ProjectMeta.Fill(meta));
        Assert.Equal(false, ProjectMeta.Physical(meta));

        var python = (JsonObject)JsonNode.Parse("""{"layout": "layout_inconnu", "fill": 0}""")!;
        Assert.Equal(null, ProjectMeta.Layout(python));
        Assert.Equal(false, ProjectMeta.Fill(python));
        Assert.Equal(null, ProjectMeta.Fill([]));
    }

    [Test]
    public void ThumbnailFitsWithoutUpscaling()
    {
        var src = new PixelBuffer(4, 2);
        for (int i = 0; i < 8; i++)
        {
            byte v = (byte)(i % 4 < 2 ? 0 : 200);
            src.Data[i * 4] = v; src.Data[i * 4 + 1] = v; src.Data[i * 4 + 2] = v; src.Data[i * 4 + 3] = 255;
        }
        var t = Thumbnail.Fit(src, 2, 2);
        Assert.Equal(2, t.Width);
        Assert.Equal(1, t.Height);
        Assert.Equal((byte)0, t.Data[0]);
        Assert.Equal((byte)200, t.Data[4]);
        Assert.Equal((byte)255, t.Data[7]);
        var same = Thumbnail.Fit(src, 100, 100);
        Assert.Equal(4, same.Width);
    }
}
