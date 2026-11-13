using System.Numerics;
using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;
using WallCraft.Core.Services;

namespace WallCraft.Core.Tests;

/// <summary>
/// Comparaison au code Python : les fichiers de tests/fixtures sont produits par tools/export_golden.py
/// en exécutant la version Python sur un jeu fixe de cas.
/// </summary>
public class GoldenTests
{
    private const double Tol = 0.01;

    private static JsonObject Load(string name) => (JsonObject)JsonNode.Parse(File.ReadAllText(Fixtures.Path(name)))!;
    private static double D(JsonNode? n) => n!.GetValue<double>();
    private static int I(JsonNode? n) => (int)n!.GetValue<double>();
    private static string S(JsonNode? n) => n!.GetValue<string>();
    private static double? ND(JsonNode? n) => n is null ? null : n.GetValue<double>();
    private static IEnumerable<JsonObject> Arr(JsonNode? n) => ((JsonArray)n!).OfType<JsonObject>();

    // --- Générateur aléatoire ---

    [Test]
    public void RandomSequences()
    {
        foreach (var s in Arr(Load("random.json")["seeds"]))
        {
            var seed = BigInteger.Parse(s["seed"]!.ToJsonString().Trim('"'));
            string id = $"graine {seed}";

            var state = new PythonRandom(seed).State;
            Assert.SequenceEqual(((JsonArray)s["state_head"]!).Select(v => (uint)v!.GetValue<double>()), state.Words.Take(4), $"{id} état");

            var r = new PythonRandom(seed);
            Assert.SequenceEqual(((JsonArray)s["random"]!).Select(D), Enumerable.Range(0, 20).Select(_ => r.Random()), $"{id} random");

            foreach (var g in Arr(s["getrandbits"]).Where(g => I(g["k"]) <= 32))
            {
                r = new PythonRandom(seed);
                int k = I(g["k"]);
                Assert.SequenceEqual(((JsonArray)g["values"]!).Select(v => (uint)v!.GetValue<double>()), Enumerable.Range(0, 20).Select(_ => r.GetRandBits(k)), $"{id} getrandbits({k})");
            }
            foreach (var g in Arr(s["randint"]))
            {
                r = new PythonRandom(seed);
                int a = I(g["a"]), b = I(g["b"]);
                Assert.SequenceEqual(((JsonArray)g["values"]!).Select(I), Enumerable.Range(0, 20).Select(_ => r.RandInt(a, b)), $"{id} randint({a},{b})");
            }
            r = new PythonRandom(seed);
            foreach (var g in Arr(s["shuffle_chain"]))
            {
                var list = Enumerable.Range(0, I(g["n"])).ToList();
                r.Shuffle(list);
                Assert.SequenceEqual(((JsonArray)g["result"]!).Select(I), list, $"{id} shuffle({I(g["n"])})");
            }
            r = new PythonRandom(seed);
            Assert.SequenceEqual(((JsonArray)s["choice"]!).Select(v => v!.GetValue<bool>()), Enumerable.Range(0, 20).Select(_ => r.Choice(new[] { true, false })), $"{id} choice");
            r = new PythonRandom(seed);
            Assert.SequenceEqual(((JsonArray)s["uniform"]!).Select(D), Enumerable.Range(0, 20).Select(_ => r.Uniform(-0.1, 0.1)), $"{id} uniform");
            foreach (var g in Arr(s["sample"]))
            {
                r = new PythonRandom(seed);
                var population = Enumerable.Range(0, I(g["n"])).ToList();
                Assert.SequenceEqual(((JsonArray)g["result"]!).Select(I), r.Sample(population, I(g["k"])), $"{id} sample({I(g["n"])},{I(g["k"])})");
            }
        }
    }

    // --- Graines ---

    [Test]
    public void SeedKeysAndSeeds()
    {
        foreach (var c in Arr(Load("seeds.json")["cases"]))
        {
            var images = Arr(c["images"]).Select(i => (S(i["path"]), D(i["ratio"])));
            string key = LayoutEngine.SeedKey(S(c["mode"]), D(c["tw"]), D(c["th"]), I(c["variant"]), images);
            Assert.Equal(S(c["key"]), key, $"clé {S(c["id"])}");
            Assert.Equal(c["seed"]!.GetValue<long>(), PythonCompat.Sha1Prefix48(key), $"graine {S(c["id"])}");
        }
    }

    // --- Dispositions ---

    private static List<CompositionImage> Images(JsonNode? node) => Arr(node).Select(i =>
    {
        var size = (JsonArray)i["size"]!;
        var img = new CompositionImage(S(i["path"]), I(size[0]), I(size[1]));
        if (i["focus"] is JsonArray f) img.Focus = new FocusPoint(D(f[0]), D(f[1]));
        return img;
    }).ToList();

