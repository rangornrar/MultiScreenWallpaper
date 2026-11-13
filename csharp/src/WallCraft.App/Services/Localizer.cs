using System.Globalization;
using Microsoft.Windows.ApplicationModel.Resources;
using WallCraft.Core.Geometry;
using WallCraft.Core.Presentation;

namespace WallCraft.App.Services;

/// <summary>Une langue de l'interface : code court (celui de settings.json, comme en Python), culture .resw et nom affiché.</summary>
public sealed record UiLanguage(string Code, string Culture, string Name);

/// <summary>
/// Textes de l'interface lus dans <c>Strings/&lt;culture&gt;/Resources.resw</c>, dans une langue que l'on peut changer
/// sans redémarrer : la fenêtre s'abonne à <see cref="LanguageChanged"/> et relit ses textes.
/// </summary>
public sealed class Localizer
{
    /// <summary>Les 4 langues, avec leur nom dans leur propre langue (comme <c>locales.LANGUAGES</c>).</summary>
    public static readonly IReadOnlyList<UiLanguage> Languages =
    [
        new("en", "en-US", "English"),
        new("fr", "fr-FR", "Français"),
        new("es", "es-ES", "Español"),
        new("de", "de-DE", "Deutsch"),
    ];

    public static Localizer Current { get; } = new();

    private ResourceManager? _manager;
    private ResourceMap? _map;
    private ResourceContext? _context;

    private Localizer() { }

    /// <summary>Code court de la langue active (« fr », « en »…).</summary>
    public string Language { get; private set; } = "en";

    public UiLanguage CurrentLanguage => Languages.First(l => l.Code == Language);

    public event EventHandler? LanguageChanged;

    /// <summary>Langue du système si elle fait partie des 4, sinon l'anglais (<c>detect_os_language</c>).</summary>
    public static string DetectSystemLanguage()
    {
        string code = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
        return Languages.Any(l => l.Code == code) ? code : "en";
    }

    /// <summary>Change la langue (code court ou culture) ; un code inconnu est ignoré. Lève <see cref="LanguageChanged"/>.</summary>
    public void SetLanguage(string? code)
    {
        var lang = Languages.FirstOrDefault(l => string.Equals(l.Code, code, StringComparison.OrdinalIgnoreCase)
                                              || string.Equals(l.Culture, code, StringComparison.OrdinalIgnoreCase));
        if (lang is null) return;
        Language = lang.Code;
        EnsureLoaded();
        if (_context is not null) _context.QualifierValues["Language"] = lang.Culture;
        CultureInfo.CurrentUICulture = Culture;
        CultureInfo.DefaultThreadCurrentUICulture = Culture;
        LanguageChanged?.Invoke(this, EventArgs.Empty);
    }

    private void EnsureLoaded()
    {
        if (_manager is not null) return;
        try
        {
            _manager = new ResourceManager();
            _map = _manager.MainResourceMap.TryGetSubtree("Resources");
            _context = _manager.CreateResourceContext();
            _context.QualifierValues["Language"] = CurrentLanguage.Culture;
        }
        catch (Exception)
        {
            // Ressources absentes (exécution hors du dossier publié) : les clés s'affichent telles quelles.
            _map = null;
        }
    }

    /// <summary>Texte d'une clé ; la clé elle-même si elle est introuvable.</summary>
    public string Get(string key)
    {
        EnsureLoaded();
        if (_map is null || _context is null) return key;
        try
        {
            var value = _map.TryGetValue(key, _context)?.ValueAsString;
            return string.IsNullOrEmpty(value) ? key : value;
        }
        catch (Exception)
        {
            return key;
        }
    }

    public string this[string key] => Get(key);

    /// <summary>Texte avec marqueurs <c>{0}</c>, <c>{1}</c>… remplis.</summary>
    public string Format(string key, params object?[] args)
    {
        string text = Get(key);
        try
        {
            return string.Format(Culture, text, args);
        }
        catch (FormatException)
        {
            return text;
        }
    }

    /// <summary>Texte accordé : <c>Plural("n_screens", 3)</c> → « 3 écrans » (<c>_n</c> en Python).</summary>
    public string Plural(string key, int count) => Format(key + DisplayText.PluralSuffix(count), count);

    /// <summary>Séparateur décimal des nombres affichés (point en anglais, virgule sinon, comme <c>_decimal</c>).</summary>
    public string DecimalSeparator => Language == "en" ? "." : ",";

    public CultureInfo Culture => CultureInfo.GetCultureInfo(CurrentLanguage.Culture);

    /// <summary>Mots des noms d'écrans (« Gauche · Philips 23″ ») dans la langue active.</summary>
    public PositionWords PositionWords => new(Get("pos_left"), Get("pos_center"), Get("pos_right"), Get("pos_top"), Get("pos_bottom"), Get("pos_screen"));
}
