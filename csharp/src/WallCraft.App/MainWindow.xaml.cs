using Microsoft.UI.Xaml;
using Microsoft.Windows.ApplicationModel.Resources;

namespace WallCraft.App;

public sealed partial class MainWindow : Window
{
    private const string FallbackName = "WallCraft Pro";

    public MainWindow()
    {
        InitializeComponent();

        ExtendsContentIntoTitleBar = true;
        SetTitleBar(TitleBar);

        var name = LoadDisplayName();
        Title = name;
        TitleText.Text = name;
        DisplayNameText.Text = name;
    }

    /// <summary>Lit la clé AppDisplayName ; repli sur « WallCraft Pro » si les ressources sont absentes.</summary>
    private static string LoadDisplayName()
    {
        try
        {
            var value = new ResourceLoader().GetString("AppDisplayName");
            return string.IsNullOrWhiteSpace(value) ? FallbackName : value;
        }
        catch (Exception)
        {
            return FallbackName;
        }
    }
}