    private static void AssertPlacement(JsonObject expected, CompositionImage img, string id)
    {
        Assert.Near(D(expected["x"]), img.X, Tol, $"{id} x");
        Assert.Near(D(expected["y"]), img.Y, Tol, $"{id} y");
        if (expected["w"] is null) Assert.True(img.W is null, $"{id} w non placé"); else Assert.Near(D(expected["w"]), img.W ?? double.NaN, Tol, $"{id} w");
        if (expected["h"] is null) Assert.True(img.H is null, $"{id} h non placé"); else Assert.Near(D(expected["h"]), img.H ?? double.NaN, Tol, $"{id} h");
        var crop = (JsonArray)expected["crop"]!;
        Assert.Near(D(crop[0]), img.Crop.Left, 1e-9, $"{id} crop.l");
        Assert.Near(D(crop[1]), img.Crop.Top, 1e-9, $"{id} crop.t");
        Assert.Near(D(crop[2]), img.Crop.Right, 1e-9, $"{id} crop.r");
        Assert.Near(D(crop[3]), img.Crop.Bottom, 1e-9, $"{id} crop.b");
        if (expected["z"] is not null) Assert.Equal(I(expected["z"]), img.ZIndex, $"{id} z");
        if (expected["angle"] is not null) Assert.Equal(I(expected["angle"]), img.Angle, $"{id} angle");
    }

    [Test]
    public void Layouts()
    {
        var engine = new LayoutEngine { OptimalMaxTime = 1e9 };
        int count = 0;
        var failures = new List<string>();
        foreach (var c in Arr(Load("layouts.json")["cases"]))
        {
            string id = S(c["id"]);
            var images = Images(c["images"]);
            var target = (JsonArray)c["target"]!;
            engine.Apply(S(c["mode"]), D(target[0]), D(target[1]), images, c["fill"]!.GetValue<bool>(), I(c["variant"]));
            var expected = Arr(c["result"]).ToList();
            try
            {
                for (int k = 0; k < images.Count; k++) AssertPlacement(expected[k], images[k], $"{id} image {k}");
            }
            catch (AssertionException e)
            {
                failures.Add(e.Message);
            }
            count++;
        }
        Assert.True(count > 1000, $"seulement {count} cas");
        Assert.True(failures.Count == 0, $"{failures.Count}/{count} cas différents, dont : {string.Join(" | ", failures.Take(5))}");
    }

    [Test]
    public void Variants()
    {
        var engine = new LayoutEngine { OptimalMaxTime = 1e9 };
        foreach (var c in Arr(Load("variants.json")["cases"]))
        {
            string id = S(c["id"]);
            var images = Images(c["images"]);
            var target = (JsonArray)c["target"]!;
            var result = engine.Variants(S(c["mode"]), D(target[0]), D(target[1]), images, c["fill"]!.GetValue<bool>(), I(c["count"]));
            var expected = ((JsonArray)c["variants"]!).Select(v => Arr(v).ToList()).ToList();
            Assert.Equal(expected.Count, result.Count, $"{id} nombre de variantes");
            for (int v = 0; v < expected.Count; v++)
            {
                for (int k = 0; k < images.Count; k++)
                {
                    var p = result[v][k];
                    var clone = images[k].Clone();
                    clone.X = p.X; clone.Y = p.Y; clone.W = p.W; clone.H = p.H; clone.Crop = p.Crop; clone.ZIndex = p.ZIndex;
                    AssertPlacement(expected[v][k], clone, $"{id} variante {v} image {k}");
                }
            }
        }
    }

    [Test]
    public void Placements()
    {
        var engine = new LayoutEngine();
        foreach (var c in Arr(Load("placement.json")["cases"]))
        {
            string id = S(c["id"]);
            var im = (JsonObject)c["image"]!;
            var size = (JsonArray)im["size"]!;
            var img = new CompositionImage("x.jpg", I(size[0]), I(size[1]));
            if (im["focus"] is JsonArray f) img.Focus = new FocusPoint(D(f[0]), D(f[1]));
            for (int i = 0; i < I(im["rotations_cw"]); i++) img.RotateClockwise();
            Assert.Equal(I(im["angle"]), img.Angle, $"{id} angle");
            var crop = (JsonArray)im["crop"]!;
            img.Crop = new CropBox(D(crop[0]), D(crop[1]), D(crop[2]), D(crop[3]));
            Assert.Near(D(im["visible_aspect"]), img.VisibleAspect, 1e-12, $"{id} ratio visible");
            var box = ((JsonArray)c["box"]!).Select(D).ToArray();
            if (S(c["function"]) == "fit_inside") LayoutEngine.FitInside(img, box[0], box[1], box[2], box[3]);
            else engine.CropCover(img, box[0], box[1], box[2], box[3]);
            AssertPlacement((JsonObject)c["result"]!, img, id);
        }
    }

