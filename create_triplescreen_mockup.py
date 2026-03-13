from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "html" / "assets" / "wallcraft_triplescreen_mockup.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a landing-page mockup showing an image inside WallCraft Pro and the result on a 3-screen setup."
    )
    parser.add_argument("source_image", help="Path to the source image to showcase.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output image path. Default: {DEFAULT_OUTPUT}",
    )
    return parser.parse_args()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\segoeuib.ttf") if bold else Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\bahnschrift.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf") if bold else Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def paste_rounded(base: Image.Image, overlay: Image.Image, box: tuple[int, int], radius: int) -> None:
    mask = rounded_mask(overlay.size, radius)
    base.paste(overlay, box, mask)


def contain(image: Image.Image, size: tuple[int, int], background: tuple[int, int, int]) -> Image.Image:
    target = Image.new("RGB", size, background)
    fitted = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    target.paste(fitted, (x, y))
    return target


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def draw_shadow(base: Image.Image, rect: tuple[int, int, int, int], radius: int, blur: int, color: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = rect
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.rounded_rectangle(rect, radius=radius, fill=color)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(shadow)


def draw_card(base: Image.Image, rect: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int, int], outline: tuple[int, int, int, int]) -> None:
    draw_shadow(base, rect, radius, 28, (0, 0, 0, 110))
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=2)
    base.alpha_composite(overlay)


def wallpaper_slices(image: Image.Image, size: tuple[int, int], screens: int) -> list[Image.Image]:
    virtual = cover(image, (size[0] * screens, size[1]))
    slices = []
    for index in range(screens):
        left = index * size[0]
        slices.append(virtual.crop((left, 0, left + size[0], size[1])))
    return slices


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], content: str, font: ImageFont.ImageFont, fill: tuple[int, int, int], anchor: str | None = None) -> None:
    draw.text(xy, content, font=font, fill=fill, anchor=anchor)


