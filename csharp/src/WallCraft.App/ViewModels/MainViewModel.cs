using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Graphics.Canvas;
using WallCraft.App.Dialogs;
using WallCraft.App.Services;
using WallCraft.Core.Editing;
using WallCraft.Core.Geometry;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;
using WallCraft.Core.Persistence;
using WallCraft.Core.Presentation;
using WallCraft.Core.Services;

namespace WallCraft.App.ViewModels;

/// <summary>Demande de redessin : <see cref="Live"/> pendant un glisser (l'aperçu sur les écrans limite sa fréquence).</summary>
public sealed class RedrawEventArgs(bool live) : EventArgs
{
    public bool Live { get; } = live;
}

/// <summary>
/// État et commandes de la fenêtre principale (portage de <c>WallpaperApp</c>, ui.py). L'édition souris/clavier est dans
/// <see cref="EditController"/> ; ce modèle relie le document, les écrans, les réglages et les traitements longs
/// (lancés hors du fil d'interface). À utiliser sur le fil d'interface.
/// </summary>
public sealed partial class MainViewModel : ObservableObject
{
    /// <summary>Page Ko-fi (même adresse que la version Python).</summary>
    public const string KofiUrl = "https://ko-fi.com/D1D21VSKW5";

    private readonly IMainWindowServices _ui;
    private readonly Localizer _loc = Localizer.Current;
    private readonly LayoutEngine _engine = new();
    private List<MonitorInfo> _monitors = [];
    private string? _layoutSignature;
    private bool _syncingSelection;

    private string _statusText = "";
    private string _selectionText = "";
    private bool _selectionIsWarning;
    private string _summaryText = "";
    private string _libraryCountText = "";
    private bool _isBusy;
    private bool _automationBusy;
    private bool _isFill;
    private int _layoutIndex;
    private bool _showMonitors = true;
    private bool _isPreview;
    private LibraryItemViewModel? _selectedLibraryItem;
    private IReadOnlyList<string> _monitorLabels = [];

    public MainViewModel(IMainWindowServices ui, AppSettings settings, WallpaperStore store)
    {
        _ui = ui;
        Settings = settings;
        Store = store;
        Physical = settings.Physical;
        _isFill = settings.Fill;
        Document = new CompositionDocument();
        View = new ViewTransform();
        Controller = new EditController(Document, View);
        Document.Changed += OnDocumentChanged;
        View.Changed += (_, _) => RequestRedraw(live: Controller.CurrentAction != DragAction.None);
        Controller.ModeChanged += (_, _) =>
        {
            OnPropertyChanged(nameof(Mode));
            RequestRedraw();
        };
        Images.ProxyLoaded += (_, _) =>
        {
            SyncLibrary();
            RequestRedraw();
        };
        _statusText = _loc["status_ready"];
    }

    // --- Modèle ---

    public CompositionDocument Document { get; }
    public ViewTransform View { get; }
    public EditController Controller { get; }
    public ImageCache Images { get; } = new();
    public AppSettings Settings { get; }
    public WallpaperStore Store { get; }

    /// <summary>Réglages « taille réelle » en vigueur (mêmes que <c>settings.json → physical</c>).</summary>
    public PhysicalSettings Physical { get; private set; }

    /// <summary>Écrans détectés, avec leur rectangle de composition.</summary>
    public IReadOnlyList<MonitorInfo> Monitors => _monitors;

    /// <summary>Noms lisibles des écrans (« Gauche · Philips 23″ »), dans l'ordre de <see cref="Monitors"/>.</summary>
    public IReadOnlyList<string> MonitorLabels => _monitorLabels;

    /// <summary>Couleur de fond de la composition (noir, comme <c>bg_color</c> en Python).</summary>
    public Windows.UI.Color BackgroundColor { get; } = Windows.UI.Color.FromArgb(255, 0, 0, 0);

    public int CompositionWidth => (int)Document.Width;
    public int CompositionHeight => (int)Document.Height;

    public ObservableCollection<LibraryItemViewModel> LibraryItems { get; } = [];

    /// <summary>Un redessin de la zone de travail est nécessaire.</summary>
    public event EventHandler<RedrawEventArgs>? RedrawRequested;

