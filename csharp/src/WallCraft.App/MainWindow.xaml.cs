using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Graphics.Canvas.UI;
using Microsoft.Graphics.Canvas.UI.Xaml;
using Microsoft.UI;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Input;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Imaging;
using Windows.ApplicationModel.DataTransfer;
using Windows.Storage;
using Windows.Storage.Pickers;
using VirtualKey = Windows.System.VirtualKey;
using VirtualKeyModifiers = Windows.System.VirtualKeyModifiers;
using WallCraft.App.Automation;
using WallCraft.App.Dialogs;
using WallCraft.App.Rendering;
using WallCraft.App.Services;
using WallCraft.App.ViewModels;
using WallCraft.Core.Editing;
using WallCraft.Core.Geometry;
using WallCraft.Core.Layout;
using WallCraft.Core.Persistence;
using WallCraft.Core.Services;

namespace WallCraft.App;

/// <summary>
/// Fenêtre principale : barre de titre avec menus, barre d'outils, bibliothèque, zone de travail Win2D et barre d'état.
/// La vue relaie les événements à <see cref="MainViewModel"/> / <see cref="EditController"/> et dessine ; elle fournit
/// les dialogues et sélecteurs de fichiers (<see cref="IMainWindowServices"/>) et sert d'hôte au fond automatique
/// (<see cref="IAutomationHost"/>).
/// </summary>
public sealed partial class MainWindow : Window, IMainWindowServices, IAutomationHost
{
    /// <summary>Taille minimale de la fenêtre, en pixels effectifs (comme <c>minsize(1100, 700)</c>).</summary>
    private const int MinWidth = 1100, MinHeight = 700;

    private readonly Localizer _loc = Localizer.Current;
    private readonly AppSettings _settings;
    private readonly WallpaperStore _store;
    private readonly SemaphoreSlim _dialogGate = new(1, 1);
    private readonly DispatcherQueueTimer _previewTimer;
    private AutomationService? _automation;
    private PointerButton? _pressedButton;
    private (double X, double Y) _lastPointer;
    private bool _populatingLayouts;
    private bool _quitting;
    private Brush? _selectionBrush;

    /// <summary>Couleur d'alerte de la version Python (<c>warning</c>).</summary>
    private static readonly SolidColorBrush WarningBrush = new(Windows.UI.Color.FromArgb(255, 0xff, 0xc4, 0x6e));

    public MainWindow()
    {
        _settings = AppSettings.Load();
        _store = new WallpaperStore();
        ViewModel = new MainViewModel(this, _settings, _store);
        InitializeComponent();

        SetupWindowChrome();
        BuildLanguageMenu();

        _previewTimer = DispatcherQueue.CreateTimer();
        _previewTimer.Interval = TimeSpan.FromMilliseconds(60); // aperçu limité pendant un glisser, comme en Python
        _previewTimer.IsRepeating = false;
        _previewTimer.Tick += (_, _) => PreviewCanvas.Invalidate();

        ViewModel.RedrawRequested += OnRedrawRequested;
        ViewModel.TextsChanged += (_, _) => ApplyTexts();
        ViewModel.PropertyChanged += OnViewModelPropertyChanged;
        ViewModel.LibraryItems.CollectionChanged += (_, _) => UpdateLibraryEmpty();
        ViewModel.Controller.ModeChanged += (_, _) => UpdateToggles();

        RootGrid.KeyboardAccelerators.Add(EditAccelerator(VirtualKey.Z));
        RootGrid.KeyboardAccelerators.Add(EditAccelerator(VirtualKey.Y));

        ViewModel.Initialize();
        UpdateToggles();
        UpdateCursor();

        AppWindow.Closing += OnAppWindowClosing;
        Closed += (_, _) => _automation?.Dispose();
    }

    public MainViewModel ViewModel { get; }

    // --- Fenêtre ---

