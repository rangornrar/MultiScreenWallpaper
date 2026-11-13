using System.Text.Json.Nodes;
using WallCraft.Core.Editing;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;

namespace WallCraft.Core.Tests;

/// <summary>
/// Édition de la composition : les scénarios de fixtures/editing.json (produits par tools/export_golden_editing.py en
/// pilotant la vraie classe WallpaperApp de ui.py) sont rejoués sur le cœur C# et l'état est comparé après chaque opération.
/// </summary>
public class EditingTests
{
    private static JsonObject Load() => (JsonObject)JsonNode.Parse(File.ReadAllText(Fixtures.Path("editing.json")))!;
    private static double D(JsonNode? n) => n!.GetValue<double>();
    private static int I(JsonNode? n) => (int)n!.GetValue<double>();
    private static string S(JsonNode? n) => n!.GetValue<string>();

    private static void Near(double expected, double actual, string message)
        => Assert.Near(expected, actual, 1e-6 * Math.Max(1, Math.Abs(expected)), message);

    private static PointerButton Button(JsonNode? n) => (n is null ? 1 : I(n)) switch
    {
        1 => PointerButton.Left,
        2 => PointerButton.Middle,
        _ => PointerButton.Right,
    };

    private static EditMode Mode(string mode) => mode switch
    {
        "move" => EditMode.Move,
        "scale" => EditMode.Scale,
        "crop" => EditMode.Crop,
        _ => throw new ArgumentException(mode),
    };

    /// <summary>Rejoue un scénario Python et compare l'état après chaque opération ; renvoie le nombre d'opérations comparées.</summary>
    private static int Replay(JsonObject scenario)
    {
        string name = S(scenario["name"]);
        var target = (JsonArray)scenario["target"]!;
        var viewport = (JsonArray)scenario["viewport"]!;
        var screens = ((JsonArray)scenario["monitors"]!).Select(m =>
        {
            var a = (JsonArray)m!;
            return (D(a[0]), D(a[1]), D(a[2]), D(a[3]));
        }).ToList();

        var doc = new CompositionDocument(D(target[0]), D(target[1]));
        var view = new ViewTransform();
        var ctl = new EditController(doc, view);
        ctl.FitToView(D(viewport[0]), D(viewport[1]));
        var engine = new LayoutEngine();
        int counter = 0;
        int step = 0;

        foreach (var s in ((JsonArray)scenario["steps"]!).OfType<JsonObject>())
        {
            var op = (JsonObject)s["op"]!;
            string kind = S(op["op"]);
            var mods = op["shift"]?.GetValue<bool>() == true ? EditModifiers.Shift : EditModifiers.None;
            switch (kind)
            {
                case "start": break;
                case "down": ctl.PointerPressed(D(op["x"]), D(op["y"]), Button(op["button"]), mods); break;
                case "move": ctl.PointerMoved(D(op["x"]), D(op["y"]), mods); break;
                case "up": ctl.PointerReleased(D(op["x"]), D(op["y"]), Button(op["button"])); break;
                case "wheel": ctl.Wheel(D(op["x"]), D(op["y"]), D(op["delta"])); break;
                case "mode": ctl.Mode = Mode(S(op["mode"])); break;
                case "add":
                    ctl.AddImagesAtViewCenter(((JsonArray)op["sizes"]!).Select(sz =>
                        new CompositionImage($"img{counter++}.png", I(sz![0]), I(sz[1])) { Focus = FocusPoint.Center }).ToList());
                    break;
                case "fit": ctl.FitToView(D(op["viewport"]![0]), D(op["viewport"]![1])); break;
                case "resize": ctl.ViewportResized(D(op["viewport"]![0]), D(op["viewport"]![1])); break;
                case "geometry": doc.SetSize(D(op["size"]![0]), D(op["size"]![1])); break;
                case "autofill": doc.ApplyLayout(engine, S(op["layout"]), op["fill"]!.GetValue<bool>(), screens); break;
                case "undo": doc.Undo(); break;
                case "redo": doc.Redo(); break;
                case "rotate": doc.RotateSelected(); break;
                case "remove": doc.RemoveSelected(); break;
                case "back": doc.SendBackward(); break;
                case "front": doc.BringForward(); break;
                case "select": doc.Select(I(op["index"])); break;
                case "adjust":
                    if (doc.Selected is { } sel)
                    {
                        sel.Brightness = D(op["brightness"]);
                        doc.Commit("Adjust", ChangeReason.Adjusted);
                    }
                    break;
                default: throw new InvalidOperationException(kind);
            }
            Compare((JsonObject)s["state"]!, doc, view, ctl, $"{name} étape {step} ({kind})");
            step++;
        }
        return step - 1;
    }

