using System.Text.Json.Nodes;
using WallCraft.Core.Layout;
using WallCraft.Core.Model;

namespace WallCraft.Core.Editing;

/// <summary>Pourquoi la composition a changé : l'interface choisit quoi redessiner.</summary>
public enum ChangeReason
{
    /// <summary>Nouveau projet (composition vidée).</summary>
    Reset,
    /// <summary>Projet ouvert.</summary>
    Opened,
    Added,
    Removed,
    /// <summary>Ordre des calques modifié.</summary>
    Layer,
    Rotated,
    /// <summary>Image déplacée, redimensionnée ou rognée à la souris.</summary>
    Edited,
    /// <summary>Retouches (luminosité, contraste…) validées.</summary>
    Adjusted,
    /// <summary>Disposition automatique ou variante appliquée.</summary>
    Layout,
    /// <summary>Taille de la composition changée (écrans branchés, taille réelle…).</summary>
    Geometry,
    /// <summary>Seule la sélection a changé.</summary>
    Selection,
    Undo,
    Redo,
}

/// <summary>Changement de la composition. <see cref="Live"/> : glisser en cours (l'aperçu peut limiter sa fréquence de rafraîchissement).</summary>
public sealed class CompositionChangedEventArgs(ChangeReason reason, bool live = false) : EventArgs
{
    public ChangeReason Reason { get; } = reason;
    public bool Live { get; } = live;
}

/// <summary>
/// La composition en cours d'édition : images ordonnées (la dernière est au-dessus), sélection, taille,
/// métadonnées du projet et historique. Portage des commandes d'édition de ui.py, sans interface :
/// chaque modification lève <see cref="Changed"/> pour que la fenêtre se redessine.
/// </summary>
public sealed class CompositionDocument
{
    private List<CompositionImage> _images = [];

    public CompositionDocument(double width = 1920, double height = 1080)
    {
        Width = width;
        Height = height;
        History.Save("Init", _images);
    }

    /// <summary>Images dans l'ordre des calques (ZIndex = position dans la liste après chaque commande).</summary>
    public IReadOnlyList<CompositionImage> Images => _images;

    /// <summary>Index de l'image sélectionnée (<c>active_idx</c>), ou null.</summary>
    public int? SelectedIndex { get; private set; }

    public CompositionImage? Selected => SelectedIndex is int i && i >= 0 && i < _images.Count ? _images[i] : null;

    /// <summary>Taille de la composition (<c>target_w</c>, <c>target_h</c>).</summary>
    public double Width { get; private set; }
    public double Height { get; private set; }

    /// <summary>Métadonnées libres du projet (disposition, Ajuster/Remplir, taille réelle, écrans…).</summary>
    public JsonObject Meta { get; set; } = [];

    public EditHistory History { get; } = new();

    public event EventHandler<CompositionChangedEventArgs>? Changed;

    public bool CanUndo => History.CanUndo;
    public bool CanRedo => History.CanRedo;
    public bool CanSendBackward => Selected is not null && SelectedIndex > 0;
    public bool CanBringForward => Selected is not null && SelectedIndex < _images.Count - 1;

    // --- Projet ---

    /// <summary>Nouveau projet (<c>cmd_new_project</c>) : plus d'images, plus de sélection, historique repart de zéro.</summary>
    public void Reset()
    {
        _images = [];
        SelectedIndex = null;
        Meta = [];
        History.Clear();
        History.Save("Init", _images);
        Raise(ChangeReason.Reset);
    }

    /// <summary>Projet ouvert (<c>cmd_open_project</c>) : les calques suivent l'ordre chargé, l'historique repart de zéro.</summary>
    public void Load(IEnumerable<CompositionImage> images, JsonObject? meta = null)
    {
        _images = [.. images];
        SyncZIndices();
        SelectedIndex = null;
        if (meta is not null) Meta = meta;
        History.Clear();
        History.Save("Open", _images);
        Raise(ChangeReason.Opened);
    }

    // --- Sélection ---

    /// <summary>Sélectionne une image (<c>_select_image</c>) ; un index hors limites est ignoré. Renvoie vrai si l'index était valide.</summary>
    public bool Select(int index)
    {
        if (index < 0 || index >= _images.Count) return false;
        SelectedIndex = index;
        Raise(ChangeReason.Selection);
        return true;
    }

