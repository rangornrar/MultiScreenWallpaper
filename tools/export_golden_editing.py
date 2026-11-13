#!/usr/bin/env python3
"""
Résultats de référence pour l'édition de la composition (souris, poignées, aimantation, zoom,
annuler/rétablir), utilisés par les tests C# : csharp/tests/fixtures/editing.json.

Pilote la VRAIE classe WallpaperApp (ui.py) sans fenêtre : l'objet est créé avec __new__ et
seuls les attributs d'état utilisés par l'édition sont posés ; le dessin (canevas Tk, bibliothèque,
barre d'état) est remplacé par des objets factices. Les méthodes d'édition elles-mêmes
(on_left_down, on_left_drag, on_left_up, on_zoom, on_pan_*, cmd_*, _save_state, _auto_fit,
_relayout_after_geometry_change…) sont celles de ui.py, non modifiées.

    python3.12 tools/export_golden_editing.py        (depuis la racine du dépôt)

Chaque scénario est une suite d'opérations (événements souris en coordonnées écran, commandes) ;
l'état complet est enregistré après chaque opération. Sortie déterministe (graines fixes).
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from PIL import Image  # noqa: E402

import ui  # noqa: E402
from image_tools import LoadedImage  # noqa: E402

OUT = os.path.join(ROOT, "csharp", "tests", "fixtures", "editing.json")
LAYOUT_IDS = ["layout_mosaic", "layout_lines", "layout_grid", "layout_v_strip", "layout_h_strip", "layout_optimal"]
SIZES = [(1920, 1080), (1080, 1920), (4000, 3000), (1000, 1000), (3000, 1000), (640, 480), (2560, 1440), (900, 1600)]


# --- Objets factices remplaçant Tk ---

class FakeCanvas:
    def __init__(self, w, h):
        self.w, self.h = w, h

    def winfo_width(self):
        return self.w

    def winfo_height(self):
        return self.h

    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def config(self, **_kw):
        pass


class FakeRoot:
    def update_idletasks(self):
        pass

    def update(self):
        pass

    def after_idle(self, fn):
        fn()


class FakeVar:
    def set(self, _v):
        pass


class FakeCombo:
    def __init__(self):
        self.idx = 0

    def current(self, idx=None):
        if idx is not None:
            self.idx = idx
        return self.idx


class Event:
    def __init__(self, x=0, y=0, state=0, delta=0, num=None):
        self.x, self.y, self.state, self.delta, self.num = x, y, state, delta, num
        self.widget = None


def make_app(target, viewport, monitors=None):
    app = ui.WallpaperApp.__new__(ui.WallpaperApp)
    app.root = FakeRoot()
    app.canvas = FakeCanvas(*viewport)
    app.target_w, app.target_h = target
    app.monitor_layout = monitors or []
    app.images = []
    app.active_idx = None
    app.history = []
    app.history_idx = -1
    app.zoom = 0.15
    app.pan_x = 50
    app.pan_y = 50
    app.mode = "move"
    app._drag_data = {"x": 0, "y": 0, "item": None, "action": None}
    app._layout_ids = LAYOUT_IDS
    app.combo_layout = FakeCombo()
    app._fill = False
    app.status_var = FakeVar()
    # Dessin et panneaux : rien à faire sans fenêtre.
    app._refresh_canvas = lambda live=False: None
    app._refresh_library_panel = lambda: None
    app._refresh_texts = lambda: None
    app._u = lambda key, *a: key
    # Comme __init__ : cadrage puis premier état de l'historique.
    app._auto_fit()
    app._save_state("Init")
    return app


_counter = [0]


def make_images(sizes):
    out = []
    for w, h in sizes:
        img = LoadedImage(f"img{_counter[0]}.png", Image.new("RGB", (8, 8), "gray"))
        _counter[0] += 1
        # Seule la taille d'origine compte pour l'édition : pas besoin de vrais pixels.
        img.original_size = (w, h)
        img._aspect = w / h
        img.focus = (0.5, 0.5)
        out.append(img)
    return out


def num(v):
    return None if v is None else float(v)


def snapshot(app):
    return {
        "images": [{"path": i.path, "x": num(i.x), "y": num(i.y), "w": num(i.w), "h": num(i.h), "angle": i.angle,
                    "z": i.z_index, "crop": [float(c) for c in i.crop_box_norm]} for i in app.images],
        "active": app.active_idx,
        "history": [app.history_idx, len(app.history)],
        "view": [float(app.zoom), float(app.pan_x), float(app.pan_y)],
        "mode": app.mode,
    }


def run_op(app, op):
    kind = op["op"]
    state = 0x0001 if op.get("shift") else 0
    if kind == "down":
        e = Event(op["x"], op["y"], state)
        if op.get("button", 1) == 1:
            app.on_left_down(e)
        else:
            app.on_pan_start(e)
    elif kind == "move":
        e = Event(op["x"], op["y"], state)
        if op.get("button", 1) == 1:
            app.on_left_drag(e)
        else:
            app.on_pan_drag(e)
    elif kind == "up":
        if op.get("button", 1) == 1:
            app.on_left_up(Event(op["x"], op["y"], state))
        # Boutons du milieu et de droite : aucun gestionnaire de relâchement en Python.
    elif kind == "wheel":
        app.on_zoom(Event(op["x"], op["y"], delta=op["delta"]))
    elif kind == "mode":
        app.set_mode(op["mode"])
    elif kind == "add":
        images = make_images(op["sizes"])
        ui.askopenfilenames = lambda **_kw: [i.path for i in images]
        ui.load_images_from_paths = lambda _paths, _errors=None: images
        app.cmd_add_images()
    elif kind == "fit":
        app.canvas.w, app.canvas.h = op["viewport"]
        app._auto_fit()
    elif kind == "resize":
        app.canvas.w, app.canvas.h = op["viewport"]
        app._on_stage_resized()
    elif kind == "geometry":
        old = (app.target_w, app.target_h)
        app.target_w, app.target_h = op["size"]
        app._relayout_after_geometry_change(old)
    elif kind == "autofill":
        app.combo_layout.idx = LAYOUT_IDS.index(op["layout"])
        app._fill = op["fill"]
        app.cmd_autofill()
    elif kind == "undo":
        app.cmd_undo()
    elif kind == "redo":
        app.cmd_redo()
    elif kind == "rotate":
        app.cmd_rotate()
    elif kind == "remove":
        app.cmd_remove_img()
    elif kind == "back":
        app.cmd_layer_backward()
    elif kind == "front":
        app.cmd_layer_forward()
    elif kind == "select":
        app._select_image(op["index"])
    elif kind == "adjust":
        img = app._selected()
        if img is not None:
            img.brightness = op["brightness"]
            app._save_state("Adjust")
    else:
        raise ValueError(kind)


def run_scenario(name, target, viewport, ops, monitors=None):
    _counter[0] = 0
    app = make_app(target, viewport, monitors)
    steps = [{"op": {"op": "start"}, "state": snapshot(app)}]
    for op in ops:
        run_op(app, op)
        steps.append({"op": op, "state": snapshot(app)})
    return {"name": name, "target": list(target), "viewport": list(viewport),
            "monitors": [m["canvas"] for m in (monitors or [])], "steps": steps}


# --- Construction des scénarios sur une application vivante ---

class Builder:
    """Exécute les opérations au fur et à mesure pour calculer les coordonnées écran à partir de l'état courant."""

    def __init__(self, name, target=(5760, 1080), viewport=(1200, 600), monitors=None):
        _counter[0] = 0
        self.name, self.target, self.viewport, self.monitors = name, target, viewport, monitors
        self.app = make_app(target, viewport, monitors)
        self.ops = []

    def do(self, op, **kw):
        op = {"op": op, **kw}
        run_op(self.app, op)
        self.ops.append(op)
        return self

    def screen(self, lx, ly):
        a = self.app
        return lx * a.zoom + a.pan_x, ly * a.zoom + a.pan_y

    def img(self, i):
        return self.app.images[i]

    def corner(self, i, c):
        m = self.img(i)
        lx = m.x + (m.w if c in ("tr", "br") else 0)
        ly = m.y + (m.h if c in ("bl", "br") else 0)
        return self.screen(lx, ly)

    def drag(self, start, moves, shift=False, button=1):
        x0, y0 = start
        self.do("down", x=x0, y=y0, button=button, shift=shift)
        x, y = x0, y0
        for (dx, dy) in moves:
            x, y = x0 + dx, y0 + dy
            self.do("move", x=x, y=y, button=button, shift=shift)
        return self.do("up", x=x, y=y, button=button, shift=shift)

    def drag_logic(self, i, tx, ty, shift=False, steps=2):
        """Glisse l'image i depuis son centre pour amener son coin haut-gauche en (tx, ty) logiques."""
        m = self.img(i)
        sx, sy = self.screen(m.x + m.w / 2, m.y + m.h / 2)
        dx, dy = (tx - m.x) * self.app.zoom, (ty - m.y) * self.app.zoom
        return self.drag((sx, sy), [(dx * k / steps, dy * k / steps) for k in range(1, steps + 1)], shift=shift)

    def result(self):
        return self.name, self.target, self.viewport, self.ops, self.monitors


