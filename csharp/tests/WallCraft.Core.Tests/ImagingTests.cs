using System.Text.Json.Nodes;
using WallCraft.Core.Imaging;
using WallCraft.Core.Model;

namespace WallCraft.Core.Tests;

public class ImagingTests
{
    private static JsonObject Load() => (JsonObject)JsonNode.Parse(File.ReadAllText(Fixtures.Path("imaging.json")))!;

    [Test]
    public void EnhanceMatchesPillowExactly()
    {
        foreach (var c in Load()["enhance"]!.AsArray().OfType<JsonObject>())
        {
            var size = c["size"]!.AsArray();
            var input = new PixelBuffer((int)size[0]!, (int)size[1]!, Convert.FromHexString((string)c["input"]!));
            string filter = (string)c["filter"]!;
            PixelBuffer output = filter switch
            {
                "brightness" => Filters.Brightness(input, (double)c["factor"]!),
                "contrast" => Filters.Contrast(input, (double)c["factor"]!),
                "color" => Filters.Color(input, (double)c["factor"]!),
                _ => Filters.Apply(input, (double)c["factor"]![0]!, (double)c["factor"]![1]!, (double)c["factor"]![2]!),
            };
            Assert.Equal((string)c["output"]!, Convert.ToHexStringLower(output.Data), (string)c["id"]!);
        }
    }

    [Test]
    public void RotateMatchesPillow()
    {
        foreach (var c in Load()["rotate"]!.AsArray().OfType<JsonObject>())
        {
            var size = c["size"]!.AsArray();
            var input = new PixelBuffer((int)size[0]!, (int)size[1]!, Convert.FromHexString((string)c["input"]!));
            var output = input.Rotate((int)c["angle"]!);
            var os = c["output_size"]!.AsArray();
            Assert.Equal(((int)os[0]!, (int)os[1]!), (output.Width, output.Height), $"taille {c["angle"]}");
            Assert.Equal((string)c["output"]!, Convert.ToHexStringLower(output.Data), $"pixels {c["angle"]}");
        }
    }

    [Test]
    public void FocusFromFacesMatchesPython()
    {
        foreach (var c in Load()["faces"]!.AsArray().OfType<JsonObject>())
        {
            var faces = c["faces"]!.AsArray().Select(f => f!.AsArray()).Select(f => new FaceBox((double)f[0]!, (double)f[1]!, (double)f[2]!, (double)f[3]!)).ToList();
            var size = c["size"]!.AsArray();
            var focus = FocusFinder.FromFaces(faces, (int)size[0]!, (int)size[1]!);
            if (c["focus"] is JsonArray e)
            {
                Assert.Near((double)e[0]!, focus!.Value.X, 1e-12);
                Assert.Near((double)e[1]!, focus!.Value.Y, 1e-12);
            }
            else Assert.True(focus is null, "aucun visage → pas de point");
        }
    }

    [Test]
    public void FocusFromDetailCloseToPython()
    {
        foreach (var c in Load()["detail"]!.AsArray().OfType<JsonObject>())
        {
            var size = c["size"]!.AsArray();
            int w = (int)size[0]!, h = (int)size[1]!;
            var gray = Enumerable.Repeat(PixelBuffer.Luma(40, 40, 40), w * h).ToArray();
            if (c["rect"] is JsonArray r)
            {
                byte light = PixelBuffer.Luma(240, 240, 240);
                for (int y = (int)r[1]!; y <= (int)r[3]!; y++)
                    for (int x = (int)r[0]!; x <= (int)r[2]!; x++) gray[y * w + x] = light;
            }
            var focus = FocusFinder.FromDetail(gray, w, h);
            var e = c["focus"]!.AsArray();
            Assert.Near((double)e[0]!, focus.X, 0.05, $"{c["id"]} x");
            Assert.Near((double)e[1]!, focus.Y, 0.05, $"{c["id"]} y");
        }
    }
}
