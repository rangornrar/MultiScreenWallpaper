using System.Numerics;
using Microsoft.Graphics.Canvas;
using Microsoft.Graphics.Canvas.Brushes;
using Windows.Foundation;
using WallCraft.App.ViewModels;
using WallCraft.Core.Presentation;

namespace WallCraft.App.Rendering;

/// <summary>
/// Aperçu « vue réelle » : les écrans dessinés comme des moniteurs posés sur un bureau, montrant ce que chacun affichera
/// (portage de <c>_refresh_sim_view</c> et <c>_sim_backdrop_image</c>, ui_views.py).
/// </summary>
internal static class PreviewRenderer
{
    public static void Draw(CanvasDrawingSession ds, double cw, double ch, MainViewModel vm)
    {
        ds.Clear(Palette.Rgb(16, 24, 41));
        if (vm.Monitors.Count == 0 || cw < 10 || ch < 10) return;
        float w = (float)cw, h = (float)ch;
        float deskY = (float)PreviewLayout.DeskY(ch);

        // Mur puis bureau : dégradés verticaux
        using (var wall = new CanvasLinearGradientBrush(ds, Palette.Rgb(8, 14, 28), Palette.Rgb(18, 28, 48))
               { StartPoint = new Vector2(0, 0), EndPoint = new Vector2(0, deskY) })
        {
            ds.FillRectangle(0, 0, w, deskY, wall);
        }
        using (var desk = new CanvasLinearGradientBrush(ds, Palette.Rgb(20, 24, 32), Palette.Rgb(10, 12, 16))
               { StartPoint = new Vector2(0, deskY), EndPoint = new Vector2(0, h) })
        {
            ds.FillRectangle(0, deskY, w, h - deskY, desk);
        }
        ds.DrawLine(0, deskY, w, deskY, Palette.DeskLine);
        ds.DrawLine(0, deskY + 1, w, deskY + 1, Palette.DeskHighlight);
        ds.DrawLine(0, deskY + 36, w, deskY + 36, Palette.DeskEdge);

        var canvases = vm.Monitors.Select(m => m.Canvas ?? m.DesktopRect).ToList();
        var screens = PreviewLayout.Screens(canvases, vm.Document.Width, vm.Document.Height, vm.Physical.Enabled, cw, ch);
        foreach (var s in screens)
        {
            double mx = s.X, my = s.Y, mw = s.Width, mh = s.Height;
            ds.FillRectangle(new Rect(mx + 7, my + 10, mw, mh + 2), Palette.MonitorShadow);
            ds.FillRectangle(new Rect(mx - 6, my - 6, mw + 12, mh + 12), Palette.MonitorCase);
            ds.DrawRectangle(new Rect(mx - 6, my - 6, mw + 12, mh + 12), Palette.MonitorCaseLine, 1);
            ds.FillRectangle(new Rect(mx - 2, my - 2, mw + 4, mh + 4), Palette.MonitorBezel);
            ds.DrawRectangle(new Rect(mx - 2, my - 2, mw + 4, mh + 4), Palette.MonitorBezelLine, 1);

            var panel = new Rect(s.InnerLeft, s.InnerTop, Math.Max(0, s.InnerRight - s.InnerLeft), Math.Max(0, s.InnerBottom - s.InnerTop));
            ds.FillRectangle(panel, Palette.Panel);
            using (ds.CreateLayer(1f, panel))
            {
                foreach (var slice in PreviewLayout.Slices(s, vm.Document.Images))
                {
                    DrawingHelpers.DrawImagePart(ds, vm.Images, slice.Image, new Rect(slice.X, slice.Y, slice.Width, slice.Height),
                        slice.SourceLeft, slice.SourceTop, slice.SourceRight, slice.SourceBottom);
                }
            }
            ds.DrawLine((float)s.InnerLeft, (float)s.InnerTop + 1, (float)s.InnerRight, (float)s.InnerTop + 1, Palette.PanelGlare);
            ds.DrawRectangle(panel, Palette.PanelLine, 1);

            string label = s.Index < vm.MonitorLabels.Count ? vm.MonitorLabels[s.Index] : vm.Monitors[s.Index].Name;
            DrawingHelpers.Chip(ds, mx + 12, my + 12, label, Palette.PreviewChip, Palette.PreviewChipText, maxWidth: mw - 24);

            // Pied du moniteur
            double standX = mx + mw / 2;
            double standTop = s.InnerBottom + 4;
            if (deskY - 7 > standTop)
            {
                ds.FillRectangle(new Rect(standX - 7, standTop, 14, deskY - 7 - standTop), Palette.Stand);
                ds.DrawRectangle(new Rect(standX - 7, standTop, 14, deskY - 7 - standTop), Palette.StandLine, 1);
            }
            ds.FillRectangle(new Rect(standX - 30, deskY - 7, 60, 12), Palette.StandFoot);
            ds.DrawRectangle(new Rect(standX - 30, deskY - 7, 60, 12), Palette.StandFootLine, 1);
            ds.FillRectangle(new Rect(mx + mw * 0.16, deskY + 10, mw * 0.68, 12), Palette.StandShadow);
        }
        vm.Images.EndFrame();
    }
}