    private static void Compare(JsonObject state, CompositionDocument doc, ViewTransform view, EditController ctl, string id)
    {
        var images = ((JsonArray)state["images"]!).OfType<JsonObject>().ToList();
        Assert.Equal(images.Count, doc.Images.Count, $"{id} nombre d'images");
        for (int i = 0; i < images.Count; i++)
        {
            var e = images[i];
            var a = doc.Images[i];
            string iid = $"{id} image {i}";
            Assert.Equal(S(e["path"]), a.Path, $"{iid} chemin");
            Near(D(e["x"]), a.X, $"{iid} x");
            Near(D(e["y"]), a.Y, $"{iid} y");
            Near(D(e["w"]), a.W ?? double.NaN, $"{iid} w");
            Near(D(e["h"]), a.H ?? double.NaN, $"{iid} h");
            Assert.Equal(I(e["angle"]), a.Angle, $"{iid} angle");
            Assert.Equal(I(e["z"]), a.ZIndex, $"{iid} z");
            var crop = (JsonArray)e["crop"]!;
            Near(D(crop[0]), a.Crop.Left, $"{iid} rognage gauche");
            Near(D(crop[1]), a.Crop.Top, $"{iid} rognage haut");
            Near(D(crop[2]), a.Crop.Right, $"{iid} rognage droite");
            Near(D(crop[3]), a.Crop.Bottom, $"{iid} rognage bas");
        }
        int? active = state["active"] is null ? null : I(state["active"]);
        Assert.Equal(active, doc.SelectedIndex, $"{id} sélection");
        var history = (JsonArray)state["history"]!;
        Assert.Equal(I(history[0]), doc.History.Index, $"{id} position dans l'historique");
        Assert.Equal(I(history[1]), doc.History.Count, $"{id} taille de l'historique");
        var v = (JsonArray)state["view"]!;
        Near(D(v[0]), view.Zoom, $"{id} zoom");
        Near(D(v[1]), view.OffsetX, $"{id} décalage x");
        Near(D(v[2]), view.OffsetY, $"{id} décalage y");
        Assert.Equal(Mode(S(state["mode"])), ctl.Mode, $"{id} outil");
    }

    [Test]
    public void ScenariosIdentiquesAPython()
    {
        var data = Load();
        Assert.Equal(EditController.SnapDistance, D(data["snap_dist"]), "SNAP_DIST");
        Assert.Equal(EditController.MinCrop, D(data["min_crop"]), "MIN_CROP");
        var scenarios = ((JsonArray)data["scenarios"]!).OfType<JsonObject>().ToList();
        int ops = scenarios.Sum(Replay);
        Assert.True(scenarios.Count >= 60 && ops > 3000, $"{scenarios.Count} scénarios, {ops} opérations");
    }

    // --- Tests ciblés (lisibles sans la fixture) ---

    private static (CompositionDocument Doc, ViewTransform View, EditController Ctl) Setup()
    {
        var doc = new CompositionDocument(5760, 1080);
        var view = new ViewTransform();
        view.Set(0.2, 0, 0);
        return (doc, view, new EditController(doc, view));
    }

    private static CompositionImage Img(string path, double x, double y, double w, double h)
        => new(path, (int)w, (int)h) { X = x, Y = y, W = w, H = h };