    /// <summary>La langue a changé : la fenêtre relit ses textes.</summary>
    public event EventHandler? TextsChanged;

    // --- État affiché ---

    public string StatusText { get => _statusText; set => SetProperty(ref _statusText, value); }
    public string SelectionText { get => _selectionText; private set => SetProperty(ref _selectionText, value); }
    public bool SelectionIsWarning { get => _selectionIsWarning; private set => SetProperty(ref _selectionIsWarning, value); }
    public string SummaryText { get => _summaryText; private set => SetProperty(ref _summaryText, value); }
    public string LibraryCountText { get => _libraryCountText; private set => SetProperty(ref _libraryCountText, value); }

    /// <summary>Traitement long en cours (rendu, application, disposition…) : curseur occupé, « Appliquer » grisé.</summary>
    public bool IsBusy
    {
        get => _isBusy;
        private set
        {
            if (SetProperty(ref _isBusy, value)) RefreshCommands();
        }
    }

    /// <summary>Le fond automatique travaille (réapplication, rotation) : « Appliquer » est grisé.</summary>
    public bool AutomationBusy
    {
        get => _automationBusy;
        set
        {
            if (SetProperty(ref _automationBusy, value)) RefreshCommands();
        }
    }

    /// <summary>Cadrage : Remplir (vrai) ou Ajuster (faux).</summary>
    public bool IsFill => _isFill;

    public int LayoutIndex
    {
        get => _layoutIndex;
        set
        {
            if (value < 0 || value >= LayoutModes.All.Count) return;
            SetProperty(ref _layoutIndex, value);
        }
    }

    /// <summary>Disposition choisie (<c>LayoutModes.*</c>).</summary>
    public string LayoutMode => LayoutModes.All[_layoutIndex];

    /// <summary>Noms des 6 dispositions dans la langue active.</summary>
    public IReadOnlyList<string> LayoutNames => LayoutModes.All.Select(id => _loc[id]).ToList();

    public bool ShowMonitors
    {
        get => _showMonitors;
        set
        {
            if (SetProperty(ref _showMonitors, value)) RequestRedraw();
        }
    }

    /// <summary>Vue « Aperçu sur les écrans » (sinon « Composition »).</summary>
    public bool IsPreview
    {
        get => _isPreview;
        set
        {
            if (SetProperty(ref _isPreview, value)) RequestRedraw();
        }
    }

    public EditMode Mode
    {
        get => Controller.Mode;
        set => Controller.Mode = value;
    }

    public LibraryItemViewModel? SelectedLibraryItem
    {
        get => _selectedLibraryItem;
        set
        {
            if (!SetProperty(ref _selectedLibraryItem, value) || _syncingSelection) return;
            if (value is not null) Document.Select(value.Index);
        }
    }

    public bool HasSelection => Document.Selected is not null;
    public bool CanApply => !IsBusy && !AutomationBusy;

    // --- Démarrage, langue, écrans ---

    /// <summary>Langue des réglages (ou du système), détection des écrans et premiers textes.</summary>
    public void Initialize()
    {
        string language = Settings.Language is { } saved && Localizer.Languages.Any(l => l.Code == saved) ? saved : Localizer.DetectSystemLanguage();
        _loc.SetLanguage(language);
        RefreshMonitors(force: true, announce: false);
        RefreshTexts();
    }

    /// <summary>Change la langue de l'interface sans redémarrer (<c>on_lang_changed</c>) et la mémorise.</summary>
    public void SetLanguage(string code)
    {
        _loc.SetLanguage(code);
        Settings.Language = _loc.Language;
        SaveSettings();
        RefreshTexts();
    }

    private void RefreshTexts()
    {
        if (!IsBusy) StatusText = _loc["status_ready"];
        _monitorLabels = MonitorNames.Labels(_monitors, _loc.PositionWords, _loc.DecimalSeparator);
        OnPropertyChanged(nameof(LayoutNames));
        SyncLibrary(rebuild: true);
        RefreshSummary();
        TextsChanged?.Invoke(this, EventArgs.Empty);
        RequestRedraw();
    }

