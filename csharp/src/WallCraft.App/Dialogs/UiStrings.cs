using System.Globalization;
using Microsoft.Windows.ApplicationModel.Resources;
using WallCraft.Core.Geometry;

namespace WallCraft.App.Dialogs;

/// <summary>Textes de l'interface (<c>Strings/&lt;langue&gt;/Resources.resw</c>) ; la clé elle-même si elle manque.</summary>
public static class UiStrings
{
    private static ResourceLoader? _loader;
    private static bool _unavailable;

    public static string Get(string key)
    {
        if (_unavailable) return key;
        try
        {
            string value = (_loader ??= new ResourceLoader()).GetString(key);
            return string.IsNullOrEmpty(value) ? key : value;
        }
        catch (Exception)
        {
            _unavailable = true; // ressources absentes (ex. resources.pri manquant) : on affiche les clés
            return key;
        }
    }

    public static string Format(string key, params object?[] args) => string.Format(CultureInfo.CurrentCulture, Get(key), args);

    /// <summary>Pluriel : <c>&lt;clé&gt;_One</c> ou <c>&lt;clé&gt;_Other</c> selon <paramref name="count"/>.</summary>
    public static string Plural(string key, int count) => Format(count == 1 ? key + "_One" : key + "_Other", count);

    /// <summary>Mots Gauche/Centre/Droite… pour <see cref="MonitorNames.Labels"/>, dans la langue de l'interface.</summary>
    public static PositionWords PositionWords() => new(
        Get("pos_left"), Get("pos_center"), Get("pos_right"), Get("pos_top"), Get("pos_bottom"), Get("pos_screen"));

    /// <summary>Séparateur décimal de la langue d'interface (« , » en français, « . » en anglais).</summary>
    public static string DecimalSeparator() => CultureInfo.CurrentUICulture.NumberFormat.NumberDecimalSeparator;
}