    private void SetupWindowChrome()
    {
        ExtendsContentIntoTitleBar = true;
        SetTitleBar(TitleBarDrag);
        var bar = AppWindow.TitleBar;
        bar.PreferredHeightOption = TitleBarHeightOption.Tall;
        // Boutons de titre aux couleurs du thème sombre
        bar.ButtonBackgroundColor = Colors.Transparent;
        bar.ButtonInactiveBackgroundColor = Colors.Transparent;
        bar.ButtonForegroundColor = Colors.White;
        bar.ButtonInactiveForegroundColor = Windows.UI.Color.FromArgb(255, 0x9a, 0xa9, 0xbf);
        bar.ButtonHoverBackgroundColor = Windows.UI.Color.FromArgb(0x1a, 255, 255, 255);
        bar.ButtonHoverForegroundColor = Colors.White;
        bar.ButtonPressedBackgroundColor = Windows.UI.Color.FromArgb(0x33, 255, 255, 255);
        bar.ButtonPressedForegroundColor = Colors.White;

        string icon = Path.Combine(AppContext.BaseDirectory, "Assets", "WallCraft.ico");
        if (File.Exists(icon))
        {
            AppWindow.SetIcon(icon);
            TitleIcon.Source = new BitmapImage(new Uri(icon));
        }

        // Démarrage centré, 80 % de la zone de travail de l'écran (_center_window)
        double scale = GetDpiForWindow(WinRT.Interop.WindowNative.GetWindowHandle(this)) / 96.0;
        if (scale <= 0) scale = 1;
        var area = DisplayArea.GetFromWindowId(AppWindow.Id, DisplayAreaFallback.Primary).WorkArea;
        int w = Math.Max((int)(MinWidth * scale), (int)(area.Width * 0.8));
        int h = Math.Max((int)(MinHeight * scale), (int)(area.Height * 0.8));
        w = Math.Min(w, area.Width);
        h = Math.Min(h, area.Height);
        AppWindow.MoveAndResize(new Windows.Graphics.RectInt32(area.X + (area.Width - w) / 2, area.Y + (area.Height - h) / 2, w, h));
        if (AppWindow.Presenter is OverlappedPresenter presenter)
        {
            presenter.PreferredMinimumWidth = (int)(MinWidth * scale);
            presenter.PreferredMinimumHeight = (int)(MinHeight * scale);
        }
    }

    [DllImport("user32.dll")]
    private static extern uint GetDpiForWindow(nint hwnd);

    /// <summary>Fond automatique et icône de notification ; renvoie vrai si la fenêtre doit être affichée (pas <c>--tray</c>).</summary>
    public bool StartAutomation(bool startHidden)
    {
        _automation = new AutomationService(this, _settings, _store);
        _automation.BusyChanged += (_, _) => ViewModel.AutomationBusy = _automation.IsBusy;
        return _automation.Start(startHidden);
    }

    private void OnAppWindowClosing(AppWindow sender, AppWindowClosingEventArgs args)
    {
        if (_quitting) return;
        WindowTray.HideInsteadOfClosing(this, args, _automation?.IsTrayActive == true);
    }

    private void OnQuitClick(object sender, RoutedEventArgs e) => Quit();

    private void OnKofiClick(object sender, RoutedEventArgs e)
    {
        try
        {
            Process.Start(new ProcessStartInfo(MainViewModel.KofiUrl) { UseShellExecute = true });
        }
        catch (Exception ex) when (ex is Win32Exception or InvalidOperationException)
        {
            ViewModel.StatusText = ex.Message;
        }
    }

    // --- Textes (langue changeable à chaud) ---

    private void BuildLanguageMenu()
    {
        foreach (var lang in Localizer.Languages)
        {
            var item = new RadioMenuFlyoutItem { Text = lang.Name, GroupName = "language", Tag = lang.Code };
            item.Click += (_, _) => ViewModel.SetLanguage(lang.Code);
            LanguageMenu.Items.Add(item);
        }
    }