    /// <summary>
    /// Détecte les écrans (ou prend <paramref name="detected"/>) et recalcule la composition (<c>_on_monitors_changed</c>) :
    /// sans <paramref name="force"/>, rien ne change si la configuration est la même. Les images gardent leur place relative.
    /// </summary>
    public bool RefreshMonitors(bool force, IReadOnlyList<MonitorInfo>? detected = null, bool announce = true)
    {
        List<MonitorInfo> monitors;
        if (detected is not null)
        {
            monitors = detected.Select(m => m.Clone()).ToList();
        }
        else
        {
            try
            {
                monitors = Platform.Windows.Monitors.Enumerate();
            }
            catch (Exception)
            {
                monitors = [];
            }
        }
        string? signature = monitors.Count > 0 ? CompositionLayout.Signature(monitors) : null;
        if (!force && signature == _layoutSignature) return false;
        _monitors = monitors;
        _layoutSignature = signature;
        var (width, height) = monitors.Count > 0 ? CompositionLayout.Apply(monitors, Physical) : (1920, 1080);
        Document.SetSize(width, height);
        _monitorLabels = MonitorNames.Labels(_monitors, _loc.PositionWords, _loc.DecimalSeparator);
        Controller.FitToView(View.ViewportWidth, View.ViewportHeight);
        if (announce) StatusText = _loc["status_screens_changed"];
        RefreshSummary();
        RequestRedraw();
        return true;
    }

    private void SaveSettings()
    {
        try
        {
            Settings.Physical = Physical;
            Settings.Save();
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // Réglages non enregistrés : l'application continue avec les valeurs en mémoire (comme en Python).
        }
    }

    // --- Document → affichage ---

    private void OnDocumentChanged(object? sender, CompositionChangedEventArgs e)
    {
        // Pendant un glisser, la bibliothèque n'est mise à jour qu'au relâchement (comme _refresh_library_panel).
        if (!e.Live) SyncLibrary();
        if (e.Reason is ChangeReason.Selection or ChangeReason.Undo or ChangeReason.Redo or ChangeReason.Opened
            or ChangeReason.Reset or ChangeReason.Removed or ChangeReason.Added)
        {
            OnPropertyChanged(nameof(HasSelection));
        }
        RefreshCommands();
        RefreshSummary();
        RefreshSelectionText();
        RequestRedraw(e.Live);
    }

    public void RequestRedraw(bool live = false) => RedrawRequested?.Invoke(this, new RedrawEventArgs(live));

    /// <summary>
    /// Bibliothèque : calque du dessus en premier ; la liste est reconstruite si l'ordre ou le nombre d'images a changé,
    /// sinon chaque ligne est mise à jour (alerte basse résolution, miniature). La sélection suit le document.
    /// </summary>
    private void SyncLibrary(bool rebuild = false)
    {
        var images = Document.Images;
        bool sameShape = !rebuild && LibraryItems.Count == images.Count
            && LibraryItems.All(item => item.Index < images.Count && string.Equals(images[item.Index].Path, item.FullPath, StringComparison.Ordinal))
            && LibraryItems.Select(i => i.Index).SequenceEqual(Enumerable.Range(0, images.Count).Reverse());
        _syncingSelection = true;
        try
        {
            if (!sameShape)
            {
                SelectedLibraryItem = null;
                LibraryItems.Clear();
                for (int i = images.Count - 1; i >= 0; i--) LibraryItems.Add(new LibraryItemViewModel(images[i], i));
            }
            foreach (var item in LibraryItems) item.Update(images[item.Index], Images, _loc);
            SelectedLibraryItem = Document.SelectedIndex is int sel ? LibraryItems.FirstOrDefault(i => i.Index == sel) : null;
        }
        finally
        {
            _syncingSelection = false;
        }
        LibraryCountText = _loc.Plural("n_images", images.Count);
    }

    private void RefreshSummary()
    {
        string summary = $"{CompositionWidth} × {CompositionHeight}  •  {_loc.Plural("n_screens", _monitors.Count)}";
        if (Physical.Enabled) summary += $" ({_loc["physical_badge"]})";
        SummaryText = summary + $"  •  {_loc.Plural("n_images", Document.Images.Count)}";
    }

