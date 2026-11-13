using System.Globalization;
using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Persistence;

namespace WallCraft.Core.Services;

/// <summary>Rotation d'images depuis un dossier (settings.json → "rotation").</summary>
public sealed record RotationPrefs
{
    public const int DefaultMinutes = 60;
    public const int MaxMinutes = 24 * 60;
    public const int MaxCount = 30;

    public bool Enabled { get; init; }
    public string Folder { get; init; } = "";
    /// <summary>Intervalle entre deux rotations, de 1 à 1440 minutes.</summary>
    public int Minutes { get; init; } = DefaultMinutes;
    /// <summary>Nombre d'images tirées ; null = un par écran (valeur absente du fichier, comme en Python).</summary>
    public int? Count { get; init; }

    /// <summary>Nombre d'images à tirer pour <paramref name="monitorCount"/> écrans.</summary>
    public int EffectiveCount(int monitorCount) => Count ?? monitorCount;
}

/// <summary>
/// Réglages du fond automatique (dialogue « Fond automatique » et icône de notification), avec exactement
/// les clés JSON de la version Python : <c>keep_wallpaper</c>, <c>tray</c>, <c>rotation</c> {enabled, folder, minutes, count}.
/// <see cref="Autostart"/> n'est pas dans settings.json : il vient du registre (clé Run).
/// </summary>
public sealed record AutomationPrefs
{
    public bool KeepWallpaper { get; init; } = true;
    public bool Tray { get; init; } = true;
    public bool Autostart { get; init; }
    public RotationPrefs Rotation { get; init; } = new();

    /// <summary>Lecture tolérante (valeurs absentes ou invalides → valeurs par défaut de Python).</summary>
    public static AutomationPrefs Read(AppSettings settings, bool autostart = false)
    {
        var rot = settings["rotation"] as JsonObject;
        return new AutomationPrefs
        {
            KeepWallpaper = ReadBool(settings["keep_wallpaper"], true),
            Tray = ReadBool(settings["tray"], true),
            Autostart = autostart,
            Rotation = new RotationPrefs
            {
                Enabled = rot is not null && Json.Truthy(rot["enabled"]),
                Folder = (rot is null ? null : Json.String(rot["folder"])) ?? "",
                Minutes = ReadInt(rot?["minutes"]) is int m ? Math.Max(1, m) : RotationPrefs.DefaultMinutes,
                Count = ReadInt(rot?["count"]) is int c ? Math.Max(1, c) : null,
            },
        };
    }

    /// <summary>Écrit keep_wallpaper, tray et rotation (l'objet rotation est remplacé en entier, comme settings.update de Python).</summary>
    public void WriteTo(AppSettings settings)
    {
        settings["keep_wallpaper"] = KeepWallpaper;
        settings["tray"] = Tray;
        var rot = new JsonObject
        {
            ["enabled"] = Rotation.Enabled,
            ["folder"] = Rotation.Folder,
            ["minutes"] = Rotation.Minutes,
        };
        if (Rotation.Count is int count) rot["count"] = count;
        settings["rotation"] = rot;
    }

    /// <summary>
    /// Saisie d'un nombre entier comme <c>as_int</c> du dialogue Python : <c>int(float(texte))</c> borné à [lo, hi],
    /// <paramref name="default"/> si le texte n'est pas un nombre.
    /// </summary>
    public static int ParseClamped(string? text, int @default, int lo, int hi)
    {
        if (!double.TryParse(text?.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out double d) || !double.IsFinite(d))
            return @default;
        double t = Math.Truncate(d);
        return (int)Math.Max(lo, Math.Min(hi, t));
    }

    private static bool ReadBool(JsonNode? node, bool @default) => node is null ? @default : Json.Truthy(node);

    /// <summary>Comme <c>int(x)</c> de Python sur un nombre ou une chaîne numérique ; null sinon.</summary>
    private static int? ReadInt(JsonNode? node)
    {
        // Valeur écrite en mémoire par WriteTo (JsonValue d'un int : TryGetValue<double> échoue dessus).
        if (node is JsonValue iv && iv.TryGetValue(out int i)) return i;
        double? d = Json.Number(node) ?? Json.ParseNumber(Json.String(node));
        if (d is not double v) return null;
        v = Math.Truncate(v);
        return (int)Math.Max(int.MinValue, Math.Min(int.MaxValue, v));
    }
}

/// <summary>Échéance de la prochaine rotation (<c>_schedule_rotation</c>).</summary>
public static class RotationSchedule
{
    /// <summary>
    /// Null si la rotation est désactivée ou sans dossier ; sinon garde <paramref name="current"/>, ou repart de
    /// <paramref name="now"/> + intervalle si <paramref name="reset"/> ou s'il n'y avait pas d'échéance.
    /// </summary>
    public static DateTimeOffset? Next(RotationPrefs rotation, DateTimeOffset now, DateTimeOffset? current, bool reset)
    {
        if (!rotation.Enabled || string.IsNullOrEmpty(rotation.Folder)) return null;
        if (reset || current is null) return now.AddMinutes(Math.Max(1, rotation.Minutes));
        return current;
    }

    public static bool IsDue(DateTimeOffset? next, DateTimeOffset now) => next is DateTimeOffset t && now >= t;
}