    /// <summary>Retire la sélection.</summary>
    public void ClearSelection()
    {
        if (SelectedIndex is null) return;
        SelectedIndex = null;
        Raise(ChangeReason.Selection);
    }

    /// <summary>Changement de sélection depuis le contrôleur (clic) : null autorisé, pas d'événement si rien ne change.</summary>
    internal bool SetSelection(int? index)
    {
        if (SelectedIndex == index) return false;
        SelectedIndex = index;
        return true;
    }

    // --- Commandes ---

    /// <summary>
    /// Ajoute des images (<c>cmd_add_images</c>) : 600 unités de large, centrées sur (<paramref name="centerX"/>, <paramref name="centerY"/>)
    /// — le centre de la vue en coordonnées de composition — et décalées de (40, 26) l'une après l'autre ; la dernière est sélectionnée.
    /// </summary>
    public void AddImages(IEnumerable<CompositionImage> images, double centerX, double centerY)
    {
        var added = images.ToList();
        if (added.Count == 0) return;
        for (int i = 0; i < added.Count; i++)
        {
            var m = added[i];
            m.W = 600;
            m.H = Math.Truncate(600 / m.CurrentAspect);
            m.X = centerX - (m.W.Value * 0.5) + (40 * i);
            m.Y = centerY - (m.H.Value * 0.5) + (26 * i);
            m.ZIndex = _images.Count + i;
        }
        _images.AddRange(added);
        SelectedIndex = _images.Count - 1;
        Commit("Add", ChangeReason.Added);
    }

    /// <summary>Supprime l'image sélectionnée (<c>cmd_remove_img</c>).</summary>
    public bool RemoveSelected()
    {
        if (SelectedIndex is not int idx || idx < 0 || idx >= _images.Count) return false;
        _images.RemoveAt(idx);
        SyncZIndices();
        SelectedIndex = null;
        Commit("Del", ChangeReason.Removed);
        return true;
    }

    /// <summary>Envoie l'image sélectionnée un calque en dessous (<c>cmd_layer_backward</c>) : échange avec sa voisine, la sélection suit.</summary>
    public bool SendBackward()
    {
        if (SelectedIndex is not int idx || idx <= 0 || idx >= _images.Count) return false;
        (_images[idx - 1], _images[idx]) = (_images[idx], _images[idx - 1]);
        SelectedIndex = idx - 1;
        SyncZIndices();
        Commit("LayerBack", ChangeReason.Layer);
        return true;
    }

    /// <summary>Met l'image sélectionnée un calque au-dessus (<c>cmd_layer_forward</c>).</summary>
    public bool BringForward()
    {
        if (SelectedIndex is not int idx || idx < 0 || idx >= _images.Count - 1) return false;
        (_images[idx + 1], _images[idx]) = (_images[idx], _images[idx + 1]);
        SelectedIndex = idx + 1;
        SyncZIndices();
        Commit("LayerFront", ChangeReason.Layer);
        return true;
    }

    /// <summary>
    /// Quart de tour horaire de l'image sélectionnée (<c>cmd_rotate</c>) : le rognage est annulé (il était défini dans
    /// l'ancienne orientation), la surface est conservée au nouveau ratio et l'image reste centrée au même point.
    /// </summary>
    public bool RotateSelected()
    {
        var img = Selected;
        if (img is null) return false;
        double w = img.W ?? 0, h = img.H ?? 0;
        double cx = img.X + w / 2, cy = img.Y + h / 2;
        double area = Math.Max(1, w * h);
        img.Crop = CropBox.Full;
        img.RotateClockwise();
        double ratio = img.VisibleAspect;
        img.W = Math.Max(1, PythonCompat.RoundToInt(Math.Pow(area * ratio, 0.5)));
        img.H = Math.Max(1, PythonCompat.RoundToInt(img.W.Value / ratio));
        img.X = cx - img.W.Value / 2;
        img.Y = cy - img.H.Value / 2;
        Commit("Rotate", ChangeReason.Rotated);
        return true;
    }

