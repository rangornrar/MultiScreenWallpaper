using Microsoft.UI.Xaml;

namespace WallCraft.App;

public partial class App : Application
{
    private Window? _window;

    public App()
    {
        InitializeComponent();
    }

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
        _window = new MainWindow();
        _window.Activate();
    }
}
