using Windows.ApplicationModel;

namespace WallCraft.App.Services;

/// <summary>
/// Lancement au démarrage dans la version Microsoft Store : tâche de démarrage déclarée dans le manifeste du paquet
/// (la clé HKCU\…\Run est redirigée dans un paquet et ne servirait à rien). L'utilisateur la retrouve aussi dans
/// Paramètres > Applications > Démarrage ; s'il l'y a désactivée, lui seul peut la réactiver.
/// </summary>
public static class StoreStartup
{
    public const string TaskId = "WallCraftStartup"; // identique au TaskId de Package.appxmanifest

    public static bool IsPackaged => !string.IsNullOrEmpty(Core.Services.AppPaths.PackageFamilyName);

    private static StartupTask Task() => StartupTask.GetAsync(TaskId).AsTask().GetAwaiter().GetResult();

    public static bool IsEnabled()
    {
        try { return Task().State is StartupTaskState.Enabled or StartupTaskState.EnabledByPolicy; }
        catch (Exception) { return false; }
    }

    /// <summary>Active ou désactive la tâche ; false si Windows l'a refusé (désactivée par l'utilisateur ou une stratégie).</summary>
    public static bool Set(bool enabled)
    {
        var task = Task();
        if (!enabled)
        {
            task.Disable();
            return true;
        }
        var state = task.RequestEnableAsync().AsTask().GetAwaiter().GetResult();
        if (state is StartupTaskState.Enabled or StartupTaskState.EnabledByPolicy) return true;
        if (state == StartupTaskState.DisabledByUser)
            _ = Windows.System.Launcher.LaunchUriAsync(new Uri("ms-settings:startupapps"));
        return false;
    }

    /// <summary>True si Windows a lancé WallCraft par la tâche de démarrage (ouverture dans la zone de notification).</summary>
    public static bool LaunchedAtStartup()
    {
        if (!IsPackaged) return false;
        try
        {
            var args = Microsoft.Windows.AppLifecycle.AppInstance.GetCurrent().GetActivatedEventArgs();
            return args.Kind == Microsoft.Windows.AppLifecycle.ExtendedActivationKind.StartupTask;
        }
        catch (Exception) { return false; }
    }
}
