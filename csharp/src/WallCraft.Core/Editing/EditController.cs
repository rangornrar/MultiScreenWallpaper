using WallCraft.Core.Layout;
using WallCraft.Core.Model;

namespace WallCraft.Core.Editing;

/// <summary>Outil actif de la zone de composition.</summary>
public enum EditMode
{
    /// <summary>Déplacer : glisser une image la déplace (avec aimantation).</summary>
    Move,
    /// <summary>Redimensionner : les poignées changent la taille en gardant les proportions.</summary>
    Scale,
    /// <summary>Rogner : les poignées réduisent ou élargissent la partie visible de l'image.</summary>
    Crop,
}

public enum PointerButton { Left, Middle, Right }

[Flags]
public enum EditModifiers
{
    None = 0,
    /// <summary>Maj maintenue : pas d'aimantation pendant le déplacement.</summary>
    Shift = 1,
    Control = 4,
}

/// <summary>Coin d'une image où se trouve une poignée (même ordre de test qu'en Python : tl, tr, br, bl).</summary>
public enum HandleCorner { TopLeft, TopRight, BottomRight, BottomLeft }

/// <summary>Geste en cours.</summary>
public enum DragAction { None, Pan, Move, Scale, Crop }

/// <summary>Touches reconnues par <see cref="EditController.KeyDown"/>.</summary>
public enum EditKey { Z, Y, R, Delete }

/// <summary>Poignée à dessiner : centre en pixels de la zone d'affichage.</summary>
public readonly record struct HandleInfo(HandleCorner Corner, double X, double Y);

/// <summary>Rectangle en pixels de la zone d'affichage.</summary>
public readonly record struct ScreenRect(double X, double Y, double Width, double Height);

/// <summary>
/// Gestes de souris et raccourcis sur la composition, sans interface : la fenêtre relaie les événements (coordonnées en
/// pixels de la zone d'affichage) et redessine sur <see cref="CompositionDocument.Changed"/> et <see cref="ViewTransform.Changed"/>.
/// Portage fidèle de <c>on_left_down</c>, <c>on_left_drag</c>, <c>on_left_up</c>, <c>on_pan_*</c>, <c>on_zoom</c> (ui.py)
/// et des poignées de <c>_draw_handles</c> (ui_views.py).
/// </summary>
public sealed class EditController
{
    /// <summary>Distance d'aimantation, en unités de composition (<c>SNAP_DIST</c>).</summary>
    public const double SnapDistance = 25;
    /// <summary>Diamètre des poignées dessinées, en pixels écran.</summary>
    public const double HandleSize = 10;
    /// <summary>Un clic prend une poignée s'il est à moins de cette distance (en x ET en y, strictement), en pixels écran.</summary>
    public const double HandleHitTolerance = 10;
    /// <summary>Plus petite part visible d'une image rognée, en fraction de l'image (<c>MIN_CROP</c>).</summary>
    public const double MinCrop = 0.05;
    /// <summary>Plus petite taille (largeur et hauteur) en redimensionnement, en unités de composition.</summary>
    public const double MinScaleSize = 40;

    private readonly CompositionDocument _doc;
    private readonly ViewTransform _view;
    private Drag _drag = new();
    private EditMode _mode = EditMode.Move;

    /// <summary>État du geste en cours (équivalent de <c>_drag_data</c>).</summary>
    private sealed class Drag
    {
        public DragAction Action;
        public HandleCorner Corner;
        public int Item = -1;
        public double StartLogicX, StartLogicY;   // slx, sly
        public double LastScreenX, LastScreenY;   // lx, ly (déplacement de la vue)
        public double OrigX, OrigY, OrigW, OrigH; // ox, oy, ow, oh
        public double Aspect = 1.0;
        public CropBox Crop0 = CropBox.Full;
        public PointerButton Button;
    }

    public EditController(CompositionDocument document, ViewTransform view)
    {
        _doc = document;
        _view = view;
    }