    /// <summary>
    /// Disposition automatique (<c>cmd_autofill</c> / <c>_apply_auto_layout</c>). En mosaïque avec au plus une image par écran,
    /// chaque image va sur son écran (<paramref name="screenRects"/> = rectangles des écrans dans la composition).
    /// L'état est enregistré APRÈS la mise en page : Annuler revient à l'état précédent.
    /// </summary>
    public void ApplyLayout(LayoutEngine engine, string mode, bool fill,
                            IReadOnlyList<(double X, double Y, double W, double H)>? screenRects = null, int variant = 0)
    {
        if (_images.Count == 0) return;
        if (mode == LayoutModes.Mosaic && screenRects is { Count: > 0 } && _images.Count <= screenRects.Count)
        {
            var rects = screenRects.OrderBy(r => r.X).ThenBy(r => r.Y).ToList(); // tri stable, comme sorted()
            engine.PlaceOnScreens(_images, rects, fill);
        }
        else
        {
            engine.Apply(mode, Width, Height, _images, fill, variant);
        }
        SyncZIndices();
        Commit("Auto", ChangeReason.Layout);
    }

    /// <summary>Applique une variante calculée par <see cref="LayoutEngine.Variants"/> (<c>_apply_variant</c>).</summary>
    public void ApplyPlacement(IReadOnlyList<Placement> placement)
    {
        LayoutEngine.ApplyPlacement(_images, placement);
        SyncZIndices();
        Commit("Variant", ChangeReason.Layout);
    }

    /// <summary>
    /// Nouvelle taille de composition (<c>_relayout_after_geometry_change</c>) : chaque image garde la même place relative
    /// (centre mis à l'échelle sur chaque axe) et sa taille est multipliée par le plus petit des deux facteurs, tronquée.
    /// </summary>
    public void SetSize(double width, double height)
    {
        double ow = Width, oh = Height;
        Width = width;
        Height = height;
        if ((ow == width && oh == height) || _images.Count == 0)
        {
            if (ow != width || oh != height) Raise(ChangeReason.Geometry);
            return;
        }
        double fx = width / ow, fy = height / oh;
        double f = Math.Min(fx, fy);
        foreach (var img in _images)
        {
            double w = img.W ?? 0, h = img.H ?? 0;
            double cx = (img.X + w / 2) * fx, cy = (img.Y + h / 2) * fy;
            img.W = Math.Max(1, Math.Truncate(w * f));
            img.H = Math.Max(1, Math.Truncate(h * f));
            img.X = cx - img.W.Value / 2;
            img.Y = cy - img.H.Value / 2;
        }
        Commit("Geometry", ChangeReason.Geometry);
    }

    /// <summary>
    /// Enregistre l'état après une modification faite directement sur les images (retouches validées : <c>AdjustDialog.close</c>
    /// appelle <c>_save_state("Adjust")</c>), puis prévient l'interface.
    /// </summary>
    public void Commit(string label, ChangeReason reason)
    {
        History.Save(label, _images);
        Raise(reason);
    }

    // --- Annuler / rétablir ---

    /// <summary>Annule (<c>cmd_undo</c>) : les images de l'état précédent sont recopiées et la sélection est retirée.</summary>
    public bool Undo()
    {
        var images = History.Undo();
        if (images is null) return false;
        Restore(images, ChangeReason.Undo);
        return true;
    }

    /// <summary>Rétablit (<c>cmd_redo</c>).</summary>
    public bool Redo()
    {
        var images = History.Redo();
        if (images is null) return false;
        Restore(images, ChangeReason.Redo);
        return true;
    }

    private void Restore(List<CompositionImage> images, ChangeReason reason)
    {
        _images = images;
        SelectedIndex = null;
        Raise(reason);
    }

    /// <summary>Les ZIndex suivent l'ordre de la liste (<c>_sync_z_indices</c>).</summary>
    private void SyncZIndices()
    {
        for (int i = 0; i < _images.Count; i++) _images[i].ZIndex = i;
    }

    internal void Raise(ChangeReason reason, bool live = false) => Changed?.Invoke(this, new CompositionChangedEventArgs(reason, live));
}
