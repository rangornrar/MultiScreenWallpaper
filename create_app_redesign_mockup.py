from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = Path(r"C:\Users\user\Downloads\Gemini_Generated_Image_t1k5lut1k5lut1k5.png")
OUTPUT = ROOT / "assets" / "wallcraft_app_redesign_concept.png"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\seguiemj.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf") if bold else Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\bahnschrift.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf") if bold else Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def contain(image: Image.Image, size: tuple[int, int], background: tuple[int, int, int]) -> Image.Image:
    target = Image.new("RGB", size, background)
    fitted = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    target.paste(fitted, (x, y))
    return target


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def paste_rounded(base: Image.Image, overlay: Image.Image, box: tuple[int, int], radius: int) -> None:
    base.paste(overlay, box, rounded_mask(overlay.size, radius))


def shadow(base: Image.Image, rect: tuple[int, int, int, int], radius: int, blur: int = 28, alpha: int = 110) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(rect, radius=radius, fill=(0, 0, 0, alpha))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def card(base: Image.Image, rect: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int, int], outline: tuple[int, int, int, int]) -> None:
    shadow(base, rect, radius)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=1)
    base.alpha_composite(layer)


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, font: ImageFont.ImageFont, active: bool = False) -> None:
    bbox = draw.textbbox((0, 0), label, font=font)
    w = bbox[2] - bbox[0] + 28
    fill = (92, 199, 255) if active else (24, 34, 48)
    outline = (130, 210, 255) if active else (49, 63, 84)
    text_fill = (8, 14, 24) if active else (186, 199, 220)
    draw.rounded_rectangle((x, y, x + w, y + 34), radius=16, fill=fill, outline=outline, width=1)
    draw.text((x + 14, y + 8), label, font=font, fill=text_fill)


def slices(image: Image.Image, size: tuple[int, int], count: int) -> list[Image.Image]:
    panorama = cover(image, (size[0] * count, size[1]))
    return [panorama.crop((i * size[0], 0, (i + 1) * size[0], size[1])) for i in range(count)]


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], content: str, font: ImageFont.ImageFont, fill: tuple[int, int, int], anchor: str | None = None) -> None:
    draw.text(xy, content, font=font, fill=fill, anchor=anchor)


def background(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    bg = cover(source, size).filter(ImageFilter.GaussianBlur(24))
    bg = Image.blend(Image.new("RGB", size, (5, 10, 18)), bg, 0.22)
    layer = Image.new("RGBA", size, (0, 0, 0, 255))
    layer.alpha_composite(bg.convert("RGBA"))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((120, -40, 820, 500), fill=(57, 148, 212, 38))
    glow_draw.ellipse((1100, 40, 1760, 760), fill=(54, 197, 222, 30))
    glow_draw.ellipse((600, 600, 1500, 1150), fill=(70, 116, 255, 18))
    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60)))
    return layer


def draw_slider(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, value: float, label: str, font_label: ImageFont.ImageFont, font_value: ImageFont.ImageFont) -> None:
    text(draw, (x, y), label, font_label, (154, 170, 191))
    text(draw, (x + width, y), f"{int(value * 100)}%", font_value, (228, 238, 251), anchor="ra")
    y += 28
    draw.rounded_rectangle((x, y, x + width, y + 8), radius=4, fill=(32, 43, 60))
    draw.rounded_rectangle((x, y, x + int(width * value), y + 8), radius=4, fill=(91, 198, 255))


