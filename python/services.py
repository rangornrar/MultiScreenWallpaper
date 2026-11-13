# services.py
"""
Ce qui fait vivre WallCraft après le clic sur « Appliquer » :

- ConfigStore : un fond mémorisé par configuration d'écrans (portable seul, sur sa station, etc.) ;
- Watcher : réapplique le bon fond quand les écrans changent, ou quand Windows a remis
  un thème (synchronisation du compte, mise à jour) ;
- rotation d'images depuis un dossier ;
- icône dans la zone de notification (pystray) et lancement au démarrage (registre HKCU\\...\\Run).

Aucune de ces fonctions n'appelle Tk : l'interface les pilote depuis son propre thread.
"""
import glob
import json
import os
import random
import sys
import time

from display_geometry import layout_signature

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "WallCraft"


def app_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(base, "WallCraft")
    os.makedirs(path, exist_ok=True)
    return path


# --- Un fond par configuration d'écrans ---

class ConfigStore:
    """configs/<empreinte>/ contient les images par écran et un manifest.json."""

    def __init__(self, root=None):
        self.root = root or os.path.join(app_data_dir(), "configs")
        os.makedirs(self.root, exist_ok=True)

    def dir_for(self, monitors):
        path = os.path.join(self.root, layout_signature(monitors))
        os.makedirs(path, exist_ok=True)
        return path

    def save(self, monitors, results, keep_prefix):
        """Enregistre le manifest des fichiers appliqués et supprime les anciens fichiers de cette configuration."""
        folder = self.dir_for(monitors)
        manifest = {
            "signature": layout_signature(monitors),
            "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "screens": [{"x": m["x"], "y": m["y"], "width": m["width"], "height": m["height"],
                         "name": m.get("name", ""), "file": os.path.basename(path)} for m, path in results],
        }
        with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        for old in glob.glob(os.path.join(folder, "wallcraft_*")):
            if not os.path.basename(old).startswith(keep_prefix):
                try:
                    os.remove(old)
                except OSError:
                    pass

    def _manifest_path(self, monitors):
        return os.path.join(self.root, layout_signature(monitors), "manifest.json")

    def release(self, monitors):
        """L'utilisateur a choisi un autre fond : plus de réapplication automatique pour cette configuration."""
        path = self._manifest_path(monitors)
        try:
            with open(path, encoding="utf-8") as f:
                manifest = json.load(f)
            manifest["released"] = True
            with open(path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except (OSError, ValueError):
            pass

    def is_released(self, monitors):
        try:
            with open(self._manifest_path(monitors), encoding="utf-8") as f:
                return bool(json.load(f).get("released"))
        except (OSError, ValueError):
            return False

    def load(self, monitors):
        """Retourne [(moniteur, chemin)] mémorisés pour cette configuration, ou []."""
        folder = os.path.join(self.root, layout_signature(monitors))
        try:
            with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, ValueError):
            return []
        results = []
        for s in manifest.get("screens", []):
            path = os.path.join(folder, s.get("file", ""))
            if os.path.isfile(path):
                results.append(({k: s[k] for k in ("x", "y", "width", "height", "name") if k in s}, path))
        return results


THEME_MARKERS = (
    "/microsoft/windows/themes/",  # thèmes et synchronisation du compte
    "transcodedwallpaper",
    "/windows/web/",               # fonds fournis par Windows
    "spotlight", "contentdeliverymanager",  # Windows à la une
)


def is_theme_wallpaper(path):
    """True si le fichier vient d'un thème Windows (et non d'un choix de l'utilisateur)."""
    if not path:
        return True
    low = path.replace("\\", "/").lower()
    return any(marker in low for marker in THEME_MARKERS)


def wallpaper_change(expected_paths, current):
    """
    Compare les fonds actuels à ceux appliqués par WallCraft :
    - None : rien n'a changé ;
    - "theme" : Windows a remis un thème (synchronisation, mise à jour) → réappliquer ;
    - "user" : l'utilisateur a choisi un autre fond → ne plus y toucher.
    `current` = résultat de screen_splitter.get_current_wallpapers().
    """
    if not expected_paths or not current:
        return None
    expected = {os.path.normcase(os.path.abspath(p)) for p in expected_paths}
    replaced = [c.get("path", "") for c in current
                if os.path.normcase(os.path.abspath(c.get("path") or "")) not in expected]
    if not replaced:
        return None
    return "theme" if all(is_theme_wallpaper(p) for p in replaced) else "user"


def wallpaper_was_replaced(expected_paths, current):
    """Compatibilité : True si au moins un écran n'affiche plus un fichier appliqué par WallCraft."""
    return wallpaper_change(expected_paths, current) is not None


# --- Rotation ---

def list_images(folder):
    if not folder or not os.path.isdir(folder):
        return []
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTENSIONS)]
    return sorted(files)


