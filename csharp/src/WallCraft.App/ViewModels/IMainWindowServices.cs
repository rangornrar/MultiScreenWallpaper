using WallCraft.App.Dialogs;
using WallCraft.Core.Geometry;
using WallCraft.Core.Layout;

namespace WallCraft.App.ViewModels;

/// <summary>
/// Ce que la fenêtre fournit à <see cref="MainViewModel"/> : messages, sélecteurs de fichiers et dialogues (qui ont besoin
/// du HWND ou du XamlRoot). Tous les membres sont appelés sur le fil d'interface.
/// </summary>
public interface IMainWindowServices
{
    /// <summary>Message d'information ou d'avertissement (titre « Information »).</summary>
    Task ShowInfoAsync(string message);

    /// <summary>Message d'erreur (titre « Erreur »).</summary>
    Task ShowErrorAsync(string message);

    /// <summary>Question oui/non ; vrai si l'utilisateur valide.</summary>
    Task<bool> ConfirmAsync(string message);

    Task<IReadOnlyList<string>> PickImagesAsync();

    /// <summary>Fichier PNG ou JPEG où exporter l'image complète.</summary>
    Task<string?> PickExportFileAsync();

    Task<string?> PickProjectToSaveAsync();

    Task<string?> PickProjectToOpenAsync();

    Task<string?> PickFolderAsync();

    /// <summary>Choix d'une variante (<see cref="VariantsDialog"/>) ; index choisi ou null.</summary>
    Task<int?> ChooseVariantAsync(IReadOnlyList<IReadOnlyList<Placement>> variants);

    /// <summary>Taille réelle des écrans (<see cref="PhysicalSizeDialog"/>) ; nouveaux réglages ou null.</summary>
    Task<PhysicalSettings?> EditPhysicalSizeAsync(IReadOnlyList<MonitorInfo> monitors, PhysicalSettings current);

    /// <summary>Retouches de l'image (<see cref="AdjustDialog"/>) avec aperçu en direct ; valeurs validées ou null.</summary>
    Task<AdjustValues?> AdjustAsync(AdjustValues initial, Action<double, double, double, double> preview);
}
