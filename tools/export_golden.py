#!/usr/bin/env python3
"""
Résultats de référence pour le portage C# (phase 1 de docs/MIGRATION_CSHARP.md).

Exécute le code Python actuel sur un jeu FIXE de cas et écrit des JSON dans
csharp/tests/fixtures/. La sortie est déterministe : pas de date, pas d'horloge, pas de
dépendance à l'ordre d'itération d'un set. Les tests C# comparent le portage à ces fichiers.

    python3.12 tools/export_golden.py        (depuis la racine du dépôt)

Aucun fichier du dépôt n'est modifié ; seuls les fichiers de la fixture sont (ré)écrits.
Les images sont créées en mémoire et leur point d'intérêt est fixé explicitement : aucune
détection de visage ne tourne.
"""
import copy
import hashlib
import json
import ntpath
import os
import platform
import random
import sys
import tempfile
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

import PIL  # noqa: E402
from PIL import Image  # noqa: E402

import display_geometry as dg  # noqa: E402
import screen_splitter  # noqa: E402
import services  # noqa: E402
from image_tools import AutoLayoutStrategy as ALS, LoadedImage  # noqa: E402

FIXTURES = os.path.join(ROOT, "csharp", "tests", "fixtures")

# Le garde-fou de temps du mode optimal rend le résultat dépendant de la vitesse de la machine :
# on le désactive pour que le nombre d'essais complet soit toujours fait.
ALS.OPTIMAL_MAX_TIME = 1e9

MODES = ["layout_mosaic", "layout_lines", "layout_grid", "layout_v_strip", "layout_h_strip", "layout_optimal"]
REGULAR_MODES = ("layout_grid", "layout_lines", "layout_v_strip", "layout_h_strip")


# --------------------------------------------------------------------------------------
# Utilitaires
# --------------------------------------------------------------------------------------

def meta(description, **extra):
    m = {
        "generator": "tools/export_golden.py",
        "python": platform.python_version(),
        "pillow": PIL.__version__,
        "description": description,
    }
    m.update(extra)
    return m


def dump(name, description, body, **meta_extra):
    data = {"meta": meta(description, **meta_extra)}
    data.update(body)
    path = os.path.join(FIXTURES, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, allow_nan=False)
        f.write("\n")
    return path


def tup(v):
    """Tuples -> listes (JSON), récursivement."""
    if isinstance(v, (tuple, list)):
        return [tup(x) for x in v]
    return v


_BASE = {}


def make_image(path, w, h, focus):
    """
    LoadedImage en mémoire de w x h pixels avec point d'intérêt fixé. Les images de même taille
    partagent leurs pixels (clone) : les dispositions n'utilisent que le ratio.
    """
    base = _BASE.get((w, h))
    if base is None:
        base = LoadedImage("<base>", Image.new("RGB", (w, h)))
        base._original = None  # libère la RAM (jusqu'à ~100 Mo par image)
        _BASE[(w, h)] = base
    img = base.clone()
    img.path = path
    if focus is not None:
        img.focus = (focus[0], focus[1])
    return img


@contextmanager
def windows_paths():
    """Fait utiliser ntpath (sémantique Windows) à services.py : os.path.normcase/abspath."""
    old = os.path
    os.path = ntpath
    try:
        yield
    finally:
        os.path = old


# --------------------------------------------------------------------------------------
# Jeu d'images
# --------------------------------------------------------------------------------------

# (chemin, largeur, hauteur, focus)
IMAGES = [
    ("C:\\Photos\\Vacances\\IMG_0001.jpg", 6000, 4000, (0.5, 0.4)),
    ("C:\\Photos\\Vacances\\IMG_0002.jpg", 4000, 6000, (0.5, 0.3)),
    ("C:\\Photos\\Famille\\été 2026\\carré.png", 3000, 3000, (0.5, 0.5)),
    ("D:\\Images\\panorama_pyrénées.jpg", 6000, 2000, (0.8, 0.5)),
    ("D:\\Images\\petite.jpg", 600, 400, (0.2, 0.7)),
    ("C:\\Users\\Public\\Pictures\\Tulips.jpg", 1024, 768, (0.1, 0.1)),
    ("D:\\Fonds\\4k_ville.png", 3840, 2160, (0.65, 0.35)),
    ("D:\\Fonds\\vertical_1080x1920.jpg", 1080, 1920, (0.5, 0.2)),
    ("C:\\Photos\\2025\\DSC_0100.JPG", 5472, 3648, (0.3, 0.6)),
    ("C:\\Photos\\2025\\DSC_0101.JPG", 3648, 5472, (0.9, 0.2)),
    ("E:\\Scans\\carte postale.tif", 3300, 2550, (0.0, 0.0)),
    ("D:\\Images\\bandeau_3x1.png", 3000, 1000, (0.5, 0.5)),
    ("C:\\Photos\\日本\\京都.jpg", 4032, 3024, (1.0, 1.0)),
]
SETS = {
    1: [0],
    2: [0, 1],
    3: [3, 1, 4],
    5: [0, 1, 2, 3, 4],
    8: [0, 1, 2, 3, 4, 5, 6, 7],
    13: list(range(13)),
}
TARGETS = [(5760, 1080), (1920, 1080), (6175, 1143), (1080, 1920), (3840, 2160)]
SMALL_TARGETS = [(5760, 1080), (1920, 1080)]


def build_images(n):
    return [make_image(*IMAGES[i]) for i in SETS[n]]


def image_inputs(imgs):
    return [{"path": i.path, "size": list(i.original_size), "focus": list(i.focus)} for i in imgs]


def placement_out(i):
    return {"x": i.x, "y": i.y, "w": i.w, "h": i.h, "crop": tup(i.crop_box_norm), "z": i.z_index, "angle": i.angle}


# --------------------------------------------------------------------------------------
# Capture du score du mode optimal sans modifier image_tools.py (sys.monitoring, Python 3.12+)
# --------------------------------------------------------------------------------------

_OPT = {"data": None, "names": None}


def _tree_str(node, names):
    if node["type"] == "leaf":
        return str(names[id(node["img"])])
    return "%s(%s,%s)" % (node["type"], _tree_str(node["left"], names), _tree_str(node["right"], names))


def _on_optimal_return(code, offset, retval):
    loc = sys._getframe(1).f_locals
    if "best" not in loc or "best_tree" not in loc:
        return  # retour anticipé (n <= 1)
    names = _OPT["names"]
    if names is None:
        return  # appel hors apply_capture (traces aléatoires)
    variant = loc["variant"]
    best = loc["best"]
    chosen = min(variant, len(best) - 1)
    _OPT["data"] = {
        "iterations": loc["iterations"],
        "iterations_run": loc["it"] + 1,
        "keep": loc["keep"],
        "chosen_rank": chosen,
        "score": best[chosen][0],
        "best_iteration": best[chosen][1],
        "ratio_total": loc["best_tree"]["R"],
        "tree": _tree_str(loc["best_tree"], names),
        "ranked": [{"score": s, "iteration": it_, "tree": _tree_str(t, names)} for (s, it_, t) in best],
    }


def _install_monitor():
    mon = sys.monitoring
    tool = mon.PROFILER_ID
    mon.use_tool_id(tool, "export_golden")
    mon.register_callback(tool, mon.events.PY_RETURN, _on_optimal_return)
    mon.set_local_events(tool, ALS._optimal_fit.__code__, mon.events.PY_RETURN)


