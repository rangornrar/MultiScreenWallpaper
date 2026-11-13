using Microsoft.UI.Dispatching;
using WallCraft.App.Dialogs;
using WallCraft.App.Services;
using WallCraft.Core.Geometry;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;
using WallCraft.Core.Persistence;
using WallCraft.Core.Services;
using WallCraft.Platform.Windows;

namespace WallCraft.App.Automation;

/// <summary>
/// Fond automatique (portage de <c>ui_automation.py</c>) : toutes les 4 s, détecte les écrans branchés/débranchés et
/// réapplique le fond mémorisé pour la nouvelle configuration ; toutes les 60 s, vérifie que le fond n'a pas été
/// remplacé (thème Windows → réappliquer ; choix de l'utilisateur → <see cref="WallpaperStore.Release"/> et ne plus y
/// toucher) ; rotation d'images depuis un dossier ; icône de notification.
/// Le travail lourd s'exécute hors du fil d'interface, une seule opération à la fois (ni pendant un travail de la fenêtre).
/// À créer et utiliser sur le fil d'interface.
/// </summary>
public sealed class AutomationService : IDisposable
{
    /// <summary>Intervalle de surveillance des écrans et de la rotation.</summary>
    public static readonly TimeSpan TickInterval = TimeSpan.FromSeconds(4);
    /// <summary>Intervalle de vérification du fond remplacé.</summary>
    public static readonly TimeSpan KeepCheckInterval = TimeSpan.FromSeconds(60);

    private readonly IAutomationHost _host;
    private readonly AppSettings _settings;
    private readonly WallpaperStore _store;
    private readonly DispatcherQueueTimer _timer;
    private TrayService? _tray;
    private bool _busy, _ticking, _disposed;
    private DateTimeOffset _lastKeepCheck = DateTimeOffset.MinValue;
    private DateTimeOffset? _nextRotationAt;
    private List<string> _lastRotation = [];

    public AutomationService(IAutomationHost host, AppSettings settings, WallpaperStore store)
    {
        _host = host ?? throw new ArgumentNullException(nameof(host));
        _settings = settings ?? throw new ArgumentNullException(nameof(settings));
        _store = store ?? throw new ArgumentNullException(nameof(store));
        var dispatcher = DispatcherQueue.GetForCurrentThread()
            ?? throw new InvalidOperationException("AutomationService doit être créé sur le fil d'interface.");
        _timer = dispatcher.CreateTimer();
        _timer.Interval = TickInterval;
        _timer.IsRepeating = true;
        _timer.Tick += (_, _) => OnTick();
    }

    /// <summary>True pendant une opération du service (réapplication, vérification, rotation).</summary>
    public bool IsBusy => _busy;

    /// <summary>Début ou fin d'une opération du service (pour griser « Appliquer » dans la fenêtre).</summary>
    public event EventHandler? BusyChanged;

    /// <summary>L'icône de notification est-elle affichée ? (fermer la fenêtre la cache alors au lieu de quitter)</summary>
    public bool IsTrayActive => _tray?.IsActive == true;

    /// <summary>Prochaine rotation prévue, ou null.</summary>
    public DateTimeOffset? NextRotationAt => _nextRotationAt;