    /// <summary>Résumé de la sélection dans la barre d'état (<c>_refresh_inspector_panel</c>).</summary>
    private void RefreshSelectionText()
    {
        var img = Document.Selected;
        if (img is null)
        {
            SelectionText = Document.Images.Count > 0 ? _loc["selection_hint"] : "";
            SelectionIsWarning = false;
            return;
        }
        string name = DisplayText.SelectionName(Path.GetFileName(img.Path));
        var parts = new List<string>
        {
            _loc.Format("selection_summary", name, (int)(img.W ?? 0), (int)(img.H ?? 0), img.ZIndex + 1, Math.Max(1, Document.Images.Count)),
            $"{_loc["position"]} {(int)img.X}, {(int)img.Y}",
            $"{_loc["crop"]} {DisplayText.CropPercent(img)} %",
        };
        string? low = DisplayText.LowResolution(img, _loc.DecimalSeparator);
        if (low is not null) parts.Add("⚠ " + _loc.Format("lowres_tip", low));
        SelectionText = string.Join("  •  ", parts);
        SelectionIsWarning = low is not null;
    }

    private void RefreshCommands()
    {
        OnPropertyChanged(nameof(CanApply));
        OnPropertyChanged(nameof(HasSelection));
        ApplyWallpaperCommand.NotifyCanExecuteChanged();
        RotateCommand.NotifyCanExecuteChanged();
        AdjustCommand.NotifyCanExecuteChanged();
        RemoveCommand.NotifyCanExecuteChanged();
        SendBackwardCommand.NotifyCanExecuteChanged();
        BringForwardCommand.NotifyCanExecuteChanged();
    }

    // --- Traitements longs ---

    /// <summary>
    /// Exécute <paramref name="work"/> hors du fil d'interface (<c>_run_in_background</c>) : un seul à la fois, statut
    /// « Traitement… » et curseur occupé. Une exception est montrée à l'utilisateur ; renvoie alors default.
    /// </summary>
    private async Task<(bool Ok, T? Result)> RunBusyAsync<T>(Func<Task<T>> work, string statusKey = "status_processing")
    {
        if (IsBusy) return (false, default);
        IsBusy = true;
        StatusText = _loc[statusKey];
        try
        {
            return (true, await Task.Run(work));
        }
        catch (Exception e)
        {
            IsBusy = false;
            StatusText = _loc["status_ready"];
            await _ui.ShowErrorAsync(e.Message);
            return (false, default);
        }
        finally
        {
            if (IsBusy)
            {
                IsBusy = false;
                StatusText = _loc["status_ready"];
            }
        }
    }

    private async Task<bool> RequireImagesAsync()
    {
        if (Document.Images.Count > 0) return true;
        await _ui.ShowInfoAsync(_loc["msg_no_images"]);
        return false;
    }

    private async Task<bool> RequireMonitorsAsync()
    {
        if (_monitors.Count > 0) return true;
        await _ui.ShowErrorAsync(_loc["err_no_monitors"]);
        return false;
    }

    private List<CompositionImage> Snapshot() => Document.Images.Select(i => i.Clone()).ToList();
    private List<MonitorInfo> MonitorSnapshot() => _monitors.Select(m => m.Clone()).ToList();

    // --- Images ---

    [RelayCommand]
    private async Task AddImagesAsync()
    {
        var paths = await _ui.PickImagesAsync();
        await AddPathsAsync(paths);
    }

    /// <summary>
    /// Ajoute des images (sélecteur ou glisser-déposer) : taille et vignette lues en arrière-plan, images placées au centre
    /// de la vue (<c>cmd_add_images</c>). Le point d'intérêt se calcule ensuite en arrière-plan.
    /// </summary>
    public async Task AddPathsAsync(IReadOnlyList<string> paths)
    {
        if (paths.Count == 0) return;
        var loads = paths.Select(p => (Path: p, Task: Images.LoadAsync(p))).ToList();
        var added = new List<CompositionImage>();
        var errors = new List<string>();
        foreach (var (path, task) in loads)
        {
            try
            {
                var proxy = await task;
                added.Add(new CompositionImage(path, proxy.Width, proxy.Height));
            }
            catch (Exception e)
            {
                errors.Add($"{Path.GetFileName(path)} : {e.Message}");
            }
        }
        if (errors.Count > 0) await _ui.ShowInfoAsync(_loc.Format("msg_load_errors", DisplayText.FormatErrors(errors)));
        if (added.Count == 0) return;
        Controller.AddImagesAtViewCenter(added);
    }

