"""
Images de la fiche Microsoft Store : docs/store/screenshots/<langue>/*.png et docs/store/logo-300.png

Reprend les captures du site (tools/make_screenshots.py) au format PNG demandé par Partner Center
(1366 × 768 minimum) ; la 4e capture montre la fenêtre « Fond automatique » sur la fenêtre principale.

    python tools/make_store_assets.py
"""
import os
import sys

from PIL import Image, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENS = os.path.join(ROOT, "site", "assets", "screens")
OUT = os.path.join(ROOT, "docs", "store")
LANGS = ("fr", "en", "es", "de")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_msix_assets import motif  # noqa: E402


def with_dialog(main_path, dialog_path):
    base = Image.open(main_path).convert("RGB")
    base = ImageEnhance.Brightness(base).enhance(0.45)
    dialog = Image.open(dialog_path).convert("RGB")
    dialog = dialog.resize((round(dialog.width * 1.25), round(dialog.height * 1.25)), Image.LANCZOS)
    x, y = (base.width - dialog.width) // 2, (base.height - dialog.height) // 2
    base.paste((90, 110, 140), (x - 2, y - 2, x + dialog.width + 2, y + dialog.height + 2))
    base.paste(dialog, (x, y))
    return base


def main():
    for lang in LANGS:
        src = os.path.join(SCREENS, lang)
        out = os.path.join(OUT, "screenshots", lang)
        os.makedirs(out, exist_ok=True)
        shots = {
            "1-composition.png": Image.open(os.path.join(src, "main.webp")).convert("RGB"),
            "2-apercu-ecrans.png": Image.open(os.path.join(src, "preview.webp")).convert("RGB"),
            "3-taille-reelle.png": Image.open(os.path.join(src, "main-real-size.webp")).convert("RGB"),
            "4-fond-automatique.png": with_dialog(os.path.join(src, "main.webp"), os.path.join(src, "automation.webp")),
        }
        for name, img in shots.items():
            assert img.width >= 1366 and img.height >= 768, (name, img.size)
            img.save(os.path.join(out, name), optimize=True)
    logo = Image.new("RGBA", (300, 300), (16, 20, 28, 255))
    icon = motif(300, margin=0.14)
    logo.paste(icon, (0, 0), icon)
    logo.save(os.path.join(OUT, "logo-300.png"), optimize=True)
    print("Images du Store dans", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