def apply_capture(mode, tw, th, imgs, fill, variant):
    """ALS.apply ; pour le mode optimal, retourne aussi les informations de recherche."""
    _OPT["data"] = None
    _OPT["names"] = {id(im): k for k, im in enumerate(imgs)}
    try:
        ALS.apply(mode, tw, th, imgs, fill=fill, variant=variant)
    finally:
        _OPT["names"] = None
    if mode == "layout_optimal" and len(imgs) > 1:
        d = _OPT["data"]
        assert d is not None and d["iterations_run"] == d["iterations"], "recherche optimale interrompue"
        return d
    return None


# --------------------------------------------------------------------------------------
# 1. seeds.json
# --------------------------------------------------------------------------------------

class _Stub:
    def __init__(self, path, ratio):
        self.path, self._ratio = path, ratio

    def visible_aspect(self):
        return self._ratio


def _seed_case(cid, mode, tw, th, variant, items):
    stubs = [_Stub(p, r) for p, r in items]
    key = repr((mode, round(tw), round(th), variant, [(str(i.path), round(i.visible_aspect(), 4)) for i in stubs]))
    seed = ALS._seed(mode, tw, th, stubs, variant)
    assert hashlib.sha1(key.encode()).hexdigest()[:12] == "%012x" % seed
    return {
        "id": cid, "mode": mode, "tw": tw, "th": th, "variant": variant,
        "images": [{"path": p, "ratio": r, "ratio_rounded": round(r, 4)} for p, r in items],
        "tw_rounded": round(tw), "th_rounded": round(th),
        "key": key, "sha1": hashlib.sha1(key.encode()).hexdigest(), "seed": seed,
    }


def seeds_cases():
    A = "C:\\Photos\\Vacances\\IMG_0001.jpg"
    B = "C:\\Photos\\Vacances\\IMG_0002.jpg"
    real = [(p, w / h) for p, w, h, _ in IMAGES]
    cases = []

    def add(cid, mode, tw, th, variant, items):
        cases.append(_seed_case(cid, mode, tw, th, variant, items))

    # Modes, variantes, tailles entières
    for k, mode in enumerate(MODES):
        add("real5_%s_v0" % mode, mode, 5760, 1080, 0, real[:5])
        add("real3_%s_v%d" % (mode, k % 3), mode, 1920, 1080, k % 3, [real[3], real[1], real[4]])
    add("optimal_13_v2", "layout_optimal", 6175, 1143, 2, real)
    add("mosaic_variant_11", "layout_mosaic", 3840, 2160, 11, real[:8])
    add("one_image", "layout_grid", 1080, 1920, 0, real[:1])
    add("empty_list", "layout_grid", 1920, 1080, 0, [])
    # Tailles non entières, arrondi « au pair » de Python (banker's rounding)
    add("size_float_6175.0", "layout_optimal", 6175.0, 1143.0, 0, real[:3])
    add("size_float_1920.4", "layout_optimal", 1920.4, 1080.4, 0, real[:3])
    add("size_half_even_down", "layout_optimal", 1920.5, 1080.5, 0, real[:2])   # 1920 et 1080
    add("size_half_even_up", "layout_optimal", 1921.5, 1081.5, 0, real[:2])     # 1922 et 1082
    add("size_two_point_five", "layout_mosaic", 2.5, 3.5, 0, real[:2])          # 2 et 4
    add("size_float_5759.6", "layout_lines", 5759.6, 1079.5, 1, real[:2])
    # Chemins : antislashs, apostrophe, guillemets, Unicode, caractères échappés par repr
    add("path_windows_backslash", "layout_grid", 1920, 1080, 0, [("C:\\Photos\\été 2026\\a.jpg", 1.5)])
    add("path_apostrophe", "layout_grid", 1920, 1080, 0, [("C:\\Users\\l'été\\b.png", 0.5625)])
    add("path_double_quotes", "layout_grid", 1920, 1080, 0, [("C:\\Photos\\\"quoted\".jpg", 1.7778)])
    add("path_both_quotes", "layout_grid", 1920, 1080, 0, [("C:\\Users\\l'été\\\"x\".png", 1.3333)])
    add("path_unicode", "layout_lines", 1920, 1080, 1,
        [("D:\\Ünïcode\\ñandú.jpg", 2.0), ("C:\\日本\\京都.jpg", 0.75), ("E:\\ü\\é.png", 1.0)])
    add("path_posix", "layout_mosaic", 1920, 1080, 0, [("/home/user/Pictures/a b.jpg", 1.5), ("relative/c.png", 0.5)])
    add("path_empty_string", "layout_mosaic", 1920, 1080, 0, [("", 1.0)])
    add("path_control_chars", "layout_mosaic", 1920, 1080, 0, [("C:\\a\nb\tc\rd.jpg", 1.0), ("C:\\nul\x00x.jpg", 1.0)])
    add("path_escapes_other", "layout_mosaic", 1920, 1080, 0,
        [("C:\\\x7f\x1b.jpg", 1.0), ("C:\\nbsp\xa0.jpg", 1.0), ("C:\\zw\u200b.jpg", 1.0), ("C:\\soft\xad.jpg", 1.0)])
    add("path_emoji_and_astral", "layout_mosaic", 1920, 1080, 0,
        [("C:\\Photos\\\U0001F600.jpg", 1.0), ("C:\\Photos\\\U0001D11E.jpg", 1.0), ("C:\\Photos\\e\u0301.jpg", 1.0)])
    add("path_both_quotes_backslash_end", "layout_mosaic", 1920, 1080, 0, [("it's \"a\" \\", 1.0)])
    add("path_unpaired_quote_start", "layout_mosaic", 1920, 1080, 0, [("'", 1.0), ("\"", 1.0)])
    # Ratios : repr variés
    for rid, ratio in [("1.0", 1.0), ("0.5625", 0.5625), ("1.7778", 1920 / 1080), ("1.3333", 4 / 3), ("2.0", 2.0),
                       ("0.75", 0.75), ("3.0", 3.0), ("0.6667", 4000 / 6000), ("12345.6789", 12345.6789),
                       ("1e-05_arrondi", 1e-05), ("0.0001", 0.0001), ("1e16", 1e16),
                       ("1.2345678901234568e17", 123456789012345678.0), ("123456789012345.6", 123456789012345.6),
                       ("1e15", 1e15)]:
        add("ratio_" + rid, "layout_grid", 1920, 1080, 0, [(A, ratio)])
    # Arrondi à 4 décimales : cas limites entre Python round() et Math.Round
    for rid, ratio in [("1.00005", 1.00005), ("0.00005", 0.00005), ("1.23455", 1.23455), ("2.00005", 2.00005),
                       ("0.99995", 0.99995), ("3.14155", 3.14155), ("0.12345", 0.12345), ("0.00015", 0.00015),
                       ("5.00005", 5.00005), ("1.5e-05", 1.5e-05)]:
        add("round4_" + rid, "layout_grid", 1920, 1080, 0, [(B, ratio)])
    # Ratios via crop (visible_aspect) : exemple multi-images de l'ordre réel
    add("multi_ratio_order", "layout_optimal", 5760, 1080, 1, [(A, 1.5), (B, 2 / 3), (A, 1.5)])
    return cases


# --------------------------------------------------------------------------------------
# 2. random.json
# --------------------------------------------------------------------------------------

