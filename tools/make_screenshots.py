"""
Captures d'écran du site (site/assets/screens/<langue>/*.webp) prises sur la vraie application Python,
dans les 4 langues, avec des images de démonstration générées (aucune photo réelle).

Sous Linux : xvfb-run -a -s "-screen 0 1920x1080x24" python3 tools/make_screenshots.py
La police « Segoe UI » de Windows est remplacée par Inter (fontconfig) pour un rendu proche.
"""
import os
import random
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "python")
OUT = os.path.join(ROOT, "site", "assets", "screens")
LANGS = ("fr", "en", "es", "de")
WINDOW = (1600, 940)


def setup_fonts(tmp):
    """Alias fontconfig : Segoe UI → Inter, Segoe UI Semibold → Inter SemiBold."""
    conf = os.path.join(tmp, "fonts.conf")
    with open(conf, "w", encoding="utf-8") as f:
        f.write("""<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>
<include ignore_missing="yes">/etc/fonts/fonts.conf</include>
<match target="pattern"><test name="family"><string>Segoe UI</string></test>
<edit name="family" mode="assign" binding="strong"><string>Inter</string></edit></match>
<match target="pattern"><test name="family"><string>Segoe UI Semibold</string></test>
<edit name="family" mode="assign" binding="strong"><string>Inter</string></edit>
<edit name="weight" mode="assign" binding="strong"><const>semibold</const></edit></match>
</fontconfig>""")
    os.environ["FONTCONFIG_FILE"] = conf


# --- Images de démonstration (paysages générés, déterministes) ---

def _ridge(rng, width, base, amplitude, roughness):
    """Ligne de crête par déplacement du point médian."""
    n = 1
    pts = [base + rng.uniform(-amplitude, amplitude), base + rng.uniform(-amplitude, amplitude)]
    amp = amplitude
    while n < width // 4:
        new = []
        for a, b in zip(pts, pts[1:]):
            new += [a, (a + b) / 2 + rng.uniform(-amp, amp)]
        new.append(pts[-1])
        pts, n, amp = new, n * 2, amp * roughness
    return [pts[int(i * (len(pts) - 1) / (width - 1))] for i in range(width)]


