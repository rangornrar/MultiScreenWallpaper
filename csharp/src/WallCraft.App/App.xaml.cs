using Microsoft.UI.Xaml;

namespace WallCraft.App;

public partial class App : Application
{
    private MainWindow? _window;

    public App()
    {
        InitializeComponent();
    }

    /// <summary>
    /// <c>--diagnostic</c> : vérification de la couche Windows sans interface. <c>--selftest fichier</c> : vérification du
    /// paquet MSIX installé (CI). <c>--tray</c> (démarrage avec Windows) : la fenêtre reste cachée tant que l'icône de
    /// notification est active.
    /// </summary>
    protected override async void OnLaunched(LaunchActivatedEventArgs args)
    {
        // Version Microsoft Store : données dans le dossier réel du paquet (voir AppPaths).
        Core.Services.AppPaths.PackageFamilyName = Platform.Windows.PackageInfo.FamilyName();
        var commandLine = Environment.GetCommandLineArgs().Skip(1).ToArray();
        if (commandLine.Contains("--selftest"))
        {
            int selftest = await Services.StoreSelfTest.RunAsync(commandLine.SkipWhile(a => a != "--selftest").Skip(1).FirstOrDefault());
            Exit();
            Environment.Exit(selftest);
            return;
        }
        if (commandLine.Contains("--diagnostic"))
        {
            int code = await Services.Diagnostic.RunAsync(commandLine.Where(a => a != "--diagnostic").ToArray());
            Exit();
            Environment.Exit(code);
            return;
        }
        // Démarrage avec Windows : --tray (clé Run de l'exe GitHub) ou tâche de démarrage du paquet (version Store).
        bool startHidden = commandLine.Contains("--tray") || Services.StoreStartup.LaunchedAtStartup();
        _window = new MainWindow();
        if (_window.StartAutomation(startHidden)) _window.Activate();
    }
}
