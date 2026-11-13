"""
Icônes du paquet MSIX (Microsoft Store) : python/msix/Assets/*.png

Même motif que l'icône de la zone de notification (trois écrans et un pied), dessiné
en grand puis réduit pour rester net à chaque taille demandée par Windows.

    python tools/make_msix_assets.py
"""
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python", "msix", "Assets")
COLORS = [(138, 180, 248), (120, 212, 160), (255, 196, 110)]
STAND = (200, 210, 225)


def motif(size, margin=0.08):
    """Trois écrans et un pied, centrés dans un carré transparent de `size` px."""
    k = 8
    big = size * k
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = big * margin
    w = big - 2 * m
    gap = w * 0.05
    sw = (w - 2 * gap) / 3
    sh = sw * 0.62                      # écrans en paysage
    top = (big - (sh + w * 0.21)) / 2   # motif centré verticalement, pied compris
    for i, c in enumerate(COLORS):
        x0 = m + i * (sw + gap)
        d.rounded_rectangle([x0, top, x0 + sw, top + sh], radius=sw * 0.14, fill=c)
    cx = big / 2
    d.rectangle([cx - w * 0.06, top + sh + w * 0.03, cx + w * 0.06, top + sh + w * 0.15], fill=STAND)
    d.rounded_rectangle([cx - w * 0.2, top + sh + w * 0.15, cx + w * 0.2, top + sh + w * 0.21],
                        radius=w * 0.02, fill=STAND)
    return img.resize((size, size), Image.LANCZOS)


def wide(width, height):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    icon = motif(height)
    img.paste(icon, ((width - height) // 2, 0), icon)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {}
    for scale in (100, 200):
        f = scale / 100
        files[f"StoreLogo.scale-{scale}.png"] = motif(round(50 * f))
        files[f"Square44x44Logo.scale-{scale}.png"] = motif(round(44 * f))
        files[f"Square150x150Logo.scale-{scale}.png"] = motif(round(150 * f), margin=0.2)
        files[f"Wide310x150Logo.scale-{scale}.png"] = wide(round(310 * f), round(150 * f))
    # Barre des tâches, menu Démarrer, Paramètres : tailles exactes, sans plaque de couleur.
    for size in (16, 24, 32, 48, 256):
        files[f"Square44x44Logo.targetsize-{size}.png"] = motif(size, margin=0.02)
        files[f"Square44x44Logo.targetsize-{size}_altform-unplated.png"] = motif(size, margin=0.02)
    for name, img in files.items():
        img.save(os.path.join(OUT, name), optimize=True)
    print(f"{len(files)} icônes dans {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
