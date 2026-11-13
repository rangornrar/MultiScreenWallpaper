using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

namespace WallCraft.App.Dialogs;

/// <summary>Construction commune des dialogues : style Windows 11, thème sombre, fenêtre parente.</summary>
internal static class DialogHelpers
{
    /// <summary>
    /// Dialogue vide au style Windows 11 (« DefaultContentDialogStyle », sinon un ContentDialog créé en code garde
    /// l'ancien style), en thème sombre. <paramref name="maxWidth"/> remplace la largeur maximale de 548 px.
    /// </summary>
    public static ContentDialog Create(XamlRoot root, string titleKey, double? maxWidth = null)
    {
        ArgumentNullException.ThrowIfNull(root);
        var dialog = new ContentDialog
        {
            XamlRoot = root,
            Title = UiStrings.Get(titleKey),
            RequestedTheme = ElementTheme.Dark,
            DefaultButton = ContentDialogButton.Primary,
        };
        if (Application.Current?.Resources.TryGetValue("DefaultContentDialogStyle", out object? style) == true && style is Style s)
            dialog.Style = s;
        if (maxWidth is double w)
        {
            dialog.Resources["ContentDialogMaxWidth"] = w;
            dialog.Resources["ContentDialogMinWidth"] = Math.Min(w, 320.0);
        }
        return dialog;
    }

    public static TextBlock Label(string text, bool secondary = false, bool wrap = false)
    {
        var t = new TextBlock { Text = text, VerticalAlignment = VerticalAlignment.Center };
        if (secondary && Application.Current?.Resources.TryGetValue("TextFillColorSecondaryBrush", out object? b) == true && b is Brush brush)
            t.Foreground = brush;
        if (wrap) t.TextWrapping = TextWrapping.Wrap;
        return t;
    }

    public static TextBlock Header(string text)
    {
        var t = Label(text);
        if (Application.Current?.Resources.TryGetValue("BodyStrongTextBlockStyle", out object? s) == true && s is Style style)
            t.Style = style;
        t.Margin = new Thickness(0, 12, 0, 4);
        return t;
    }

    public static CheckBox Check(string text, bool value) => new()
    {
        IsChecked = value,
        Content = new TextBlock { Text = text, TextWrapping = TextWrapping.Wrap },
    };

    public static void Place(Grid grid, FrameworkElement element, int row, int column, int columnSpan = 1)
    {
        Grid.SetRow(element, row);
        Grid.SetColumn(element, column);
        if (columnSpan > 1) Grid.SetColumnSpan(element, columnSpan);
        grid.Children.Add(element);
    }
}