class TracingRandom(random.Random):
    """random.Random qui journalise les appels de haut niveau (pas ceux faits en interne)."""

    def __init__(self, seed, names):
        super().__init__(seed)
        self.ops, self.names, self._depth = [], names, 0

    def _call(self, name, fn, *args):
        self._depth += 1
        try:
            return fn(*args)
        finally:
            self._depth -= 1

    def random(self):
        r = super().random()
        if self._depth == 0:
            self.ops.append({"op": "random", "result": r})
        return r

    def uniform(self, a, b):
        r = self._call("uniform", super().uniform, a, b)
        if self._depth == 0:
            self.ops.append({"op": "uniform", "a": a, "b": b, "result": r})
        return r

    def randint(self, a, b):
        r = self._call("randint", super().randint, a, b)
        if self._depth == 0:
            self.ops.append({"op": "randint", "a": a, "b": b, "result": r})
        return r

    def choice(self, seq):
        r = self._call("choice", super().choice, seq)
        if self._depth == 0:
            self.ops.append({"op": "choice", "options": list(seq), "result": r})
        return r

    def shuffle(self, x):
        self._call("shuffle", super().shuffle, x)
        if self._depth == 0:
            self.ops.append({"op": "shuffle", "n": len(x), "after": [self.names[id(i)] for i in x]})


def _trace_mosaic(seed):
    imgs = [make_image(*IMAGES[i]) for i in range(8)]
    rng = TracingRandom(seed, {id(im): k for k, im in enumerate(imgs)})
    ALS._perfect_mosaic(5760, 1080, imgs, rng, ALS._apply_fit_inside)
    return {"function": "_perfect_mosaic", "n_images": 8, "target": [5760, 1080], "ops": rng.ops, "next_random": rng.random()}


def _trace_optimal(seed):
    imgs = [make_image(*IMAGES[i]) for i in (0, 1, 2, 3, 4, 5)]
    rng = TracingRandom(seed, {id(im): k for k, im in enumerate(imgs)})
    ALS._optimal_fit(5760, 1080, imgs, rng=rng, iterations=20)
    return {"function": "_optimal_fit", "n_images": 6, "target": [5760, 1080], "iterations": 20, "ops": rng.ops,
            "next_random": rng.random()}


def random_cases(seed_cases):
    by_id = {c["id"]: c for c in seed_cases}
    derived = ["real5_layout_mosaic_v0", "real5_layout_optimal_v0", "real3_layout_lines_v1",
               "mosaic_variant_11", "size_float_6175.0"]
    seeds = [(0, "literal"), (1, "literal"), (42, "literal"), (2 ** 32 - 1, "literal"), (2 ** 32 + 5, "literal"),
             (0x1234567890ab, "literal"), (2 ** 48 - 1, "literal")]
    seeds += [(by_id[d]["seed"], "seeds.json:" + d) for d in derived]

    out = []
    for seed, source in seeds:
        st = random.Random(seed).getstate()[1]
        e = {"seed": seed, "source": source, "state_head": list(st[:4]), "state_index": st[624]}
        r = random.Random(seed)
        e["random"] = [r.random() for _ in range(20)]
        e["getrandbits"] = [{"k": k, "values": (lambda g: [g.getrandbits(k) for _ in range(20)])(random.Random(seed))}
                            for k in (1, 7, 31, 32, 33, 53, 64)]
        e["randint"] = [{"a": 1, "b": n, "values": (lambda g: [g.randint(1, n) for _ in range(20)])(random.Random(seed))}
                        for n in (2, 3, 7, 100)]
        g = random.Random(seed)
        shuf = []
        for n in (2, 5, 13):
            lst = list(range(n))
            g.shuffle(lst)
            shuf.append({"n": n, "result": lst})
        e["shuffle_chain"] = shuf
        g = random.Random(seed)
        e["choice"] = [g.choice([True, False]) for _ in range(20)]
        g = random.Random(seed)
        e["uniform"] = [g.uniform(-0.1, 0.1) for _ in range(20)]
        e["sample"] = [{"n": n, "k": k, "result": random.Random(seed).sample(list(range(n)), k)}
                       for n, k in ((5, 2), (3, 3), (10, 3), (10, 10), (21, 4), (22, 4), (25, 5), (30, 3), (100, 7), (200, 10))]
        e["mixed_mosaic"] = _trace_mosaic(seed)
        e["mixed_optimal"] = _trace_optimal(seed)
        out.append(e)
    return out


# --------------------------------------------------------------------------------------
# 3. layouts*.json
# --------------------------------------------------------------------------------------

def layout_cases():
    cases = []
    for n in (1, 2, 3, 5, 8, 13):
        targets = TARGETS if n <= 5 else SMALL_TARGETS
        for tw, th in targets:
            for mode in MODES:
                for fill in (False, True):
                    for variant in range(4 if mode in REGULAR_MODES else 3):
                        imgs = build_images(n)
                        entry = {
                            "id": "%s|fill=%d|v=%d|%dx%d|n=%d" % (mode, fill, variant, tw, th, n),
                            "mode": mode, "fill": fill, "variant": variant, "target": [tw, th],
                            "images": image_inputs(imgs),
                        }
                        opt = apply_capture(mode, tw, th, imgs, fill, variant)
                        entry["result"] = [placement_out(i) for i in imgs]
                        if mode == "layout_optimal":
                            entry["optimal"] = opt
                        cases.append(entry)
    return cases


# --------------------------------------------------------------------------------------
# 4. variants.json
# --------------------------------------------------------------------------------------

def variants_cases():
    specs = []
    for mode in MODES:
        for fill in (False, True):
            specs.append((mode, fill, 5))
    for mode in MODES:
        specs.append((mode, False, 3))
    specs += [("layout_mosaic", True, 3), ("layout_optimal", True, 3)]
    for mode in ("layout_mosaic", "layout_optimal", "layout_lines", "layout_grid"):
        for fill in (False, True):
            specs.append((mode, fill, 8))
    out = []
    for mode, fill, n in specs:
        imgs = build_images(n)
        res = ALS.variants(mode, 5760, 1080, imgs, fill=fill, count=4)
        out.append({
            "id": "%s|fill=%d|n=%d" % (mode, fill, n), "mode": mode, "fill": fill, "target": [5760, 1080],
            "count": 4, "images": image_inputs(imgs),
            "variants": [[{"x": p[0], "y": p[1], "w": p[2], "h": p[3], "crop": tup(p[4]), "z": p[5]} for p in pl]
                         for pl in res],
        })
    return out


# --------------------------------------------------------------------------------------
# 5. placement.json
# --------------------------------------------------------------------------------------