def pick_rotation(files, count, previous=(), rng=None):
    """Tire `count` images en évitant celles de la rotation précédente quand c'est possible."""
    rng = rng or random.Random()
    pool = [f for f in files if f not in set(previous)]
    if len(pool) < count:
        pool = list(files)
    return rng.sample(pool, min(count, len(pool)))


# --- Démarrage avec Windows ---

def autostart_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --tray'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pythonw if os.path.isfile(pythonw) else sys.executable
    main = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{exe}" "{main}" --tray'


def get_autostart():
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except OSError:
        return False


def set_autostart(enabled):
    if sys.platform != "win32":
        return False
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    return True


# --- Icône de notification ---

def tray_icon_image(size=64):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 64
    colors = [(138, 180, 248), (120, 212, 160), (255, 196, 110)]
    for i, c in enumerate(colors):
        x0 = (4 + i * 19) * s
        d.rounded_rectangle([x0, 18 * s, x0 + 17 * s, 40 * s], radius=3 * s, fill=c)
    d.rectangle([28 * s, 42 * s, 36 * s, 50 * s], fill=(200, 210, 225))
    d.rectangle([20 * s, 50 * s, 44 * s, 54 * s], fill=(200, 210, 225))
    return img


class TrayIcon:
    """
    Icône pystray dans son propre thread. Les clics sont transmis à `post(action)`,
    que l'interface relaie vers le thread Tk (file d'attente).
    `state()` renvoie un dict de cases cochées : rotation, keep, autostart.
    """

    def __init__(self, texts, post, state):
        self.texts, self.post, self.state = texts, post, state
        self.icon = None

    def start(self):
        try:
            import pystray
        except Exception:
            return False
        t, post, state = self.texts, self.post, self.state

        def item(label, action, checked=None, default=False):
            return pystray.MenuItem(label, lambda *_: post(action), checked=checked, default=default)

        menu = pystray.Menu(
            item(t["open"], "open", default=True),
            item(t["reapply"], "reapply"),
            item(t["next"], "next"),
            pystray.Menu.SEPARATOR,
            item(t["rotation"], "toggle_rotation", checked=lambda _: state().get("rotation", False)),
            item(t["keep"], "toggle_keep", checked=lambda _: state().get("keep", False)),
            item(t["autostart"], "toggle_autostart", checked=lambda _: state().get("autostart", False)),
            pystray.Menu.SEPARATOR,
            item(t["quit"], "quit"),
        )
        self.icon = pystray.Icon(APP_NAME, tray_icon_image(), "WallCraft", menu)
        self.icon.run_detached()
        return True

    def refresh(self):
        if self.icon:
            try:
                self.icon.update_menu()
            except Exception:
                pass

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None


# --- Rendu et application ---

def render_and_apply(images, size, monitors, bg, store):
    """
    Rendu HD, découpe par écran, application Windows, puis mémorisation pour cette configuration.
    Retourne (statut, erreurs, résultats) avec statut parmi ok, partial, span, failed, no_monitors.
    À appeler hors du thread Tk.
    """
    from PIL import Image
    from image_tools import compose_wallpaper_contain
    from screen_splitter import set_multi_wallpaper_windows, set_wallpaper_span, split_wallpaper_by_monitors

    final = compose_wallpaper_contain(size, images, bg)
    out_dir = store.dir_for(monitors)
    # Nom unique à chaque application : Windows ne garde pas en cache une ancienne version.
    prefix = "wallcraft_" + time.strftime("%Y%m%d-%H%M%S")
    results = split_wallpaper_by_monitors(final, monitors, out_dir, prefix)
    if not results:
        return "no_monitors", [], []
    ok, errors, applied = set_multi_wallpaper_windows(results, bg)
    if ok:
        store.save(monitors, results, prefix)  # supprime les anciens fichiers seulement après succès
        return "ok", [], results
    if applied > 0:
        # Au moins un écran a reçu son image : on signale sans basculer en panorama.
        return "partial", errors, results
    # Repli « Étendre » : une seule image à la géométrie du bureau Windows, reconstruite
    # depuis les images par écran (juste aussi en mode taille réelle).
    x0 = min(m["x"] for m in monitors); y0 = min(m["y"] for m in monitors)
    x1 = max(m["x"] + m["width"] for m in monitors); y1 = max(m["y"] + m["height"] for m in monitors)
    span = Image.new("RGB", (x1 - x0, y1 - y0), bg)
    for m, path in results:
        with Image.open(path) as piece:
            span.paste(piece.convert("RGB"), (m["x"] - x0, m["y"] - y0))
    span_path = os.path.join(out_dir, prefix + "_span.png")
    span.save(span_path, "PNG")
    if set_wallpaper_span(span_path):
        store.save(monitors, results, prefix)
        return "span", errors, results
    return "failed", errors, results
