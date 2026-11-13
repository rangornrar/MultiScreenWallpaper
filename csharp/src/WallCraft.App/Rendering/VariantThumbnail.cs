using System.Numerics;
using System.Runtime.InteropServices.WindowsRuntime;
using Microsoft.Graphics.Canvas;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Imaging;
using Windows.Foundation;
using WallCraft.App.ViewModels;
using WallCraft.Core.Layout;

namespace WallCraft.App.Rendering;

/// <summary>Vignette d'une variante de disposition pour <c>VariantsDialog</c>, dessinée depuis les vignettes de travail.</summary>
internal static class VariantThumbnail
{
    public static Task<ImageSource> RenderAsync(MainViewModel vm, IReadOnlyList<Placement> placement, double width)
    {
        var doc = vm.Document;
        int tw = Math.Max(1, (int)Math.Round(width));
        int th = Math.Max(1, (int)Math.Round(width * doc.Height / Math.Max(1, doc.Width)));
        var images = doc.Images.Select(i => i.Clone()).ToList();
        LayoutEngine.ApplyPlacement(images, placement);

        using var target = new CanvasRenderTarget(CanvasDevice.GetSharedDevice(), tw, th, 96);
        using (var ds = target.CreateDrawingSession())
        {
            ds.Clear(Palette.Stage);
            ds.Transform = Matrix3x2.CreateScale((float)(tw / Math.Max(1, doc.Width)));
            foreach (var img in images.OrderBy(i => i.ZIndex))
            {
                DrawingHelpers.DrawImagePart(ds, vm.Images, img, new Rect(img.X, img.Y, img.W ?? 0, img.H ?? 0), 0, 0, img.W ?? 0, img.H ?? 0);
            }
            foreach (var m in vm.Monitors)
            {
                if (m.Canvas is { } c) ds.DrawRectangle(new Rect(c.X, c.Y, c.Width, c.Height), Palette.Monitor, (float)(2 * doc.Width / tw));
            }
        }
        byte[] pixels = target.GetPixelBytes();
        var bitmap = new WriteableBitmap(tw, th);
        using (var stream = bitmap.PixelBuffer.AsStream()) stream.Write(pixels, 0, pixels.Length);
        bitmap.Invalidate();
        return Task.FromResult<ImageSource>(bitmap);
    }
}