    [Test]
    public void PoigneesDessineesLaOuEllesSontTestees()
    {
        var (doc, view, ctl) = Setup();
        doc.Load([Img("a", 100, 50, 1000, 500)]);
        Assert.Equal(0, ctl.Handles.Count, "pas de poignées sans sélection");
        doc.Select(0);
        Assert.Equal(0, ctl.Handles.Count, "pas de poignées en Déplacer");
        ctl.Mode = EditMode.Crop;
        var handles = ctl.Handles;
        Assert.Equal(4, handles.Count);
        Assert.Equal(new HandleInfo(HandleCorner.BottomRight, 220, 110), handles[2]);
        foreach (var h in handles)
        {
            Assert.Equal(h.Corner, ctl.HitTestHandle(h.X + 9.9, h.Y - 9.9));
            Assert.Equal<HandleCorner?>(null, ctl.HitTestHandle(h.X + 10, h.Y));
        }
        Assert.Equal(new ScreenRect(20, 10, 200, 100), ctl.SelectionScreenRect!.Value);
        Near(0.2, view.Zoom, "zoom");
    }

    [Test]
    public void AimantationEtMaj()
    {
        var (doc, _, ctl) = Setup();
        doc.Load([Img("a", 1000, 0, 500, 500), Img("b", 3000, 600, 400, 400)]);
        // b (au-dessus) amené à 10 unités à droite du bord droit de a : collé à x = 1500
        ctl.PointerPressed(3100 * 0.2, 700 * 0.2, PointerButton.Left);
        ctl.PointerMoved((3100 - 1490) * 0.2, (700 - 300) * 0.2);
        Near(1500, doc.Images[1].X, "aimanté au bord droit");
        Near(300, doc.Images[1].Y, "pas d'aimantation verticale sur les autres images");
        ctl.PointerMoved((3100 - 1490) * 0.2, (700 - 590) * 0.2, EditModifiers.Shift);
        Near(1510, doc.Images[1].X, "Maj : pas d'aimantation");
        Near(10, doc.Images[1].Y, "Maj : pas d'aimantation en haut");
        int before = doc.History.Count;
        ctl.PointerReleased(0, 0, PointerButton.Left);
        Assert.Equal(before + 1, doc.History.Count, "geste enregistré");
        Assert.Equal("Move", doc.History.CurrentLabel);
    }

    [Test]
    public void EvenementsChanged()
    {
        var (doc, _, ctl) = Setup();
        var reasons = new List<(ChangeReason, bool)>();
        doc.Changed += (_, e) => reasons.Add((e.Reason, e.Live));
        ctl.AddImagesAtViewCenter([new CompositionImage("a", 1600, 900)]);
        ctl.PointerPressed(1100, 500, PointerButton.Left);        // dans le vide : désélection et déplacement de la vue
        ctl.PointerReleased(1100, 500, PointerButton.Left);
        var img = doc.Images[0];
        var (sx, sy) = ctl.View.LogicToScreen(img.X + 10, img.Y + 10);
        ctl.PointerPressed(sx, sy, PointerButton.Left);           // sélection + déplacement
        ctl.PointerMoved(sx + 5, sy);
        ctl.PointerReleased(sx + 5, sy, PointerButton.Left);
        Assert.True(ctl.KeyDown(EditKey.Z, EditModifiers.Control));
        Assert.True(ctl.KeyDown(EditKey.R, EditModifiers.Control)); // rien de sélectionné après annulation : sans effet
        Assert.True(!ctl.KeyDown(EditKey.Z));
        Assert.SequenceEqual(
            [(ChangeReason.Added, false), (ChangeReason.Selection, false), (ChangeReason.Selection, false),
             (ChangeReason.Edited, true), (ChangeReason.Edited, false), (ChangeReason.Undo, false)],
            reasons);
    }

    [Test]
    public void NouveauProjetEtRecadrage()
    {
        var (doc, view, ctl) = Setup();
        ctl.FitToView(1200, 600);
        ctl.Wheel(600, 300, 120);
        Assert.True(view.UserZoomed);
        Assert.True(!ctl.ViewportResized(1400, 700), "pas de recadrage après un zoom de l'utilisateur");
        ctl.AddImagesAtViewCenter([new CompositionImage("a", 100, 100)]);
        ctl.Mode = EditMode.Scale;
        ctl.NewProject();
        Assert.Equal(0, doc.Images.Count);
        Assert.Equal(EditMode.Move, ctl.Mode);
        Assert.Equal(1, doc.History.Count);
        Assert.True(!view.UserZoomed);
        Near(Math.Min(1400 * 0.95 / 5760, 700 * 0.94 / 1080), view.Zoom, "recadré");
    }
}