    [RelayCommand(CanExecute = nameof(HasSelection))]
    private void Rotate() => Document.RotateSelected();

    [RelayCommand(CanExecute = nameof(HasSelection))]
    private void Remove()
    {
        if (Document.RemoveSelected()) StatusText = _loc["status_removed"];
    }

    private bool CanSendBackward() => Document.CanSendBackward;
    private bool CanBringForward() => Document.CanBringForward;

    [RelayCommand(CanExecute = nameof(CanSendBackward))]
    private void SendBackward() => Document.SendBackward();

    [RelayCommand(CanExecute = nameof(CanBringForward))]
    private void BringForward() => Document.BringForward();

    /// <summary>Retouches de l'image sélectionnée, avec aperçu en direct ; validées, elles entrent dans l'historique.</summary>
    [RelayCommand(CanExecute = nameof(HasSelection))]
    private async Task AdjustAsync()
    {
        var img = Document.Selected;
        if (img is null) return;
        var values = await _ui.AdjustAsync(new AdjustValues(img.Brightness, img.Contrast, img.Saturation, img.Blur), (b, c, s, f) =>
        {
            img.Brightness = b;
            img.Contrast = c;
            img.Saturation = s;
            img.Blur = f;
            RequestRedraw(live: true);
        });
        if (values is null) return;
        img.Brightness = values.Brightness;
        img.Contrast = values.Contrast;
        img.Saturation = values.Saturation;
        img.Blur = values.Blur;
        Document.Commit("Adjust", ChangeReason.Adjusted);
    }

    /// <summary>Touches d'édition (Ctrl+Z, Ctrl+Y, Ctrl+R, Suppr) ; Suppr passe par <see cref="RemoveCommand"/> pour le message d'état.</summary>
    public void HandleEditKey(EditKey key, EditModifiers modifiers)
    {
        if (key == EditKey.Delete) Remove();
        else Controller.KeyDown(key, modifiers);
    }

    // --- Dispositions ---

    /// <summary>Change le cadrage (Ajuster/Remplir), le mémorise et refait la disposition (<c>_set_fill</c>).</summary>
    public void SetFill(bool fill)
    {
        if (fill == _isFill) return;
        _isFill = fill;
        OnPropertyChanged(nameof(IsFill));
        Settings.Fill = fill;
        SaveSettings();
        if (Document.Images.Count > 0) _ = AutoArrangeAsync();
    }

    /// <summary>Disposition automatique calculée en arrière-plan (<c>cmd_autofill</c>) ; Annuler revient à l'état précédent.</summary>
    [RelayCommand]
    private async Task AutoArrangeAsync()
    {
        if (Document.Images.Count == 0 || IsBusy) return;
        string mode = LayoutMode;
        bool fill = _isFill;
        int w = CompositionWidth, h = CompositionHeight;
        if (fill) await Images.EnsureFocusAsync(Document.Images);
        var images = Snapshot();
        var monitors = MonitorSnapshot();
        var (ok, placement) = await RunBusyAsync(() => Task.FromResult(Compute()));
        if (ok && placement is not null && SameImages(images)) Document.ApplyPlacement(placement);

        List<Placement> Compute()
        {
            AutoLayout.Apply(_engine, mode, w, h, monitors, images, fill);
            return images.Select(c => new Placement(c.X, c.Y, c.W ?? 0, c.H ?? 0, c.Crop, c.ZIndex)).ToList();
        }
    }

    /// <summary>Les images n'ont pas changé (ajout, suppression, ordre) pendant le calcul.</summary>
    private bool SameImages(List<CompositionImage> snapshot)
        => snapshot.Count == Document.Images.Count
           && snapshot.Select(i => i.Path).SequenceEqual(Document.Images.Select(i => i.Path), StringComparer.Ordinal);