    /// <summary>Relit tous les textes fixes de la fenêtre dans la langue active (<c>_refresh_texts</c>).</summary>
    private void ApplyTexts()
    {
        string name = _loc["AppDisplayName"];
        Title = name;
        TitleText.Text = name;

        FileMenu.Title = _loc["menu_file"];
        ImageMenu.Title = _loc["menu_image"];
        ScreensMenu.Title = _loc["menu_screens"];
        LanguageMenu.Title = _loc["menu_language"];
        foreach (var item in LanguageMenu.Items.OfType<RadioMenuFlyoutItem>()) item.IsChecked = (string)item.Tag == _loc.Language;

        NewProjectItem.Text = _loc["btn_new_project"];
        OpenProjectItem.Text = _loc["menu_open"];
        SaveProjectItem.Text = _loc["menu_save"];
        AddImagesItem.Text = _loc["btn_add_images"].TrimStart('+', ' ');
        ExportItem.Text = _loc["menu_export"];
        SplitItem.Text = _loc["menu_split"];
        ApplyItem.Text = _loc["btn_apply"];
        QuitItem.Text = _loc["menu_quit"];
        RotateItem.Text = _loc["btn_rotate"];
        AdjustItem.Text = _loc["btn_adjust"];
        BringForwardItem.Text = _loc["btn_layer_front"];
        SendBackwardItem.Text = _loc["btn_layer_back"];
        RemoveItem.Text = _loc["btn_remove"];
        PhysicalItem.Text = _loc["menu_physical"];
        PrefsItem.Text = _loc["menu_prefs"];
        RedetectItem.Text = _loc["menu_reload_screens"];

        AddImagesText.Text = _loc["btn_add_images"].TrimStart('+', ' ');
        LayoutLabel.Text = _loc["lbl_layout"];
        AutoArrangeText.Text = _loc["btn_auto_arrange"];
        VariantsText.Text = _loc["btn_variants"];
        FitLabel.Text = _loc["lbl_fit"];
        FitButton.Content = _loc["fill_fit"];
        FillButton.Content = _loc["fill_fill"];
        ApplyText.Text = _loc["btn_apply"];

        LibraryTitle.Text = _loc["library_title"];
        LibraryEmptyText.Text = _loc["library_empty"];
        SendBackwardText.Text = _loc["btn_layer_back"];
        BringForwardText.Text = _loc["btn_layer_front"];
        RotateText.Text = _loc["btn_rotate"];
        AdjustText.Text = _loc["btn_adjust"];
        RemoveText.Text = _loc["btn_remove"];

        ComposeTab.Text = _loc["view_compose"];
        PreviewTab.Text = _loc["view_preview"];
        MoveToolText.Text = _loc["mode_move"];
        ScaleToolText.Text = _loc["mode_scale"];
        CropToolText.Text = _loc["mode_crop"];
        PreviewHintText.Text = _loc["preview_hint"];
        ShowMonitorsCheck.Content = _loc["chk_show_monitors"];
        KofiLink.Content = _loc["btn_kofi"];

        _populatingLayouts = true;
        LayoutCombo.ItemsSource = ViewModel.LayoutNames;
        LayoutCombo.SelectedIndex = ViewModel.LayoutIndex;
        _populatingLayouts = false;
        UpdateLibraryEmpty();
    }

    private void UpdateLibraryEmpty()
        => LibraryEmptyText.Visibility = ViewModel.LibraryItems.Count == 0 ? Visibility.Visible : Visibility.Collapsed;