def landscape(size, sky_top, sky_bottom, layers, seed, sun=None, stars=False):
    from PIL import Image, ImageDraw, ImageFilter
    w, h = size
    rng = random.Random(seed)
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(sky_top, sky_bottom)))
    if stars:
        for _ in range(w * h // 2500):
            x, y = rng.randrange(w), rng.randrange(int(h * 0.6))
            v = rng.randrange(150, 255)
            d.point((x, y), fill=(v, v, v))
    if sun:
        (sx, sy, r, color) = sun
        glow = Image.new("RGB", size, (0, 0, 0))
        ImageDraw.Draw(glow).ellipse([sx * w - r * 3, sy * h - r * 3, sx * w + r * 3, sy * h + r * 3], fill=color)
        glow = glow.filter(ImageFilter.GaussianBlur(r * 1.5))
        img = Image.blend(img, Image.composite(glow, img, glow.convert("L")), 0.6)
        d = ImageDraw.Draw(img)
        d.ellipse([sx * w - r, sy * h - r, sx * w + r, sy * h + r], fill=color)
    for base, amp, rough, color in layers:
        ridge = _ridge(rng, w, base * h, amp * h, rough)
        d.polygon([(0, h)] + [(x, ridge[x]) for x in range(w)] + [(w, h)], fill=color)
    return img


def demo_images(folder):
    from PIL import ImageDraw
    specs = [
        ("coucher-de-soleil.jpg", (4000, 2250), (40, 30, 90), (250, 150, 90),
         [(0.55, 0.08, 0.55, (90, 50, 90)), (0.68, 0.06, 0.5, (60, 35, 70)), (0.8, 0.05, 0.5, (30, 20, 40))], 1, (0.7, 0.5, 90, (255, 220, 150)), False),
        ("montagnes-bleues.jpg", (3600, 2400), (120, 170, 220), (220, 235, 245),
         [(0.45, 0.12, 0.55, (140, 160, 190)), (0.6, 0.1, 0.5, (90, 115, 150)), (0.78, 0.07, 0.5, (50, 70, 100))], 2, None, False),
        ("nuit-etoilee.jpg", (2400, 3600), (8, 12, 35), (40, 60, 110),
         [(0.7, 0.05, 0.6, (20, 25, 45)), (0.85, 0.04, 0.5, (8, 10, 20))], 3, (0.3, 0.2, 70, (240, 240, 220)), True),
        ("dunes.jpg", (3000, 2000), (230, 170, 110), (250, 220, 170),
         [(0.55, 0.06, 0.45, (220, 140, 80)), (0.7, 0.05, 0.45, (190, 110, 60)), (0.85, 0.04, 0.4, (150, 80, 45))], 4, (0.25, 0.3, 60, (255, 245, 210)), False),
        ("foret-brume.jpg", (3200, 2000), (170, 200, 190), (230, 240, 230),
         [(0.5, 0.05, 0.7, (120, 150, 140)), (0.62, 0.06, 0.75, (70, 105, 95)), (0.8, 0.05, 0.75, (30, 55, 50))], 5, None, False),
    ]
    paths = []
    for name, size, top, bottom, layers, seed, sun, stars in specs:
        p = os.path.join(folder, name)
        landscape(size, top, bottom, layers, seed, sun, stars).save(p, quality=90)
        paths.append(p)
    # Petite image (900×600) : déclenche l'alerte « basse résolution » une fois agrandie
    small = landscape((900, 600), (60, 110, 160), (180, 210, 230),
                      [(0.6, 0.08, 0.5, (40, 90, 70)), (0.8, 0.05, 0.5, (20, 60, 45))], 6)
    ImageDraw.Draw(small).ellipse([620, 90, 700, 170], fill=(255, 240, 200))
    p = os.path.join(folder, "petite-image.jpg")
    small.save(p, quality=90)
    paths.append(p)
    return paths


# --- Pilotage de l'application ---

MONITORS = [  # la configuration réelle de test : Philips 23″ + deux iiyama 24,5″
    {"x": -3840, "y": 0, "width": 1920, "height": 1080, "name": "\\\\.\\DISPLAY2", "hw_id": "PHLC069#a", "width_mm": 509.0, "height_mm": 286.0},
    {"x": -1920, "y": 0, "width": 1920, "height": 1080, "name": "\\\\.\\DISPLAY3", "hw_id": "IVM6132#b", "width_mm": 544.0, "height_mm": 303.0},
    {"x": 0, "y": 0, "width": 1920, "height": 1080, "name": "\\\\.\\DISPLAY1", "hw_id": "IVM6132#c", "width_mm": 544.0, "height_mm": 303.0},
]


def main():
    tmp = tempfile.mkdtemp()
    setup_fonts(tmp)
    os.environ["LOCALAPPDATA"] = os.path.join(tmp, "appdata")
    sys.path.insert(0, APP)
    os.chdir(APP)

    from PIL import ImageGrab
    import tkinter as tk
    import locales
    import screen_splitter
    import ui
    import ui_automation as UA

    screen_splitter.get_monitor_layout = lambda: [dict(m) for m in MONITORS]
    UA.get_monitor_layout = screen_splitter.get_monitor_layout
    UA.enrich_with_physical_size = lambda ms: ms
    for name in ("showinfo", "showwarning", "showerror"):
        setattr(ui.messagebox, name, lambda *a, **k: None)

    photos = demo_images(tmp)

    def grab(root, path, extra=()):
        """Capture la fenêtre (et ses dialogues), enregistrée en WebP."""
        for _ in range(5):
            root.update()
            time.sleep(0.15)
        boxes = [(root.winfo_rootx(), root.winfo_rooty(), root.winfo_rootx() + root.winfo_width(), root.winfo_rooty() + root.winfo_height())]
        for w in extra:
            boxes = [(w.winfo_rootx(), w.winfo_rooty(), w.winfo_rootx() + w.winfo_width(), w.winfo_rooty() + w.winfo_height())]
        x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
        x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1), xdisplay=os.environ["DISPLAY"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path, "WEBP", quality=88, method=6)
        print(os.path.relpath(path, ROOT), img.size)

    import shutil
    for lang in LANGS:
        # Réglages remis à zéro pour chaque langue (la capture « taille réelle » de la langue précédente
        # ne doit pas rester activée)
        shutil.rmtree(os.environ["LOCALAPPDATA"], ignore_errors=True)
        locales.set_language(lang)
        root = tk.Tk()
        root.geometry(f"{WINDOW[0]}x{WINDOW[1]}+0+0")
        app = ui.WallpaperApp(root)
        app.lang_var.set(lang)
        app.on_lang_changed()
        out = os.path.join(OUT, lang)

        ui.askopenfilenames = lambda **k: photos
        app.cmd_add_images()
        app.combo_layout.current(app._layout_ids.index("layout_optimal"))
        app._fill = True
        app._refresh_view_buttons()
        app.cmd_autofill()
        low = next(i for i, im in enumerate(app.images) if "petite" in im.path)
        app._select_image(low)
        app._user_zoomed = False
        app._auto_fit()
        grab(root, os.path.join(out, "main.webp"))

        app.set_view("preview")
        grab(root, os.path.join(out, "preview.webp"))
        app.set_view("compose")

        # Fenêtre « Taille réelle des écrans »
        holder = {}
        orig = UA.PhysicalDialog
        UA.PhysicalDialog = lambda *a, **k: holder.setdefault("d", orig(*a, **k))
        app.cmd_physical()
        d = holder["d"]
        d.enabled.set(True)
        grab(root, os.path.join(out, "real-size.webp"), extra=[d.win])
        d.ok()
        UA.PhysicalDialog = orig
        app._user_zoomed = False
        app._auto_fit()
        grab(root, os.path.join(out, "main-real-size.webp"))

        # Fenêtre « Fond automatique »
        holder = {}
        orig = UA.AutoDialog
        UA.AutoDialog = lambda *a, **k: holder.setdefault("d", orig(*a, **k))
        app.cmd_auto_prefs()
        grab(root, os.path.join(out, "automation.webp"), extra=[holder["d"].win])
        holder["d"].win.destroy()
        UA.AutoDialog = orig

        # Variantes (calcul en arrière-plan, puis fenêtre de choix)
        holder = {}
        orig = ui.VariantsDialog
        ui.VariantsDialog = lambda *a, **k: holder.setdefault("d", orig(*a, **k))
        app.cmd_variants()
        deadline = time.time() + 60
        while "d" not in holder and time.time() < deadline:
            root.update()
            time.sleep(0.05)
        grab(root, os.path.join(out, "variants.webp"), extra=[holder["d"].win])
        holder["d"].win.destroy()
        ui.VariantsDialog = orig

        try:
            app.quit_app()
        except Exception:
            root.destroy()

    # Résultat sur le bureau : la composition HD découpée sur trois écrans dessinés (sans texte)
    desk(photos)


