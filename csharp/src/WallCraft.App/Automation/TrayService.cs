using CommunityToolkit.Mvvm.Input;
using H.NotifyIcon;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml.Controls;
using WallCraft.App.Dialogs;
using WallCraft.Core.Imaging;

namespace WallCraft.App.Automation;

/// <summary>Commandes du menu de l'icône de notification (mêmes actions que <c>TrayIcon</c> Python).</summary>
public enum TrayAction
{
    Open,
    Reapply,
    Next,
    ToggleRotation,
    ToggleKeep,
    ToggleAutostart,
    Quit,
}

/// <summary>État des cases du menu, lu à chaque ouverture.</summary>
public readonly record struct TrayState(bool Rotation, bool Keep, bool Autostart);

/// <summary>
/// Icône dans la zone de notification (H.NotifyIcon.WinUI) : Ouvrir (aussi au double-clic), Réappliquer, Images
/// suivantes, Rotation ✓, Garder le fond ✓, Démarrer avec Windows ✓, Quitter. Les choix sont remontés par
/// <see cref="ActionInvoked"/>, toujours sur le fil d'interface. À créer sur le fil d'interface.
/// </summary>
public sealed class TrayService : IDisposable
{
    private readonly Func<TrayState> _state;
    private readonly DispatcherQueue _dispatcher;
    private TaskbarIcon? _icon;
    private ToggleMenuFlyoutItem? _rotation, _keep, _autostart;

    public TrayService(Func<TrayState> state)
    {
        _state = state ?? throw new ArgumentNullException(nameof(state));
        _dispatcher = DispatcherQueue.GetForCurrentThread()
            ?? throw new InvalidOperationException("TrayService doit être créé sur le fil d'interface.");
    }

    /// <summary>Choix de l'utilisateur dans le menu (ou double-clic → <see cref="TrayAction.Open"/>).</summary>
    public event EventHandler<TrayAction>? ActionInvoked;

    public bool IsActive => _icon is not null;

    /// <summary>Crée l'icône. False si la zone de notification n'est pas disponible.</summary>
    public bool Start()
    {
        if (_icon is not null) return true;
        try
        {
            var menu = new MenuFlyout();
            menu.Items.Add(Item("tray_open", TrayAction.Open));
            menu.Items.Add(Item("tray_reapply", TrayAction.Reapply));
            menu.Items.Add(Item("tray_next", TrayAction.Next));
            menu.Items.Add(new MenuFlyoutSeparator());
            menu.Items.Add(_rotation = Toggle("tray_rotation", TrayAction.ToggleRotation));
            menu.Items.Add(_keep = Toggle("tray_keep", TrayAction.ToggleKeep));
            menu.Items.Add(_autostart = Toggle("tray_autostart", TrayAction.ToggleAutostart));
            menu.Items.Add(new MenuFlyoutSeparator());
            menu.Items.Add(Item("tray_quit", TrayAction.Quit));

            var icon = new TaskbarIcon
            {
                ToolTipText = UiStrings.Get("AppDisplayName"),
                ContextMenuMode = ContextMenuMode.PopupMenu,
                ContextFlyout = menu,
                DoubleClickCommand = new RelayCommand(() => Raise(TrayAction.Open)),
                NoLeftClickDelay = true,
            };
            // Les cases sont lues juste avant la construction du menu natif.
            icon.PreviewTrayContextMenuOpen += (_, _) => RefreshChecks();
            icon.Icon = new System.Drawing.Icon(new MemoryStream(TrayIconArt.CreateIco()), 32, 32);
            icon.ForceCreate(enablesEfficiencyMode: false);
            _icon = icon;
            return true;
        }
        catch (Exception)
        {
            _icon?.Dispose();
            _icon = null;
            return false;
        }
    }

    /// <summary>Relit l'état des cases (appelé automatiquement à l'ouverture du menu).</summary>
    public void RefreshChecks()
    {
        TrayState s;
        try { s = _state(); }
        catch (Exception) { return; }
        if (_rotation is not null) _rotation.IsChecked = s.Rotation;
        if (_keep is not null) _keep.IsChecked = s.Keep;
        if (_autostart is not null) _autostart.IsChecked = s.Autostart;
    }

    private MenuFlyoutItem Item(string key, TrayAction action) => new()
    {
        Text = UiStrings.Get(key),
        Command = new RelayCommand(() => Raise(action)),
    };

    private ToggleMenuFlyoutItem Toggle(string key, TrayAction action) => new()
    {
        Text = UiStrings.Get(key),
        Command = new RelayCommand(() => Raise(action)),
    };

    /// <summary>Remonte l'action sur le fil d'interface, après la fermeture du menu natif.</summary>
    private void Raise(TrayAction action) => _dispatcher.TryEnqueue(() => ActionInvoked?.Invoke(this, action));

    public void Dispose()
    {
        if (_icon is null) return;
        try { _icon.Dispose(); }
        catch (Exception) { }
        _icon = null;
    }
}