    /// <summary>Variantes de la disposition choisie, calculées en arrière-plan puis montrées côte à côte (<c>cmd_variants</c>).</summary>
    [RelayCommand]
    private async Task VariantsAsync()
    {
        if (IsBusy || !await RequireImagesAsync()) return;
        string mode = LayoutMode;
        if (mode == LayoutModes.Mosaic && Document.Images.Count <= _monitors.Count) mode = LayoutModes.Optimal; // une seule variante possible
        bool fill = _isFill;
        int w = CompositionWidth, h = CompositionHeight;
        if (fill) await Images.EnsureFocusAsync(Document.Images);
        var images = Snapshot();
        var (ok, variants) = await RunBusyAsync(() => Task.FromResult(_engine.Variants(mode, w, h, images, fill)), "variants_computing");
        if (!ok || variants is null || variants.Count == 0) return;
        int? chosen = await _ui.ChooseVariantAsync(variants.Select(v => (IReadOnlyList<Placement>)v).ToList());
        if (chosen is int i && i >= 0 && i < variants.Count && SameImages(images)) Document.ApplyPlacement(variants[i]);
    }

    // --- Application et export ---

    [RelayCommand(CanExecute = nameof(CanApply))]
    private async Task ApplyWallpaperAsync()
    {
        if (!await RequireImagesAsync() || !await RequireMonitorsAsync()) return;
        var images = Snapshot();
        var monitors = MonitorSnapshot();
        int w = CompositionWidth, h = CompositionHeight;
        var bg = BackgroundColor;
        var store = Store;
        var (ok, outcome) = await RunBusyAsync(() => WallpaperApplier.RenderAndApplyAsync(images, w, h, monitors, bg, store));
        if (!ok || outcome is null) return;
        string errors = DisplayText.FormatErrors(outcome.Errors);
        switch (outcome.Status)
        {
            case ApplyStatus.Ok:
                await _ui.ShowInfoAsync(_loc["msg_apply_ok"]);
                break;
            case ApplyStatus.Partial:
                await _ui.ShowInfoAsync(_loc.Format("msg_apply_partial", errors));
                break;
            case ApplyStatus.Span:
                await _ui.ShowInfoAsync(_loc.Format("msg_span_fallback", errors));
                break;
            case ApplyStatus.NoMonitors:
                await _ui.ShowErrorAsync(_loc["err_no_monitors"]);
                break;
            default:
                await _ui.ShowErrorAsync(_loc["err_api_fail"] + (errors.Length > 0 ? "\n\n" + errors : ""));
                break;
        }
    }

    /// <summary>Exporte l'image complète en PNG ou JPEG (selon l'extension choisie), en pleine résolution.</summary>
    [RelayCommand]
    private async Task ExportImageAsync()
    {
        if (IsBusy || !await RequireImagesAsync()) return;
        if (await _ui.PickExportFileAsync() is not { } path) return;
        var images = Snapshot();
        int w = CompositionWidth, h = CompositionHeight;
        var bg = BackgroundColor;
        bool jpeg = Path.GetExtension(path).ToLowerInvariant() is ".jpg" or ".jpeg";
        var (ok, _) = await RunBusyAsync(async () =>
        {
            using var composite = await HdRenderer.ComposeAsync(images, w, h, bg);
            await composite.SaveAsync(path, jpeg ? CanvasBitmapFileFormat.Jpeg : CanvasBitmapFileFormat.Png, 0.95f);
            return path;
        });
        if (ok) StatusText = _loc.Format("msg_exported", Path.GetFileName(path));
    }

    /// <summary>Exporte une image PNG par écran, à la taille native de chaque écran (<c>cmd_export_split</c>).</summary>
    [RelayCommand]
    private async Task ExportSplitAsync()
    {
        if (IsBusy || !await RequireImagesAsync() || !await RequireMonitorsAsync()) return;
        if (await _ui.PickFolderAsync() is not { } folder) return;
        var images = Snapshot();
        var monitors = MonitorSnapshot();
        int w = CompositionWidth, h = CompositionHeight;
        var bg = BackgroundColor;
        var (ok, count) = await RunBusyAsync(async () =>
        {
            using var composite = await HdRenderer.ComposeAsync(images, w, h, bg);
            return (await HdRenderer.SplitAsync(composite, monitors, folder, "wallcraft")).Count;
        });
        if (ok) await _ui.ShowInfoAsync(_loc.Format("msg_split_done", count, folder));
    }