def placement_cases():
    # (id, taille, focus, rotations, crop, boîte)
    specs = [
        ("wide_in_square", (6000, 4000), (0.5, 0.5), 0, None, (0, 0, 1000, 1000)),
        ("wide_in_tall", (6000, 4000), (0.5, 0.5), 0, None, (100, 50, 500, 1500)),
        ("tall_in_wide", (4000, 6000), (0.5, 0.5), 0, None, (0, 0, 1920, 1080)),
        ("square_in_wide", (3000, 3000), (0.5, 0.5), 0, None, (1920, 0, 1920, 1080)),
        ("same_ratio", (1920, 1080), (0.5, 0.5), 0, None, (10, 20, 960, 540)),
        ("focus_top_left", (6000, 4000), (0.0, 0.0), 0, None, (0, 0, 1000, 1000)),
        ("focus_bottom_right", (6000, 4000), (1.0, 1.0), 0, None, (0, 0, 1000, 1000)),
        ("focus_top_left_tall", (4000, 6000), (0.0, 0.0), 0, None, (0, 0, 1920, 1080)),
        ("focus_bottom_right_tall", (4000, 6000), (1.0, 1.0), 0, None, (0, 0, 1920, 1080)),
        ("focus_center_panorama", (6000, 2000), (0.5, 0.5), 0, None, (0, 0, 1920, 1080)),
        ("focus_0.9_0.2_wide", (6000, 4000), (0.9, 0.2), 0, None, (0, 0, 1000, 1000)),
        ("focus_0.9_0.2_tall", (4000, 6000), (0.9, 0.2), 0, None, (0, 0, 1920, 1080)),
        ("focus_out_of_range", (6000, 4000), (1.5, -0.2), 0, None, (0, 0, 1000, 1000)),
        ("rotated_270_once", (6000, 4000), (0.5, 0.5), 1, None, (0, 0, 1000, 1000)),
        ("rotated_180_twice", (6000, 4000), (0.3, 0.7), 2, None, (0, 0, 1000, 1000)),
        ("rotated_90_thrice", (6000, 4000), (0.3, 0.7), 3, None, (0, 0, 1920, 1080)),
        ("rotated_270_tall_box", (6000, 4000), (0.1, 0.9), 1, None, (0, 0, 500, 1500)),
        ("already_cropped_square", (6000, 4000), (0.5, 0.5), 0, (0.25, 0.0, 0.75, 1.0), (0, 0, 1000, 1000)),
        ("already_cropped_wide", (6000, 4000), (0.2, 0.5), 0, (0.0, 0.1, 0.5, 0.9), (0, 0, 1920, 1080)),
        ("already_cropped_and_rotated", (6000, 4000), (0.5, 0.5), 1, (0.1, 0.2, 0.9, 0.6), (0, 0, 800, 1200)),
        ("half_pixel_box_even", (6000, 4000), (0.5, 0.5), 0, None, (0, 0, 100.5, 100)),
        ("half_pixel_box_odd", (6000, 4000), (0.5, 0.5), 0, None, (0, 0, 101.5, 100)),
        ("half_pixel_box_2_5", (6000, 4000), (0.5, 0.5), 0, None, (0, 0, 2.5, 3.5)),
        ("tiny_box_rounds_to_zero", (6000, 4000), (0.5, 0.5), 0, None, (0, 0, 0.4, 0.4)),
        ("fractional_box", (6000, 4000), (0.37, 0.61), 0, None, (12.75, 33.3, 1279.99, 719.51)),
        ("truncation_fit", (1000, 999), (0.5, 0.5), 0, None, (0, 0, 1919.9, 1079.9)),
        ("zero_width_box", (6000, 4000), (0.5, 0.5), 0, None, (5, 5, 0, 100)),
        ("negative_height_box", (6000, 4000), (0.5, 0.5), 0, None, (5, 5, 100, -3)),
        ("origin_offset_integer", (3000, 3000), (0.5, 0.5), 0, None, (7, 9, 100, 100)),
        ("very_tall_panorama_box", (6000, 2000), (0.95, 0.5), 0, None, (0, 0, 10, 1000)),
        ("tiny_image", (600, 400), (0.2, 0.7), 0, None, (0, 0, 640, 360)),
    ]
    out = []
    for cid, size, focus, rots, crop, box in specs:
        for fn_name, fn in (("fit_inside", ALS._apply_fit_inside), ("crop_cover", ALS._apply_crop_cover)):
            img = make_image("C:\\x\\%s.jpg" % cid, size[0], size[1], focus)
            for _ in range(rots):
                img.rotate_cw()
            if crop is not None:
                img.crop_box_norm = crop
            before = {"angle": img.angle, "crop": tup(img.crop_box_norm), "current_aspect": img.current_aspect(),
                      "visible_aspect": img.visible_aspect()}
            fn(img, *box)
            out.append({
                "id": "%s|%s" % (cid, fn_name), "function": fn_name,
                "image": {"size": list(size), "focus": list(focus), "rotations_cw": rots, **before},
                "box": list(box),
                "result": {"x": img.x, "y": img.y, "w": img.w, "h": img.h, "crop": tup(img.crop_box_norm)},
            })
    return out


# --------------------------------------------------------------------------------------
# 6. geometry.json
# --------------------------------------------------------------------------------------

def make_edid(cm=None, detailed_mm=None, header_ok=True, name_descriptor=False, length=128, hi_nibbles=None):
    b = bytearray(128)
    if header_ok:
        b[0:8] = b"\x00\xff\xff\xff\xff\xff\xff\x00"
    else:
        b[0:8] = b"\x00\xff\xff\xff\xff\xff\xff\x01"
    if cm:
        b[21], b[22] = cm
    d = 54
    if detailed_mm:
        w, h = detailed_mm
        b[d] = 0x01; b[d + 1] = 0x1D  # horloge de pixel non nulle
        b[d + 12] = w & 0xFF; b[d + 13] = h & 0xFF
        b[d + 14] = ((w >> 8) << 4) | (h >> 8)
    if name_descriptor:
        b[d + 0] = 0; b[d + 1] = 0; b[d + 3] = 0xFC
        b[d + 5:d + 12] = b"PHL 24\n"
        b[d + 12] = 99; b[d + 13] = 99  # ignoré : pas de descripteur de timing
    if hi_nibbles is not None:
        b[d + 14] = hi_nibbles
    return bytes(b[:length]) if length <= 128 else bytes(b) + bytes(length - 128)


def edid_cases():
    short = make_edid(cm=(60, 34), detailed_mm=(527, 296))[:127]
    cases = [
        ("detailed_and_cm_agree", make_edid(cm=(51, 29), detailed_mm=(509, 286))),
        ("detailed_wins_over_cm", make_edid(cm=(53, 30), detailed_mm=(527, 296))),
        ("detailed_only", make_edid(detailed_mm=(544, 303))),
        ("cm_only_name_descriptor", make_edid(cm=(60, 34), name_descriptor=True)),
        ("inconsistent_cm_vs_detailed", make_edid(cm=(160, 90), detailed_mm=(509, 286))),
        ("detailed_too_small_falls_back_to_cm", make_edid(cm=(53, 30), detailed_mm=(16, 9))),
        ("detailed_width_exactly_50_falls_back", make_edid(cm=(53, 30), detailed_mm=(50, 286))),
        ("detailed_height_exactly_50_falls_back", make_edid(cm=(53, 30), detailed_mm=(509, 50))),
        ("detailed_width_51_accepted", make_edid(cm=(53, 30), detailed_mm=(51, 51))),
        ("detailed_high_nibbles_1200x700", make_edid(detailed_mm=(1200, 700))),
        ("detailed_too_small_no_cm", make_edid(detailed_mm=(16, 9))),
        ("invalid_header", make_edid(cm=(53, 30), detailed_mm=(527, 296), header_ok=False)),
        ("too_short_127_bytes", short),
        ("empty", b""),
        ("all_zero_sizes", make_edid()),
        ("cm_width_only", make_edid(cm=(53, 0))),
        ("cm_height_only", make_edid(cm=(0, 30))),
        ("extension_block_256_bytes", make_edid(cm=(53, 30), detailed_mm=(527, 296), length=256)),
        ("pixel_clock_low_byte_only", None),
    ]
    out = []
    for cid, data in cases:
        if cid == "pixel_clock_low_byte_only":
            b = bytearray(make_edid(cm=(53, 30)))
            b[54] = 0x01; b[55] = 0x00; b[54 + 12] = 0xFF; b[54 + 13] = 0xFF
            data = bytes(b)
        r = dg.parse_edid_size_mm(data)
        out.append({"id": cid, "hex": data.hex(), "result": list(r) if r else None})
    out.append({"id": "none_input", "hex": None, "result": dg.parse_edid_size_mm(None)})
    return out