def handwritten():
    out = []

    # 1. Déplacement avec Maj (sans aimantation), puis annuler/rétablir au-delà des bornes
    b = Builder("deplacement_maj_annuler").do("add", sizes=[[1920, 1080], [1000, 1000]])
    b.drag(b.screen(b.img(1).x + 100, b.img(1).y + 50), [(30, 10), (61.5, -17.25)], shift=True)
    for op in ("undo", "undo", "undo", "redo", "redo", "redo"):
        b.do(op)
    out.append(b.result())

    # 2. Aimantation sur le bord gauche et le haut de la composition (et pas avec Maj)
    b = Builder("aimantation_bords_composition").do("add", sizes=[[1920, 1080]])
    b.drag_logic(0, 12.0, -20.0)
    b.drag_logic(0, 300.0, 300.0)
    b.drag_logic(0, -24.5, 24.5)
    b.drag_logic(0, 10.0, 10.0, shift=True)
    # Bord droit de la composition : pas d'aimantation en Python
    b.drag_logic(0, 5760 - b.img(0).w + 10, 500.0)
    out.append(b.result())

    # 3. Aimantation sur les bords d'une autre image (gauche et droit en x ; aucune en y)
    b = Builder("aimantation_autres_images").do("add", sizes=[[1000, 1000]]).do("add", sizes=[[1000, 1000]])
    b.drag_logic(1, 2000.0, 300.0, shift=True)
    b.drag_logic(0, 1000.0, 500.0, shift=True)
    o = b.img(0)
    b.drag_logic(1, o.x + o.w + 10, o.y + 7)      # bord gauche contre le bord droit de l'image 0
    b.drag_logic(1, o.x - 20, o.y + o.h + 3)      # bord gauche contre le bord gauche de l'image 0
    b.drag_logic(1, o.x - o.w + 15, 900.0)        # bord DROIT près du bord gauche : pas d'aimantation
    b.drag_logic(1, 20.0, 300.0)                  # x=0 puis vérification des autres images
    out.append(b.result())

    # 4. Redimensionnement par les quatre poignées, proportions gardées, minimum 40
    b = Builder("redimensionner_poignees").do("add", sizes=[[1920, 1080]]).do("mode", mode="scale")
    x, y = b.corner(0, "br")
    b.drag((x + 3, y - 4), [(40, 5), (80, 90)])
    x, y = b.corner(0, "tl")
    b.drag((x - 5, y + 6), [(30, 2)])
    b.do("undo").do("select", index=0)
    x, y = b.corner(0, "tr")
    b.drag((x, y), [(-500, 400)])
    x, y = b.corner(0, "bl")
    b.drag((x + 9, y + 9), [(-20, 60)])
    x, y = b.corner(0, "br")
    b.drag((x, y), [(-9999, 3)])
    # Clic sur le corps de l'image : sélection seulement, ni déplacement ni historique
    m = b.img(0)
    b.drag(b.screen(m.x + m.w / 2, m.y + m.h / 2), [(50, 50)])
    # Poignée à 10 px exactement : hors de portée
    x, y = b.corner(0, "br")
    b.drag((x + 10, y), [(30, 30)])
    out.append(b.result())

    # 5. Rognage par les poignées : limites MIN_CROP et bords de l'image, puis rotation
    b = Builder("rogner_poignees").do("add", sizes=[[3000, 1000]]).do("mode", mode="crop")
    x, y = b.corner(0, "tl")
    b.drag((x, y), [(20, 8)])
    b.do("select", index=0)
    x, y = b.corner(0, "br")
    b.drag((x, y), [(-9999, -9999)])
    b.do("undo").do("select", index=0)
    x, y = b.corner(0, "tr")
    b.drag((x, y), [(300, -300)])
    b.do("undo").do("select", index=0)
    x, y = b.corner(0, "bl")
    b.drag((x + 4, y - 4), [(33, -11)])
    b.do("select", index=0)
    x, y = b.corner(0, "tr")
    b.drag((x - 2, y + 1), [(-17, 23), (-40, 31)])
    # Clic dans l'image en mode Rogner : déplacement
    m = b.img(0)
    b.drag(b.screen(m.x + m.w / 2, m.y + m.h / 2), [(25, -14)])
    b.do("rotate").do("undo").do("redo")
    out.append(b.result())

    # 6. Zoom molette centré sur le pointeur, bornes, déplacement de la vue
    b = Builder("zoom_et_vue").do("add", sizes=[[1000, 1000]])
    for _ in range(3):
        b.do("wheel", x=100, y=200, delta=120)
    for _ in range(2):
        b.do("wheel", x=900, y=50, delta=-120)
    for _ in range(60):
        b.do("wheel", x=600, y=300, delta=120)   # borne haute 10
    for _ in range(120):
        b.do("wheel", x=10, y=10, delta=-120)    # borne basse 0,01
    b.do("fit", viewport=[1200, 600])
    b.drag((5, 5), [(20, 10), (55, -35)])
    b.drag((1100, 500), [(-100, -50)], button=2)
    b.drag((1100, 500), [(50, 20)], button=3)
    b.do("resize", viewport=[1400, 700]).do("wheel", x=700, y=350, delta=120).do("resize", viewport=[1000, 500])
    b.do("fit", viewport=[40, 40]).do("fit", viewport=[49, 600]).do("fit", viewport=[600, 50])
    out.append(b.result())

    # 7. Historique : profondeur maximale (20), nouvel état après annulation
    b = Builder("historique_profondeur").do("add", sizes=[[1000, 1000]])
    for k in range(24):
        m = b.img(0)
        b.drag(b.screen(m.x + 50, m.y + 50), [(7, 3)], shift=True)
    for _ in range(25):
        b.do("undo")
    for _ in range(3):
        b.do("redo")
    b.do("select", index=0).do("rotate").do("redo").do("undo").do("undo")
    # Un simple clic sur une image enregistre un état (comme en Python)
    m = b.img(0)
    b.drag(b.screen(m.x + 50, m.y + 50), [])
    out.append(b.result())

    # 8. Calques, suppression, rotation, retouche
    b = Builder("calques_suppression_rotation").do("add", sizes=[[1920, 1080], [1080, 1920], [1000, 1000]])
    for op in ("back", "back", "back", "front", "rotate", "rotate"):
        b.do(op)
    b.do("adjust", brightness=1.4)
    for op in ("remove", "remove", "undo"):
        b.do(op)
    b.do("select", index=2).do("front").do("select", index=7).do("rotate").do("select", index=0).do("back")
    m = b.img(0)
    b.drag(b.screen(m.x + m.w / 2, m.y + m.h / 2), [])  # zone commune : l'image au z le plus grand
    b.drag((2, 2), [])                                   # clic dans le vide : désélection
    b.do("rotate").do("remove")
    out.append(b.result())

    # 9. Changement de géométrie des écrans et dispositions automatiques
    mons = [{"canvas": [3840, 0, 1920, 1080]}, {"canvas": [0, 0, 1920, 1080]}, {"canvas": [1920, 0, 1920, 1080]}]
    b = Builder("geometrie_et_dispositions", monitors=mons).do("add", sizes=[[1920, 1080], [1080, 1920]])
    b.do("autofill", layout="layout_mosaic", fill=False).do("autofill", layout="layout_mosaic", fill=True).do("undo")
    b.do("geometry", size=[5760, 1200]).do("geometry", size=[3840, 1080]).do("geometry", size=[3840, 1080])
    b.do("add", sizes=[[4000, 3000], [640, 480]])
    b.do("autofill", layout="layout_grid", fill=False).do("autofill", layout="layout_lines", fill=True)
    b.do("autofill", layout="layout_mosaic", fill=False).do("undo").do("redo")
    b.do("autofill", layout="layout_v_strip", fill=True).do("autofill", layout="layout_h_strip", fill=False)
    out.append(b.result())
    return out


