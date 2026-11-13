# display_geometry.py
"""
Géométrie des écrans : où se trouve chaque écran dans la composition.

Deux modes :
- « pixels » : la grille de Windows (bureau virtuel), un pixel de composition = un pixel d'écran ;
- « physique » : chaque écran est placé selon sa taille réelle (mm) et l'espace entre les dalles.
  Une ligne d'horizon reste droite et à la même échelle d'un écran à l'autre, même entre
  un 27″ 1440p et un 24″ 1080p. La partie de l'image cachée derrière les bords est perdue,
  comme une vraie fenêtre.

Chaque moniteur reçoit une clé « canvas » = (x, y, w, h) en pixels de composition ;
`canvas_size` donne la taille de la composition. Le découpage et l'interface n'utilisent que ces valeurs.
"""
import hashlib
import json
import math
import os
import sys

DEFAULT_MM_PER_PX = 0.2715  # écran 24″ 1080p, utilisé si la taille physique est inconnue
IS_WINDOWS = sys.platform == "win32"


# --- Taille physique (EDID) ---

def parse_edid_size_mm(edid):
    """Taille de la zone d'affichage en mm depuis un bloc EDID (descripteur détaillé, sinon octets 21-22 en cm)."""
    if not edid or len(edid) < 128 or bytes(edid[:8]) != b"\x00\xff\xff\xff\xff\xff\xff\x00":
        return None
    d = edid[54:72]
    if d[0] or d[1]:  # descripteur de timing détaillé
        w = d[12] | ((d[14] & 0xF0) << 4)
        h = d[13] | ((d[14] & 0x0F) << 8)
        if w > 50 and h > 50:
            return float(w), float(h)
    if edid[21] and edid[22]:
        return edid[21] * 10.0, edid[22] * 10.0
    return None


def _edid_for_adapter(adapter_name):
    """EDID du moniteur branché sur « \\\\.\\DISPLAYn » (Windows), avec son identifiant stable."""
    import ctypes
    import winreg
    from ctypes import wintypes

    class DISPLAY_DEVICEW(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("DeviceName", wintypes.WCHAR * 32),
                    ("DeviceString", wintypes.WCHAR * 128), ("StateFlags", wintypes.DWORD),
                    ("DeviceID", wintypes.WCHAR * 128), ("DeviceKey", wintypes.WCHAR * 128)]

    dev = DISPLAY_DEVICEW()
    dev.cb = ctypes.sizeof(dev)
    EDD_GET_DEVICE_INTERFACE_NAME = 1
    if not ctypes.windll.user32.EnumDisplayDevicesW(adapter_name, 0, ctypes.byref(dev), EDD_GET_DEVICE_INTERFACE_NAME):
        return None, None
    # \\?\DISPLAY#GSM5B7F#5&2f3b8a6&0&UID4352#{e6f07b5f-...}
    parts = dev.DeviceID.split("#")
    if len(parts) < 3:
        return None, None
    model, instance = parts[1], parts[2]
    path = f"SYSTEM\\CurrentControlSet\\Enum\\DISPLAY\\{model}\\{instance}\\Device Parameters"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            edid, _ = winreg.QueryValueEx(key, "EDID")
    except OSError:
        return None, f"{model}#{instance}"
    return bytes(edid), f"{model}#{instance}"


def enrich_with_physical_size(monitors):
    """Ajoute width_mm/height_mm (EDID, sinon screeninfo) et un identifiant stable à chaque moniteur."""
    for m in monitors:
        m.setdefault("width_mm", None)
        m.setdefault("height_mm", None)
        m.setdefault("hw_id", m.get("name", ""))
        size = None
        if IS_WINDOWS and m.get("name", "").startswith("\\\\.\\"):
            try:
                edid, hw_id = _edid_for_adapter(m["name"])
                if hw_id:
                    m["hw_id"] = hw_id
                size = parse_edid_size_mm(edid)
            except Exception:
                size = None
        if size is None and m.get("width_mm") and m.get("height_mm"):
            size = (float(m["width_mm"]), float(m["height_mm"]))
        if size:
            w_mm, h_mm = size
            # L'EDID décrit la dalle en paysage : on suit l'orientation réelle de l'écran.
            if (m["width"] < m["height"]) != (w_mm < h_mm):
                w_mm, h_mm = h_mm, w_mm
            m["width_mm"], m["height_mm"] = w_mm, h_mm
    return monitors


def diagonal_inches(width_mm, height_mm):
    return math.hypot(width_mm, height_mm) / 25.4


# --- Réglages physiques ---

class PhysicalSettings:
    """Réglages modifiables par l'utilisateur : tailles corrigées, décalages verticaux, espace entre dalles."""

    def __init__(self, enabled=False, bezel_mm=0.0, overrides=None):
        self.enabled = enabled
        self.bezel_mm = float(bezel_mm)
        # hw_id -> {"width_mm", "height_mm", "offset_x_mm", "offset_y_mm"}
        self.overrides = dict(overrides or {})

    def to_dict(self):
        return {"enabled": self.enabled, "bezel_mm": self.bezel_mm, "overrides": self.overrides}

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(bool(data.get("enabled", False)), float(data.get("bezel_mm", 0.0)), data.get("overrides", {}))