    public CompositionDocument Document => _doc;
    public ViewTransform View => _view;

    /// <summary>Outil actif ; les poignées ne sont visibles et actives qu'en Redimensionner et Rogner.</summary>
    public EditMode Mode
    {
        get => _mode;
        set
        {
            if (_mode == value) return;
            _mode = value;
            ModeChanged?.Invoke(this, EventArgs.Empty);
        }
    }

    public event EventHandler? ModeChanged;

    /// <summary>Geste en cours : l'interface en déduit le curseur (main pendant <see cref="DragAction.Pan"/>, croix sinon).</summary>
    public DragAction CurrentAction => _drag.Action;

    /// <summary>Poignée tenue pendant un redimensionnement ou un rognage.</summary>
    public HandleCorner? ActiveHandle => _drag.Action is DragAction.Scale or DragAction.Crop ? _drag.Corner : null;

    // --- Géométrie affichée ---

    /// <summary>Rectangle d'une image dans la zone d'affichage (non arrondi : c'est celui qu'utilisent les tests de clic).</summary>
    public ScreenRect ImageScreenRect(CompositionImage img)
    {
        var (sx, sy) = _view.LogicToScreen(img.X, img.Y);
        return new ScreenRect(sx, sy, (img.W ?? 0) * _view.Zoom, (img.H ?? 0) * _view.Zoom);
    }

    /// <summary>Cadre de l'image sélectionnée, ou null.</summary>
    public ScreenRect? SelectionScreenRect => _doc.Selected is { } img ? ImageScreenRect(img) : null;

    /// <summary>
    /// Poignées à dessiner (cercles de <see cref="HandleSize"/> px centrés sur les coins de l'image sélectionnée) ;
    /// vide hors des outils Redimensionner et Rogner. Ce sont exactement les points testés par <see cref="HitTestHandle"/>.
    /// </summary>
    public IReadOnlyList<HandleInfo> Handles
    {
        get
        {
            if (_mode is not (EditMode.Scale or EditMode.Crop) || _doc.Selected is not { } img) return [];
            var r = ImageScreenRect(img);
            return
            [
                new(HandleCorner.TopLeft, r.X, r.Y),
                new(HandleCorner.TopRight, r.X + r.Width, r.Y),
                new(HandleCorner.BottomRight, r.X + r.Width, r.Y + r.Height),
                new(HandleCorner.BottomLeft, r.X, r.Y + r.Height),
            ];
        }
    }

    /// <summary>Poignée sous le point écran (la première dans l'ordre tl, tr, br, bl), ou null.</summary>
    public HandleCorner? HitTestHandle(double sx, double sy)
    {
        foreach (var h in Handles)
        {
            if (Math.Abs(sx - h.X) < HandleHitTolerance && Math.Abs(sy - h.Y) < HandleHitTolerance) return h.Corner;
        }
        return null;
    }

    /// <summary>Image sous le point écran : celle de plus grand ZIndex (bords inclus), à égalité la première de la liste ; ou null.</summary>
    public int? HitTestImage(double sx, double sy)
    {
        var (lx, ly) = _view.ScreenToLogic(sx, sy);
        int? clicked = null;
        int maxZ = -1;
        var images = _doc.Images;
        for (int i = 0; i < images.Count; i++)
        {
            var img = images[i];
            if (img.W is not double w || img.H is not double h) continue;
            if (img.X <= lx && lx <= img.X + w && img.Y <= ly && ly <= img.Y + h && img.ZIndex > maxZ)
            {
                maxZ = img.ZIndex;
                clicked = i;
            }
        }
        return clicked;
    }

    // --- Souris ---