    // --- Géométrie ---

    private static List<MonitorInfo> Monitors(JsonNode? node) => Arr(node).Select(m => new MonitorInfo
    {
        Name = m["name"]?.GetValue<string>() ?? "", X = I(m["x"]), Y = I(m["y"]), Width = I(m["width"]), Height = I(m["height"]),
        WidthMm = ND(m["width_mm"]), HeightMm = ND(m["height_mm"]), HwId = m["hw_id"]?.GetValue<string>() ?? "",
    }).ToList();

    private static PhysicalSettings Settings(JsonNode? node) => PhysicalSettings.FromJson(node);

    [Test]
    public void Edids()
    {
        foreach (var c in Arr(Load("geometry.json")["edid"]))
        {
            var bytes = Convert.FromHexString(c["hex"]?.GetValue<string>() ?? "");
            var result = Edid.ParseSizeMm(bytes);
            if (c["result"] is JsonArray r)
            {
                Assert.True(result is not null, $"{S(c["id"])} : taille attendue");
                Assert.Equal(D(r[0]), result!.Value.WidthMm, S(c["id"]));
                Assert.Equal(D(r[1]), result!.Value.HeightMm, S(c["id"]));
            }
            else Assert.True(result is null, $"{S(c["id"])} : aucune taille attendue");
        }
        foreach (var c in Arr(Load("geometry.json")["diagonal_inches"]))
            Assert.Near(D(c["inches"]), Edid.DiagonalInches(D(c["width_mm"]), D(c["height_mm"])), 1e-12);
    }

    [Test]
    public void VendorsAndLabels()
    {
        var geo = Load("geometry.json");
        foreach (var c in Arr(geo["vendors"]))
            Assert.Equal(S(c["vendor"]), MonitorNames.Vendor(new MonitorInfo { HwId = c["hw_id"]?.GetValue<string>() ?? "" }), $"fabricant {c["hw_id"]}");

        foreach (var c in Arr(geo["labels"]))
        {
            var monitors = Monitors(c["monitors"]);
            if (c["settings"] is JsonObject s) CompositionLayout.Apply(monitors, Settings(s));
            else if (c["canvas"] is JsonArray canvas)
                for (int i = 0; i < monitors.Count; i++)
                {
                    var r = ((JsonArray)canvas[i]!).Select(I).ToArray();
                    monitors[i].Canvas = new IntRect(r[0], r[1], r[2], r[3]);
                }
            foreach (var res in Arr(c["results"]))
            {
                var words = S(res["words_id"]) == "fr" ? PositionWords.French : PositionWords.English;
                Assert.SequenceEqual(((JsonArray)res["labels"]!).Select(S), MonitorNames.Labels(monitors, words, S(res["decimal"])), $"noms {S(c["id"])} {S(res["words_id"])}");
            }
        }
    }

    [Test]
    public void UpscaleFactors()
    {
        foreach (var c in Arr(Load("geometry.json")["upscale_factor"]))
        {
            var size = (JsonArray)c["original_size"]!;
            var crop = ((JsonArray)c["crop"]!).Select(D).ToArray();
            var img = new CompositionImage("x", I(size[0]), I(size[1]))
            {
                Angle = I(c["angle"]), Crop = new CropBox(crop[0], crop[1], crop[2], crop[3]), W = D(c["w"]), H = D(c["h"]),
            };
            Assert.Near(D(c["factor"]), Upscale.Factor(img), 1e-12, S(c["id"]));
        }
    }

    [Test]
    public void PhysicalSettingsRoundTrip()
    {
        foreach (var c in Arr(Load("geometry.json")["physical_settings"]))
        {
            var expected = (JsonObject)c["to_dict"]!;
            var actual = PhysicalSettings.FromJson(c["input"]).ToJson();
            Assert.Equal(expected["enabled"]!.GetValue<bool>(), actual["enabled"]!.GetValue<bool>(), "enabled");
            Assert.Equal(D(expected["bezel_mm"]), D(actual["bezel_mm"]), "bezel_mm");
            Assert.Equal(((JsonObject)expected["overrides"]!).Count, ((JsonObject)actual["overrides"]!).Count, "overrides");
        }
    }

