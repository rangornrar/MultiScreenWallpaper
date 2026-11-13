namespace WallCraft.Core.Editing;

/// <summary>
/// Passage des coordonnées de la zone d'affichage (pixels écran, origine en haut à gauche de la zone) aux coordonnées
/// de la composition : <c>écran = composition × Zoom + décalage</c>. Portage de <c>screen_to_logic</c>, <c>logic_to_screen</c>,
/// <c>on_zoom</c>, <c>on_pan_*</c> et <c>_auto_fit</c> (ui.py, ui_views.py).
/// </summary>
public sealed class ViewTransform
{
    public const double MinZoom = 0.01;
    public const double MaxZoom = 10.0;
    /// <summary>Facteur appliqué à chaque cran de molette vers l'avant (vers l'arrière : <see cref="WheelOutFactor"/>).</summary>
    public const double WheelInFactor = 1.1;
    public const double WheelOutFactor = 0.9;
    /// <summary>Part de la zone occupée par la composition après <see cref="FitTo"/> (largeur, hauteur).</summary>
    public const double FitMarginX = 0.95;
    public const double FitMarginY = 0.94;
    /// <summary>En dessous de cette taille (largeur ou hauteur), la zone n'est pas encore affichée : pas de cadrage.</summary>
    public const double MinFitViewport = 50;

    /// <summary>Valeurs de départ de Python, avant le premier cadrage.</summary>
    public double Zoom { get; private set; } = 0.15;
    public double OffsetX { get; private set; } = 50;
    public double OffsetY { get; private set; } = 50;

    /// <summary>Taille actuelle de la zone d'affichage (pour le centre de la vue et le recadrage au redimensionnement).</summary>
    public double ViewportWidth { get; private set; }
    public double ViewportHeight { get; private set; }

    /// <summary>
    /// Vrai dès que l'utilisateur a zoomé à la molette (<c>_user_zoomed</c>) : la vue n'est alors plus recadrée
    /// automatiquement quand la zone change de taille. Remis à faux par <see cref="ResetUserZoom"/> (nouveau projet).
    /// </summary>
    public bool UserZoomed { get; private set; }

    /// <summary>Le zoom ou le décalage a changé : redessiner.</summary>
    public event EventHandler? Changed;

    public (double X, double Y) ScreenToLogic(double sx, double sy) => ((sx - OffsetX) / Zoom, (sy - OffsetY) / Zoom);
    public (double X, double Y) LogicToScreen(double lx, double ly) => ((lx * Zoom) + OffsetX, (ly * Zoom) + OffsetY);

    /// <summary>Centre de la zone d'affichage en coordonnées de composition (là où arrivent les images ajoutées).</summary>
    public (double X, double Y) ViewCenter => ScreenToLogic(Math.Max(1, ViewportWidth) * 0.5, Math.Max(1, ViewportHeight) * 0.5);

    /// <summary>Règle zoom et décalage directement (restauration d'une vue, tests).</summary>
    public void Set(double zoom, double offsetX, double offsetY)
    {
        Zoom = zoom;
        OffsetX = offsetX;
        OffsetY = offsetY;
        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>Mémorise la taille de la zone sans recadrer.</summary>
    public void SetViewport(double width, double height)
    {
        ViewportWidth = width;
        ViewportHeight = height;
    }

    /// <summary>
    /// Cadre toute la composition dans la zone et la centre (<c>_auto_fit</c>). Sans effet si la zone fait moins de
    /// <see cref="MinFitViewport"/> px de côté (pas encore affichée). Le zoom obtenu n'est pas borné, comme en Python.
    /// </summary>
    public bool FitTo(double viewportWidth, double viewportHeight, double compositionWidth, double compositionHeight)
    {
        SetViewport(viewportWidth, viewportHeight);
        if (viewportWidth < MinFitViewport || viewportHeight < MinFitViewport) return false;
        double scale = Math.Min((viewportWidth * FitMarginX) / compositionWidth, (viewportHeight * FitMarginY) / compositionHeight);
        Zoom = scale;
        OffsetX = (viewportWidth - compositionWidth * scale) / 2;
        OffsetY = (viewportHeight - compositionHeight * scale) / 2;
        Changed?.Invoke(this, EventArgs.Empty);
        return true;
    }

    /// <summary>
    /// La zone a changé de taille (<c>_on_stage_resized</c>) : recadrage automatique tant que l'utilisateur n'a pas zoomé
    /// lui-même ; sinon la vue garde son zoom et son décalage. Renvoie vrai si la vue a été recadrée.
    /// </summary>
    public bool ViewportResized(double width, double height, double compositionWidth, double compositionHeight)
    {
        if (!UserZoomed) return FitTo(width, height, compositionWidth, compositionHeight);
        SetViewport(width, height);
        Changed?.Invoke(this, EventArgs.Empty);
        return false;
    }

    /// <summary>
    /// Un cran de molette (<c>on_zoom</c>) : ×1,1 vers l'avant (<paramref name="delta"/> &gt; 0), ×0,9 sinon, borné à
    /// [<see cref="MinZoom"/>, <see cref="MaxZoom"/>] ; le point de la composition sous le pointeur ne bouge pas.
    /// Comme en Python, chaque événement compte pour un cran quelle que soit l'amplitude de <paramref name="delta"/>.
    /// </summary>
    public void ZoomAt(double sx, double sy, double delta)
    {
        double f = delta > 0 ? WheelInFactor : WheelOutFactor;
        var (lx, ly) = ScreenToLogic(sx, sy);
        Zoom = Math.Max(MinZoom, Math.Min(Zoom * f, MaxZoom));
        UserZoomed = true;
        OffsetX = sx - lx * Zoom;
        OffsetY = sy - ly * Zoom;
        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>Décale la vue de (dx, dy) pixels écran (<c>on_pan_drag</c>).</summary>
    public void PanBy(double dx, double dy)
    {
        OffsetX += dx;
        OffsetY += dy;
        Changed?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>Nouveau projet : la vue se recadre de nouveau automatiquement.</summary>
    public void ResetUserZoom() => UserZoomed = false;
}
