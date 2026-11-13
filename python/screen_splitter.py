# screen_splitter.py
import contextlib
import ctypes
import os
import sys

from PIL import Image

# On essaie d'importer screeninfo, sinon on fera sans
try:
    from screeninfo import get_monitors as _get_monitors
except ImportError:
    _get_monitors = None

IS_WINDOWS = sys.platform == "win32"

# --- STRUCTURES WINDOWS (Low Level) ---

class GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8)]

    def __init__(self, name):
        import uuid
        u = uuid.UUID(name)
        self.Data1 = u.time_low
        self.Data2 = u.time_mid
        self.Data3 = u.time_hi_version
        self.Data4 = (ctypes.c_ubyte * 8)(*u.bytes[8:])

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]

CLSID_DesktopWallpaper = GUID("{C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD}")
IID_IDesktopWallpaper  = GUID("{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}")

DWPOS_FILL = 4
DWPOS_SPAN = 5

_FUNC = ctypes.WINFUNCTYPE if IS_WINDOWS else ctypes.CFUNCTYPE

# VTable d'IDesktopWallpaper (ordre exact de shobjidl_core.h)
class IDesktopWallpaperVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))),
        ("AddRef", _FUNC(ctypes.c_ulong, ctypes.c_void_p)),
        ("Release", _FUNC(ctypes.c_ulong, ctypes.c_void_p)),
        ("SetWallpaper", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p)),
        ("GetWallpaper", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p))),
        # Les chaînes rendues sont allouées par CoTaskMemAlloc : on les reçoit en pointeur brut pour les libérer.
        ("GetMonitorDevicePathAt", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p))),
        ("GetMonitorDevicePathCount", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint))),
        ("GetMonitorRECT", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(RECT))),
        ("SetBackgroundColor", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.c_ulong)),
        ("GetBackgroundColor", ctypes.c_void_p),
        ("SetPosition", _FUNC(ctypes.c_long, ctypes.c_void_p, ctypes.c_int)),
    ]

class IDesktopWallpaper(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(IDesktopWallpaperVtbl))]

# --- DPI ---

@contextlib.contextmanager
def per_monitor_dpi():
    """
    Passe temporairement le thread en DPI « Per-Monitor V2 » (Windows 10 1703+) pour que
    les coordonnées des écrans soient en pixels physiques, même si l'interface reste
    « system aware ». Sans effet hors Windows ou sur les anciennes versions.
    """
    previous = None
    setter = None
    if IS_WINDOWS:
        try:
            setter = ctypes.windll.user32.SetThreadDpiAwarenessContext
            setter.restype = ctypes.c_void_p
            setter.argtypes = [ctypes.c_void_p]
            previous = setter(ctypes.c_void_p(-4))  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        except (AttributeError, OSError):
            setter = None
    try:
        yield
    finally:
        if setter and previous:
            setter(ctypes.c_void_p(previous))

# --- FONCTIONS UTILITAIRES ---

def get_monitor_layout():
    """Récupère la configuration réelle des écrans via screeninfo, en pixels physiques."""
    monitors = []
    if _get_monitors is None: return monitors
    try:
        with per_monitor_dpi():
            found = list(_get_monitors())
        for m in found:
            monitors.append({
                "x": int(getattr(m, "x", 0)),
                "y": int(getattr(m, "y", 0)),
                "width": int(getattr(m, "width", 0)),
                "height": int(getattr(m, "height", 0)),
                "name": getattr(m, "name", "monitor") or "monitor",
                "device_id": getattr(m, "name", "") or "",
            })
        # Tri gauche -> droite puis haut -> bas, stable même pour des écrans empilés
        monitors.sort(key=lambda m: (m["x"], m["y"]))
    except Exception:
        return []
    return monitors

def virtual_desktop_bbox(monitors):
    if not monitors: return (0, 0, 1920, 1080)
    xs = [m["x"] for m in monitors]
    ys = [m["y"] for m in monitors]
    x1s = [m["x"] + m["width"] for m in monitors]
    y1s = [m["y"] + m["height"] for m in monitors]
    return (min(xs), min(ys), max(x1s), max(y1s))

def _clamp_box(box, max_w, max_h):
    l, t, r, b = box
    l = max(0, min(l, max_w)); r = max(0, min(r, max_w))
    t = max(0, min(t, max_h)); b = max(0, min(b, max_h))
    return (l, t, r, b)