def mon(name, x, y, w, h, wmm=None, hmm=None, hw=None):
    return {"name": name, "x": x, "y": y, "width": w, "height": h, "width_mm": wmm, "height_mm": hmm, "hw_id": hw}


HW_PHL = "PHLC069#5&2a9e1f3&0&UID16843008"
HW_IVM_A = "IVM6132#5&1c8a4f2&0&UID4353"
HW_IVM_B = "IVM6132#5&1c8a4f2&0&UID4354"
HW_LG = "GSM5B7F#4&11aa22bb&0&UID4352"
HW_DELL = "DELA0B1#4&33cc44dd&0&UID4353"
HW_UNKNOWN = "ZZZ0001#4&55ee66ff&0&UID4354"


def real_config():
    return [
        mon("\\\\.\\DISPLAY2", -3840, 0, 1920, 1080, 509, 286, HW_PHL),
        mon("\\\\.\\DISPLAY3", -1920, 0, 1920, 1080, 544, 303, HW_IVM_B),
        mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 544, 303, HW_IVM_A),
    ]


def geometry_configs():
    """(id, moniteurs, [(nom_de_variante, réglages | None)])"""
    def phys(bezel, overrides=None):
        return {"enabled": True, "bezel_mm": bezel, "overrides": overrides or {}}

    pixels = ("pixels", {"enabled": False, "bezel_mm": 0.0, "overrides": {}})
    std = [pixels, ("physical_bezel0", phys(0.0)), ("physical_bezel15", phys(15.0))]
    return [
        ("real_triple", real_config(), [
            pixels, ("pixels_settings_none", None), ("physical_bezel0", phys(0.0)), ("physical_bezel15", phys(15.0)),
            ("physical_overrides", phys(15.0, {
                HW_PHL: {"width_mm": 527, "height_mm": 296, "offset_y_mm": 4.5},
                HW_IVM_B: {"offset_x_mm": -3, "offset_y_mm": 12},
            })),
            ("physical_disabled_with_overrides", {"enabled": False, "bezel_mm": 15.0, "overrides": {
                HW_PHL: {"width_mm": 527, "height_mm": 296}}}),
        ]),
        ("pair_27_and_24", [
            mon("\\\\.\\DISPLAY1", 0, 0, 2560, 1440, 597, 336, HW_LG),
            mon("\\\\.\\DISPLAY2", 2560, 360, 1920, 1080, 531, 299, HW_DELL),
        ], std + [("physical_bezel10", phys(10.0))]),
        ("stacked_two", [
            mon("\\\\.\\DISPLAY2", 0, -1080, 1920, 1080, 527, 296, HW_DELL),
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
        ], [pixels, ("physical_bezel5", phys(5.0))]),
        ("l_shape_three", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
            mon("\\\\.\\DISPLAY2", 0, 1080, 1920, 1080, 527, 296, HW_DELL),
            mon("\\\\.\\DISPLAY3", 1920, 0, 1920, 1080, 527, 296, HW_PHL),
        ], std),
        ("not_contiguous", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
            mon("\\\\.\\DISPLAY2", 2100, 200, 1920, 1080, 527, 296, HW_DELL),
        ], std),
        ("no_physical_sizes", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, None, None, None),
            mon("\\\\.\\DISPLAY2", 1920, 0, 2560, 1440, None, None, None),
        ], std),
        ("single_1440p", [mon("\\\\.\\DISPLAY1", 0, 0, 2560, 1440, 597, 336, HW_LG)], std),
        ("portrait_beside_landscape", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
            mon("\\\\.\\DISPLAY2", 1920, -420, 1080, 1920, 298, 530, HW_DELL),
        ], std),
        ("quad_2x2", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
            mon("\\\\.\\DISPLAY2", 1920, 0, 1920, 1080, 527, 296, HW_DELL),
            mon("\\\\.\\DISPLAY3", 0, 1080, 1920, 1080, 527, 296, HW_PHL),
            mon("\\\\.\\DISPLAY4", 1920, 1080, 1920, 1080, 527, 296, HW_IVM_A),
        ], std),
        ("primary_in_the_middle", [
            mon("\\\\.\\DISPLAY2", -2560, -200, 2560, 1440, 597, 336, HW_LG),
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 531, 299, HW_DELL),
            mon("\\\\.\\DISPLAY3", 1920, 100, 1920, 1080, 527, 296, HW_PHL),
        ], std),
        ("adjacent_with_2px_tolerance", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
            mon("\\\\.\\DISPLAY2", 1922, 0, 1920, 1080, 527, 296, HW_DELL),
        ], std),
        ("mirrored_same_rect", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
            mon("\\\\.\\DISPLAY2", 0, 0, 1920, 1080, 527, 296, HW_DELL),
        ], std),
        ("mixed_density_4k_and_1080p", [
            mon("\\\\.\\DISPLAY1", 0, 0, 3840, 2160, 597, 336, HW_LG),
            mon("\\\\.\\DISPLAY2", 3840, 0, 1920, 1080, 531, 299, HW_DELL),
        ], std),
        ("partial_sizes_known", [
            mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 527, 296, HW_LG),
            mon("\\\\.\\DISPLAY2", 1920, 0, 1920, 1080, None, None, HW_DELL),
        ], std + [("physical_override_supplies_size", phys(0.0, {HW_DELL: {"width_mm": 600, "height_mm": 340}}))]),
        ("empty", [], [pixels, ("physical_bezel0", phys(0.0))]),
    ]


def make_settings(spec):
    if spec is None:
        return None
    return dg.PhysicalSettings(spec["enabled"], spec["bezel_mm"], copy.deepcopy(spec["overrides"]))


def layout_results():
    out = []
    for cid, monitors, variants in geometry_configs():
        for vname, spec in variants:
            ms = copy.deepcopy(monitors)
            settings = make_settings(spec)
            positions = dg.physical_positions(ms, settings or dg.PhysicalSettings())
            size = dg.apply_layout(ms, settings)
            out.append({
                "id": "%s|%s" % (cid, vname), "config": cid, "variant": vname,
                "monitors": copy.deepcopy(monitors),
                "settings": spec,
                "physical_positions_mm": tup(positions),
                "size": list(size),
                "canvas": [tup(m["canvas"]) for m in ms] if ms else [],
            })
    return out