    /// <summary>
    /// Démarre la surveillance et l'icône (<c>_start_services</c>). Retourne true si la fenêtre doit être affichée :
    /// avec <paramref name="startHidden"/> (option <c>--tray</c>) elle reste cachée, sauf si l'icône n'a pas pu être créée.
    /// </summary>
    public bool Start(bool startHidden)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        EnsureTray();
        ScheduleRotation(reset: true);
        _timer.Start();
        return !(startHidden && IsTrayActive);
    }

    /// <summary>Réglages actuels pour <see cref="AutomationDialog"/> (démarrage avec Windows lu dans le registre).</summary>
    public AutomationPrefs CurrentPrefs() => AutomationPrefs.Read(_settings, SafeAutostart());

    /// <summary>
    /// Applique les réglages validés dans <see cref="AutomationDialog"/> (<c>cmd_auto_prefs</c>) : settings.json, clé Run,
    /// avertissement si le dossier de rotation est vide, nouvelle échéance de rotation, icône affichée ou retirée.
    /// </summary>
    public void ApplyPrefs(AutomationPrefs prefs)
    {
        ArgumentNullException.ThrowIfNull(prefs);
        prefs.WriteTo(_settings);
        SaveSettings();
        try
        {
            if (prefs.Autostart != SafeAutostart()) SetAutostart(prefs.Autostart);
        }
        catch (Exception e) when (e is UnauthorizedAccessException or System.Security.SecurityException or IOException or InvalidOperationException)
        {
            _host.ShowWarning(UiStrings.Format("msg_autostart_failed", e.Message));
        }
        if (prefs.Rotation.Enabled && Rotation.ListImages(prefs.Rotation.Folder).Count == 0)
            _host.ShowWarning(UiStrings.Get("msg_rotation_empty"));
        ScheduleRotation(reset: true);
        EnsureTray();
    }

    /// <summary>Action choisie dans le menu de l'icône (<c>_handle_action</c>).</summary>
    public void HandleTrayAction(TrayAction action)
    {
        switch (action)
        {
            case TrayAction.Open:
                _host.ShowMainWindow();
                break;
            case TrayAction.Reapply:
                ReapplySaved(force: true);
                break;
            case TrayAction.Next:
                RotationTick(manual: true);
                break;
            case TrayAction.ToggleRotation:
            {
                var prefs = Prefs();
                (prefs with { Rotation = prefs.Rotation with { Enabled = !prefs.Rotation.Enabled } }).WriteTo(_settings);
                SaveSettings();
                ScheduleRotation(reset: true);
                break;
            }
            case TrayAction.ToggleKeep:
            {
                var prefs = Prefs();
                (prefs with { KeepWallpaper = !prefs.KeepWallpaper }).WriteTo(_settings);
                SaveSettings();
                break;
            }
            case TrayAction.ToggleAutostart:
                try { SetAutostart(!SafeAutostart()); }
                catch (Exception e) when (e is UnauthorizedAccessException or System.Security.SecurityException or IOException or InvalidOperationException) { }
                break;
            case TrayAction.Quit:
                _host.Quit();
                break;
        }
    }

    // --- Surveillance ---

    private bool KeepWallpaper => Prefs().KeepWallpaper;

    /// <summary>Réglages de settings.json, sans lire le registre (appel fréquent).</summary>
    private AutomationPrefs Prefs() => AutomationPrefs.Read(_settings);

    /// <summary>Toutes les 4 s (<c>_service_tick</c>) : écrans, fond remplacé (60 s), rotation.</summary>
    private async void OnTick()
    {
        if (_ticking || _disposed) return;
        _ticking = true;
        try
        {
            if (!AnyBusy)
            {
                var detected = await Task.Run(() => Monitors.Enumerate());
                if (_disposed || AnyBusy) return;
                if (detected.Count > 0 && CompositionLayout.Signature(detected) != CompositionLayout.Signature(_host.Monitors))
                {
                    _host.OnMonitorsChanged(detected);
                    _host.ShowStatus(UiStrings.Get("status_screens_changed"));
                    if (KeepWallpaper) ReapplySaved();
                }
                else if (KeepWallpaper && DateTimeOffset.Now - _lastKeepCheck > KeepCheckInterval)
                {
                    _lastKeepCheck = DateTimeOffset.Now;
                    CheckWallpaperKept();
                }
            }
            if (RotationSchedule.IsDue(_nextRotationAt, DateTimeOffset.Now)) RotationTick();
        }
        catch (Exception)
        {
            // Surveillance silencieuse : une erreur passagère (écran en cours de branchement…) ne l'arrête pas.
        }
        finally
        {
            _ticking = false;
        }
    }

    private bool AnyBusy => _busy || _host.IsBusy;

    /// <summary>Compare le fond actuel au fond mémorisé (<c>_check_wallpaper_kept</c>).</summary>
    public void CheckWallpaperKept()
    {
        var monitors = _host.Monitors.ToList();
        if (monitors.Count == 0 || _store.IsReleased(monitors)) return;
        var saved = _store.Load(monitors);
        if (saved.Count == 0) return;
        var expected = saved.Select(s => s.Path).ToList();
        RunExclusive(
            () => Task.FromResult(WallpaperWatch.Detect(expected, DesktopWallpaper.Current().Select(c => (string?)c.Path).ToList())),
            change =>
            {
                if (change == WallpaperChange.Theme) ReapplySaved();
                else if (change == WallpaperChange.User) _store.Release(monitors); // choix de l'utilisateur : on n'y touche plus
            });
    }

    /// <summary>
    /// Réapplique les images mémorisées pour la configuration d'écrans actuelle, sans nouveau rendu (<c>_reapply_saved</c>).
    /// <paramref name="force"/> : même si l'utilisateur a choisi un autre fond ; sans fond mémorisé, applique la composition.
    /// </summary>
    public void ReapplySaved(bool force = false)
    {
        var monitors = _host.Monitors.ToList();
        if (!force && _store.IsReleased(monitors)) return;
        var saved = _store.Load(monitors);
        if (saved.Count == 0)
        {
            if (force && _host.HasImages && !AnyBusy) _host.ApplyComposition();
            return;
        }
        var pieces = saved.Select(s => (new MonitorInfo { Name = s.Name, X = s.X, Y = s.Y, Width = s.Width, Height = s.Height }, s.Path)).ToList();
        var bg = _host.BackgroundColor;
        RunExclusive(
            () => Task.FromResult(DesktopWallpaper.Apply(pieces, (bg.R, bg.G, bg.B))),
            result =>
            {
                if (result.Applied > 0) _host.ShowStatus(UiStrings.Get("status_reapplied"));
            });
    }

    // --- Rotation ---

    /// <summary>Recalcule l'échéance de rotation (<c>_schedule_rotation</c>).</summary>
    public void ScheduleRotation(bool reset = false) =>
        _nextRotationAt = RotationSchedule.Next(Prefs().Rotation, DateTimeOffset.Now, _nextRotationAt, reset);

    /// <summary>
    /// Tire de nouvelles images du dossier de rotation, les dispose et les applique en arrière-plan (<c>_rotation_tick</c>).
    /// <paramref name="manual"/> : demandé par l'utilisateur (avertit si le dossier est vide).
    /// </summary>
    public void RotationTick(bool manual = false)
    {
        var rot = Prefs().Rotation;
        var files = Rotation.ListImages(rot.Folder);
        ScheduleRotation(reset: true);
        var monitors = _host.Monitors.Select(m => m.Clone()).ToList();
        if (files.Count == 0 || monitors.Count == 0 || AnyBusy)
        {
            if (manual && files.Count == 0) _host.ShowWarning(UiStrings.Get("msg_rotation_empty"));
            return;
        }
        var chosen = Rotation.Pick(files, Math.Max(1, rot.EffectiveCount(monitors.Count)), _lastRotation);
        _lastRotation = chosen;
        var (width, height) = CompositionLayout.Apply(monitors, _host.Physical);
        string mode = _host.LayoutMode;
        bool fill = _host.Fill;
        var bg = _host.BackgroundColor;

        RunExclusive(async () =>
        {
            var images = await LoadImagesAsync(chosen, fill);
            if (images.Count == 0) return (ApplyOutcome?)null;
            AutoLayout.Apply(new LayoutEngine(), mode, width, height, monitors, images, fill);
            return await WallpaperApplier.RenderAndApplyAsync(images, width, height, monitors, bg, _store);
        }, outcome =>
        {
            if (outcome?.Status is ApplyStatus.Ok or ApplyStatus.Partial or ApplyStatus.Span)
                _host.ShowStatus(UiStrings.Format("status_rotation", chosen.Count));
        });
    }

    /// <summary>Lit la taille des images (et leur point d'intérêt pour « Remplir ») ; les fichiers illisibles sont ignorés.</summary>
    private static async Task<List<CompositionImage>> LoadImagesAsync(IEnumerable<string> paths, bool fill)
    {
        var images = new List<CompositionImage>();
        foreach (var path in paths)
        {
            try
            {
                var (w, h) = await ImageDecoder.ReadSizeAsync(path);
                var img = new CompositionImage(path, w, h);
                if (fill)
                {
                    try { img.Focus = await FaceFocus.FindAsync(await ImageDecoder.DecodeAsync(path, ImageDecoder.ProxyMaxSize)); }
                    catch (Exception) { img.Focus = FocusPoint.Center; }
                }
                images.Add(img);
            }
            catch (Exception)
            {
                // Image illisible : on continue avec les autres.
            }
        }
        return images;
    }

    // --- Outils ---

    /// <summary>
    /// Exécute <paramref name="work"/> hors du fil d'interface si rien d'autre ne tourne (<c>_run_in_background</c>,
    /// mode silencieux) ; <paramref name="done"/> revient sur le fil d'interface, seulement en cas de succès.
    /// </summary>
    private async void RunExclusive<T>(Func<Task<T>> work, Action<T> done)
    {
        if (AnyBusy || _disposed) return;
        SetBusy(true);
        T result;
        try
        {
            result = await Task.Run(work);
        }
        catch (Exception)
        {
            return; // tâche de fond silencieuse, comme quiet=True en Python
        }
        finally
        {
            SetBusy(false);
        }
        if (_disposed) return;
        try { done(result); }
        catch (Exception) { }
    }

    private void SetBusy(bool value)
    {
        if (_busy == value) return;
        _busy = value;
        BusyChanged?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>Affiche ou retire l'icône selon le réglage <c>tray</c> (<c>_ensure_tray</c>).</summary>
    private void EnsureTray()
    {
        bool wanted = Prefs().Tray;
        if (wanted && _tray is null)
        {
            var tray = new TrayService(() =>
            {
                var p = CurrentPrefs();
                return new TrayState(p.Rotation.Enabled, p.KeepWallpaper, p.Autostart);
            });
            if (tray.Start())
            {
                tray.ActionInvoked += (_, action) => HandleTrayAction(action);
                _tray = tray;
            }
            else
            {
                tray.Dispose();
            }
        }
        else if (!wanted && _tray is not null)
        {
            _tray.Dispose();
            _tray = null;
        }
    }

    private void SaveSettings()
    {
        try { _settings.Save(); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException) { }
    }

    private static bool SafeAutostart()
    {
        try { return Autostart.IsEnabled(); }
        catch (Exception e) when (e is UnauthorizedAccessException or System.Security.SecurityException or IOException) { return false; }
    }

    private static void SetAutostart(bool enabled)
    {
        string exe = Environment.ProcessPath ?? throw new InvalidOperationException("Chemin de l'exécutable inconnu.");
        Autostart.Set(enabled, exe);
    }

    /// <summary>Arrête la surveillance et retire l'icône (à appeler avant de quitter).</summary>
    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _timer.Stop();
        _tray?.Dispose();
        _tray = null;
    }
}
