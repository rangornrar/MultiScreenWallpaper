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

    private readonly string? _legacyRoot;

    public WallpaperStore(string? root = null)
        : this(root ?? Path.Combine(AppPaths.DataDirectory(), "configs"),
               root is null && !string.IsNullOrEmpty(AppPaths.PackageFamilyName)
                   ? Path.Combine(AppPaths.LegacyDataDirectory(), "configs")
                   : null)
    {
    }

    internal WallpaperStore(string root, string? legacyRoot)
    {
        Root = root;
        _legacyRoot = legacyRoot;
        Directory.CreateDirectory(Root);
    }

    public string Root { get; }

    public string DirectoryFor(IEnumerable<MonitorInfo> monitors)
    {
        var path = Path.Combine(Root, CompositionLayout.Signature(monitors));
        ImportConfiguration(path);
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
        string path = ManifestPath(monitors);
        ImportConfiguration(Path.GetDirectoryName(path)!);
        try { return JsonNode.Parse(File.ReadAllText(path)) as JsonObject; }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or JsonException) { return null; }
    }

    /// <summary>L'utilisateur a choisi un autre fond : plus de réapplication automatique pour cette configuration.</summary>
    public void Release(IEnumerable<MonitorInfo> monitors) => SetReleased(monitors, true);

    public void SetReleased(IEnumerable<MonitorInfo> monitors, bool released)
    {
        var list = monitors.ToList();
        var manifest = ReadManifest(list);
        if (manifest is null) return;
        manifest["released"] = released;
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
            string? file = Json.String(s["file"]);
            if (!IsWallpaperFile(file)) continue;
            string path = Path.Combine(folder, file!);
            if (!File.Exists(path)) continue;
            result.Add(new AppliedScreen(
                (int)(Json.Number(s["x"]) ?? 0), (int)(Json.Number(s["y"]) ?? 0),
                (int)(Json.Number(s["width"]) ?? 0), (int)(Json.Number(s["height"]) ?? 0),
                Json.String(s["name"]) ?? "", path));
        }
        return result;
    }

    /// <summary>Le panorama de secours des versions Python et C# partage le préfixe des images par écran.</summary>
    public static string? SpanPath(string screenPath)
    {
        string file = Path.GetFileName(screenPath);
        int suffix = file.LastIndexOf("_pos_", StringComparison.Ordinal);
        if (suffix <= 0) return null;
        string span = Path.Combine(Path.GetDirectoryName(screenPath)!, file[..suffix] + "_span.png");
        return File.Exists(span) ? span : null;
    }

    public List<string> ExpectedPaths(IReadOnlyList<AppliedScreen> screens)
    {
        var expected = screens.Select(screen => screen.Path).ToList();
        if (expected.Count == 0) return expected;
        string? span = SpanPath(expected[0]);
        if (span is not null) expected.Add(span);
        if (_legacyRoot is not null)
        {
            // Le fond actif au moment de la migration peut encore pointer vers les fichiers Python.
            string configuration = Path.GetFileName(Path.GetDirectoryName(expected[0]))!;
            expected.AddRange(expected.Select(path => Path.Combine(_legacyRoot, configuration, Path.GetFileName(path))).ToArray());
        }
        return expected;
    }

    private void ImportConfiguration(string target)
    {
        if (_legacyRoot is null) return;
        string source = Path.Combine(_legacyRoot, Path.GetFileName(target));
        string sourceManifest = Path.Combine(source, "manifest.json");
        if (File.Exists(Path.Combine(target, "manifest.json")) || !File.Exists(sourceManifest)) return;
        string staging = target + "." + Guid.NewGuid().ToString("N");
        try
        {
            string contents = File.ReadAllText(sourceManifest);
            if (JsonNode.Parse(contents) is not JsonObject manifest || manifest["screens"] is not JsonArray screens || screens.Count == 0)
                return;
            Directory.CreateDirectory(staging);
            string? span = null;
            foreach (var screen in screens)
            {
                string? file = Json.String((screen as JsonObject)?["file"]);
                if (!IsWallpaperFile(file)) return;
                string path = Path.Combine(source, file!);
                File.Copy(path, Path.Combine(staging, file!), overwrite: true);
                span ??= SpanPath(path);
            }
            if (span is not null) File.Copy(span, Path.Combine(staging, Path.GetFileName(span)));
            File.WriteAllText(Path.Combine(staging, "manifest.json"), contents);

            // Un ancien échec de rendu peut avoir réservé un dossier vide. Un dossier rempli reste prioritaire.
            if (Directory.Exists(target) && !Directory.EnumerateFileSystemEntries(target).Any()) Directory.Delete(target);
            Directory.Move(staging, target);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or JsonException) { }
        finally
        {
            if (Directory.Exists(staging))
            {
                try { Directory.Delete(staging, recursive: true); }
                catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
            }
        }
    }

    private static bool IsWallpaperFile(string? file) => file is not null
        && file.IndexOfAny(['/', '\\', ':']) < 0
        && file.EndsWith(".png", StringComparison.OrdinalIgnoreCase);
}