    [Test]
    public void CompositionLayouts()
    {
        foreach (var c in Arr(Load("geometry.json")["layouts"]))
        {
            string id = S(c["id"]);
            var monitors = Monitors(c["monitors"]);
            var settings = c["settings"] is null ? null : Settings(c["settings"]);
            var positions = CompositionLayout.PhysicalPositions(monitors, settings ?? new PhysicalSettings());
            var expectedPos = ((JsonArray)c["physical_positions_mm"]!).Select(p => ((JsonArray)p!).Select(D).ToArray()).ToList();
            for (int i = 0; i < monitors.Count; i++)
            {
                Assert.Near(expectedPos[i][0], positions[i].X, 1e-9, $"{id} mm x {i}");
                Assert.Near(expectedPos[i][1], positions[i].Y, 1e-9, $"{id} mm y {i}");
                Assert.Near(expectedPos[i][2], positions[i].W, 1e-9, $"{id} mm w {i}");
                Assert.Near(expectedPos[i][3], positions[i].H, 1e-9, $"{id} mm h {i}");
            }
            var size = CompositionLayout.Apply(monitors, settings);
            var expectedSize = ((JsonArray)c["size"]!).Select(I).ToArray();
            Assert.Equal((expectedSize[0], expectedSize[1]), size, $"{id} taille");
            var canvas = ((JsonArray)c["canvas"]!).Select(r => ((JsonArray)r!).Select(I).ToArray()).ToList();
            for (int i = 0; i < monitors.Count; i++)
                Assert.Equal(new IntRect(canvas[i][0], canvas[i][1], canvas[i][2], canvas[i][3]), monitors[i].Canvas!.Value, $"{id} canvas {i}");
        }
    }

    [Test]
    public void Signatures()
    {
        foreach (var c in Arr(Load("geometry.json")["signatures"]))
            Assert.Equal(S(c["signature"]), CompositionLayout.Signature(Monitors(c["monitors"])), $"empreinte {S(c["id"])}");
    }

    [Test]
    public void SplitBoxes()
    {
        var layouts = Arr(Load("geometry.json")["layouts"]).ToDictionary(l => S(l["id"]));
        foreach (var c in Arr(Load("split.json")["cases"]))
        {
            string id = S(c["id"]);
            var canvasRects = c["canvas"] as JsonArray;
            var monitors = c["layout"] is null
                ? canvasRects!.Select(r => new MonitorInfo { Name = "", Width = I(((JsonArray)r!)[2]), Height = I(((JsonArray)r!)[3]) }).ToList()
                : Monitors(layouts[S(c["layout"])]["monitors"]);
            if (S(c["mode"]) == "canvas")
            {
                var canvas = ((JsonArray)c["canvas"]!).Select(r => ((JsonArray)r!).Select(I).ToArray()).ToList();
                for (int i = 0; i < monitors.Count; i++) monitors[i].Canvas = new IntRect(canvas[i][0], canvas[i][1], canvas[i][2], canvas[i][3]);
            }
            var size = ((JsonArray)c["image_size"]!).Select(I).ToArray();
            var boxes = CompositionLayout.SplitBoxes(monitors, size[0], size[1]);
            foreach (var piece in Arr(c["pieces"]))
            {
                int index = I(piece["index"]);
                if (piece["box"] is JsonArray b)
                {
                    var e = b.Select(I).ToArray();
                    Assert.Equal((e[0], e[1], e[2], e[3]), boxes[index]!.Value, $"{id} écran {index}");
                }
                else Assert.True(boxes[index] is null, $"{id} écran {index} : rien attendu");
            }
        }
    }

    // --- Services ---

    [Test]
    public void ThemeDetection()
    {
        var svc = Load("services.json");
        foreach (var c in Arr(svc["is_theme_wallpaper"]))
            Assert.Equal(c["result"]!.GetValue<bool>(), WallpaperWatch.IsThemeWallpaper(c["path"]?.GetValue<string>()), $"thème {c["path"]}");

        foreach (var c in Arr(svc["wallpaper_change"]))
        {
            var expected = ((JsonArray)c["expected_paths"]!).Select(S).ToList();
            var current = Arr(c["current"]).Select(x => x["path"]?.GetValue<string>()).ToList();
            var want = c["result"] is null ? WallpaperChange.None : S(c["result"]) == "theme" ? WallpaperChange.Theme : WallpaperChange.User;
            Assert.Equal(want, WallpaperWatch.Detect(expected, current), S(c["id"]));
        }
    }

    [Test]
    public void RotationPicks()
    {
        foreach (var c in Arr(Load("services.json")["pick_rotation"]))
        {
            var files = ((JsonArray)c["files"]!).Select(S).ToList();
            var previous = ((JsonArray)c["previous"]!).Select(S).ToList();
            var result = Rotation.Pick(files, I(c["count"]), previous, new PythonRandom(c["seed"]!.GetValue<long>()));
            Assert.SequenceEqual(((JsonArray)c["result"]!).Select(S), result, S(c["id"]));
        }
    }
}