def build() -> Path:
    source_path = DEFAULT_SOURCE if DEFAULT_SOURCE.exists() else ROOT / "assets" / "wallcraft_app_ui_1773221294829.png"
    source = Image.open(source_path).convert("RGB")

    canvas = background(source, (1800, 1120))
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(58, bold=True)
    subtitle_font = load_font(24)
    section_font = load_font(25, bold=True)
    body_font = load_font(22)
    body_small = load_font(18)
    chip_font = load_font(17, bold=True)
    tiny_font = load_font(16)

    text(draw, (72, 54), "WallCraft Pro Redesign Concept", title_font, (238, 244, 255))
    text(draw, (74, 126), "Direction: studio de composition moderne, futuriste et sobre", subtitle_font, (153, 173, 198))

    app_rect = (54, 180, 1746, 1038)
    card(canvas, app_rect, 34, (9, 14, 22, 232), (70, 92, 120, 110))

    topbar = (76, 202, 1724, 278)
    card(canvas, topbar, 26, (12, 18, 29, 240), (80, 104, 136, 90))
    text(draw, (104, 224), "WallCraft Pro", load_font(29, bold=True), (238, 244, 255))
    text(draw, (104, 254), "Project: Tropical panorama | 5760 x 1080 | 3 monitors detected", tiny_font, (140, 159, 182))
    chip(draw, 742, 223, "Fit inside", chip_font, active=False)
    chip(draw, 862, 223, "Maximum optimization", chip_font, active=True)
    chip(draw, 1086, 223, "Split export", chip_font, active=False)
    chip(draw, 1240, 223, "Apply", chip_font, active=False)
    draw.rounded_rectangle((1518, 218, 1692, 260), radius=20, fill=(96, 199, 255), outline=(146, 222, 255), width=1)
    text(draw, (1605, 229), "Apply Wallpaper", tiny_font, (8, 14, 24), anchor="ma")

    rail = (76, 298, 164, 1016)
    library = (180, 298, 474, 1016)
    stage = (492, 298, 1336, 784)
    output = (492, 802, 1336, 1016)
    inspector = (1354, 298, 1724, 1016)
    for rect, radius in [(rail, 26), (library, 28), (stage, 30), (output, 28), (inspector, 28)]:
        card(canvas, rect, radius, (12, 18, 29, 226), (70, 92, 120, 84))

    # Left rail
    icons = [
        ("Library", True),
        ("Canvas", False),
        ("Layouts", False),
        ("Output", False),
    ]
    y = rail[1] + 36
    for label, active in icons:
        fill = (91, 198, 255, 40) if active else (0, 0, 0, 0)
        outline = (122, 208, 255, 80) if active else (0, 0, 0, 0)
        if active:
            draw.rounded_rectangle((rail[0] + 12, y - 8, rail[0] + 76, y + 48), radius=18, fill=fill, outline=outline, width=1)
        draw.ellipse((rail[0] + 28, y + 2, rail[0] + 48, y + 22), fill=(91, 198, 255) if active else (77, 95, 118))
        text(draw, (rail[0] + 20, y + 32), label, tiny_font, (231, 240, 250) if active else (132, 150, 172))
        y += 118

    # Library panel
    text(draw, (204, 326), "Imported images", section_font, (235, 242, 252))
    text(draw, (206, 360), "2 images loaded", tiny_font, (143, 162, 185))
    draw.rounded_rectangle((348, 320, 448, 360), radius=18, fill=(24, 34, 48), outline=(58, 75, 98), width=1)
    text(draw, (398, 333), "+ Add", tiny_font, (228, 238, 251), anchor="ma")

    lib_card_1 = (198, 394, 456, 562)
    lib_card_2 = (198, 580, 456, 748)
    for idx, rect in enumerate((lib_card_1, lib_card_2), start=1):
        draw.rounded_rectangle(rect, radius=24, fill=(17, 25, 38), outline=(56, 72, 92), width=1)
        thumb = contain(source, (rect[2] - rect[0] - 24, 90), (15, 23, 34))
        paste_rounded(canvas, thumb, (rect[0] + 12, rect[1] + 12), 18)
        text(draw, (rect[0] + 16, rect[1] + 118), f"Beach panorama {idx}", body_small, (233, 241, 251))
        text(draw, (rect[0] + 16, rect[1] + 144), "Fit inside | unlocked", tiny_font, (142, 160, 183))
        draw.rounded_rectangle((rect[0] + 16, rect[1] + 168, rect[0] + 98, rect[1] + 196), radius=12, fill=(25, 39, 57), outline=(56, 72, 92), width=1)
        text(draw, (rect[0] + 57, rect[1] + 176), "Selected" if idx == 1 else "Ready", load_font(14, bold=True), (93, 200, 255) if idx == 1 else (180, 190, 204), anchor="ma")

    helper = (198, 770, 456, 982)
    draw.rounded_rectangle(helper, radius=24, fill=(14, 22, 34), outline=(56, 72, 92), width=1)
    text(draw, (216, 794), "Workflow", body_font, (234, 241, 251))
    bullets = [
        "1. Import images",
        "2. Choose a layout strategy",
        "3. Adjust inside the stage",
        "4. Split and apply",
    ]
    by = 832
    for bullet in bullets:
        draw.ellipse((216, by + 8, 224, by + 16), fill=(91, 198, 255))
        text(draw, (236, by), bullet, tiny_font, (148, 166, 187))
        by += 34

    # Stage
    text(draw, (520, 324), "Composition stage", section_font, (235, 242, 252))
    text(draw, (522, 358), "Center view with overlays, snap hints and floating tools", tiny_font, (143, 162, 185))
    tool_x = 1102
    chip(draw, tool_x, 320, "Move", chip_font, active=True)
    chip(draw, tool_x + 92, 320, "Crop", chip_font, active=False)

    stage_area = (520, 394, 1308, 738)
    draw.rounded_rectangle(stage_area, radius=26, fill=(7, 12, 20), outline=(43, 60, 80), width=1)
    for x in range(stage_area[0] + 22, stage_area[2], 34):
        draw.line((x, stage_area[1], x, stage_area[3]), fill=(255, 255, 255, 10))
    for y_line in range(stage_area[1] + 22, stage_area[3], 34):
        draw.line((stage_area[0], y_line, stage_area[2], y_line), fill=(255, 255, 255, 10))

    stage_preview = contain(source, (680, 160), (8, 12, 20))
    paste_rounded(canvas, stage_preview, (574, 474), 18)
    overlay_y = 468
    for i in range(3):
        left = 560 + i * 234
        top = overlay_y if i != 1 else overlay_y - 10
        right = left + 224
        bottom = top + 178
        draw.rounded_rectangle((left, top, right, bottom), radius=22, outline=(255, 105, 124), width=2)
        text(draw, (left + 16, top + 14), f"Screen {i + 1}", tiny_font, (255, 150, 160))

    toolbar = (676, 676, 1152, 722)
    draw.rounded_rectangle(toolbar, radius=22, fill=(14, 22, 34, 245), outline=(64, 80, 102), width=1)
    chip(draw, toolbar[0] + 14, toolbar[1] + 6, "Auto arrange", chip_font, active=False)
    chip(draw, toolbar[0] + 152, toolbar[1] + 6, "Snap on", chip_font, active=True)
    chip(draw, toolbar[0] + 258, toolbar[1] + 6, "Monitors", chip_font, active=False)

    # Output dock
    text(draw, (520, 826), "Output preview", section_font, (235, 242, 252))
    text(draw, (522, 860), "Live monitor result and export targets", tiny_font, (143, 162, 185))
    out_slices = slices(source, (214, 120), 3)
    start_x = 544
    for idx, piece in enumerate(out_slices):
        ox = start_x + idx * 242
        oy = 894
        shadow(canvas, (ox - 8, oy - 8, ox + 222, oy + 132), 20, blur=16, alpha=80)
        draw.rounded_rectangle((ox - 8, oy - 8, ox + 222, oy + 132), radius=20, fill=(5, 9, 15), outline=(70, 92, 120), width=1)
        paste_rounded(canvas, piece, (ox, oy), 14)
        text(draw, (ox + 107, oy + 140), f"Display {idx + 1}", tiny_font, (138, 157, 180), anchor="ma")
    draw.rounded_rectangle((1220, 884, 1304, 924), radius=18, fill=(24, 34, 48), outline=(56, 72, 92), width=1)
    text(draw, (1262, 898), "Split", tiny_font, (228, 238, 251), anchor="ma")
    draw.rounded_rectangle((1220, 934, 1304, 974), radius=18, fill=(91, 198, 255), outline=(132, 214, 255), width=1)
    text(draw, (1262, 948), "Apply", tiny_font, (8, 14, 24), anchor="ma")

    # Inspector
    text(draw, (1382, 326), "Inspector", section_font, (235, 242, 252))
    text(draw, (1384, 360), "Contextual controls for the selected image", tiny_font, (143, 162, 185))

    sections = [
        (396, "Selected image"),
        (582, "Transform"),
        (770, "Layout strategy"),
        (924, "Export"),
    ]
    for top, label in sections:
        draw.rounded_rectangle((1376, top, 1702, top + 150), radius=22, fill=(14, 22, 34), outline=(56, 72, 92), width=1)
        text(draw, (1396, top + 18), label, body_font, (233, 241, 251))

    thumb = contain(source, (110, 58), (14, 22, 34))
    paste_rounded(canvas, thumb, (1398, 434), 14)
    text(draw, (1526, 432), "Beach panorama", body_small, (232, 240, 250))
    text(draw, (1526, 460), "2048 x 375", tiny_font, (145, 164, 187))
    chip(draw, 1510, 478, "Active", load_font(14, bold=True), active=True)

    draw_slider(draw, 1398, 620, 276, 0.55, "Scale", tiny_font, tiny_font)
    draw_slider(draw, 1398, 680, 276, 0.34, "Offset X", tiny_font, tiny_font)
    draw_slider(draw, 1398, 740, 276, 0.62, "Offset Y", tiny_font, tiny_font)

    chip(draw, 1398, 798, "Maximum optimization", tiny_font, active=True)
    chip(draw, 1398, 842, "Preserve full image", tiny_font, active=False)
    chip(draw, 1398, 886, "No crop", tiny_font, active=False)

    draw.rounded_rectangle((1398, 952, 1674, 992), radius=18, fill=(24, 34, 48), outline=(56, 72, 92), width=1)
    text(draw, (1536, 965), "Export PNG by monitor", tiny_font, (228, 238, 251), anchor="ma")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(OUTPUT, quality=95)
    return OUTPUT


if __name__ == "__main__":
    print(build())