# --- Scénarios aléatoires (graine fixe), construits à partir de l'état courant ---

def random_scenario(seed):
    rng = random.Random(seed)
    T = rng.choice([(5760, 1080), (3840, 1080), (1920, 1080), (3840, 2160)])
    V = rng.choice([(1200, 600), (1000, 700), (1600, 800)])
    _counter[0] = 0
    app = make_app(T, V)
    ops = []

    def do(op):
        run_op(app, op)
        ops.append(op)

    def lsc(lx, ly):
        return lx * app.zoom + app.pan_x, ly * app.zoom + app.pan_y

    def r(v):
        return round(v, rng.choice([0, 1, 2]))

    for _ in range(rng.randint(15, 35)):
        k = rng.random()
        if not app.images or k < 0.07:
            do({"op": "add", "sizes": [list(rng.choice(SIZES)) for _ in range(rng.randint(1, 3))]})
        elif k < 0.35:
            # Glisser depuis l'intérieur d'une image (ou parfois juste à côté)
            img = rng.choice(app.images)
            sx, sy = lsc(img.x + img.w * rng.uniform(-0.05, 1.05), img.y + img.h * rng.uniform(-0.05, 1.05))
            shift = rng.random() < 0.3
            do({"op": "down", "x": r(sx), "y": r(sy), "button": 1, "shift": shift})
            for _m in range(rng.randint(0, 4)):
                # Parfois vers un bord d'une autre image ou de la composition, pour tester l'aimantation
                if rng.random() < 0.4 and app._drag_data.get("action") == "move":
                    o = rng.choice(app.images)
                    tx = rng.choice([0, o.x, o.x + o.w]) + rng.uniform(-30, 30)
                    ty = rng.choice([0, o.y]) + rng.uniform(-30, 30)
                    d = app._drag_data
                    lx = d["slx"] + (tx - d["ox"])
                    ly = d["sly"] + (ty - d["oy"])
                    sx, sy = lsc(lx, ly)
                else:
                    sx, sy = sx + rng.uniform(-80, 80), sy + rng.uniform(-80, 80)
                do({"op": "move", "x": r(sx), "y": r(sy), "button": 1, "shift": shift})
            do({"op": "up", "x": r(sx), "y": r(sy), "button": 1, "shift": shift})
        elif k < 0.55:
            # Poignée de l'image sélectionnée (mode Redimensionner ou Rogner)
            if app.mode == "move":
                do({"op": "mode", "mode": rng.choice(["scale", "crop"])})
            if app.active_idx is None:
                do({"op": "select", "index": rng.randrange(len(app.images))})
            img = app.images[app.active_idx]
            hx, hy = rng.choice([(img.x, img.y), (img.x + img.w, img.y), (img.x + img.w, img.y + img.h), (img.x, img.y + img.h)])
            sx, sy = lsc(hx, hy)
            sx, sy = sx + rng.uniform(-11, 11), sy + rng.uniform(-11, 11)
            do({"op": "down", "x": r(sx), "y": r(sy), "button": 1})
            for _m in range(rng.randint(1, 3)):
                sx, sy = sx + rng.uniform(-120, 120), sy + rng.uniform(-120, 120)
                do({"op": "move", "x": r(sx), "y": r(sy), "button": 1})
            do({"op": "up", "x": r(sx), "y": r(sy), "button": 1})
        elif k < 0.62:
            do({"op": "wheel", "x": r(rng.uniform(0, V[0])), "y": r(rng.uniform(0, V[1])), "delta": rng.choice([120, -120])})
        elif k < 0.66:
            b = rng.choice([1, 2, 3])
            sx, sy = rng.uniform(0, V[0]), rng.uniform(0, V[1])
            ex, ey = r(sx + rng.uniform(-100, 100)), r(sy + rng.uniform(-100, 100))
            do({"op": "down", "x": r(sx), "y": r(sy), "button": b, "shift": False})
            do({"op": "move", "x": ex, "y": ey, "button": b, "shift": False})
            do({"op": "up", "x": ex, "y": ey, "button": b, "shift": False})
        elif k < 0.70:
            do({"op": "mode", "mode": rng.choice(["move", "scale", "crop"])})
        elif k < 0.78:
            do({"op": rng.choice(["undo", "undo", "redo"])})
        elif k < 0.82:
            do({"op": "rotate"})
        elif k < 0.85:
            do({"op": rng.choice(["back", "front"])})
        elif k < 0.88:
            do({"op": "select", "index": rng.randrange(len(app.images) + 1)})
        elif k < 0.90:
            do({"op": "remove"})
        elif k < 0.93:
            do({"op": "autofill", "layout": rng.choice(LAYOUT_IDS[:5]), "fill": rng.random() < 0.5})
        elif k < 0.95:
            do({"op": "geometry", "size": [rng.choice([1920, 3840, 5760, 4000]), rng.choice([1080, 1200, 2160])]})
        elif k < 0.97:
            do({"op": "fit", "viewport": list(rng.choice([(1200, 600), (900, 900), (40, 40)]))})
        else:
            do({"op": "resize", "viewport": list(rng.choice([(1300, 650), (800, 600)]))})
    return f"aleatoire_{seed}", T, V, ops, None


def main():
    scenarios = []
    for name, target, viewport, ops, monitors in handwritten():
        scenarios.append(run_scenario(name, target, viewport, ops, monitors))
    for seed in range(60):
        name, target, viewport, ops, monitors = random_scenario(seed)
        # Rejoue depuis zéro : les images et l'état ne dépendent que des opérations enregistrées.
        scenarios.append(run_scenario(name, target, viewport, ops, monitors))
    data = {"snap_dist": ui.SNAP_DIST, "min_crop": ui.MIN_CROP, "scenarios": scenarios}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    steps = sum(len(s["steps"]) - 1 for s in scenarios)
    print(f"{len(scenarios)} scénarios, {steps} opérations -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
