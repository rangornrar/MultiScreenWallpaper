"""
Résultats de référence pour les retouches (PIL.ImageEnhance) et le point d'intérêt (facefocus),
utilisés par les tests C# : csharp/tests/fixtures/imaging.json. Sortie déterministe.
"""
import json
import os
import random
import sys

import PIL
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python"))
import facefocus  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "csharp", "tests", "fixtures", "imaging.json")


def sample_image(seed, w, h, alpha=True):
    rng = random.Random(seed)
    data = bytes(rng.randrange(256) if (i % 4 != 3 or alpha) else 255 for i in range(w * h * 4))
    return Image.frombytes("RGBA", (w, h), data)


def enhance_cases():
    cases = []
    for seed, (w, h) in ((1, (23, 17)), (2, (8, 8)), (3, (31, 5))):
        img = sample_image(seed, w, h, alpha=seed != 2)
        for name, cls in (("brightness", ImageEnhance.Brightness), ("contrast", ImageEnhance.Contrast), ("color", ImageEnhance.Color)):
            for factor in (0.0, 0.35, 0.5, 1.0, 1.3, 2.0, 3.7):
                out = cls(img).enhance(factor)
                cases.append({"id": f"{name}|{seed}|{factor}", "filter": name, "factor": factor,
                              "size": [w, h], "input": img.tobytes().hex(), "output": out.tobytes().hex()})
        # Enchaînement de la version Python : luminosité, contraste, saturation
        out = ImageEnhance.Color(ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(1.2)).enhance(0.8)).enhance(1.5)
        cases.append({"id": f"chain|{seed}", "filter": "chain", "factor": [1.2, 0.8, 1.5],
                      "size": [w, h], "input": img.tobytes().hex(), "output": out.tobytes().hex()})
    return cases


def rotate_cases():
    img = sample_image(9, 5, 3)
    return [{"angle": a, "size": [5, 3], "input": img.tobytes().hex(), "output": img.rotate(a, expand=True).tobytes().hex(),
             "output_size": list(img.rotate(a, expand=True).size)} for a in (0, 90, 180, 270)]


def face_cases():
    cases = []
    for faces, size in (([], (100, 100)), ([(10, 20, 30, 30)], (200, 100)), ([(0, 0, 50, 50), (150, 50, 20, 20)], (200, 100)),
                        ([(180, 90, 40, 40)], (200, 100))):
        r = facefocus.focus_from_faces(faces, size)
        cases.append({"faces": [list(f) for f in faces], "size": list(size), "focus": list(r) if r else None})
    return cases


def detail_cases():
    cases = []
    for cid, size, rect in (("flat", (320, 200), None), ("top_left", (320, 200), (10, 10, 80, 60)),
                            ("bottom_right", (400, 300), (300, 220, 390, 290)), ("center", (160, 160), (60, 60, 100, 100)),
                            ("tall", (200, 500), (20, 380, 120, 480))):
        img = Image.new("RGB", size, (40, 40, 40))
        if rect:
            ImageDraw.Draw(img).rectangle(rect, fill=(240, 240, 240))
        focus = facefocus.focus_from_detail(img)
        gray = img.convert("L")
        cases.append({"id": cid, "size": list(size), "rect": list(rect) if rect else None, "focus": list(focus),
                      "gray_values": sorted(set(gray.tobytes()))})
    return cases


def main():
    data = {
        "meta": {"generator": "tools/export_golden_imaging.py", "python": sys.version.split()[0], "pillow": PIL.__version__,
                 "description": "Retouches ImageEnhance (octets RGBA en hexadécimal) et point d'intérêt (visages, contours)."},
        "enhance": enhance_cases(),
        "rotate": rotate_cases(),
        "faces": face_cases(),
        "detail": detail_cases(),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