def split_wallpaper_by_monitors(final_image: Image.Image, monitors, out_dir, base_name="wallpaper"):
    """
    Découpe l'image du bureau virtuel en une image par écran.
    Retourne une liste de (moniteur, chemin) : le rectangle du moniteur sert ensuite
    à retrouver l'écran Windows correspondant, quelle que soit la disposition.
    """
    if not monitors: raise RuntimeError("Aucun moniteur détecté.")
    if not os.path.isdir(out_dir): raise RuntimeError(f"Dossier introuvable: {out_dir}")

    img_w, img_h = final_image.size
    if all("canvas" in m for m in monitors):
        # Rectangles de composition (mode pixels ou physique, voir display_geometry)
        rects = [m["canvas"] for m in monitors]
        comp_w = max(r[0] + r[2] for r in rects); comp_h = max(r[1] + r[3] for r in rects)
    else:
        x0, y0, x1, y1 = virtual_desktop_bbox(monitors)
        rects = [(m["x"] - x0, m["y"] - y0, m["width"], m["height"]) for m in monitors]
        comp_w, comp_h = x1 - x0, y1 - y0
    rx = img_w / comp_w; ry = img_h / comp_h
    results = []

    for i, m in enumerate(monitors):
        cx, cy, cw, ch = rects[i]
        px0 = cx * rx; py0 = cy * ry
        px1 = (cx + cw) * rx; py1 = (cy + ch) * ry

        box = _clamp_box((int(round(px0)), int(round(py0)), int(round(px1)), int(round(py1))), img_w, img_h)
        if box[2] <= box[0] or box[3] <= box[1]: continue

        crop_im = final_image.crop(box)
        if crop_im.size != (m["width"], m["height"]):
            crop_im = crop_im.resize((m["width"], m["height"]), Image.Resampling.LANCZOS)

        fname = f"{base_name}_pos_{i:02d}.png"
        fpath = os.path.join(out_dir, fname)
        crop_im.save(fpath, "PNG")
        results.append((m, fpath))

    return results

def match_monitors(split_results, windows_monitors):
    """
    Associe chaque image découpée à un écran Windows par recouvrement de rectangles.
    split_results : [(moniteur screeninfo, chemin)] ; windows_monitors : [{"id", "rect": (l, t, r, b)}].
    Retourne [(id Windows, chemin)] et la liste des images sans écran.
    """
    def overlap(a, b):
        w = min(a[2], b[2]) - max(a[0], b[0])
        h = min(a[3], b[3]) - max(a[1], b[1])
        return max(0, w) * max(0, h)

    pairs, unmatched = [], []
    free = list(windows_monitors)
    for m, path in split_results:
        rect = (m["x"], m["y"], m["x"] + m["width"], m["y"] + m["height"])
        best = max(free, key=lambda wm: overlap(rect, wm["rect"]), default=None)
        if best is None or overlap(rect, best["rect"]) == 0:
            unmatched.append(path)
            continue
        free.remove(best)
        pairs.append((best["id"], path))
    return pairs, unmatched

# --- CŒUR DU SYSTÈME (CTYPES) ---

def set_multi_wallpaper_windows(split_results, bg_color=(0, 0, 0)):
    """
    Applique une image par écran via IDesktopWallpaper.
    Retourne (succès, erreurs, appliqués) : succès vaut True si tout a été appliqué sans erreur,
    `erreurs` est une liste de messages lisibles et `appliqués` le nombre d'écrans mis à jour.
    """
    if not IS_WINDOWS:
        return False, ["L'application du fond d'écran nécessite Windows 10 ou 11."], 0

    ole32 = ctypes.windll.ole32
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    errors = []

    hr_init = ole32.CoInitialize(None)
    p_desktop_wallpaper = ctypes.POINTER(IDesktopWallpaper)()

    try:
        with per_monitor_dpi():
            CLSCTX_LOCAL_SERVER = 4
            hr = ole32.CoCreateInstance(
                ctypes.byref(CLSID_DesktopWallpaper),
                None,
                CLSCTX_LOCAL_SERVER,
                ctypes.byref(IID_IDesktopWallpaper),
                ctypes.byref(p_desktop_wallpaper)
            )
            if hr != 0 or not p_desktop_wallpaper:
                return False, [f"CoCreateInstance a échoué (0x{hr & 0xFFFFFFFF:08X})."], 0

            vtbl = p_desktop_wallpaper.contents.lpVtbl.contents

            # 1. Écrans connus de Windows ; ceux dont GetMonitorRECT échoue sont inactifs et ignorés.
            count = ctypes.c_uint()
            vtbl.GetMonitorDevicePathCount(p_desktop_wallpaper, ctypes.byref(count))
            windows_monitors = []
            for i in range(count.value):
                raw = ctypes.c_void_p()
                if vtbl.GetMonitorDevicePathAt(p_desktop_wallpaper, i, ctypes.byref(raw)) != 0 or not raw.value:
                    continue
                try:
                    mid = ctypes.wstring_at(raw.value)
                finally:
                    ole32.CoTaskMemFree(raw)
                rect = RECT()
                if vtbl.GetMonitorRECT(p_desktop_wallpaper, mid, ctypes.byref(rect)) != 0:
                    continue
                windows_monitors.append({"id": mid, "rect": (rect.left, rect.top, rect.right, rect.bottom)})

            if not windows_monitors:
                return False, ["Windows ne signale aucun écran actif."], 0

            # 2. Remplissage exact (évite d'hériter d'un mode « Étendre » précédent) et fond assorti.
            r, g, b = bg_color
            vtbl.SetBackgroundColor(p_desktop_wallpaper, r | (g << 8) | (b << 16))
            hr_pos = vtbl.SetPosition(p_desktop_wallpaper, DWPOS_FILL)
            if hr_pos != 0:
                errors.append(f"SetPosition a échoué (0x{hr_pos & 0xFFFFFFFF:08X}).")

            # 3. Association par rectangle puis application
            pairs, unmatched = match_monitors(split_results, windows_monitors)
            for path in unmatched:
                errors.append(f"Aucun écran Windows ne correspond à {os.path.basename(path)}.")
            applied = 0
            for mid, path in pairs:
                hr_set = vtbl.SetWallpaper(p_desktop_wallpaper, mid, os.path.abspath(path))
                if hr_set != 0:
                    errors.append(f"SetWallpaper a échoué pour {os.path.basename(path)} (0x{hr_set & 0xFFFFFFFF:08X}).")
                else:
                    applied += 1

            return applied > 0 and not errors, errors, applied

    except Exception as e:
        errors.append(f"Erreur ctypes : {e}")
        return False, errors, 0

    finally:
        if p_desktop_wallpaper:
            p_desktop_wallpaper.contents.lpVtbl.contents.Release(p_desktop_wallpaper)
        if hr_init in (0, 1):  # S_OK ou S_FALSE : appel à équilibrer
            ole32.CoUninitialize()

