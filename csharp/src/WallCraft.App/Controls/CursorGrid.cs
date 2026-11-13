using Microsoft.UI.Input;
using Microsoft.UI.Xaml.Controls;

namespace WallCraft.App.Controls;

/// <summary>Grille dont on peut changer le curseur (<c>ProtectedCursor</c> n'est accessible qu'aux classes dérivées).</summary>
public sealed partial class CursorGrid : Grid
{
    private InputSystemCursorShape? _shape;

    /// <summary>Curseur au-dessus de la grille et de ses enfants (null : curseur par défaut).</summary>
    public void SetCursor(InputSystemCursorShape? shape)
    {
        if (_shape == shape) return;
        _shape = shape;
        ProtectedCursor = shape is { } s ? InputSystemCursor.Create(s) : null;
    }
}