def signature_cases():
    out = []
    for cid, monitors, _ in geometry_configs():
        out.append(_sig_entry(cid, monitors))
    # Cas particuliers : ordre d'entrée différent, noms Unicode, ordre de tri par point de code
    real = real_config()
    out.append(_sig_entry("real_triple_reversed_input", list(reversed(real))))
    out.append(_sig_entry("unicode_names", [mon("Écran é", 0, 0, 1920, 1080), mon("日本語", 1920, 0, 1920, 1080)]))
    out.append(_sig_entry("sort_by_code_point_bmp_vs_astral",
                          [mon("\U0001F5A5", 0, 0, 1920, 1080), mon("\uff71", 0, 0, 1920, 1080)]))
    out.append(_sig_entry("same_name_sorted_by_coordinates", [
        mon("M", 1920, 0, 1920, 1080), mon("M", -1920, 0, 1920, 1080), mon("M", 0, 0, 1920, 1080)]))
    out.append(_sig_entry("name_missing_key", [{"x": 0, "y": 0, "width": 800, "height": 600}]))
    out.append(_sig_entry("quote_and_backslash_in_name", [mon("a\"b\\c'd\n", 0, 0, 1, 1)]))
    return out


def _sig_entry(cid, monitors):
    key = sorted((m.get("name", ""), m["x"], m["y"], m["width"], m["height"]) for m in monitors)
    return {"id": cid, "monitors": copy.deepcopy(monitors), "key_json": json.dumps(key),
            "signature": dg.layout_signature(monitors)}


WORDS = {
    "fr": {"left": "Gauche", "center": "Centre", "right": "Droite", "top": "Haut", "bottom": "Bas", "screen": "Écran {}"},
    "en": {"left": "Left", "center": "Center", "right": "Right", "top": "Top", "bottom": "Bottom", "screen": "Screen {}"},
}
LANGS = [("fr", ","), ("en", ".")]


def label_cases():
    cfg = {cid: (monitors, variants) for cid, monitors, variants in geometry_configs()}
    L = {}
    L["single_no_size"] = [mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080)]
    L["single_with_size_philips"] = [mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 509, 286, HW_PHL)]
    L["pair_row"] = cfg["pair_27_and_24"][0]
    L["pair_row_input_reversed"] = list(reversed(cfg["pair_27_and_24"][0]))
    L["real_triple"] = cfg["real_triple"][0]
    L["stacked_two"] = cfg["stacked_two"][0]
    L["stacked_two_input_reversed"] = list(reversed(cfg["stacked_two"][0]))
    L["four_in_row"] = [mon("\\\\.\\DISPLAY%d" % (k + 1), 1920 * k, 0, 1920, 1080, 527, 296, HW_LG) for k in range(4)]
    L["l_shape_three"] = cfg["l_shape_three"][0]
    L["quad_2x2"] = cfg["quad_2x2"][0]
    L["mirrored_same_rect"] = cfg["mirrored_same_rect"][0]
    L["three_stacked"] = [mon("\\\\.\\DISPLAY%d" % (k + 1), 0, 1080 * k, 1920, 1080) for k in range(3)]
    L["unknown_vendor_and_mixed_sizes"] = [
        mon("\\\\.\\DISPLAY1", 0, 0, 1920, 1080, 600, 340, HW_UNKNOWN),
        mon("\\\\.\\DISPLAY2", 1920, 0, 2560, 1440, None, None, HW_DELL),
        mon("\\\\.\\DISPLAY3", 4480, 0, 1280, 1024, 376, 301, None)]
    L["portrait_landscape"] = cfg["portrait_beside_landscape"][0]
    L["one_pixel_overlap_tolerance"] = [mon("A", 0, 0, 1920, 1080, 527, 296, HW_LG), mon("B", 1919, 0, 1920, 1080, 527, 296, HW_DELL)]
    L["diagonals_27_and_31_5"] = [mon("A", 0, 0, 2560, 1440, 596, 335, HW_LG), mon("B", 2560, 0, 3840, 2160, 697, 392, HW_LG)]
    L["empty"] = []

    out = []
    for cid, monitors in L.items():
        entry = {"id": cid, "monitors": copy.deepcopy(monitors), "results": []}
        for lang, dec in LANGS:
            entry["results"].append({"words_id": lang, "decimal": dec, "labels": dg.monitor_labels(copy.deepcopy(monitors), WORDS[lang], dec)})
        out.append(entry)
    # Avec « canvas » (le libellé se base alors sur les rectangles de composition)
    for cid, vname in (("real_triple", "physical_bezel15"), ("real_triple", "pixels"), ("l_shape_three", "physical_bezel0"),
                       ("stacked_two", "physical_bezel5"), ("pair_27_and_24", "physical_bezel10"),
                       ("not_contiguous", "physical_bezel15"), ("quad_2x2", "physical_bezel15")):
        monitors, variants = cfg[cid]
        spec = dict(variants)[vname]
        ms = copy.deepcopy(monitors)
        dg.apply_layout(ms, make_settings(spec))
        entry = {"id": "%s|canvas=%s" % (cid, vname), "monitors": copy.deepcopy(monitors), "settings": spec,
                 "canvas": [tup(m["canvas"]) for m in ms], "results": []}
        for lang, dec in LANGS:
            entry["results"].append({"words_id": lang, "decimal": dec, "labels": dg.monitor_labels(ms, WORDS[lang], dec)})
        out.append(entry)
    return out


def vendor_cases():
    hws = [HW_PHL, HW_IVM_A, HW_LG, "gsm5b7f#1", "DEL#x", "ZZZ0001#a", "ABC", "", None, "12#x", "A1B#x", "AB#x", "éAB#x",
           "ßAB#x", "SAM#1", "sam#1", "XMI#1", "LGD#1", "BOE#1", "HWP#1", "ENC#1", "#abc", "ABC#", "ǅAB#x", "ΑΒΓ#x", "日本語#x"]
    return [{"hw_id": h, "vendor": dg.monitor_vendor({"hw_id": h})} for h in hws] + \
           [{"hw_id": "<absent>", "vendor": dg.monitor_vendor({})}]


def upscale_cases():
    specs = [
        ("identity", (1920, 1080), 0, None, (1920, 1080)),
        ("stretched_2_5x", (1000, 600), 0, None, (2500, 1500)),
        ("downscaled", (6000, 4000), 0, None, (1920, 1280)),
        ("rotated_90_swaps", (4000, 3000), 3, None, (1080, 1440)),
        ("rotated_270_swaps", (4000, 3000), 1, None, (3000, 4000)),
        ("rotated_180_keeps", (4000, 3000), 2, None, (2000, 1500)),
        ("cropped_half_width", (4000, 3000), 0, (0.25, 0.0, 0.75, 1.0), (4000, 3000)),
        ("cropped_square", (6000, 4000), 0, (0.2, 0.0, 0.8, 1.0), (1000, 1000)),
        ("cropped_and_rotated", (4000, 3000), 1, (0.1, 0.2, 0.9, 0.6), (1920, 1080)),
        ("tiny_crop_clamped_to_1px", (1000, 1000), 0, (0.5, 0.5, 0.5, 0.5), (500, 500)),
        ("height_dominates", (2000, 500), 0, None, (2000, 1500)),
        ("fractional_displayed_size", (3000, 2000), 0, None, (1921, 1081)),
        ("crop_tiny_nonzero", (800, 600), 0, (0.0, 0.0, 0.0005, 1.0), (640, 360)),
    ]
    out = []
    for cid, size, rots, crop, disp in specs:
        img = make_image("C:\\x\\u.jpg", size[0], size[1], (0.5, 0.5))
        for _ in range(rots):
            img.rotate_cw()
        if crop:
            img.crop_box_norm = crop
        img.w, img.h = disp
        out.append({"id": cid, "original_size": list(size), "angle": img.angle, "crop": tup(img.crop_box_norm),
                    "w": img.w, "h": img.h, "factor": dg.upscale_factor(img)})
    return out