    /// <summary>
    /// Bouton enfoncé. Gauche : poignée de l'image sélectionnée (Redimensionner/Rogner), sinon image cliquée (sélection, et
    /// déplacement sauf en Redimensionner), sinon désélection et déplacement de la vue. Milieu et droit : déplacement de la vue.
    /// </summary>
    public void PointerPressed(double sx, double sy, PointerButton button, EditModifiers modifiers = EditModifiers.None)
    {
        if (button != PointerButton.Left)
        {
            StartPan(sx, sy, button);
            return;
        }
        var (lx, ly) = _view.ScreenToLogic(sx, sy);

        if (_mode is EditMode.Crop or EditMode.Scale && _doc.Selected is { } sel && HitTestHandle(sx, sy) is HandleCorner corner)
        {
            double w = sel.W ?? 0, h = sel.H ?? 0;
            _drag = new Drag
            {
                Action = _mode == EditMode.Crop ? DragAction.Crop : DragAction.Scale,
                Corner = corner,
                Item = _doc.SelectedIndex!.Value,
                StartLogicX = lx, StartLogicY = ly,
                OrigX = sel.X, OrigY = sel.Y, OrigW = w, OrigH = h,
                Aspect = Math.Max(0.01, w / Math.Max(1, h)),
                Crop0 = sel.Crop,
                Button = button,
            };
            return;
        }

        int? clicked = HitTestImage(sx, sy);
        bool selectionChanged = _doc.SetSelection(clicked);
        if (clicked is int idx)
        {
            var img = _doc.Images[idx];
            _drag = _mode == EditMode.Scale
                ? new Drag { Action = DragAction.None, Item = idx, Button = button }
                : new Drag { Action = DragAction.Move, Item = idx, StartLogicX = lx, StartLogicY = ly, OrigX = img.X, OrigY = img.Y, Button = button };
        }
        else
        {
            StartPan(sx, sy, button);
        }
        if (selectionChanged) _doc.Raise(ChangeReason.Selection);
    }

    /// <summary>Pointeur déplacé (bouton enfoncé ou non : sans geste en cours, rien ne se passe).</summary>
    public void PointerMoved(double sx, double sy, EditModifiers modifiers = EditModifiers.None)
    {
        switch (_drag.Action)
        {
            case DragAction.None:
                return;
            case DragAction.Pan:
                _view.PanBy(sx - _drag.LastScreenX, sy - _drag.LastScreenY);
                _drag.LastScreenX = sx;
                _drag.LastScreenY = sy;
                return;
        }
        if (_drag.Item < 0 || _drag.Item >= _doc.Images.Count) return;
        var (lx, ly) = _view.ScreenToLogic(sx, sy);
        var img = _doc.Images[_drag.Item];
        switch (_drag.Action)
        {
            case DragAction.Move: Move(img, lx, ly, snap: (modifiers & EditModifiers.Shift) == 0); break;
            case DragAction.Crop: CropFromHandle(img, lx, ly); break;
            case DragAction.Scale: ScaleFromHandle(img, lx, ly); break;
        }
        _doc.Raise(ChangeReason.Edited, live: true);
    }

    /// <summary>Bouton relâché : un déplacement, redimensionnement ou rognage est enregistré dans l'historique (même sans mouvement).</summary>
    public void PointerReleased(double sx, double sy, PointerButton button)
    {
        var drag = _drag;
        if (button != drag.Button && drag.Action != DragAction.None) return; // relâchement d'un autre bouton pendant un geste
        _drag = new Drag();
        switch (drag.Action)
        {
            case DragAction.Move: _doc.Commit("Move", ChangeReason.Edited); break;
            case DragAction.Scale: _doc.Commit("Scale", ChangeReason.Edited); break;
            case DragAction.Crop: _doc.Commit("Crop", ChangeReason.Edited); break;
        }
    }

    /// <summary>Un cran de molette au point (sx, sy) : zoom centré sur le pointeur.</summary>
    public void Wheel(double sx, double sy, double delta) => _view.ZoomAt(sx, sy, delta);