    private void OnViewModelPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        switch (e.PropertyName)
        {
            case nameof(MainViewModel.IsBusy):
                UpdateCursor();
                break;
            case nameof(MainViewModel.IsFill):
                UpdateToggles();
                break;
            case nameof(MainViewModel.LayoutIndex):
                if (LayoutCombo.SelectedIndex != ViewModel.LayoutIndex)
                {
                    _populatingLayouts = true;
                    LayoutCombo.SelectedIndex = ViewModel.LayoutIndex;
                    _populatingLayouts = false;
                }
                break;
            case nameof(MainViewModel.SelectedLibraryItem):
                if (!ReferenceEquals(LibraryList.SelectedItem, ViewModel.SelectedLibraryItem))
                    LibraryList.SelectedItem = ViewModel.SelectedLibraryItem;
                if (ViewModel.SelectedLibraryItem is { } item) LibraryList.ScrollIntoView(item);
                break;
            case nameof(MainViewModel.SelectionIsWarning):
                _selectionBrush ??= SelectionTextBlock.Foreground;
                SelectionTextBlock.Foreground = ViewModel.SelectionIsWarning ? WarningBrush : _selectionBrush;
                break;
        }
    }

    // --- Barre d'outils et zone de travail ---

    private void OnLayoutSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_populatingLayouts && LayoutCombo.SelectedIndex >= 0) ViewModel.LayoutIndex = LayoutCombo.SelectedIndex;
    }

    private void OnFitClick(object sender, RoutedEventArgs e)
    {
        ViewModel.SetFill(false);
        UpdateToggles();
    }

    private void OnFillClick(object sender, RoutedEventArgs e)
    {
        ViewModel.SetFill(true);
        UpdateToggles();
    }

    private void OnToolClick(object sender, RoutedEventArgs e)
    {
        ViewModel.Mode = ReferenceEquals(sender, ScaleToolButton) ? EditMode.Scale
                       : ReferenceEquals(sender, CropToolButton) ? EditMode.Crop : EditMode.Move;
        UpdateToggles();
    }

    /// <summary>Boutons à bascule exclusifs : cadrage et outil actifs.</summary>
    private void UpdateToggles()
    {
        FitButton.IsChecked = !ViewModel.IsFill;
        FillButton.IsChecked = ViewModel.IsFill;
        MoveToolButton.IsChecked = ViewModel.Mode == EditMode.Move;
        ScaleToolButton.IsChecked = ViewModel.Mode == EditMode.Scale;
        CropToolButton.IsChecked = ViewModel.Mode == EditMode.Crop;
    }

    private void OnShowMonitorsClick(object sender, RoutedEventArgs e) => ViewModel.ShowMonitors = ShowMonitorsCheck.IsChecked == true;

    private void OnViewSelectionChanged(SelectorBar sender, SelectorBarSelectionChangedEventArgs args)
    {
        bool preview = ReferenceEquals(ViewSelector.SelectedItem, PreviewTab);
        ViewModel.IsPreview = preview;
        CompositionCanvas.Visibility = preview ? Visibility.Collapsed : Visibility.Visible;
        PreviewCanvas.Visibility = preview ? Visibility.Visible : Visibility.Collapsed;
        ToolsPanel.Visibility = preview ? Visibility.Collapsed : Visibility.Visible;
        ShowMonitorsCheck.Visibility = preview ? Visibility.Collapsed : Visibility.Visible;
        PreviewHintText.Visibility = preview ? Visibility.Visible : Visibility.Collapsed;
        (preview ? PreviewCanvas : CompositionCanvas).Invalidate();
    }

    private void OnLibrarySelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (LibraryList.SelectedItem is LibraryItemViewModel item) ViewModel.SelectedLibraryItem = item;
    }

    private void OnRedrawRequested(object? sender, RedrawEventArgs e)
    {
        if (ViewModel.IsPreview)
        {
            if (!e.Live)
            {
                _previewTimer.Stop();
                PreviewCanvas.Invalidate();
            }
            else if (!_previewTimer.IsRunning)
            {
                _previewTimer.Start();
            }
        }
        else
        {
            CompositionCanvas.Invalidate();
        }
    }

    private void OnCreateResources(CanvasControl sender, CanvasCreateResourcesEventArgs args) => ViewModel.Images.ResetDevice();

    private void OnCompositionDraw(CanvasControl sender, CanvasDrawEventArgs args)
        => CompositionRenderer.Draw(args.DrawingSession, sender.ActualWidth, sender.ActualHeight, ViewModel);

    private void OnPreviewDraw(CanvasControl sender, CanvasDrawEventArgs args)
        => PreviewRenderer.Draw(args.DrawingSession, sender.ActualWidth, sender.ActualHeight, ViewModel);

    /// <summary>La zone change de taille : recadrage tant que l'utilisateur n'a pas zoomé (<c>_on_stage_resized</c>).</summary>
    private void OnCompositionSizeChanged(object sender, SizeChangedEventArgs e)
    {
        if (e.NewSize.Width < 1 || e.NewSize.Height < 1) return; // vue masquée : garder la dernière taille
        ViewModel.Controller.ViewportResized(e.NewSize.Width, e.NewSize.Height);
        CompositionCanvas.Invalidate();
    }

    private void OnPreviewSizeChanged(object sender, SizeChangedEventArgs e) => PreviewCanvas.Invalidate();

    // --- Souris et clavier sur la composition (relayés à EditController) ---

    private static EditModifiers Modifiers(VirtualKeyModifiers keys)
        => ((keys & VirtualKeyModifiers.Shift) != 0 ? EditModifiers.Shift : EditModifiers.None)
         | ((keys & VirtualKeyModifiers.Control) != 0 ? EditModifiers.Control : EditModifiers.None);

    private void OnStagePointerPressed(object sender, PointerRoutedEventArgs e)
    {
        var point = e.GetCurrentPoint(CompositionCanvas);
        e.Handled = true;
        if (_pressedButton is not null) return; // un deuxième bouton pendant un geste est ignoré
        var button = point.Properties.PointerUpdateKind switch
        {
            PointerUpdateKind.MiddleButtonPressed => PointerButton.Middle,
            PointerUpdateKind.RightButtonPressed => PointerButton.Right,
            _ => PointerButton.Left,
        };
        CompositionCanvas.Focus(FocusState.Pointer);
        CompositionCanvas.CapturePointer(e.Pointer);
        _pressedButton = button;
        _lastPointer = (point.Position.X, point.Position.Y);
        ViewModel.Controller.PointerPressed(point.Position.X, point.Position.Y, button, Modifiers(e.KeyModifiers));
        UpdateCursor();
    }

    private void OnStagePointerMoved(object sender, PointerRoutedEventArgs e)
    {
        if (_pressedButton is null) return;
        var point = e.GetCurrentPoint(CompositionCanvas);
        _lastPointer = (point.Position.X, point.Position.Y);
        ViewModel.Controller.PointerMoved(point.Position.X, point.Position.Y, Modifiers(e.KeyModifiers));
        e.Handled = true;
    }

    private void OnStagePointerReleased(object sender, PointerRoutedEventArgs e)
    {
        if (_pressedButton is not PointerButton pressed) return;
        var point = e.GetCurrentPoint(CompositionCanvas);
        var button = point.Properties.PointerUpdateKind switch
        {
            PointerUpdateKind.MiddleButtonReleased => PointerButton.Middle,
            PointerUpdateKind.RightButtonReleased => PointerButton.Right,
            PointerUpdateKind.LeftButtonReleased => PointerButton.Left,
            _ => pressed,
        };
        if (button != pressed) return;
        _pressedButton = null;
        ViewModel.Controller.PointerReleased(point.Position.X, point.Position.Y, button);
        CompositionCanvas.ReleasePointerCapture(e.Pointer);
        UpdateCursor();
        e.Handled = true;
    }

    /// <summary>Capture perdue (autre fenêtre, Alt+Tab…) : le geste est terminé et enregistré comme un relâchement.</summary>
    private void OnStagePointerCaptureLost(object sender, PointerRoutedEventArgs e)
    {
        if (_pressedButton is not PointerButton pressed) return;
        _pressedButton = null;
        ViewModel.Controller.PointerReleased(_lastPointer.X, _lastPointer.Y, pressed);
        UpdateCursor();
    }

    private void OnStagePointerWheelChanged(object sender, PointerRoutedEventArgs e)
    {
        var point = e.GetCurrentPoint(CompositionCanvas);
        ViewModel.Controller.Wheel(point.Position.X, point.Position.Y, point.Properties.MouseWheelDelta);
        e.Handled = true;
    }

    /// <summary>Curseur : occupé pendant un traitement, main pendant un déplacement de la vue, croix sinon.</summary>
    private void UpdateCursor()
    {
        if (ViewModel.IsBusy)
        {
            RootGrid.SetCursor(InputSystemCursorShape.Wait);
            StageHost.SetCursor(InputSystemCursorShape.Wait);
            return;
        }
        RootGrid.SetCursor(null);
        StageHost.SetCursor(ViewModel.Controller.CurrentAction == DragAction.Pan ? InputSystemCursorShape.SizeAll : InputSystemCursorShape.Cross);
    }

    private KeyboardAccelerator EditAccelerator(VirtualKey key)
    {
        var accelerator = new KeyboardAccelerator { Key = key, Modifiers = VirtualKeyModifiers.Control };
        accelerator.Invoked += (s, args) =>
        {
            args.Handled = true;
            if (DialogOpen()) return;
            ViewModel.HandleEditKey(key == VirtualKey.Z ? EditKey.Z : EditKey.Y, EditModifiers.Control);
        };
        return accelerator;
    }

    /// <summary>Raccourcis des menus : sans effet quand un dialogue est ouvert (l'image derrière ne doit pas changer).</summary>
    private void OnAcceleratorInvoked(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        if (DialogOpen() || FocusIsTextInput()) args.Handled = true;
    }

    /// <summary>Tous les dialogues passent par <see cref="RunDialogAsync"/> : le verrou pris = un dialogue ouvert.</summary>
    private bool DialogOpen() => _dialogGate.CurrentCount == 0;

    /// <summary>Suppr ne supprime pas d'image pendant une saisie (<c>_on_delete_key</c>).</summary>
    private bool FocusIsTextInput()
        => Content.XamlRoot is { } root && FocusManager.GetFocusedElement(root) is TextBox or PasswordBox or NumberBox or AutoSuggestBox or RichEditBox;

    // --- Glisser-déposer depuis l'Explorateur ---

    private void OnDragOver(object sender, DragEventArgs e)
    {
        if (e.DataView.Contains(StandardDataFormats.StorageItems)) e.AcceptedOperation = DataPackageOperation.Copy;
    }

    private async void OnDrop(object sender, DragEventArgs e)
    {
        if (!e.DataView.Contains(StandardDataFormats.StorageItems)) return;
        var deferral = e.GetDeferral();
        List<string> paths;
        try
        {
            var items = await e.DataView.GetStorageItemsAsync();
            paths = items.OfType<StorageFile>().Select(f => f.Path)
                .Where(p => Rotation.ImageExtensions.Contains(Path.GetExtension(p))).ToList();
        }
        finally
        {
            deferral.Complete();
        }
        await ViewModel.AddPathsAsync(paths);
    }

    // --- IMainWindowServices : messages ---

    private nint Hwnd => WinRT.Interop.WindowNative.GetWindowHandle(this);

    /// <summary>Un seul dialogue à la fois (WinUI refuse deux ContentDialog ouverts) ; sans fenêtre affichée, rien n'est montré.</summary>
    private async Task<T?> RunDialogAsync<T>(Func<XamlRoot, Task<T?>> show)
    {
        await _dialogGate.WaitAsync();
        try
        {
            if (Content.XamlRoot is not { } root || !AppWindow.IsVisible) return default;
            return await show(root);
        }
        finally
        {
            _dialogGate.Release();
        }
    }

    private Task<bool> ShowMessageAsync(string titleKey, string message, bool confirm) => RunDialogAsync(async root =>
    {
        var dialog = DialogHelpers.Create(root, titleKey);
        dialog.Content = new ScrollViewer
        {
            Content = new TextBlock { Text = message, TextWrapping = TextWrapping.Wrap, IsTextSelectionEnabled = true },
            MaxHeight = 420,
        };
        if (confirm)
        {
            dialog.PrimaryButtonText = _loc["btn_ok"];
            dialog.CloseButtonText = _loc["btn_cancel"];
        }
        else
        {
            dialog.CloseButtonText = _loc["btn_ok"];
            dialog.DefaultButton = ContentDialogButton.Close;
        }
        return await dialog.ShowAsync() == ContentDialogResult.Primary;
    });

    public Task ShowInfoAsync(string message) => ShowMessageAsync("info_title", message, confirm: false);

    public Task ShowErrorAsync(string message) => ShowMessageAsync("error_title", message, confirm: false);

    public Task<bool> ConfirmAsync(string message) => ShowMessageAsync("app_title", message, confirm: true);

    // --- IMainWindowServices : fichiers ---

    public async Task<IReadOnlyList<string>> PickImagesAsync()
    {
        var picker = new FileOpenPicker { ViewMode = PickerViewMode.Thumbnail, SuggestedStartLocation = PickerLocationId.PicturesLibrary };
        WinRT.Interop.InitializeWithWindow.Initialize(picker, Hwnd);
        foreach (var ext in Rotation.ImageExtensions) picker.FileTypeFilter.Add(ext);
        var files = await picker.PickMultipleFilesAsync();
        return files is null ? [] : files.Select(f => f.Path).ToList();
    }

    private async Task<string?> PickSaveAsync(string suggestedName, params (string Label, string[] Extensions)[] choices)
    {
        var picker = new FileSavePicker { SuggestedFileName = suggestedName };
        WinRT.Interop.InitializeWithWindow.Initialize(picker, Hwnd);
        foreach (var (label, extensions) in choices) picker.FileTypeChoices.Add(label, extensions.ToList());
        var file = await picker.PickSaveFileAsync();
        return file?.Path;
    }

    public Task<string?> PickExportFileAsync()
        => PickSaveAsync("wallcraft", (_loc["filetype_png"], new[] { ".png" }), (_loc["filetype_jpeg"], new[] { ".jpg", ".jpeg" }));

    public Task<string?> PickProjectToSaveAsync() => PickSaveAsync("projet.wallcraft", (_loc["filetype_project"], new[] { ".json" }));

    public async Task<string?> PickProjectToOpenAsync()
    {
        var picker = new FileOpenPicker();
        WinRT.Interop.InitializeWithWindow.Initialize(picker, Hwnd);
        picker.FileTypeFilter.Add(".json");
        var file = await picker.PickSingleFileAsync();
        return file?.Path;
    }

    public async Task<string?> PickFolderAsync()
    {
        var picker = new FolderPicker();
        WinRT.Interop.InitializeWithWindow.Initialize(picker, Hwnd);
        picker.FileTypeFilter.Add("*");
        var folder = await picker.PickSingleFolderAsync();
        return folder?.Path;
    }

    // --- IMainWindowServices : dialogues ---

    public async Task<int?> ChooseVariantAsync(IReadOnlyList<IReadOnlyList<Placement>> variants)
    {
        double aspect = ViewModel.Document.Width / Math.Max(1, ViewModel.Document.Height);
        return await RunDialogAsync<int?>(root => VariantsDialog.ShowAsync(root, variants,
            p => VariantThumbnail.RenderAsync(ViewModel, p, VariantsDialog.ThumbnailWidth), aspect));
    }

    public Task<PhysicalSettings?> EditPhysicalSizeAsync(IReadOnlyList<MonitorInfo> monitors, PhysicalSettings current)
        => RunDialogAsync(root => PhysicalSizeDialog.ShowAsync(root, monitors, current));

    public Task<AdjustValues?> AdjustAsync(AdjustValues initial, Action<double, double, double, double> preview)
        => RunDialogAsync(root => AdjustDialog.ShowAsync(root, initial, preview));

    private async void OnAutomationPrefsClick(object sender, RoutedEventArgs e)
    {
        if (_automation is not { } automation) return;
        var prefs = await RunDialogAsync(root => AutomationDialog.ShowAsync(root, this, automation.CurrentPrefs(), ViewModel.Monitors.Count));
        if (prefs is not null) automation.ApplyPrefs(prefs);
    }

    // --- IAutomationHost ---

    IReadOnlyList<MonitorInfo> IAutomationHost.Monitors => ViewModel.Monitors;
    PhysicalSettings IAutomationHost.Physical => ViewModel.Physical;
    string IAutomationHost.LayoutMode => ViewModel.LayoutMode;
    bool IAutomationHost.Fill => ViewModel.IsFill;
    Windows.UI.Color IAutomationHost.BackgroundColor => ViewModel.BackgroundColor;
    bool IAutomationHost.IsBusy => ViewModel.IsBusy;
    bool IAutomationHost.HasImages => ViewModel.Document.Images.Count > 0;

    void IAutomationHost.ApplyComposition()
    {
        if (ViewModel.ApplyWallpaperCommand.CanExecute(null)) ViewModel.ApplyWallpaperCommand.Execute(null);
    }

    void IAutomationHost.OnMonitorsChanged(IReadOnlyList<MonitorInfo> detected) => ViewModel.RefreshMonitors(force: true, detected);

    void IAutomationHost.ShowStatus(string message) => ViewModel.StatusText = message;

    void IAutomationHost.ShowWarning(string message)
    {
        if (AppWindow.IsVisible) _ = ShowInfoAsync(message);
        else ViewModel.StatusText = message;
    }

    public void ShowMainWindow() => WindowTray.ShowMainWindow(this);

    /// <summary>Quitte vraiment (menu Quitter ou icône de notification) : l'icône est retirée avant la fin.</summary>
    public void Quit()
    {
        _quitting = true;
        _automation?.Dispose();
        _automation = null;
        Application.Current.Exit();
    }
}
