using WallCraft.Core.Geometry;

namespace WallCraft.App.Automation;

/// <summary>
/// Ce que la fenêtre principale fournit au <see cref="AutomationService"/>. Tous les membres sont appelés sur le fil
/// d'interface.
/// </summary>
public interface IAutomationHost
{
    /// <summary>Écrans actuellement pris en compte par la fenêtre (ceux de sa composition).</summary>
    IReadOnlyList<MonitorInfo> Monitors { get; }

    /// <summary>Réglages « taille réelle » en vigueur.</summary>
    PhysicalSettings Physical { get; }

    /// <summary>Disposition choisie (<c>LayoutModes.*</c>, ex. <c>"layout_mosaic"</c>), utilisée par la rotation.</summary>
    string LayoutMode { get; }

    /// <summary>Cadrage « Remplir » (true) ou « Ajuster » (false).</summary>
    bool Fill { get; }

    /// <summary>Couleur de fond de la composition.</summary>
    Windows.UI.Color BackgroundColor { get; }

    /// <summary>True pendant un travail de la fenêtre (rendu, application…) : le service attend.</summary>
    bool IsBusy { get; }

    /// <summary>La composition contient-elle des images ? (« Réappliquer » sans fond mémorisé applique la composition.)</summary>
    bool HasImages { get; }

    /// <summary>Applique la composition actuelle (commande « Appliquer » de la fenêtre).</summary>
    void ApplyComposition();

    /// <summary>
    /// Les écrans ont changé (branchement, résolution…) : <paramref name="detected"/> = écrans détectés. La fenêtre
    /// recalcule sa composition et doit mettre à jour <see cref="Monitors"/> AVANT de rendre la main.
    /// </summary>
    void OnMonitorsChanged(IReadOnlyList<MonitorInfo> detected);

    /// <summary>Message dans la barre d'état.</summary>
    void ShowStatus(string message);

    /// <summary>Avertissement à montrer à l'utilisateur (dossier de rotation vide, démarrage impossible…).</summary>
    void ShowWarning(string message);

    /// <summary>Ramène la fenêtre au premier plan (menu « Ouvrir », double-clic) : <see cref="WindowTray.ShowMainWindow"/>.</summary>
    void ShowMainWindow();

    /// <summary>Quitte vraiment l'application (menu « Quitter ») ; appeler <see cref="AutomationService.Dispose"/> avant.</summary>
    void Quit();
}
