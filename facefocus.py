# facefocus.py
"""
Point d'intérêt d'une image pour le mode « Remplir ».

1. Visages détectés avec OpenCV (cascade de Haar fournie avec opencv-python-headless) :
   centre pondéré par la taille des visages, visé un peu au-dessus du centre des visages
   pour garder les têtes entières.
2. Sinon (paysage, OpenCV absent) : centre de gravité des contours, ramené vers le centre
   pour ne pas viser un simple bord texturé.

Retourne (x, y) normalisé dans [0, 1] dans l'orientation d'origine de l'image.
"""
import os
import sys

from PIL import Image, ImageFilter, ImageOps

_cascade = None
_cascade_failed = False


def _cascade_path():
    import cv2
    candidates = [os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")]
    if getattr(sys, "frozen", False):  # exécutable PyInstaller
        candidates.append(os.path.join(getattr(sys, "_MEIPASS", ""), "cv2", "data", "haarcascade_frontalface_default.xml"))
    return next((p for p in candidates if os.path.isfile(p)), None)


def _get_cascade():
    global _cascade, _cascade_failed
    if _cascade is not None or _cascade_failed:
        return _cascade
    try:
        import cv2
        path = _cascade_path()
        cascade = cv2.CascadeClassifier(path) if path else None
        if cascade is None or cascade.empty():
            raise RuntimeError("cascade introuvable")
        _cascade = cascade
    except Exception:
        _cascade_failed = True
    return _cascade


def detect_faces(image):
    """Rectangles (x, y, w, h) des visages en pixels de `image` ; liste vide si OpenCV est absent."""
    cascade = _get_cascade()
    if cascade is None:
        return []
    import numpy as np
    gray = ImageOps.equalize(image.convert("L"))
    arr = np.asarray(gray)
    min_side = max(24, int(min(gray.size) * 0.06))
    found = cascade.detectMultiScale(arr, scaleFactor=1.1, minNeighbors=6, minSize=(min_side, min_side))
    return [tuple(int(v) for v in f) for f in found]


def focus_from_faces(faces, size):
    if not faces:
        return None
    w, h = size
    total = sum(fw * fh for _, _, fw, fh in faces)
    cx = sum((x + fw / 2) * fw * fh for x, _, fw, fh in faces) / total
    # Viser un peu au-dessus du centre des visages laisse de la place au-dessus des têtes.
    cy = sum((y + fh * 0.4) * fw * fh for _, y, fw, fh in faces) / total
    return (min(1.0, max(0.0, cx / w)), min(1.0, max(0.0, cy / h)))


def focus_from_detail(image):
    """Centre de gravité des contours, rapproché du centre (repli sans visage)."""
    small = image.convert("L")
    small.thumbnail((160, 160))
    edges = small.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(2))
    w, h = edges.size
    data = edges.tobytes()  # niveaux de gris : un octet par pixel
    total = sx = sy = 0.0
    for i, v in enumerate(data):
        if v:
            total += v
            sx += (i % w) * v
            sy += (i // w) * v
    if total <= 0:
        return (0.5, 0.5)
    cx, cy = sx / total / max(1, w - 1), sy / total / max(1, h - 1)
    return (0.5 + (cx - 0.5) * 0.6, 0.5 + (cy - 0.5) * 0.6)


def find_focus(image: Image.Image):
    try:
        faces = detect_faces(image)
    except Exception:
        faces = []
    return focus_from_faces(faces, image.size) or focus_from_detail(image)
