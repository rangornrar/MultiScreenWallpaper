using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Geometry;
using Microsoft.Graphics.Canvas.Text;
using Windows.Foundation;
using WallCraft.App.Services;
using WallCraft.App.ViewModels;
using WallCraft.Core.Editing;
using WallCraft.Core.Presentation;

namespace WallCraft.App.Rendering;

/// <summary>Dessin de la zone de composition (portage de <c>_refresh_main_canvas</c>, ui_views.py), en Win2D.</summary>
internal static class CompositionRenderer
{
    public static void Draw(CanvasDrawingSession ds, double cw, double ch, MainViewModel vm)
    {
        ds.Clear(Palette.CanvasBackground);
        if (cw < 10 || ch < 10) return;
        var view = vm.View;
        var doc = vm.Document;
        var loc = Localizer.Current;

        // Bureau virtuel : ombre, fond, grille, bord
        var (bx, by) = view.LogicToScreen(0, 0);
        double bw = doc.Width * view.Zoom, bh = doc.Height * view.Zoom;
        const double shadowPad = 18;
        ds.FillRectangle(new Rect(bx - shadowPad, by - shadowPad, bw + 2 * shadowPad, bh + 2 * shadowPad), Palette.StageShadow);
        ds.FillRectangle(new Rect(bx, by, bw, bh), Palette.Stage);
        double step = Math.Max(26, (int)(220 * view.Zoom));
        for (double x = Math.Floor(bx - PythonMod(bx, step)); x < bx + bw; x += step)
        {
            if (x >= bx) ds.DrawLine((float)x, (float)Math.Max(0, by), (float)x, (float)Math.Min(ch, by + bh), Palette.Grid);
        }
        for (double y = Math.Floor(by - PythonMod(by, step)); y < by + bh; y += step)
        {
            if (y >= by) ds.DrawLine((float)Math.Max(0, bx), (float)y, (float)Math.Min(cw, bx + bw), (float)y, Palette.Grid);
        }
        ds.DrawRectangle(new Rect(bx, by, bw, bh), Palette.Border, 2);

        // Images, du calque du dessous vers celui du dessus
        var cache = vm.Images;
        foreach (var img in doc.Images.OrderBy(i => i.ZIndex))
        {
            var r = vm.Controller.ImageScreenRect(img);
            if (r.Width <= 0 || r.Height <= 0) continue;
            if (r.X > cw || r.Y > ch || r.X + r.Width < 0 || r.Y + r.Height < 0) continue;
            ds.FillRectangle(new Rect(r.X + 4, r.Y + 6, r.Width, r.Height), Palette.ImageShadow);
            DrawingHelpers.DrawImagePart(ds, cache, img, new Rect(r.X, r.Y, r.Width, r.Height), 0, 0, img.W ?? 0, img.H ?? 0);
            if (r.Width > 90 && r.Height > 30 && DisplayText.LowResolution(img, loc.DecimalSeparator) is { } low)
                DrawingHelpers.Chip(ds, r.X + 8, r.Y + r.Height - 8, "⚠ ×" + low, Palette.WarningChip, Palette.Warning, anchorBottom: true);
        }

        // Écrans : zones hors écran assombries, cadres en pointillés et noms
        if (vm.ShowMonitors && vm.Monitors.Count > 0)
        {
            var canvases = vm.Monitors.Where(m => m.Canvas is not null).Select(m => m.Canvas!.Value).ToList();
            foreach (var cell in ScreenCoverage.OutsideCells(canvases, doc.Width, doc.Height))
            {
                var (x0, y0) = view.LogicToScreen(cell.Left, cell.Top);
                var (x1, y1) = view.LogicToScreen(cell.Right, cell.Bottom);
                ds.FillRectangle(new Rect(x0, y0, Math.Max(0, x1 - x0), Math.Max(0, y1 - y0)), Palette.OutsideScreens);
            }
            using var dashes = new CanvasStrokeStyle { CustomDashStyle = [3f, 2f] }; // 6 px / 4 px pour un trait de 2 px
            for (int i = 0; i < vm.Monitors.Count; i++)
            {
                if (vm.Monitors[i].Canvas is not { } c) continue;
                var (mx, my) = view.LogicToScreen(c.X, c.Y);
                double mw = c.Width * view.Zoom, mh = c.Height * view.Zoom;
                ds.DrawRectangle(new Rect(mx, my, mw, mh), Palette.Monitor, 2, dashes);
                string label = i < vm.MonitorLabels.Count ? vm.MonitorLabels[i] : vm.Monitors[i].Name;
                DrawingHelpers.Chip(ds, mx + 8, my + 8, label, Palette.MonitorChip, Palette.Monitor, maxWidth: mw - 16);
            }
        }

        // Sélection et poignées par-dessus tout : exactement les points testés par EditController
        if (vm.Controller.SelectionScreenRect is { } sel)
        {
            ds.DrawRectangle(new Rect(sel.X - 3, sel.Y - 3, sel.Width + 6, sel.Height + 6), Palette.AccentLine, 1);
            ds.DrawRectangle(new Rect(sel.X, sel.Y, sel.Width, sel.Height), Palette.Accent, 2);
            float radius = (float)(EditController.HandleSize / 2);
            foreach (var h in vm.Controller.Handles)
            {
                ds.FillCircle((float)h.X, (float)h.Y, radius, Palette.Accent);
                ds.DrawCircle((float)h.X, (float)h.Y, radius, Palette.AccentLine, 2);
            }
        }

        if (doc.Images.Count == 0)
        {
            using var format = new CanvasTextFormat
            {
                FontFamily = "Segoe UI",
                FontSize = 16,
                HorizontalAlignment = CanvasHorizontalAlignment.Center,
                VerticalAlignment = CanvasVerticalAlignment.Center,
                WordWrapping = CanvasWordWrapping.Wrap,
            };
            double width = Math.Max(260, cw - 160);
            ds.DrawText(loc["canvas_empty"], new Rect((cw - width) / 2, 0, width, ch), Palette.TextMuted, format);
        }
        cache.EndFrame();
    }

    /// <summary>Reste toujours positif, comme l'opérateur % de Python (grille alignée sur l'origine de la zone).</summary>
    private static double PythonMod(double a, double b) => ((a % b) + b) % b;
}