def settings_cases():
    inputs = [None, {}, {"enabled": True}, {"enabled": 1, "bezel_mm": "12.5", "overrides": {"a": {"width_mm": 1}}},
              {"enabled": "", "bezel_mm": 3}, {"enabled": True, "bezel_mm": 15, "overrides": {"X#1": {"offset_x_mm": -2.5}}}]
    out = []
    for d in inputs:
        s = dg.PhysicalSettings.from_dict(d)
        out.append({"input": d, "to_dict": s.to_dict()})
    return out


def geometry_body(layouts):
    diag = [(509, 286), (544, 303), (527, 296), (597, 336), (600, 340), (1, 1), (0, 0), (298, 530), (696.5, 391.8), (254, 0)]
    return {
        "edid": edid_cases(),
        "diagonal_inches": [{"width_mm": w, "height_mm": h, "inches": dg.diagonal_inches(w, h)} for w, h in diag],
        "vendors": vendor_cases(),
        "labels": label_cases(),
        "upscale_factor": upscale_cases(),
        "physical_settings": settings_cases(),
        "layouts": layouts,
        "signatures": signature_cases(),
    }


# --------------------------------------------------------------------------------------
# 7. services.json
# --------------------------------------------------------------------------------------

def services_body():
    theme_paths = [
        "C:\\Users\\Patrick\\AppData\\Roaming\\Microsoft\\Windows\\Themes\\TranscodedWallpaper",
        "C:\\Users\\Patrick\\AppData\\Roaming\\Microsoft\\Windows\\Themes\\CachedFiles\\CachedImage_1920_1080_POS4.jpg",
        "C:\\Users\\Patrick\\AppData\\Roaming\\Microsoft\\Windows\\Themes\\transcodedwallpaper",
        "C:\\Users\\Patrick\\AppData\\Local\\Microsoft\\Windows\\Themes\\RoamedThemeFiles\\DesktopBackground\\a.jpg",
        "C:\\Windows\\Web\\Wallpaper\\Windows\\img0.jpg",
        "C:\\WINDOWS\\WEB\\4K\\Wallpaper\\Windows\\img0_3840x2160.jpg",
        "c:/windows/web/screen/img100.jpg",
        "C:\\Users\\Patrick\\AppData\\Local\\Packages\\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\\LocalState\\Assets\\abc",
        "C:\\Users\\Patrick\\AppData\\Local\\Packages\\MicrosoftWindows.Client.CBS\\LocalState\\Spotlight\\x.jpg",
        "C:\\ProgramData\\Microsoft\\Windows\\SystemData\\S-1-5-18\\ReadOnly\\LockScreen\\img.jpg",
        "C:\\Users\\Patrick\\Pictures\\spotlight_backup.jpg",
        "C:\\Users\\Patrick\\Pictures\\mon TranscodedWallpaper perso.jpg",
        "C:\\Users\\Patrick\\Pictures\\vacances\\IMG_0001.jpg",
        "D:\\Fonds\\wallcraft_20261112-101500_pos_00.png",
        "C:\\Users\\Patrick\\AppData\\Local\\WallCraft\\configs\\abc\\wallcraft_1_pos_00.png",
        "\\\\serveur\\partage\\fonds\\a.png",
        "C:\\Users\\Patrick\\AppData\\Roaming\\Microsoft\\Windows\\Themes",
        "C:\\Users\\Patrick\\Microsoft\\Windows\\Themes\\a.jpg",
        "/usr/share/backgrounds/a.jpg",
        "/Microsoft/Windows/Themes/x.jpg",
        "C:\\İstanbul\\SPOTLIGHT.jpg",
        "",
        None,
    ]
    is_theme = [{"path": p, "result": services.is_theme_wallpaper(p)} for p in theme_paths]

    A = "C:\\Users\\Patrick\\AppData\\Local\\WallCraft\\configs\\abc\\wallcraft_1_pos_00.png"
    B = "C:\\Users\\Patrick\\AppData\\Local\\WallCraft\\configs\\abc\\wallcraft_1_pos_01.png"
    THEME = "C:\\Users\\Patrick\\AppData\\Roaming\\Microsoft\\Windows\\Themes\\TranscodedWallpaper"
    WINWEB = "C:\\Windows\\Web\\Wallpaper\\Windows\\img0.jpg"
    USER = "C:\\Users\\Patrick\\Pictures\\vacances\\IMG_0001.jpg"
    specs = [
        ("nothing_changed", [A, B], [{"path": A}, {"path": B}]),
        ("one_theme", [A, B], [{"path": A}, {"path": THEME}]),
        ("all_theme_two_kinds", [A, B], [{"path": THEME}, {"path": WINWEB}]),
        ("one_user", [A, B], [{"path": A}, {"path": USER}]),
        ("mixed_theme_and_user", [A, B], [{"path": THEME}, {"path": USER}]),
        ("different_case", [A, B], [{"path": A.upper()}, {"path": B.lower()}]),
        ("forward_slashes_same_file", [A, B], [{"path": A.replace("\\", "/")}, {"path": B}]),
        ("dotdot_normalised", [A], [{"path": "C:\\Users\\Patrick\\AppData\\Local\\WallCraft\\configs\\x\\..\\abc\\wallcraft_1_pos_00.png"}]),
        ("expected_empty", [], [{"path": USER}]),
        ("current_empty", [A], []),
        ("both_empty", [], []),
        ("empty_path_counts_as_theme", [A], [{"path": ""}]),
        ("missing_path_key", [A, B], [{"path": A}, {}]),
        ("none_path", [A], [{"path": None}]),
        ("fewer_current_than_expected", [A, B], [{"path": A}]),
        ("more_current_than_expected", [A], [{"path": A}, {"path": USER}]),
        ("current_swapped_order", [A, B], [{"path": B}, {"path": A}]),
        ("unc_path_user", [A], [{"path": "\\\\serveur\\partage\\a.png"}]),
    ]
    changes = []
    with windows_paths():
        for cid, expected, current in specs:
            changes.append({"id": cid, "expected_paths": expected, "current": current,
                            "result": services.wallpaper_change(expected, current)})

    files = ["D:\\Fonds\\f%02d.jpg" % k for k in range(10)]
    big = ["D:\\Fonds\\g%02d.jpg" % k for k in range(40)]
    rot_specs = [
        ("basic", 3, files, [], 11),
        ("avoid_previous", 3, files, files[:3], 11),
        ("pool_too_small_falls_back_to_all", 4, files, files[:8], 5),
        ("count_greater_than_files", 12, files, [], 99),
        ("big_pool_set_algorithm", 3, big, big[:5], 2 ** 32 + 5),
        ("single_file", 1, ["D:\\Fonds\\only.jpg"], [], 0),
        ("count_zero", 0, files, [], 1),
        ("empty_files", 3, [], [], 1),
        ("previous_not_in_files", 2, files, ["Z:\\nope.jpg"], 7),
    ]
    picks = [{"id": cid, "count": c, "files": f, "previous": p, "seed": s,
              "result": services.pick_rotation(f, c, p, rng=random.Random(s))} for cid, c, f, p, s in rot_specs]
    return {"is_theme_wallpaper": is_theme, "wallpaper_change": changes, "pick_rotation": picks}


