using System.Text.Json.Nodes;

namespace WallCraft.Core.Geometry;

/// <summary>Corrections de l'utilisateur pour un écran (clé = identifiant matériel).</summary>
public sealed class MonitorOverride
{
    public double? WidthMm { get; set; }
    public double? HeightMm { get; set; }
    public double OffsetXMm { get; set; }
    public double OffsetYMm { get; set; }
}

/// <summary>Réglages « taille réelle » (même format JSON que la version Python, dans settings.json → "physical").</summary>
public sealed class PhysicalSettings
{
    public bool Enabled { get; set; }
    /// <summary>Espace entre deux dalles voisines (bordures), en mm.</summary>
    public double BezelMm { get; set; }
    public Dictionary<string, MonitorOverride> Overrides { get; } = new(StringComparer.Ordinal);

    public MonitorOverride? OverrideFor(MonitorInfo m) => Overrides.GetValueOrDefault(m.HwId);

    public JsonObject ToJson()
    {
        var overrides = new JsonObject();
        foreach (var (key, o) in Overrides)
        {
            var obj = new JsonObject();
            if (o.WidthMm is double w) obj["width_mm"] = w;
            if (o.HeightMm is double h) obj["height_mm"] = h;
            obj["offset_x_mm"] = o.OffsetXMm;
            obj["offset_y_mm"] = o.OffsetYMm;
            overrides[key] = obj;
        }
        return new JsonObject { ["enabled"] = Enabled, ["bezel_mm"] = BezelMm, ["overrides"] = overrides };
    }

    /// <summary>Lecture tolérante : une valeur absente ou invalide prend sa valeur par défaut.</summary>
    public static PhysicalSettings FromJson(JsonNode? node)
    {
        var s = new PhysicalSettings();
        if (node is not JsonObject obj) return s;
        // Comme bool(...) et float(...) de Python : 1 → vrai, "" → faux, "12.5" → 12,5.
        s.Enabled = Json.Truthy(obj["enabled"]);
        s.BezelMm = Json.Number(obj["bezel_mm"]) ?? Json.ParseNumber(Json.String(obj["bezel_mm"])) ?? 0.0;
        if (obj["overrides"] is JsonObject overrides)
        {
            foreach (var (key, value) in overrides)
            {
                if (value is not JsonObject o) continue;
                s.Overrides[key] = new MonitorOverride
                {
                    WidthMm = PositiveOrNull(Json.Number(o["width_mm"])),
                    HeightMm = PositiveOrNull(Json.Number(o["height_mm"])),
                    OffsetXMm = Json.Number(o["offset_x_mm"]) ?? 0.0,
                    OffsetYMm = Json.Number(o["offset_y_mm"]) ?? 0.0,
                };
            }
        }
        return s;

        static double? PositiveOrNull(double? v) => v is > 0 ? v : null;
    }
}
