using System.Globalization;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace WallCraft.App.Dialogs;

/// <summary>Valeurs des retouches d'une image.</summary>
public sealed record AdjustValues(double Brightness, double Contrast, double Saturation, double Blur)
{
    /// <summary>Valeurs neutres (DEFAULTS de la version Python).</summary>
    public static readonly AdjustValues Default = new(1.0, 1.0, 1.0, 0.0);
}

/// <summary>
/// Retouches de l'image sélectionnée (<c>AdjustDialog</c> Python) : luminosité, contraste, saturation, flou, avec aperçu
/// en direct. « Valider » garde les réglages, « Réinitialiser » remet les valeurs neutres, « Annuler » (ou Échap)
/// rétablit les valeurs de départ.
/// </summary>
public static class AdjustDialog
{
    /// <summary>Curseurs : clé du texte, minimum, maximum, pas (SPECS de la version Python).</summary>
    public static readonly IReadOnlyList<(string LabelKey, double Min, double Max, double Step)> Specs =
    [
        ("adjust_brightness", 0.2, 2.0, 0.05),
        ("adjust_contrast", 0.2, 2.0, 0.05),
        ("adjust_saturation", 0.0, 2.0, 0.05),
        ("adjust_blur", 0.0, 20.0, 0.5),
    ];

    /// <summary>Délai de regroupement des aperçus pendant le glissement (80 ms, comme la version Python).</summary>
    public static readonly TimeSpan PreviewDelay = TimeSpan.FromMilliseconds(80);

    /// <summary>
    /// Affiche le dialogue. <paramref name="preview"/>(luminosité, contraste, saturation, flou) est appelé sur le fil
    /// d'interface pendant le réglage, puis avec les valeurs initiales si l'utilisateur annule.
    /// Retourne les valeurs validées, ou null si l'utilisateur annule.
    /// </summary>
    public static async Task<AdjustValues?> ShowAsync(XamlRoot root, AdjustValues initial, Action<double, double, double, double> preview)
    {
        ArgumentNullException.ThrowIfNull(initial);
        ArgumentNullException.ThrowIfNull(preview);
        var dialog = DialogHelpers.Create(root, "adjust_title");
        dialog.PrimaryButtonText = UiStrings.Get("btn_ok");
        dialog.SecondaryButtonText = UiStrings.Get("adjust_reset");
        dialog.CloseButtonText = UiStrings.Get("btn_cancel");

        double[] start = [initial.Brightness, initial.Contrast, initial.Saturation, initial.Blur];
        double[] neutral = [AdjustValues.Default.Brightness, AdjustValues.Default.Contrast, AdjustValues.Default.Saturation, AdjustValues.Default.Blur];
        var sliders = new Slider[Specs.Count];
        AdjustValues Current() => new(sliders[0].Value, sliders[1].Value, sliders[2].Value, sliders[3].Value);

        var timer = DispatcherQueue.GetForCurrentThread().CreateTimer();
        timer.Interval = PreviewDelay;
        timer.IsRepeating = false;
        bool pending = false;
        void ApplyNow()
        {
            timer.Stop();
            pending = false;
            var v = Current();
            preview(v.Brightness, v.Contrast, v.Saturation, v.Blur);
        }
        timer.Tick += (_, _) => ApplyNow();

        var grid = new Grid { ColumnSpacing = 12, RowSpacing = 4, MinWidth = 420 };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(48) });
        for (int i = 0; i < Specs.Count; i++)
        {
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            var (key, min, max, step) = Specs[i];
            string format = step < 0.1 ? "F2" : "F1";
            var valueText = DialogHelpers.Label("", secondary: true);
            valueText.HorizontalAlignment = HorizontalAlignment.Right;
            var slider = new Slider
            {
                Minimum = min, Maximum = max, StepFrequency = step, SmallChange = step, LargeChange = step * 4,
                Value = Math.Clamp(start[i], min, max),
                MinWidth = 260,
                TickPlacement = TickPlacement.None,
            };
            valueText.Text = slider.Value.ToString(format, CultureInfo.CurrentCulture);
            slider.ValueChanged += (_, e) =>
            {
                valueText.Text = e.NewValue.ToString(format, CultureInfo.CurrentCulture);
                if (!pending)
                {
                    pending = true;
                    timer.Start();
                }
            };
            sliders[i] = slider;
            DialogHelpers.Place(grid, DialogHelpers.Label(UiStrings.Get(key)), i, 0);
            DialogHelpers.Place(grid, slider, i, 1);
            DialogHelpers.Place(grid, valueText, i, 2);
        }
        dialog.Content = grid;

        // « Réinitialiser » ne ferme pas le dialogue.
        dialog.SecondaryButtonClick += (_, args) =>
        {
            args.Cancel = true;
            for (int i = 0; i < sliders.Length; i++) sliders[i].Value = neutral[i];
            ApplyNow();
        };

        var result = await dialog.ShowAsync();
        timer.Stop();
        if (result == ContentDialogResult.Primary)
        {
            var final = Current();
            if (pending) preview(final.Brightness, final.Contrast, final.Saturation, final.Blur);
            return final;
        }
        preview(initial.Brightness, initial.Contrast, initial.Saturation, initial.Blur);
        return null;
    }
}
