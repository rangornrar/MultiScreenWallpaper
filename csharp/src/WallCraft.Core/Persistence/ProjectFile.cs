using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;
using WallCraft.Core.Model;

namespace WallCraft.Core.Persistence;

/// <summary>Une image du projet qui n'a pas pu être chargée, et pourquoi.</summary>
public sealed record ProjectLoadError(string Path, string Message);

/// <summary>Projet chargé : métadonnées libres (disposition, cadrage, taille réelle…) et images placées.</summary>
public sealed record Project(JsonObject Meta, List<CompositionImage> Images, List<ProjectLoadError> Errors);

/// <summary>
/// Format des projets, identique à la version Python (image_tools.save_project_json / load_project_json) :
/// les chemins d'images sont relatifs au fichier projet, les valeurs invalides sont bornées ou signalées.
/// </summary>
public static class ProjectFile
{
    public const int SchemaVersion = CoreInfo.ProjectSchemaVersion;

    private static readonly JsonSerializerOptions WriteOptions = new()
    {
        WriteIndented = true,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    public static JsonObject ToEntry(CompositionImage img) => new()
    {
        ["path"] = img.Path,
        ["x"] = img.X, ["y"] = img.Y, ["w"] = img.W, ["h"] = img.H,
        ["angle"] = img.Angle, ["z"] = img.ZIndex,
        ["crop"] = new JsonArray(img.Crop.Left, img.Crop.Top, img.Crop.Right, img.Crop.Bottom),
        ["brightness"] = img.Brightness, ["contrast"] = img.Contrast,
        ["saturation"] = img.Saturation, ["blur"] = img.Blur,
        ["focus"] = img.Focus is FocusPoint f ? new JsonArray(f.X, f.Y) : null,
    };

    /// <summary>Enregistre un projet ; les chemins sont rendus relatifs au fichier (absolus si autre lecteur).</summary>
    public static void Save(string path, JsonObject meta, IEnumerable<CompositionImage> images)
    {
        string baseDir = System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(path)) ?? ".";
        var list = new JsonArray();
        foreach (var img in images)
        {
            var entry = ToEntry(img);
            entry["path"] = RelativeOrAbsolute(img.Path, baseDir);
            list.Add((JsonNode)entry);
        }
        var data = new JsonObject
        {
            ["version"] = SchemaVersion,
            ["meta"] = meta.DeepClone(),
            ["images"] = list,
        };
        File.WriteAllText(path, data.ToJsonString(WriteOptions));
    }

    private static string RelativeOrAbsolute(string imagePath, string baseDir)
    {
        string full = System.IO.Path.GetFullPath(imagePath);
        bool sameRoot = string.Equals(System.IO.Path.GetPathRoot(full), System.IO.Path.GetPathRoot(baseDir), StringComparison.OrdinalIgnoreCase);
        return sameRoot ? System.IO.Path.GetRelativePath(baseDir, full) : full;
    }

    /// <summary>
    /// Charge un projet. <paramref name="readImageSize"/> lit la taille (largeur, hauteur) d'une image, après rotation EXIF ;
    /// elle lève une exception si le fichier est illisible. Les images en erreur sont listées, pas ignorées en silence.
    /// </summary>
    public static Project Load(string path, Func<string, (int Width, int Height)> readImageSize)
    {
        var data = JsonNode.Parse(File.ReadAllText(path)) as JsonObject ?? throw new InvalidDataException("projet invalide");
        var versionNode = data["version"];
        int version = SchemaVersion;
        if (versionNode is not null)
        {
            if (versionNode is not JsonValue v || v.GetValueKind() != JsonValueKind.Number || !v.TryGetValue(out version) || version > SchemaVersion)
                throw new InvalidDataException($"Version de projet non prise en charge : {versionNode.ToJsonString()}");
        }

        string baseDir = System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(path)) ?? ".";
        var images = new List<CompositionImage>();
        var errors = new List<ProjectLoadError>();
        var entries = (data["images"] as JsonArray ?? [])
            .OfType<JsonObject>()
            .Select((e, i) => (Entry: e, Index: i))
            .OrderBy(t => Json.Number(t.Entry["z"]) ?? 0) // OrderBy est stable, comme sorted() en Python
            .Select(t => t.Entry);

        foreach (var s in entries)
        {
            string rawPath = Json.String(s["path"]) ?? "";
            try
            {
                string full = System.IO.Path.IsPathRooted(rawPath) ? rawPath : System.IO.Path.Combine(baseDir, rawPath);
                if (!File.Exists(full)) throw new FileNotFoundException("fichier introuvable");
                var (w, h) = readImageSize(full);
                var img = new CompositionImage(full, w, h)
                {
                    X = Number(s, "x", 0),
                    Y = Number(s, "y", 0),
                    W = Math.Truncate(Number(s, "w", 100, minimum: 1)),
                    H = Math.Truncate(Number(s, "h", 100, minimum: 1)),
                };
                int angle = (((int)Number(s, "angle", 0)) % 360 + 360) % 360;
                img.Angle = angle - angle % 90;
                img.ZIndex = (int)Number(s, "z", 0);

                var crop = s["crop"] as JsonArray;
                double[] c = crop is null ? [0, 0, 1, 1] : crop.Select(n => Json.Number(n) ?? double.NaN).ToArray();
                if (c.Length != 4 || c.Any(double.IsNaN)) throw new InvalidDataException("zone de rognage invalide");
                c = c.Select(v => Math.Min(1.0, Math.Max(0.0, v))).ToArray();
                if (c[2] - c[0] < 0.01 || c[3] - c[1] < 0.01) throw new InvalidDataException("zone de rognage invalide");
                img.Crop = new CropBox(c[0], c[1], c[2], c[3]);

                img.Brightness = Number(s, "brightness", 1.0, 0.0, 4.0);
                img.Contrast = Number(s, "contrast", 1.0, 0.0, 4.0);
                img.Saturation = Number(s, "saturation", 1.0, 0.0, 4.0);
                img.Blur = Number(s, "blur", 0.0, 0.0, 100.0);
                if (s["focus"] is JsonArray f && f.Count == 2 && Json.Number(f[0]) is double fx && Json.Number(f[1]) is double fy)
                    img.Focus = new FocusPoint(Math.Clamp(fx, 0.0, 1.0), Math.Clamp(fy, 0.0, 1.0));
                images.Add(img);
            }
            catch (Exception e) when (e is IOException or InvalidDataException or UnauthorizedAccessException or ArgumentException or NotSupportedException)
            {
                errors.Add(new ProjectLoadError(rawPath, e.Message));
            }
        }
        return new Project(data["meta"] as JsonObject is { } meta ? (JsonObject)meta.DeepClone() : [], images, errors);
    }

    /// <summary>Valeur numérique avec défaut et bornes ; une valeur présente mais non numérique est une erreur (comme en Python).</summary>
    private static double Number(JsonObject entry, string key, double @default, double? minimum = null, double? maximum = null)
    {
        double value = @default;
        if (entry.TryGetPropertyValue(key, out var node))
        {
            value = Json.Number(node) ?? throw new InvalidDataException($"valeur invalide pour « {key} »");
        }
        if (minimum is double min) value = Math.Max(min, value);
        if (maximum is double max) value = Math.Min(max, value);
        return value;
    }
}