def build_mockup(source_path: Path, output_path: Path) -> Path:
    source = Image.open(source_path).convert("RGB")
    canvas = Image.new("RGBA", (1800, 1125), (5, 11, 19, 255))

    background = cover(source, canvas.size).filter(ImageFilter.GaussianBlur(18))
    background = ImageEnhance_like(background, brightness=0.34, saturation=0.9)
    canvas.alpha_composite(background.convert("RGBA"))

    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((30, -120, 780, 530), fill=(72, 186, 255, 34))
    glow_draw.ellipse((1110, 120, 1760, 840), fill=(79, 214, 194, 30))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(50)))

    draw = ImageDraw.Draw(canvas)
    title_font = load_font(62, bold=True)
    sub_font = load_font(26)
    label_font = load_font(24, bold=True)
    body_font = load_font(22)
    tiny_font = load_font(18)

    text(draw, (78, 66), "WallCraft Pro mockup", title_font, (238, 244, 255))
    text(draw, (80, 142), "Photo source dans le logiciel + rendu final sur 3 ecrans", sub_font, (160, 181, 206))

    left_rect = (60, 210, 860, 1005)
    right_rect = (910, 210, 1740, 1005)
    draw_card(canvas, left_rect, 36, (9, 16, 27, 220), (120, 165, 214, 60))
    draw_card(canvas, right_rect, 36, (9, 16, 27, 220), (120, 165, 214, 60))

    text(draw, (96, 246), "Dans WallCraft Pro", label_font, (231, 240, 255))
    text(draw, (96, 282), "Import, preview, mise en page et controle visuel", body_font, (153, 171, 194))

    app_rect = (92, 320, 828, 976)
    draw_card(canvas, app_rect, 28, (12, 21, 34, 245), (138, 184, 235, 44))
    bar = Image.new("RGBA", (app_rect[2] - app_rect[0], 58), (14, 24, 39, 255))
    bar_draw = ImageDraw.Draw(bar)
    bar_draw.rounded_rectangle((0, 0, bar.width - 1, bar.height - 1), radius=24, fill=(14, 24, 39, 255))
    for idx, color in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        bar_draw.ellipse((18 + idx * 22, 18, 30 + idx * 22, 30), fill=color)
    bar_draw.text((110, 16), "WallCraft Pro", font=load_font(22, bold=True), fill=(229, 238, 252))
    canvas.alpha_composite(bar, (app_rect[0], app_rect[1]))

    sidebar = Image.new("RGBA", (140, app_rect[3] - app_rect[1] - 70), (10, 18, 29, 255))
    sidebar_draw = ImageDraw.Draw(sidebar)
    sidebar_draw.rounded_rectangle((0, 0, sidebar.width - 1, sidebar.height - 1), radius=22, fill=(10, 18, 29, 255))
    items = ["Source", "Preview", "Layouts", "Split", "Export"]
    for index, item in enumerate(items):
        top = 28 + index * 64
        fill = (92, 178, 255, 64) if index == 1 else None
        outline = (111, 193, 255, 90) if index == 1 else None
        if fill:
            sidebar_draw.rounded_rectangle((16, top - 10, sidebar.width - 16, top + 28), radius=14, fill=fill, outline=outline, width=1)
        sidebar_draw.text((28, top), item, font=tiny_font, fill=(230, 238, 252) if index == 1 else (142, 162, 189))
    canvas.alpha_composite(sidebar, (app_rect[0] + 16, app_rect[1] + 78))

    preview_box = (app_rect[0] + 176, app_rect[1] + 82, app_rect[2] - 18, app_rect[1] + 382)
    preview_size = (preview_box[2] - preview_box[0], preview_box[3] - preview_box[1])
    preview_img = contain(source, preview_size, (14, 22, 34))
    preview_overlay = Image.new("RGBA", preview_size, (0, 0, 0, 0))
    preview_overlay_draw = ImageDraw.Draw(preview_overlay)
    preview_overlay_draw.rounded_rectangle((0, 0, preview_size[0] - 1, preview_size[1] - 1), radius=24, outline=(138, 184, 235, 54), width=2)
    preview_img = Image.alpha_composite(preview_img.convert("RGBA"), preview_overlay)
    paste_rounded(canvas, preview_img.convert("RGB"), (preview_box[0], preview_box[1]), 24)

    chips = Image.new("RGBA", (preview_size[0], 74), (0, 0, 0, 0))
    chips_draw = ImageDraw.Draw(chips)
    chip_specs = [("Fit-inside", 0), ("3 ecrans", 150), ("No crop", 280)]
    for label, left in chip_specs:
        chips_draw.rounded_rectangle((left, 12, left + 126, 52), radius=18, fill=(16, 29, 46, 220), outline=(118, 164, 214, 55), width=1)
        chips_draw.text((left + 18, 24), label, font=tiny_font, fill=(225, 234, 248))
    canvas.alpha_composite(chips, (preview_box[0] + 18, preview_box[1] + preview_size[1] - 66))

    strip_y = app_rect[1] + 420
    strip_x = app_rect[0] + 176
    thumb_size = (160, 110)
    thumbs = wallpaper_slices(source, thumb_size, 3)
    for idx, thumb in enumerate(thumbs):
        thumb_rect = (strip_x + idx * 174, strip_y)
        thumb_card = contain(thumb, thumb_size, (13, 21, 32))
        paste_rounded(canvas, thumb_card, thumb_rect, 18)
        overlay = Image.new("RGBA", thumb_size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle((0, 0, thumb_size[0] - 1, thumb_size[1] - 1), radius=18, outline=(138, 184, 235, 46), width=2)
        canvas.alpha_composite(overlay, thumb_rect)
        text(draw, (thumb_rect[0] + 14, thumb_rect[1] + thumb_size[1] + 8), f"Ecran {idx + 1}", tiny_font, (150, 170, 195))

    note_box = (app_rect[0] + 176, app_rect[1] + 552, app_rect[2] - 18, app_rect[3] - 18)
    note = Image.new("RGBA", (note_box[2] - note_box[0], note_box[3] - note_box[1]), (12, 20, 32, 245))
    note_draw = ImageDraw.Draw(note)
    note_draw.rounded_rectangle((0, 0, note.width - 1, note.height - 1), radius=24, fill=(12, 20, 32, 245), outline=(138, 184, 235, 38), width=1)
    note_draw.text((22, 22), "Setup detecte", font=label_font, fill=(233, 240, 250))
    note_draw.text((22, 58), "3 x 16:9 | Split export | Wallpaper preview ready", font=body_font, fill=(156, 176, 201))
    canvas.alpha_composite(note, (note_box[0], note_box[1]))

    text(draw, (946, 246), "Resultat sur 3 ecrans", label_font, (231, 240, 255))
    text(draw, (946, 282), "Mockup d'un setup triple ecran avec la meme photo appliquee", body_font, (153, 171, 194))

    stage_rect = (942, 330, 1708, 968)
    draw_card(canvas, stage_rect, 28, (10, 17, 28, 245), (138, 184, 235, 44))

    wall = Image.new("RGBA", (stage_rect[2] - stage_rect[0], stage_rect[3] - stage_rect[1]), (8, 13, 20, 255))
    wall_draw = ImageDraw.Draw(wall)
    for y in range(0, wall.height, 24):
        wall_draw.line((0, y, wall.width, y), fill=(255, 255, 255, 7), width=1)
    canvas.alpha_composite(wall, (stage_rect[0], stage_rect[1]))

    monitor_inner = (218, 124)
    monitor_gap = 24
    monitor_top = stage_rect[1] + 120
    total_width = monitor_inner[0] * 3 + monitor_gap * 2
    start_x = stage_rect[0] + (stage_rect[2] - stage_rect[0] - total_width) // 2
    slices = wallpaper_slices(source, monitor_inner, 3)

    for idx, slice_img in enumerate(slices):
        outer_x = start_x + idx * (monitor_inner[0] + monitor_gap)
        outer_y = monitor_top
        outer_rect = (outer_x - 10, outer_y - 10, outer_x + monitor_inner[0] + 10, outer_y + monitor_inner[1] + 10)
        draw_card(canvas, outer_rect, 24, (6, 10, 16, 255), (180, 196, 219, 50))
        paste_rounded(canvas, slice_img, (outer_x, outer_y), 16)

        bezel = Image.new("RGBA", (monitor_inner[0], monitor_inner[1]), (0, 0, 0, 0))
        bezel_draw = ImageDraw.Draw(bezel)
        bezel_draw.rounded_rectangle((0, 0, monitor_inner[0] - 1, monitor_inner[1] - 1), radius=16, outline=(186, 198, 216, 32), width=2)
        canvas.alpha_composite(bezel, (outer_x, outer_y))

        stand = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        stand_draw = ImageDraw.Draw(stand)
        stand_draw.rounded_rectangle((48, 0, 72, 48), radius=12, fill=(26, 35, 48, 255))
        stand_draw.rounded_rectangle((18, 48, 102, 62), radius=8, fill=(36, 45, 60, 255))
        stand_draw.rounded_rectangle((34, 62, 86, 100), radius=10, fill=(28, 37, 50, 255))
        canvas.alpha_composite(stand, (outer_x + (monitor_inner[0] - 120) // 2, outer_y + monitor_inner[1] + 12))

    label_band = Image.new("RGBA", (430, 54), (14, 24, 39, 220))
    label_band_draw = ImageDraw.Draw(label_band)
    label_band_draw.rounded_rectangle((0, 0, label_band.width - 1, label_band.height - 1), radius=20, fill=(14, 24, 39, 220), outline=(138, 184, 235, 45), width=1)
    label_band_draw.text((22, 14), "Panorama applique en triple ecran | 5760 x 1080", font=tiny_font, fill=(229, 238, 252))
    canvas.alpha_composite(label_band, (stage_rect[0] + 166, stage_rect[3] - 114))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=95)
    return output_path


def ImageEnhance_like(image: Image.Image, brightness: float, saturation: float) -> Image.Image:
    gray = ImageOps.grayscale(image).convert("RGB")
    image = Image.blend(gray, image, saturation)
    dark = Image.new("RGB", image.size, (0, 0, 0))
    return Image.blend(dark, image, brightness)


def main() -> None:
    args = parse_args()
    source_path = Path(args.source_image).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not source_path.exists():
        raise SystemExit(f"Source image not found: {source_path}")

    result = build_mockup(source_path, output_path)
    print(result)


if __name__ == "__main__":
    main()
