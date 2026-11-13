using System.Runtime.InteropServices;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;

namespace WallCraft.App.Automation;

/// <summary>Fermeture vers la zone de notification et retour de la fenêtre (<c>_on_close</c> et <c>show_window</c> Python).</summary>
public static class WindowTray
{
    /// <summary>
    /// À appeler dans <c>AppWindow.Closing</c> : si l'icône de notification est active, annule la fermeture et cache la
    /// fenêtre (le fond automatique continue). Retourne true si la fenêtre a été cachée, false si elle doit se fermer.
    /// </summary>
    public static bool HideInsteadOfClosing(Window window, AppWindowClosingEventArgs args, bool trayActive)
    {
        ArgumentNullException.ThrowIfNull(window);
        ArgumentNullException.ThrowIfNull(args);
        if (!trayActive) return false;
        args.Cancel = true;
        window.AppWindow.Hide();
        return true;
    }

    /// <summary>Montre la fenêtre (même jamais affichée, après un démarrage avec <c>--tray</c>), la restaure et la met au premier plan.</summary>
    public static void ShowMainWindow(Window window)
    {
        ArgumentNullException.ThrowIfNull(window);
        var appWindow = window.AppWindow;
        appWindow.Show();
        if (appWindow.Presenter is OverlappedPresenter { State: OverlappedPresenterState.Minimized } presenter)
            presenter.Restore();
        window.Activate();
        _ = SetForegroundWindow(WinRT.Interop.WindowNative.GetWindowHandle(window));
    }

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetForegroundWindow(nint hWnd);
}