    // --- Projets ---

    [RelayCommand]
    private async Task NewProjectAsync()
    {
        if (IsBusy) return;
        if (Document.Images.Count > 0 && !await _ui.ConfirmAsync(_loc["new_project_confirm"])) return;
        Controller.NewProject();
        Images.Trim([]);
        StatusText = _loc["project_reset_status"];
    }

    [RelayCommand]
    private async Task SaveProjectAsync()
    {
        if (!await RequireImagesAsync()) return;
        string? path = await _ui.PickProjectToSaveAsync();
        if (path is null) return;
        try
        {
            var meta = ProjectMeta.Build(CompositionWidth, CompositionHeight, LayoutMode, _isFill, Physical.Enabled, _monitors);
            ProjectFile.Save(path, meta, Document.Images);
            StatusText = _loc.Format("msg_saved", Path.GetFileName(path));
        }
        catch (Exception e)
        {
            await _ui.ShowErrorAsync(e.Message);
        }
    }

    /// <summary>
    /// Ouvre un projet (Python ou C#) : images relues en arrière-plan, disposition et cadrage repris des métadonnées ;
    /// les images introuvables sont signalées (<c>cmd_open_project</c>).
    /// </summary>
    [RelayCommand]
    private async Task OpenProjectAsync()
    {
        if (IsBusy) return;
        string? path = await _ui.PickProjectToOpenAsync();
        if (path is null) return;
        if (Document.Images.Count > 0 && !await _ui.ConfirmAsync(_loc["new_project_confirm"])) return;
        var (ok, project) = await RunBusyAsync(() => Task.FromResult(
            ProjectFile.Load(path, ReadImageSize)));
        if (!ok || project is null) return;
        if (ProjectMeta.Layout(project.Meta) is { } layout) LayoutIndex = LayoutModes.All.ToList().IndexOf(layout);
        if (ProjectMeta.Fill(project.Meta) is bool fill && fill != _isFill)
        {
            _isFill = fill; // comme en Python : le cadrage du projet est repris sans refaire la disposition
            OnPropertyChanged(nameof(IsFill));
        }
        Document.Load(project.Images, project.Meta);
        foreach (var img in project.Images) _ = LoadQuietlyAsync(img.Path);
        if (project.Errors.Count > 0) await _ui.ShowInfoAsync(_loc.Format("msg_load_errors", DisplayText.FormatErrors(project.Errors)));
    }

    /// <summary>Taille d'une image du projet ; une image illisible devient une erreur listée, pas un échec de l'ouverture.</summary>
    private static (int Width, int Height) ReadImageSize(string path)
    {
        try
        {
            return ImageDecoder.ReadSizeAsync(path).GetAwaiter().GetResult();
        }
        catch (Exception e) when (e is not IOException and not UnauthorizedAccessException)
        {
            throw new InvalidDataException(e.Message, e);
        }
    }

    private async Task LoadQuietlyAsync(string path)
    {
        try
        {
            await Images.LoadAsync(path);
        }
        catch (Exception)
        {
            // Image devenue illisible : elle reste un cadre vide dans la composition, le rendu HD signalera l'erreur.
        }
    }

    // --- Écrans ---

    [RelayCommand]
    private void RedetectScreens() => RefreshMonitors(force: true);

    /// <summary>Taille réelle des écrans (<c>cmd_physical</c>) : réglages mémorisés, composition recalculée et redisposée.</summary>
    [RelayCommand]
    private async Task PhysicalSizeAsync()
    {
        if (!await RequireMonitorsAsync()) return;
        var settings = await _ui.EditPhysicalSizeAsync(_monitors, Physical);
        if (settings is null) return;
        Physical = settings;
        SaveSettings();
        RefreshMonitors(force: true);
        if (Document.Images.Count > 0) await AutoArrangeAsync();
    }
}
