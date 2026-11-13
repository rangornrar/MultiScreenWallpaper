using WallCraft.App.Services;
using WallCraft.Core.Geometry;

namespace WallCraft.App.Dialogs;

/// <summary>
/// Textes de l'interface (<c>Strings/&lt;langue&gt;/Resources.resw</c>) ; la clé elle-même si elle manque.
/// Lus par <see cref="Localizer"/> : les dialogues suivent la langue choisie dans la fenêtre, sans redémarrer.
/// </summary>
public static class UiStrings
{
    public static string Get(string key) => Localizer.Current.Get(key);

    public static string Format(string key, params object?[] args) => Localizer.Current.Format(key, args);

    /// <summary>Pluriel : <c>&lt;clé&gt;_One</c> ou <c>&lt;clé&gt;_Other</c> selon <paramref name="count"/>.</summary>
    public static string Plural(string key, int count) => Localizer.Current.Plural(key, count);

    /// <summary>Mots Gauche/Centre/Droite… pour <see cref="MonitorNames.Labels"/>, dans la langue de l'interface.</summary>
    public static PositionWords PositionWords() => Localizer.Current.PositionWords;

    /// <summary>Séparateur décimal de la langue d'interface (« , » en français, « . » en anglais).</summary>
    public static string DecimalSeparator() => Localizer.Current.DecimalSeparator;
}
