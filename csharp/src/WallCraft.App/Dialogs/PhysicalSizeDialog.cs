using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using WallCraft.Core.Geometry;

namespace WallCraft.App.Dialogs;

/// <summary>
/// « Taille réelle des écrans » (<c>PhysicalDialog</c> Python) : alignement sur la taille réelle, espace entre les dalles
/// et, pour chaque écran, largeur/hauteur en mm, décalage vertical et diagonale recalculée pendant la saisie.
/// </summary>
public static class PhysicalSizeDialog
{
    /// <summary>
    /// Affiche le dialogue. Retourne les nouveaux réglages (copie, <paramref name="settings"/> n'est pas modifié),
    /// ou null si l'utilisateur annule.
    /// </summary>
    public static async Task<PhysicalSettings?> ShowAsync(XamlRoot root, IReadOnlyList<MonitorInfo> monitors, PhysicalSettings settings)
    {
        ArgumentNullException.ThrowIfNull(monitors);
        ArgumentNullException.ThrowIfNull(settings);
        var dialog = DialogHelpers.Create(root, "physical_title", maxWidth: 940);
        dialog.PrimaryButtonText = UiStrings.Get("btn_ok");
        dialog.CloseButtonText = UiStrings.Get("btn_cancel");

        var panel = new StackPanel { Spacing = 8 };
        var enabled = DialogHelpers.Check(UiStrings.Get("physical_enable"), settings.Enabled);
        panel.Children.Add(enabled);

        var bezelRow = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12 };
        bezelRow.Children.Add(DialogHelpers.Label(UiStrings.Get("physical_bezel")));
        var bezel = new TextBox { Text = PhysicalSettingsEditor.FormatBezel(settings), Width = 90 };
        bezelRow.Children.Add(bezel);
        panel.Children.Add(bezelRow);

        var table = new Grid { ColumnSpacing = 12, RowSpacing = 6, Margin = new Thickness(0, 8, 0, 0) };
        foreach (var width in new[] { 1.0, 0, 0, 0, 0, 0 })
            table.ColumnDefinitions.Add(new ColumnDefinition { Width = width > 0 ? new GridLength(1, GridUnitType.Star) : GridLength.Auto });
        for (int r = 0; r <= monitors.Count; r++) table.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

        string[] headers = ["physical_screen", "physical_res", "physical_width", "physical_height", "physical_offset", "physical_diag"];
        for (int c = 0; c < headers.Length; c++)
            DialogHelpers.Place(table, DialogHelpers.Label(UiStrings.Get(headers[c]), secondary: true), 0, c);

        var labels = MonitorNames.Labels(monitors, UiStrings.PositionWords(), UiStrings.DecimalSeparator());
        var rows = new List<(MonitorInfo Monitor, TextBox Width, TextBox Height, TextBox Offset)>();
        for (int i = 0; i < monitors.Count; i++)
        {
            var m = monitors[i];
            int r = i + 1;
            var (w, h, offset) = PhysicalSettingsEditor.InitialRow(m, settings);
            var widthBox = new TextBox { Text = w, Width = 90 };
            var heightBox = new TextBox { Text = h, Width = 90 };
            var offsetBox = new TextBox { Text = offset, Width = 90 };
            var diag = DialogHelpers.Label("", secondary: true);
            void UpdateDiag() => diag.Text = PhysicalSettingsEditor.DiagonalText(widthBox.Text, heightBox.Text) ?? UiStrings.Get("physical_unknown");
            widthBox.TextChanged += (_, _) => UpdateDiag();
            heightBox.TextChanged += (_, _) => UpdateDiag();
            UpdateDiag();

            var name = DialogHelpers.Label(labels[i]);
            name.TextTrimming = TextTrimming.CharacterEllipsis;
            ToolTipService.SetToolTip(name, $"{labels[i]}\n{m.Name}");
            DialogHelpers.Place(table, name, r, 0);
            DialogHelpers.Place(table, DialogHelpers.Label($"{m.Width} × {m.Height}"), r, 1);
            DialogHelpers.Place(table, widthBox, r, 2);
            DialogHelpers.Place(table, heightBox, r, 3);
            DialogHelpers.Place(table, offsetBox, r, 4);
            DialogHelpers.Place(table, diag, r, 5);
            rows.Add((m, widthBox, heightBox, offsetBox));
        }
        panel.Children.Add(table);

        var hint = DialogHelpers.Label(UiStrings.Get("physical_hint"), secondary: true, wrap: true);
        hint.Margin = new Thickness(0, 8, 0, 0);
        panel.Children.Add(hint);

        dialog.Content = new ScrollViewer { Content = panel, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };

        if (await dialog.ShowAsync() != ContentDialogResult.Primary) return null;
        return PhysicalSettingsEditor.Apply(settings, enabled.IsChecked == true, bezel.Text,
            rows.Select(r => new PhysicalRowInput(r.Monitor, r.Width.Text, r.Height.Text, r.Offset.Text)));
    }
}