def get_current_wallpapers():
    """
    Fond actuel de chaque écran actif : liste de {"id", "rect", "path"}.
    Sert à détecter qu'un thème Windows a remplacé le fond appliqué par WallCraft.
    """
    if not IS_WINDOWS:
        return []
    ole32 = ctypes.windll.ole32
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    hr_init = ole32.CoInitialize(None)
    p = ctypes.POINTER(IDesktopWallpaper)()
    out = []
    try:
        with per_monitor_dpi():
            if ole32.CoCreateInstance(ctypes.byref(CLSID_DesktopWallpaper), None, 4,
                                      ctypes.byref(IID_IDesktopWallpaper), ctypes.byref(p)) != 0 or not p:
                return []
            v = p.contents.lpVtbl.contents
            count = ctypes.c_uint()
            v.GetMonitorDevicePathCount(p, ctypes.byref(count))
            for i in range(count.value):
                raw = ctypes.c_void_p()
                if v.GetMonitorDevicePathAt(p, i, ctypes.byref(raw)) != 0 or not raw.value:
                    continue
                try:
                    mid = ctypes.wstring_at(raw.value)
                finally:
                    ole32.CoTaskMemFree(raw)
                rect = RECT()
                if v.GetMonitorRECT(p, mid, ctypes.byref(rect)) != 0:
                    continue
                wp = ctypes.c_void_p()
                path = ""
                if v.GetWallpaper(p, mid, ctypes.byref(wp)) == 0 and wp.value:
                    path = ctypes.wstring_at(wp.value)
                    ole32.CoTaskMemFree(wp)
                out.append({"id": mid, "rect": (rect.left, rect.top, rect.right, rect.bottom), "path": path})
        return out
    except Exception:
        return out
    finally:
        if p:
            p.contents.lpVtbl.contents.Release(p)
        if hr_init in (0, 1):
            ole32.CoUninitialize()

# --- MÉTHODE SECOURS (Panorama) ---

def set_wallpaper_span(image_path):
    """Applique une seule image étirée sur tout le bureau (mode Étendre de Windows)."""
    if not IS_WINDOWS:
        return False
    path = os.path.abspath(image_path)
    # IDesktopWallpaper d'abord : il ne passe pas par le registre, que Windows redirige
    # dans un paquet MSIX (version Microsoft Store).
    if _set_span_com(path):
        return True
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Control Panel\\Desktop", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "22")
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.CloseKey(key)
        return bool(ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3))
    except Exception:
        return False


def _set_span_com(path):
    ole32 = ctypes.windll.ole32
    hr_init = ole32.CoInitialize(None)
    p = ctypes.POINTER(IDesktopWallpaper)()
    try:
        if ole32.CoCreateInstance(ctypes.byref(CLSID_DesktopWallpaper), None, 4,
                                  ctypes.byref(IID_IDesktopWallpaper), ctypes.byref(p)) != 0 or not p:
            return False
        v = p.contents.lpVtbl.contents
        if v.SetPosition(p, DWPOS_SPAN) != 0:
            return False
        return v.SetWallpaper(p, None, path) == 0  # None : tous les écrans
    except Exception:
        return False
    finally:
        if p:
            p.contents.lpVtbl.contents.Release(p)
        if hr_init in (0, 1):
            ole32.CoUninitialize()