def desk(photos):
    """Illustration « le résultat sur trois écrans », indépendante de la langue."""
    from PIL import Image, ImageDraw, ImageFilter
    from image_tools import AutoLayoutStrategy, compose_wallpaper_contain, load_images_from_paths
    images = load_images_from_paths(photos[:5], [])
    AutoLayoutStrategy.apply("layout_optimal", 5760, 1080, images, fill=True)
    final = compose_wallpaper_contain((5760, 1080), images, (0, 0, 0))
    W, H = 2400, 760
    canvas = Image.new("RGB", (W, H), (11, 16, 26))
    d = ImageDraw.Draw(canvas)
    scale = 0.36
    sw, sh = int(1920 * scale), int(1080 * scale)
    gap = 26
    x0 = (W - 3 * sw - 2 * gap) // 2
    y0 = 90
    for i in range(3):
        x = x0 + i * (sw + gap)
        shadow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(shadow).rounded_rectangle([x - 10, y0 + 30, x + sw + 10, y0 + sh + 60], 18, fill=150)
        canvas.paste((0, 0, 0), mask=shadow.filter(ImageFilter.GaussianBlur(24)))
        d.rounded_rectangle([x - 12, y0 - 12, x + sw + 12, y0 + sh + 12], 14, fill=(24, 28, 36), outline=(52, 60, 74), width=2)
        piece = final.crop((1920 * i, 0, 1920 * (i + 1), 1080)).resize((sw, sh), Image.LANCZOS)
        canvas.paste(piece, (x, y0))
        cx = x + sw // 2
        d.rectangle([cx - 18, y0 + sh + 12, cx + 18, y0 + sh + 120], fill=(36, 41, 52))
        d.rounded_rectangle([cx - 110, y0 + sh + 116, cx + 110, y0 + sh + 134], 8, fill=(44, 50, 63))
    d.rectangle([0, y0 + sh + 134, W, H], fill=(16, 22, 34))
    path = os.path.join(OUT, "desk.webp")
    canvas.save(path, "WEBP", quality=88, method=6)
    print(os.path.relpath(path, ROOT), canvas.size)
    # Image de partage (réseaux sociaux) : 1200 × 630, en PNG pour être lue partout
    og = Image.new("RGB", (1200, 630), (11, 16, 26))
    small = canvas.resize((1200, int(1200 * canvas.height / canvas.width)), Image.LANCZOS)
    og.paste(small, (0, (630 - small.height) // 2))
    og_path = os.path.join(OUT, "og-image.png")
    og.save(og_path, optimize=True)
    print(os.path.relpath(og_path, ROOT), og.size)


if __name__ == "__main__":
    main()
