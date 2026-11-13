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
    /// <c>--diagnostic</c> : vérification de la couche Windows sans interface. <c>--tray</c> (démarrage avec Windows) :
    /// la fenêtre reste cachée tant que l'icône de notification est active.
    /// </summary>
    protected override async void OnLaunched(LaunchActivatedEventArgs args)
    {
        var commandLine = Environment.GetCommandLineArgs().Skip(1).ToArray();
        if (commandLine.Contains("--diagnostic"))
        {
            int code = await Services.Diagnostic.RunAsync(commandLine.Where(a => a != "--diagnostic").ToArray());
            Exit();
            Environment.Exit(code);
            return;
        }
        bool startHidden = commandLine.Contains("--tray");
        _window = new MainWindow();
        if (_window.StartAutomation(startHidden)) _window.Activate();
    }
}
