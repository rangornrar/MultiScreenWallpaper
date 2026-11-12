using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Services;

namespace WallCraft.Core.Persistence;

/// <summary>
/// Réglages persistants (<c>%LOCALAPPDATA%\WallCraft\settings.json</c>), partagés avec la version Python.
/// Les clés inconnues sont conservées telles quelles pour ne rien perdre en passant d'une version à l'autre.
/// </summary>
public sealed class AppSettings
{
    private static readonly JsonSerializerOptions WriteOptions = new()
    {
        WriteIndented = true,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    private readonly JsonObject _data;

    private AppSettings(JsonObject data, string path)
    {
        _data = data;
        FilePath = path;
    }

    public string FilePath { get; }

    public static AppSettings Load(string? path = null)
    {
        path ??= AppPaths.SettingsFile();
        try
        {
            if (JsonNode.Parse(File.ReadAllText(path)) is JsonObject obj) return new AppSettings(obj, path);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or JsonException) { }
        return new AppSettings([], path);
    }

    /// <summary>Écriture atomique (fichier temporaire puis remplacement), comme la version Python.</summary>
    public void Save()
    {
        string tmp = FilePath + ".tmp";
        File.WriteAllText(tmp, _data.ToJsonString(WriteOptions));
        File.Move(tmp, FilePath, overwrite: true);
    }

    public bool Fill { get => GetBool("fill"); set => _data["fill"] = value; }
    public string? Language { get => Json.String(_data["language"]); set => _data["language"] = value; }

    public PhysicalSettings Physical
    {
        get => PhysicalSettings.FromJson(_data["physical"]);
        set => _data["physical"] = value.ToJson();
    }

    /// <summary>Accès brut aux autres réglages (fond automatique, rotation…).</summary>
    public JsonNode? this[string key] { get => _data[key]; set => _data[key] = value; }

    public bool GetBool(string key, bool @default = false) => Json.Bool(_data[key]) ?? @default;
    public double GetNumber(string key, double @default = 0) => Json.Number(_data[key]) ?? @default;
    public string? GetString(string key) => Json.String(_data[key]);
}
