# screen_splitter.py
import os
import ctypes
from ctypes import wintypes
import winreg
from PIL import Image

# On essaie d'importer screeninfo, sinon on fera sans
try:
    from screeninfo import get_monitors as _get_monitors
except ImportError:
    _get_monitors = None

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

# Définition de la VTable (Table des méthodes virtuelles COM)
class IDesktopWallpaperVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))),
        ("AddRef", ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)),
        ("Release", ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)),
        # Method 3: SetWallpaper
        ("SetWallpaper", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p)),
        ("GetWallpaper", ctypes.c_void_p),
        ("GetMonitorDevicePathAt", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_wchar_p))),
        ("GetMonitorDevicePathCount", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint))),
        # Method 7: GetRect (Crucial pour l'ordre des écrans)
        ("GetRect", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(RECT))),
    ]

class IDesktopWallpaper(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(IDesktopWallpaperVtbl))]

# --- FONCTIONS UTILITAIRES ---

def get_monitor_layout():
    """Récupère la configuration réelle des écrans via screeninfo."""
    monitors = []
    if _get_monitors is None: return monitors
    try:
        for m in _get_monitors():
            monitors.append({
                "x": int(getattr(m, "x", 0)),
                "y": int(getattr(m, "y", 0)),
                "width": int(getattr(m, "width", 0)),
                "height": int(getattr(m, "height", 0)),
                "name": getattr(m, "name", "monitor"),
                "device_id": getattr(m, "name", "")
            })
        # Tri gauche -> droite pour le découpage
        monitors.sort(key=lambda m: m["x"])
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
    Découpe l'image. Retourne une liste de chemins d'images.
    IMPORTANT: Les images sont générées dans l'ordre gauche -> droite car 'monitors' est trié.
    """
    if not monitors: raise RuntimeError("Aucun moniteur détecté.")
    if not os.path.isdir(out_dir): raise RuntimeError(f"Dossier introuvable: {out_dir}")

    x0, y0, x1, y1 = virtual_desktop_bbox(monitors)
    virt_w, virt_h = x1 - x0, y1 - y0
    img_w, img_h = final_image.size
    rx = img_w / virt_w; ry = img_h / virt_h
    results = [] # Liste de tuples (id_dummy, path)

    for i, m in enumerate(monitors):
        px0 = (m["x"] - x0) * rx; py0 = (m["y"] - y0) * ry
        px1 = (m["x"] - x0 + m["width"]) * rx; py1 = (m["y"] - y0 + m["height"]) * ry

        box = _clamp_box((int(round(px0)), int(round(py0)), int(round(px1)), int(round(py1))), img_w, img_h)
        if box[2] <= box[0] or box[3] <= box[1]: continue

        crop_im = final_image.crop(box)
        if crop_im.size != (m["width"], m["height"]):
            crop_im = crop_im.resize((m["width"], m["height"]), Image.Resampling.LANCZOS)

        # On utilise un index simple dans le nom pour l'ordre de tri
        fname = f"{base_name}_pos_{i:02d}.png"
        fpath = os.path.join(out_dir, fname)
        crop_im.save(fpath, "PNG")
        results.append((m["device_id"], fpath))

    return results

# --- CŒUR DU SYSTÈME (CTYPES) ---

def set_multi_wallpaper_windows(monitor_image_map):
    """
    Applique le wallpaper en triant les ID Windows par leur position physique X.
    Cela garantit que l'image de gauche va sur l'écran de gauche, peu importe son ID (1, 2 ou 3).
    """
    ole32 = ctypes.windll.ole32
    
    # Init COM
    ole32.CoInitialize(None)
    
    p_desktop_wallpaper = ctypes.POINTER(IDesktopWallpaper)()
    
    try:
        CLSCTX_LOCAL_SERVER = 4
        hr = ole32.CoCreateInstance(
            ctypes.byref(CLSID_DesktopWallpaper), 
            None, 
            CLSCTX_LOCAL_SERVER, 
            ctypes.byref(IID_IDesktopWallpaper), 
            ctypes.byref(p_desktop_wallpaper)
        )
        
        if hr != 0 or not p_desktop_wallpaper:
            print(f"Erreur CoCreateInstance: {hr}")
            return False

        # 1. Récupérer TOUS les écrans et leurs positions RECT
        count = ctypes.c_uint()
        p_desktop_wallpaper.contents.lpVtbl.contents.GetMonitorDevicePathCount(p_desktop_wallpaper, ctypes.byref(count))
        
        windows_monitors = []
        
        print(f"Windows détecte {count.value} écrans via IDesktopWallpaper.")

        for i in range(count.value):
            monitor_id_ptr = ctypes.c_wchar_p()
            p_desktop_wallpaper.contents.lpVtbl.contents.GetMonitorDevicePathAt(p_desktop_wallpaper, i, ctypes.byref(monitor_id_ptr))
            mid = monitor_id_ptr.value
            
            # Récupérer le RECT (position physique) pour cet ID
            rect = RECT()
            hr_rect = p_desktop_wallpaper.contents.lpVtbl.contents.GetRect(p_desktop_wallpaper, ctypes.c_wchar_p(mid), ctypes.byref(rect))
            
            x_pos = 0
            if hr_rect == 0:
                x_pos = rect.left
            
            windows_monitors.append({
                "id": mid,
                "x": x_pos
            })

        # 2. TRIER les écrans Windows par position X (Gauche -> Droite)
        # C'est l'étape clé : on ignore l'ID (1, 2, 3) et on prend l'ordre visuel (Gauche, Milieu, Droite)
        windows_monitors.sort(key=lambda m: m["x"])
        
        print("Ordre physique détecté (ID : X) :")
        for wm in windows_monitors:
            print(f" - {wm['id']} : {wm['x']}")

        # 3. Appliquer les images dans l'ordre
        # monitor_image_map contient les images déjà triées de gauche à droite (split index 0, 1, 2...)
        for i, (_, img_path) in enumerate(monitor_image_map):
            if i < len(windows_monitors):
                target_monitor = windows_monitors[i]
                target_id = target_monitor["id"]
                
                print(f"Application Image {i} -> Ecran {target_id} (Pos X={target_monitor['x']})")
                
                hr_set = p_desktop_wallpaper.contents.lpVtbl.contents.SetWallpaper(
                    p_desktop_wallpaper, 
                    ctypes.c_wchar_p(target_id), 
                    ctypes.c_wchar_p(img_path)
                )
                if hr_set != 0:
                    print(f"Echec SetWallpaper (Code {hr_set})")
            else:
                print(f"Pas d'écran Windows trouvé pour l'image {i}")

        return True

    except Exception as e:
        print(f"Erreur Ctypes: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if p_desktop_wallpaper:
            p_desktop_wallpaper.contents.lpVtbl.contents.Release(p_desktop_wallpaper)
        ole32.CoUninitialize()

# --- MÉTHODE SECOURS (Panorama) ---

def set_wallpaper_span(image_path):
    path = os.path.abspath(image_path)
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Control Panel\\Desktop", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "22")
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.CloseKey(key)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
        return True
    except Exception as e:
        print(f"Erreur Span: {e}")
        return False