def _size_mm(m, settings, fallback_density):
    o = settings.overrides.get(m.get("hw_id", ""), {})
    w = o.get("width_mm") or m.get("width_mm")
    h = o.get("height_mm") or m.get("height_mm")
    if not w or not h:
        w, h = m["width"] * fallback_density, m["height"] * fallback_density
    return float(w), float(h)


def _neighbours(a, b):
    """Côté par lequel b touche a dans le bureau virtuel : 'right', 'left', 'below', 'above' ou None."""
    ax1, ay1 = a["x"] + a["width"], a["y"] + a["height"]
    bx1, by1 = b["x"] + b["width"], b["y"] + b["height"]
    v_overlap = min(ay1, by1) - max(a["y"], b["y"]) > 0
    h_overlap = min(ax1, bx1) - max(a["x"], b["x"]) > 0
    if v_overlap and abs(b["x"] - ax1) <= 2: return "right"
    if v_overlap and abs(bx1 - a["x"]) <= 2: return "left"
    if h_overlap and abs(b["y"] - ay1) <= 2: return "below"
    if h_overlap and abs(by1 - a["y"]) <= 2: return "above"
    return None


def physical_positions(monitors, settings):
    """
    Position (x_mm, y_mm, w_mm, h_mm) de chaque écran. Les écrans voisins dans Windows sont
    accolés avec l'espace `bezel_mm` et centrés l'un sur l'autre ; offset_x/y_mm corrigent la pose réelle.
    """
    known = [m["width_mm"] / m["width"] for m in monitors if m.get("width_mm")]
    density = sorted(known)[len(known) // 2] if known else DEFAULT_MM_PER_PX
    sizes = [_size_mm(m, settings, density) for m in monitors]
    pos = [None] * len(monitors)
    if not monitors:
        return []
    root = min(range(len(monitors)), key=lambda i: (abs(monitors[i]["x"]) + abs(monitors[i]["y"]), i))
    pos[root] = (0.0, 0.0)
    queue = [root]
    gap = settings.bezel_mm
    while queue:
        i = queue.pop(0)
        ax, ay = pos[i]
        aw, ah = sizes[i]
        for j, mj in enumerate(monitors):
            if pos[j] is not None:
                continue
            side = _neighbours(monitors[i], mj)
            if side is None:
                continue
            bw, bh = sizes[j]
            if side == "right": pos[j] = (ax + aw + gap, ay + (ah - bh) / 2)
            elif side == "left": pos[j] = (ax - gap - bw, ay + (ah - bh) / 2)
            elif side == "below": pos[j] = (ax + (aw - bw) / 2, ay + ah + gap)
            else: pos[j] = (ax + (aw - bw) / 2, ay - gap - bh)
            queue.append(j)
    # Écrans non contigus : position proportionnelle à celle du bureau virtuel
    for j, mj in enumerate(monitors):
        if pos[j] is None:
            pos[j] = ((mj["x"] - monitors[root]["x"]) * density, (mj["y"] - monitors[root]["y"]) * density)
    out = []
    for j, mj in enumerate(monitors):
        o = settings.overrides.get(mj.get("hw_id", ""), {})
        x = pos[j][0] + float(o.get("offset_x_mm", 0.0))
        y = pos[j][1] + float(o.get("offset_y_mm", 0.0))
        out.append((x, y, sizes[j][0], sizes[j][1]))
    return out


def apply_layout(monitors, settings=None):
    """
    Calcule la clé « canvas » de chaque moniteur et retourne (largeur, hauteur) de la composition.
    En mode physique, l'échelle est celle de l'écran le plus dense : aucun écran n'est agrandi.
    """
    if not monitors:
        return (1920, 1080)
    settings = settings or PhysicalSettings()
    if not settings.enabled:
        x0 = min(m["x"] for m in monitors); y0 = min(m["y"] for m in monitors)
        x1 = max(m["x"] + m["width"] for m in monitors); y1 = max(m["y"] + m["height"] for m in monitors)
        for m in monitors:
            m["canvas"] = (m["x"] - x0, m["y"] - y0, m["width"], m["height"])
        return (x1 - x0, y1 - y0)

    rects = physical_positions(monitors, settings)
    scale = max(m["width"] / r[2] for m, r in zip(monitors, rects))  # px de composition par mm
    mx0 = min(r[0] for r in rects); my0 = min(r[1] for r in rects)
    mx1 = max(r[0] + r[2] for r in rects); my1 = max(r[1] + r[3] for r in rects)
    for m, (x, y, w, h) in zip(monitors, rects):
        cx, cy = int(round((x - mx0) * scale)), int(round((y - my0) * scale))
        m["canvas"] = (cx, cy, int(round((x + w - mx0) * scale)) - cx, int(round((y + h - my0) * scale)) - cy)
    return (int(math.ceil((mx1 - mx0) * scale)), int(math.ceil((my1 - my0) * scale)))


def layout_signature(monitors):
    """Empreinte d'une configuration d'écrans (écrans branchés, résolution, position)."""
    key = sorted((m.get("name", ""), m["x"], m["y"], m["width"], m["height"]) for m in monitors)
    return hashlib.sha1(json.dumps(key).encode()).hexdigest()[:16]


# --- Réglages persistants de l'application ---

def settings_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(base, "WallCraft")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "settings.json")