# --------------------------------------------------------------------------------------
# 8. split.json
# --------------------------------------------------------------------------------------

class _RecImage:
    """Image factice : enregistre le rectangle passé à crop() et rend une image noire de cette taille."""

    def __init__(self, size):
        self.size = size
        self.boxes = []

    def crop(self, box):
        self.boxes.append(tuple(box))
        return Image.new("RGB", (box[2] - box[0], box[3] - box[1]))


def split_one(monitors, image_size, tmp):
    rec = _RecImage(image_size)
    results = screen_splitter.split_wallpaper_by_monitors(rec, monitors, tmp, "g")
    done = {id(m): k for k, (m, _) in enumerate(results)}
    out, calls = [], iter(rec.boxes)
    for i, m in enumerate(monitors):
        if id(m) not in done:
            out.append({"index": i, "box": None, "rect": None, "monitor_size": [m["width"], m["height"]]})
            continue
        box = next(calls)
        out.append({"index": i, "box": list(box), "rect": [box[0], box[1], box[2] - box[0], box[3] - box[1]],
                    "monitor_size": [m["width"], m["height"]],
                    "resized": (box[2] - box[0], box[3] - box[1]) != (m["width"], m["height"])})
    return out


def split_cases(layouts):
    out = []
    with tempfile.TemporaryDirectory(prefix="wallcraft_golden_") as tmp:
        for lay in layouts:
            if not lay["monitors"]:
                continue
            ms = copy.deepcopy(lay["monitors"])
            size = dg.apply_layout(ms, make_settings(lay["settings"]))
            rects = [m["canvas"] for m in ms]
            comp = (max(r[0] + r[2] for r in rects), max(r[1] + r[3] for r in rects))
            sizes = [("composition_size", size), ("half", (size[0] // 2, size[1] // 2)),
                     ("double", (size[0] * 2, size[1] * 2)), ("odd_scale", (size[0] + 37, size[1] - 11))]
            for sname, isz in sizes:
                if lay["variant"] not in ("pixels", "physical_bezel15", "physical_overrides") and sname in ("half", "odd_scale"):
                    continue
                out.append({"id": "%s|%s" % (lay["id"], sname), "layout": lay["id"], "mode": "canvas",
                            "image_size": list(isz), "composition_size_returned": list(size),
                            "composition_size_from_canvas": list(comp),
                            "canvas": [tup(r) for r in rects],
                            "pieces": split_one(ms, tuple(isz), tmp)})
            # Repli sans « canvas » : grille du bureau virtuel Windows
            if lay["variant"] == "pixels":
                raw = copy.deepcopy(lay["monitors"])
                x0, y0, x1, y1 = screen_splitter.virtual_desktop_bbox(raw)
                for sname, isz in (("bbox_size", (x1 - x0, y1 - y0)), ("half", ((x1 - x0) // 2, (y1 - y0) // 2))):
                    out.append({"id": "%s|no_canvas|%s" % (lay["id"], sname), "layout": lay["id"], "mode": "no_canvas",
                                "image_size": list(isz), "composition_size_from_canvas": [x1 - x0, y1 - y0],
                                "bbox": [x0, y0, x1, y1], "pieces": split_one(raw, tuple(isz), tmp)})
        # Rectangle vide / hors image
        ms = [dict(mon("A", 0, 0, 100, 100), canvas=(0, 0, 100, 100)), dict(mon("B", 100, 0, 100, 100), canvas=(100, 0, 0, 100)),
              dict(mon("C", 200, 0, 100, 100), canvas=(5000, 0, 100, 100)), dict(mon("D", 300, 0, 100, 100), canvas=(250, 0, 100, 100))]
        out.append({"id": "edge|empty_and_outside_rects", "layout": None, "mode": "canvas", "image_size": [300, 100],
                    "composition_size_from_canvas": [5100, 100], "canvas": [tup(m["canvas"]) for m in ms],
                    "pieces": split_one(ms, (300, 100), tmp)})
    return out


# --------------------------------------------------------------------------------------

def main():
    os.makedirs(FIXTURES, exist_ok=True)
    _install_monitor()
    written = []

    seeds = seeds_cases()
    written.append((dump("seeds.json", "Graine de AutoLayoutStrategy._seed : chaîne key (repr du tuple), sha1 et graine entière. "
                         "`ratio` = valeur brute renvoyée par visible_aspect(), `ratio_rounded` = round(ratio, 4).",
                         {"cases": seeds}), len(seeds)))

    rnd = random_cases(seeds)
    written.append((dump("random.json", "random.Random(seed) de Python (Mersenne Twister) : nouvelle instance pour chaque séquence, "
                         "sauf shuffle_chain (une instance, 3 mélanges successifs).", {"seeds": rnd}), len(rnd)))

    lays = layout_cases()
    for old in os.listdir(FIXTURES):
        if old.startswith("layouts") and old.endswith(".json"):
            os.remove(os.path.join(FIXTURES, old))
    text_probe = json.dumps(lays, indent=1, ensure_ascii=False)
    desc = ("AutoLayoutStrategy.apply sur des images en mémoire, point d'intérêt fixé. result = une entrée par image, "
            "dans l'ordre d'entrée. optimal = recherche du meilleur arbre (mode optimal avec 2 images ou plus).")
    if len(text_probe.encode("utf-8")) > 15 * 1024 * 1024:
        for mode in MODES:
            part = [c for c in lays if c["mode"] == mode]
            written.append((dump("layouts_%s.json" % mode, desc, {"max_time_disabled": True, "cases": part},
                                 max_time_disabled=True), len(part)))
    else:
        written.append((dump("layouts.json", desc, {"max_time_disabled": True, "cases": lays}, max_time_disabled=True), len(lays)))

    var = variants_cases()
    written.append((dump("variants.json", "AutoLayoutStrategy.variants(mode, tw, th, images, fill, count=4) : placements distincts.",
                         {"max_time_disabled": True, "cases": var}, max_time_disabled=True), len(var)))

    pl = placement_cases()
    written.append((dump("placement.json", "_apply_fit_inside et _apply_crop_cover appelées directement. Le focus est fixé ; "
                         "result.w/h valent null quand la boîte est vide (rien n'est modifié).", {"cases": pl}), len(pl)))

    lay_res = layout_results()
    geo = geometry_body(lay_res)
    written.append((dump("geometry.json", "display_geometry.py : EDID, diagonales, fabricants, libellés, upscale_factor, réglages, "
                         "physical_positions/apply_layout (layouts) et layout_signature.", geo),
                     sum(len(v) for v in geo.values())))

    sv = services_body()
    written.append((dump("services.json", "services.py : is_theme_wallpaper, wallpaper_change (avec ntpath, donc sémantique Windows : "
                         "casse et séparateurs ignorés) et pick_rotation.", sv, path_semantics="ntpath (Windows)"),
                     sum(len(v) for v in sv.values())))

    sp = split_cases(lay_res)
    written.append((dump("split.json", "Rectangles source (x, y, w, h) découpés par split_wallpaper_by_monitors pour chaque écran. "
                         "box = (gauche, haut, droite, bas) après arrondi et écrêtage ; resized = redimensionnement LANCZOS ensuite.",
                         {"cases": sp}), len(sp)))

    for path, n in written:
        print("%-60s %9d octets  %5d éléments" % (os.path.relpath(path, ROOT), os.path.getsize(path), n))


if __name__ == "__main__":
    main()
