using System.Globalization;
using WallCraft.Core.Model;
using WallCraft.Core.Persistence;

namespace WallCraft.Core.Presentation;

/// <summary>Mise en forme des textes affichés par la fenêtre principale (portage des petites fonctions de ui.py).</summary>
public static class DisplayText
{
    /// <summary>Longueur maximale d'un nom dans la bibliothèque (<c>name_chars</c>).</summary>
    public const int LibraryNameChars = 24;

    /// <summary>Au-delà de cette longueur, le nom est raccourci dans le résumé de la sélection.</summary>
    public const int SelectionNameChars = 34;

    /// <summary>Nombre d'erreurs listées avant « … (+n) » (<c>_format_errors</c>).</summary>
    public const int ErrorLimit = 8;

    /// <summary>
    /// Nom tronqué au milieu pour la bibliothèque : <c>name[:n//2-1] + "…" + name[-(n//2-1):]</c>, l'extension reste visible.
    /// </summary>
    public static string MiddleTruncate(string name, int maxChars = LibraryNameChars)
    {
        if (name.Length <= maxChars) return name;
        int keep = Math.Max(1, maxChars / 2 - 1);
        return name[..keep] + "…" + name[^keep..];
    }

    /// <summary>Nom raccourci du résumé de la sélection : 16 premiers caractères, « … », 12 derniers.</summary>
    public static string SelectionName(string name)
        => name.Length > SelectionNameChars ? $"{name[..16]}…{name[^12..]}" : name;

    /// <summary>« 2,5 » si l'image est nettement agrandie (<see cref="Upscale.LowResolutionThreshold"/>), sinon null (<c>lowres_text</c>).</summary>
    public static string? LowResolution(CompositionImage img, string decimalSeparator)
    {
        double factor = Upscale.Factor(img);
        if (factor < Upscale.LowResolutionThreshold) return null;
        return factor.ToString("F1", CultureInfo.InvariantCulture).Replace(".", decimalSeparator, StringComparison.Ordinal);
    }

    /// <summary>Suffixe de la ressource accordée : <c>_One</c> pour 1, <c>_Other</c> sinon (comme <c>_n</c> en Python).</summary>
    public static string PluralSuffix(int count) => count == 1 ? "_One" : "_Other";

    /// <summary>Part visible de l'image en largeur, en pourcentage tronqué (<c>int((r - l) * 100)</c>).</summary>
    public static int CropPercent(CompositionImage img) => (int)Math.Truncate((img.Crop.Right - img.Crop.Left) * 100);

    /// <summary>Liste à puces des erreurs, limitée à <paramref name="limit"/> lignes puis « • … (+n) » (<c>_format_errors</c>).</summary>
    public static string FormatErrors(IReadOnlyList<string> errors, int limit = ErrorLimit)
    {
        var lines = errors.Take(limit).Select(e => "• " + e).ToList();
        if (errors.Count > limit) lines.Add($"• … (+{errors.Count - limit})");
        return string.Join("\n", lines);
    }

    /// <summary>Erreurs de chargement : « • nom.jpg : message ».</summary>
    public static string FormatErrors(IReadOnlyList<ProjectLoadError> errors, int limit = ErrorLimit)
        => FormatErrors(errors.Select(e => $"{Path.GetFileName(e.Path)} : {e.Message}").ToList(), limit);
}