def load_settings():
    try:
        with open(settings_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(data):
    path = settings_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


# --- Noms lisibles des écrans ---

# Codes fabricant PNP (3 lettres en tête de l'identifiant matériel) les plus courants.
VENDORS = {
    "ACR": "Acer", "AOC": "AOC", "APP": "Apple", "AUO": "AUO", "AUS": "ASUS", "BNQ": "BenQ", "BOE": "BOE",
    "CMN": "Innolux", "DEL": "Dell", "EIZ": "EIZO", "ENC": "EIZO", "GBT": "Gigabyte", "GSM": "LG", "HKC": "HKC",
    "HPN": "HP", "HWP": "HP", "IVM": "iiyama", "KOS": "KOORUI", "LEN": "Lenovo", "LGD": "LG", "MEI": "Panasonic",
    "MSI": "MSI", "NEC": "NEC", "PHL": "Philips", "SAM": "Samsung", "SDC": "Samsung", "SHP": "Sharp",
    "SNY": "Sony", "VSC": "ViewSonic", "XMI": "Xiaomi",
}


def monitor_vendor(m):
    hw = m.get("hw_id") or ""
    code = hw[:3].upper() if "#" in hw else ""
    return VENDORS.get(code, code) if code.isalpha() else ""


def _format_inches(width_mm, height_mm, decimal=","):
    d = round(diagonal_inches(width_mm, height_mm), 1)
    text = f"{d:.0f}" if d == int(d) else f"{d:.1f}".replace(".", decimal)
    return text + "″"


def monitor_labels(monitors, words, decimal=","):
    """
    Noms lisibles, dans l'ordre de `monitors` : « Gauche · Philips 23″ ».
    words = {"left", "center", "right", "top", "bottom", "screen"} (« Écran {} »).
    Les écrans sont nommés de gauche à droite (ou de haut en bas s'ils sont empilés), sinon numérotés.
    """
    def rect(m):
        return m.get("canvas") or (m["x"], m["y"], m["width"], m["height"])

    order = sorted(range(len(monitors)), key=lambda i: (rect(monitors[i])[0], rect(monitors[i])[1]))
    rects = [rect(monitors[i]) for i in order]
    in_row = all(rects[k][0] + rects[k][2] <= rects[k + 1][0] + 1 for k in range(len(rects) - 1))
    order_v = sorted(range(len(monitors)), key=lambda i: (rect(monitors[i])[1], rect(monitors[i])[0]))
    rects_v = [rect(monitors[i]) for i in order_v]
    in_col = all(rects_v[k][1] + rects_v[k][3] <= rects_v[k + 1][1] + 1 for k in range(len(rects_v) - 1))

    positions = {}
    n = len(monitors)
    if n >= 2 and n <= 3 and in_row:
        names = [words["left"], words["right"]] if n == 2 else [words["left"], words["center"], words["right"]]
        positions = {i: names[k] for k, i in enumerate(order)}
    elif n == 2 and in_col:
        positions = {order_v[0]: words["top"], order_v[1]: words["bottom"]}
    elif n > 1:
        positions = {i: words["screen"].format(k + 1) for k, i in enumerate(order)}

    labels = []
    for i, m in enumerate(monitors):
        parts = []
        vendor = monitor_vendor(m)
        size = _format_inches(m["width_mm"], m["height_mm"], decimal) if m.get("width_mm") and m.get("height_mm") else ""
        detail = " ".join(p for p in (vendor, size) if p) or f"{m['width']} × {m['height']}"
        if i in positions:
            parts.append(positions[i])
        parts.append(detail)
        labels.append(" · ".join(parts))
    return labels


def upscale_factor(img):
    """
    Agrandissement subi par l'image dans la composition : 1 = pixel pour pixel, 2,5 = étirée 2,5 fois.
    `img` est une LoadedImage (taille d'origine, rotation, rognage, taille affichée w × h).
    """
    ow, oh = img.original_size
    if (img.angle % 180) == 90:
        ow, oh = oh, ow
    cl, ct, cr, cb = img.crop_box_norm
    src_w, src_h = max(1.0, ow * (cr - cl)), max(1.0, oh * (cb - ct))
    return max(img.w / src_w, img.h / src_h)
