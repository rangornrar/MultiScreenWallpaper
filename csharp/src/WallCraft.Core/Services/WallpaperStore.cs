using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using WallCraft.Core.Geometry;

namespace WallCraft.Core.Services;

/// <summary>Une image appliquée à un écran : le rectangle de l'écran et le fichier.</summary>
public sealed record AppliedScreen(int X, int Y, int Width, int Height, string Name, string Path);

/// <summary>
/// Un fond mémorisé par configuration d'écrans (portable seul, sur sa station…) : <c>configs/&lt;empreinte&gt;/</c>
/// contient les images par écran et un <c>manifest.json</c>, au même format que la version Python.
/// </summary>
public sealed class WallpaperStore
{
    private static readonly JsonSerializerOptions WriteOptions = new()
    {
        WriteIndented = true,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping, // accents lisibles, comme ensure_ascii=False
    };

    public WallpaperStore(string? root = null)
    {
        Root = root ?? Path.Combine(AppPaths.DataDirectory(), "configs");
        Directory.CreateDirectory(Root);
    }

    public string Root { get; }

    public string DirectoryFor(IEnumerable<MonitorInfo> monitors)
    {
        var path = Path.Combine(Root, CompositionLayout.Signature(monitors));
        Directory.CreateDirectory(path);
        return path;
    }

    private string ManifestPath(IEnumerable<MonitorInfo> monitors) => Path.Combine(Root, CompositionLayout.Signature(monitors), "manifest.json");

    /// <summary>Enregistre le manifest des fichiers appliqués, puis supprime les anciens fichiers de cette configuration.</summary>
    public void Save(IReadOnlyCollection<MonitorInfo> monitors, IEnumerable<(MonitorInfo Monitor, string Path)> results, string keepPrefix, DateTime? appliedAt = null)
    {
        string folder = DirectoryFor(monitors);
        var screens = new JsonArray();
        foreach (var (m, path) in results)
        {
            screens.Add((JsonNode)new JsonObject
            {
                ["x"] = m.X, ["y"] = m.Y, ["width"] = m.Width, ["height"] = m.Height,
                ["name"] = m.Name, ["file"] = System.IO.Path.GetFileName(path),
            });
        }
        var manifest = new JsonObject
        {
            ["signature"] = CompositionLayout.Signature(monitors),
            ["applied_at"] = (appliedAt ?? DateTime.Now).ToString("yyyy-MM-dd'T'HH:mm:ss", System.Globalization.CultureInfo.InvariantCulture),
            ["screens"] = screens,
        };
        File.WriteAllText(Path.Combine(folder, "manifest.json"), manifest.ToJsonString(WriteOptions));
        foreach (var old in Directory.EnumerateFiles(folder, "wallcraft_*"))
        {
            if (System.IO.Path.GetFileName(old).StartsWith(keepPrefix, StringComparison.Ordinal)) continue;
            try { File.Delete(old); } catch (IOException) { } catch (UnauthorizedAccessException) { }
        }
    }

    private JsonObject? ReadManifest(IEnumerable<MonitorInfo> monitors)
    {
        try { return JsonNode.Parse(File.ReadAllText(ManifestPath(monitors))) as JsonObject; }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or JsonException) { return null; }
    }

    /// <summary>L'utilisateur a choisi un autre fond : plus de réapplication automatique pour cette configuration.</summary>
    public void Release(IEnumerable<MonitorInfo> monitors)
    {
        var list = monitors.ToList();
        var manifest = ReadManifest(list);
        if (manifest is null) return;
        manifest["released"] = true;
        try { File.WriteAllText(ManifestPath(list), manifest.ToJsonString(WriteOptions)); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
    }

    public bool IsReleased(IEnumerable<MonitorInfo> monitors) => Json.Bool(ReadManifest(monitors)?["released"]) ?? false;

    /// <summary>Images mémorisées pour cette configuration (seulement celles dont le fichier existe encore).</summary>
    public List<AppliedScreen> Load(IEnumerable<MonitorInfo> monitors)
    {
        var list = monitors.ToList();
        var manifest = ReadManifest(list);
        var result = new List<AppliedScreen>();
        if (manifest?["screens"] is not JsonArray screens) return result;
        string folder = Path.Combine(Root, CompositionLayout.Signature(list));
        foreach (var node in screens)
        {
            if (node is not JsonObject s) continue;
            string file = Json.String(s["file"]) ?? "";
            string path = Path.Combine(folder, file);
            if (file.Length == 0 || !File.Exists(path)) continue;
            result.Add(new AppliedScreen(
                (int)(Json.Number(s["x"]) ?? 0), (int)(Json.Number(s["y"]) ?? 0),
                (int)(Json.Number(s["width"]) ?? 0), (int)(Json.Number(s["height"]) ?? 0),
                Json.String(s["name"]) ?? "", path));
        }
        return result;
    }
}
