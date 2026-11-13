using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage.Pickers;
using WallCraft.Core.Services;

namespace WallCraft.App.Dialogs;

/// <summary>
/// « Fond automatique » (<c>AutoDialog</c> Python) : garder le fond, rotation d'images depuis un dossier,
/// icône de notification et démarrage avec Windows.
/// </summary>
public static class AutomationDialog
{
    /// <summary>
    /// Affiche le dialogue. <paramref name="owner"/> sert à initialiser le sélecteur de dossier ;
    /// <paramref name="monitorCount"/> donne le nombre d'images proposé quand il n'est pas encore réglé.
    /// Retourne les nouveaux réglages, ou null si l'utilisateur annule. Rien n'est enregistré ici :
    /// voir <c>AutomationService.ApplyPrefs</c>.
    /// </summary>
    public static async Task<AutomationPrefs?> ShowAsync(XamlRoot root, Window owner, AutomationPrefs prefs, int monitorCount)
    {
        ArgumentNullException.ThrowIfNull(owner);
        ArgumentNullException.ThrowIfNull(prefs);
        var dialog = DialogHelpers.Create(root, "prefs_title", maxWidth: 640);
        dialog.PrimaryButtonText = UiStrings.Get("btn_ok");
        dialog.CloseButtonText = UiStrings.Get("btn_cancel");

        var rot = prefs.Rotation;
        var panel = new StackPanel { Spacing = 6, MinWidth = 480 };

        panel.Children.Add(DialogHelpers.Header(UiStrings.Get("prefs_section_wallpaper")));
        var keep = DialogHelpers.Check(UiStrings.Get("prefs_keep"), prefs.KeepWallpaper);
        panel.Children.Add(keep);

        panel.Children.Add(DialogHelpers.Header(UiStrings.Get("prefs_section_rotation")));
        var rotation = DialogHelpers.Check(UiStrings.Get("prefs_rotation"), rot.Enabled);
        panel.Children.Add(rotation);

        var form = new Grid { ColumnSpacing = 12, RowSpacing = 8, Margin = new Thickness(28, 4, 0, 0) };
        form.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        form.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        form.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        for (int r = 0; r < 3; r++) form.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

        var folder = new TextBox { Text = rot.Folder, PlaceholderText = UiStrings.Get("prefs_folder_none") };
        var browse = new Button { Content = UiStrings.Get("prefs_browse") };
        browse.Click += async (_, _) =>
        {
            string? picked = await PickFolderAsync(owner);
            if (!string.IsNullOrEmpty(picked)) folder.Text = picked;
        };
        var minutes = new TextBox { Text = rot.Minutes.ToString(System.Globalization.CultureInfo.InvariantCulture), Width = 90, HorizontalAlignment = HorizontalAlignment.Left };
        int defaultCount = Math.Max(1, monitorCount);
        var count = new TextBox
        {
            Text = (rot.Count ?? defaultCount).ToString(System.Globalization.CultureInfo.InvariantCulture),
            Width = 90,
            HorizontalAlignment = HorizontalAlignment.Left,
        };
        DialogHelpers.Place(form, DialogHelpers.Label(UiStrings.Get("prefs_folder")), 0, 0);
        DialogHelpers.Place(form, folder, 0, 1);
        DialogHelpers.Place(form, browse, 0, 2);
        DialogHelpers.Place(form, DialogHelpers.Label(UiStrings.Get("prefs_minutes")), 1, 0);
        DialogHelpers.Place(form, minutes, 1, 1);
        DialogHelpers.Place(form, DialogHelpers.Label(UiStrings.Get("prefs_count")), 2, 0);
        DialogHelpers.Place(form, count, 2, 1);
        panel.Children.Add(form);

        panel.Children.Add(DialogHelpers.Header(UiStrings.Get("prefs_section_startup")));
        var tray = DialogHelpers.Check(UiStrings.Get("prefs_tray"), prefs.Tray);
        var autostart = DialogHelpers.Check(UiStrings.Get("prefs_autostart"), prefs.Autostart);
        panel.Children.Add(tray);
        panel.Children.Add(autostart);

        dialog.Content = new ScrollViewer { Content = panel, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };

        if (await dialog.ShowAsync() != ContentDialogResult.Primary) return null;
        return new AutomationPrefs
        {
            KeepWallpaper = keep.IsChecked == true,
            Tray = tray.IsChecked == true,
            Autostart = autostart.IsChecked == true,
            Rotation = new RotationPrefs
            {
                Enabled = rotation.IsChecked == true,
                Folder = folder.Text.Trim(),
                Minutes = AutomationPrefs.ParseClamped(minutes.Text, RotationPrefs.DefaultMinutes, 1, RotationPrefs.MaxMinutes),
                Count = AutomationPrefs.ParseClamped(count.Text, 3, 1, RotationPrefs.MaxCount),
            },
        };
    }

    /// <summary>Sélecteur de dossier rattaché à la fenêtre (obligatoire pour une application non empaquetée).</summary>
    private static async Task<string?> PickFolderAsync(Window owner)
    {
        try
        {
            var picker = new FolderPicker { SuggestedStartLocation = PickerLocationId.PicturesLibrary };
            picker.FileTypeFilter.Add("*");
            WinRT.Interop.InitializeWithWindow.Initialize(picker, WinRT.Interop.WindowNative.GetWindowHandle(owner));
            var folder = await picker.PickSingleFolderAsync();
            return folder?.Path;
        }
        catch (Exception)
        {
            return null; // sélecteur indisponible (ex. processus élevé) : on garde la saisie manuelle
        }
    }
}