    /// <summary>Abandonne le geste en cours sans l'enregistrer (perte de capture du pointeur, Échap).</summary>
    public void CancelGesture() => _drag = new Drag();

    // --- Clavier ---

    /// <summary>
    /// Raccourcis d'édition de la version Python : Ctrl+Z annuler, Ctrl+Y rétablir, Ctrl+R pivoter, Suppr supprimer l'image
    /// sélectionnée. L'interface ne doit pas transmettre Suppr quand un champ de saisie a le focus. Renvoie vrai si la touche
    /// est prise en charge (même si la commande n'avait rien à faire).
    /// </summary>
    public bool KeyDown(EditKey key, EditModifiers modifiers = EditModifiers.None)
    {
        bool ctrl = (modifiers & EditModifiers.Control) != 0;
        switch (key)
        {
            case EditKey.Z when ctrl: _doc.Undo(); return true;
            case EditKey.Y when ctrl: _doc.Redo(); return true;
            case EditKey.R when ctrl: _doc.RotateSelected(); return true;
            case EditKey.Delete: _doc.RemoveSelected(); return true;
            default: return false;
        }
    }

    // --- Commandes qui dépendent de la vue ---

    /// <summary>Ajoute des images au centre de la zone d'affichage (<c>cmd_add_images</c>).</summary>
    public void AddImagesAtViewCenter(IEnumerable<CompositionImage> images)
    {
        var (cx, cy) = _view.ViewCenter;
        _doc.AddImages(images, cx, cy);
    }

    /// <summary>Cadre la composition dans une zone de cette taille (<c>_auto_fit</c>).</summary>
    public bool FitToView(double viewportWidth, double viewportHeight) => _view.FitTo(viewportWidth, viewportHeight, _doc.Width, _doc.Height);

    /// <summary>La zone d'affichage a changé de taille : recadrage tant que l'utilisateur n'a pas zoomé.</summary>
    public bool ViewportResized(double width, double height) => _view.ViewportResized(width, height, _doc.Width, _doc.Height);

    /// <summary>
    /// Nouveau projet (<c>cmd_new_project</c>) : composition vidée, outil Déplacer, geste abandonné, recadrage automatique.
    /// </summary>
    public void NewProject()
    {
        _drag = new Drag();
        Mode = EditMode.Move;
        _view.ResetUserZoom();
        FitToView(_view.ViewportWidth, _view.ViewportHeight);
        _doc.Reset();
    }

    // --- Gestes ---

    private void StartPan(double sx, double sy, PointerButton button)
        => _drag = new Drag { Action = DragAction.Pan, LastScreenX = sx, LastScreenY = sy, Button = button };

    /// <summary>
    /// Déplacement avec aimantation : le bord gauche se colle à x = 0 et le bord haut à y = 0 de la composition, puis le bord
    /// gauche au bord gauche ou droit de chaque autre image (dans l'ordre de la liste, la dernière cible proche l'emporte).
    /// </summary>
    private void Move(CompositionImage img, double lx, double ly, bool snap)
    {
        double nx = _drag.OrigX + (lx - _drag.StartLogicX), ny = _drag.OrigY + (ly - _drag.StartLogicY);
        if (snap)
        {
            if (Math.Abs(nx) < SnapDistance) nx = 0;
            if (Math.Abs(ny) < SnapDistance) ny = 0;
            foreach (var o in _doc.Images)
            {
                if (ReferenceEquals(o, img)) continue;
                double ow = o.W ?? 0;
                if (Math.Abs(nx - o.X) < SnapDistance) nx = o.X;
                if (Math.Abs(nx - (o.X + ow)) < SnapDistance) nx = o.X + ow;
            }
        }
        img.X = nx;
        img.Y = ny;
    }

