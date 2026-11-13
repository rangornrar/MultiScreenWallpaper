using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Layout;

namespace WallCraft.Core.Persistence;

/// <summary>
/// Métadonnées d'un projet, au format de <c>cmd_save_project</c> (ui.py) : taille de la composition, disposition,
/// Ajuster/Remplir, taille réelle et écrans. Seules la disposition et le cadrage sont relus à l'ouverture, comme en Python.
/// </summary>
public static class ProjectMeta
{
    public static JsonObject Build(double targetWidth, double targetHeight, string? layout, bool fill, bool physical,
                                   IEnumerable<MonitorInfo> monitors)
    {
        var list = new JsonArray();
        foreach (var m in monitors) list.Add((JsonNode)MonitorToJson(m));
        return new JsonObject
        {
            ["target"] = new JsonArray(Number(targetWidth), Number(targetHeight)),
            ["layout"] = layout,
            ["fill"] = fill,
            ["physical"] = physical,
            ["monitors"] = list,
        };
    }

    /// <summary>Un écran comme le dictionnaire Python (<c>get_monitor_layout</c> enrichi de l'EDID et du rectangle de composition).</summary>
    public static JsonObject MonitorToJson(MonitorInfo m)
    {
        var obj = new JsonObject
        {
            ["x"] = m.X, ["y"] = m.Y, ["width"] = m.Width, ["height"] = m.Height,
            ["name"] = m.Name, ["device_id"] = m.Name,
        };
        if (!string.IsNullOrEmpty(m.HwId)) obj["hw_id"] = m.HwId;
        if (m.WidthMm is double w && m.HeightMm is double h)
        {
            obj["width_mm"] = w;
            obj["height_mm"] = h;
        }
        if (m.Canvas is IntRect c) obj["canvas"] = new JsonArray(c.X, c.Y, c.Width, c.Height);
        return obj;
    }

    /// <summary>Disposition enregistrée, si c'est l'une des 6 connues.</summary>
    public static string? Layout(JsonObject meta)
        => Json.String(meta["layout"]) is { } id && LayoutModes.All.Contains(id) ? id : null;

    /// <summary>Remplir (vrai) ou Ajuster (faux) ; null si le projet ne le précise pas.</summary>
    public static bool? Fill(JsonObject meta) => meta.ContainsKey("fill") ? Json.Truthy(meta["fill"]) : null;

    /// <summary>Taille réelle activée à l'enregistrement ; null si le projet ne le précise pas.</summary>
    public static bool? Physical(JsonObject meta) => meta.ContainsKey("physical") ? Json.Truthy(meta["physical"]) : null;

    // Les tailles entières restent entières dans le JSON, comme en Python.
    private static JsonNode Number(double v) => v == Math.Truncate(v) && Math.Abs(v) < int.MaxValue ? JsonValue.Create((int)v) : JsonValue.Create(v);
}
