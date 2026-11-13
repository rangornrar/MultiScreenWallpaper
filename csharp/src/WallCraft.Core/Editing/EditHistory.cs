using WallCraft.Core.Model;

namespace WallCraft.Core.Editing;

/// <summary>
/// Historique annuler/rétablir par instantanés (portage de <c>_save_state</c>, <c>cmd_undo</c>, <c>cmd_redo</c> de ui.py).
/// Chaque état est une copie complète des images (position, taille, rotation, ordre, rognage, retouches) ;
/// la sélection, l'outil et la vue n'en font pas partie.
/// </summary>
public sealed class EditHistory
{
    /// <summary>Nombre maximal d'états gardés (le plus ancien est oublié au-delà), comme en Python.</summary>
    public const int MaxDepth = 20;

    private readonly List<(string Label, List<CompositionImage> Images)> _states = [];

    /// <summary>Nombre d'états enregistrés (<c>len(self.history)</c>).</summary>
    public int Count => _states.Count;

    /// <summary>Position de l'état courant (<c>self.history_idx</c>) ; -1 si l'historique est vide.</summary>
    public int Index { get; private set; } = -1;

    public bool CanUndo => Index > 0;
    public bool CanRedo => Index < _states.Count - 1;

    /// <summary>Nom de l'action qui a produit l'état courant (« Move », « Rotate »…), pour un libellé « Annuler … ».</summary>
    public string? CurrentLabel => Index >= 0 && Index < _states.Count ? _states[Index].Label : null;

    /// <summary>Nom de l'action que « Rétablir » referait.</summary>
    public string? RedoLabel => CanRedo ? _states[Index + 1].Label : null;

    /// <summary>
    /// Enregistre un nouvel état. Après une annulation, les états « rétablissables » sont abandonnés ;
    /// au-delà de <see cref="MaxDepth"/> états, le plus ancien est retiré.
    /// </summary>
    internal void Save(string label, IEnumerable<CompositionImage> images)
    {
        if (Index < _states.Count - 1) _states.RemoveRange(Index + 1, _states.Count - Index - 1);
        _states.Add((label, images.Select(i => i.Clone()).ToList()));
        Index++;
        if (_states.Count > MaxDepth)
        {
            _states.RemoveAt(0);
            Index--;
        }
    }

    /// <summary>Recule d'un état et renvoie une copie de ses images, ou null s'il n'y a rien à annuler.</summary>
    internal List<CompositionImage>? Undo()
    {
        if (!CanUndo) return null;
        Index--;
        return Current();
    }

    /// <summary>Avance d'un état et renvoie une copie de ses images, ou null s'il n'y a rien à rétablir.</summary>
    internal List<CompositionImage>? Redo()
    {
        if (!CanRedo) return null;
        Index++;
        return Current();
    }

    internal void Clear()
    {
        _states.Clear();
        Index = -1;
    }

    // Copie : les images restaurées seront modifiées, l'état enregistré doit rester intact.
    private List<CompositionImage> Current() => _states[Index].Images.Select(i => i.Clone()).ToList();
}