    /// <summary>
    /// Rognage : la partie conservée reste à la même place et à la même échelle ; le cadre suit la zone visible.
    /// Le coin tiré se déplace dans [0, 1] et garde au moins <see cref="MinCrop"/> avec le côté opposé d'origine.
    /// </summary>
    private void CropFromHandle(CompositionImage img, double lx, double ly)
    {
        var d = _drag;
        var (l0, t0, r0, b0) = (d.Crop0.Left, d.Crop0.Top, d.Crop0.Right, d.Crop0.Bottom);
        double ow = Math.Max(1, d.OrigW), oh = Math.Max(1, d.OrigH);
        double dfx = (lx - d.StartLogicX) / ow * (r0 - l0);
        double dfy = (ly - d.StartLogicY) / oh * (b0 - t0);
        double l = l0, t = t0, r = r0, b = b0;
        var c = d.Corner;
        switch (c)
        {
            case HandleCorner.TopLeft: l += dfx; t += dfy; break;
            case HandleCorner.BottomRight: r += dfx; b += dfy; break;
            case HandleCorner.TopRight: r += dfx; t += dfy; break;
            case HandleCorner.BottomLeft: l += dfx; b += dfy; break;
        }
        bool left = c is HandleCorner.TopLeft or HandleCorner.BottomLeft;
        bool top = c is HandleCorner.TopLeft or HandleCorner.TopRight;
        l = Math.Min(Math.Max(0.0, l), left ? r0 - MinCrop : l0);
        t = Math.Min(Math.Max(0.0, t), top ? b0 - MinCrop : t0);
        r = Math.Max(Math.Min(1.0, r), !left ? l0 + MinCrop : r0);
        b = Math.Max(Math.Min(1.0, b), !top ? t0 + MinCrop : b0);
        img.Crop = new CropBox(l, t, r, b);
        img.W = Math.Max(1, PythonCompat.RoundToInt(ow * (r - l) / (r0 - l0)));
        img.H = Math.Max(1, PythonCompat.RoundToInt(oh * (b - t) / (b0 - t0)));
        img.X = d.OrigX + (l - l0) / (r0 - l0) * ow;
        img.Y = d.OrigY + (t - t0) / (b0 - t0) * oh;
    }

    /// <summary>
    /// Redimensionnement : le coin opposé reste fixe, la taille suit la plus grande des deux distances au pointeur
    /// (en gardant le ratio du début du geste), au moins <see cref="MinScaleSize"/> sur chaque côté, arrondie à l'unité.
    /// </summary>
    private void ScaleFromHandle(CompositionImage img, double lx, double ly)
    {
        var d = _drag;
        double aspect = d.Aspect;
        // Point fixe : le coin opposé à la poignée tenue
        var (ax, ay) = d.Corner switch
        {
            HandleCorner.TopLeft => (d.OrigX + d.OrigW, d.OrigY + d.OrigH),
            HandleCorner.TopRight => (d.OrigX, d.OrigY + d.OrigH),
            HandleCorner.BottomRight => (d.OrigX, d.OrigY),
            _ => (d.OrigX + d.OrigW, d.OrigY),
        };
        double rawW = Math.Abs(lx - ax);
        double rawH = Math.Abs(ly - ay);
        double newW = Math.Max(MinScaleSize, Math.Max(rawW, rawH * aspect));
        double newH = Math.Max(MinScaleSize, newW / aspect);
        newW = Math.Max(MinScaleSize, PythonCompat.RoundToInt(newW));
        newH = Math.Max(MinScaleSize, PythonCompat.RoundToInt(newH));
        (img.X, img.Y) = d.Corner switch
        {
            HandleCorner.BottomRight => (ax, ay),        // ancre en haut à gauche
            HandleCorner.BottomLeft => (ax - newW, ay),  // ancre en haut à droite
            HandleCorner.TopRight => (ax, ay - newH),    // ancre en bas à gauche
            _ => (ax - newW, ay - newH),                 // ancre en bas à droite
        };
        img.W = newW;
        img.H = newH;
    }
}
