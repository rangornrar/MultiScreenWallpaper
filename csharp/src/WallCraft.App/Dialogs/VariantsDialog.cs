using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using WallCraft.Core.Layout;

namespace WallCraft.App.Dialogs;

/// <summary>Vignettes des variantes d'une disposition (<c>VariantsDialog</c> Python) ; un clic choisit la variante.</summary>
public static class VariantsDialog
{
    /// <summary>Largeur des vignettes, comme THUMB_W en Python.</summary>
    public const double ThumbnailWidth = 300;

    /// <summary>
    /// Affiche les variantes sur deux colonnes. <paramref name="renderThumbnail"/> dessine une vignette (l'appelant en
    /// connaît les images) ; elle est appelée sur le fil d'interface, une variante après l'autre, pendant que le dialogue
    /// est ouvert. <paramref name="compositionAspect"/> = largeur / hauteur de la composition.
    /// Retourne l'index de la variante choisie, ou null si l'utilisateur annule.
    /// </summary>
    public static async Task<int?> ShowAsync(XamlRoot root, IReadOnlyList<IReadOnlyList<Placement>> variants,
        Func<IReadOnlyList<Placement>, Task<ImageSource>> renderThumbnail, double compositionAspect)
    {
        ArgumentNullException.ThrowIfNull(variants);
        ArgumentNullException.ThrowIfNull(renderThumbnail);
        var dialog = DialogHelpers.Create(root, "variants_title", maxWidth: 2 * ThumbnailWidth + 120);
        dialog.CloseButtonText = UiStrings.Get("btn_cancel");
        dialog.DefaultButton = ContentDialogButton.None;

        double aspect = compositionAspect > 0 && double.IsFinite(compositionAspect) ? compositionAspect : 16.0 / 9.0;
        double thumbHeight = Math.Max(1, Math.Round(ThumbnailWidth / aspect));
        int? chosen = null;

        var grid = new Grid { ColumnSpacing = 16, RowSpacing = 16 };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        for (int r = 0; r < (variants.Count + 1) / 2; r++) grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

        var slots = new List<(Image Image, ProgressRing Ring)>();
        for (int i = 0; i < variants.Count; i++)
        {
            int index = i;
            var image = new Image { Width = ThumbnailWidth, Height = thumbHeight, Stretch = Stretch.Uniform };
            var ring = new ProgressRing { IsActive = true, Width = 32, Height = 32 };
            var surface = new Grid { Width = ThumbnailWidth, Height = thumbHeight };
            surface.Children.Add(ring);
            surface.Children.Add(image);

            var button = new Button { Content = surface, Padding = new Thickness(4) };
            AutomationProperties_SetName(button, UiStrings.Format("variant_n", i + 1));
            button.Click += (_, _) =>
            {
                chosen = index;
                dialog.Hide();
            };

            var cell = new StackPanel { Spacing = 4 };
            cell.Children.Add(button);
            var caption = DialogHelpers.Label(UiStrings.Format("variant_n", i + 1), secondary: true);
            caption.HorizontalAlignment = HorizontalAlignment.Center;
            cell.Children.Add(caption);
            DialogHelpers.Place(grid, cell, i / 2, i % 2);
            slots.Add((image, ring));
        }

        var panel = new StackPanel { Spacing = 12 };
        panel.Children.Add(DialogHelpers.Label(UiStrings.Get("variants_hint"), secondary: true, wrap: true));
        panel.Children.Add(grid);
        dialog.Content = new ScrollViewer { Content = panel, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };

        var showing = dialog.ShowAsync().AsTask();
        for (int i = 0; i < variants.Count && !showing.IsCompleted; i++)
        {
            try
            {
                slots[i].Image.Source = await renderThumbnail(variants[i]);
            }
            catch (Exception)
            {
                // Vignette impossible à dessiner : la case reste vide mais reste cliquable.
            }
            slots[i].Ring.IsActive = false;
            slots[i].Ring.Visibility = Visibility.Collapsed;
        }
        await showing;
        return chosen;
    }

    private static void AutomationProperties_SetName(DependencyObject element, string name) =>
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(element, name);
}
