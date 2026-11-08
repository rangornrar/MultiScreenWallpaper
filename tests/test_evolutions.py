"""Tests des évolutions de novembre 2026 : taille réelle, Remplir, variantes, fond automatique."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import facefocus
from display_geometry import (PhysicalSettings, apply_layout, diagonal_inches, layout_signature,
                              parse_edid_size_mm)
from image_tools import AutoLayoutStrategy, LoadedImage, load_project_json, save_project_json
from screen_splitter import split_wallpaper_by_monitors
from services import ConfigStore, pick_rotation, wallpaper_was_replaced


def solid(size, color="red"):
    return Image.new("RGB", size, color)


def monitors_27_between_24s():
    """24″ 1080p | 27″ 1440p | 24″ 1080p, alignés en haut dans Windows."""
    return [
        {"name": "L", "hw_id": "L", "x": -1920, "y": 0, "width": 1920, "height": 1080, "width_mm": 531.0, "height_mm": 299.0},
        {"name": "C", "hw_id": "C", "x": 0, "y": 0, "width": 2560, "height": 1440, "width_mm": 597.0, "height_mm": 336.0},
        {"name": "R", "hw_id": "R", "x": 2560, "y": 0, "width": 1920, "height": 1080, "width_mm": 531.0, "height_mm": 299.0},
    ]


class EdidTests(unittest.TestCase):
    def edid(self, w_mm, h_mm, cm=(0, 0)):
        data = bytearray(128)
        data[:8] = b"\x00\xff\xff\xff\xff\xff\xff\x00"
        data[21], data[22] = cm
        d = 54
        data[d], data[d + 1] = 0x01, 0x1D  # horloge pixel non nulle : descripteur de timing
        data[d + 12] = w_mm & 0xFF
        data[d + 13] = h_mm & 0xFF
        data[d + 14] = ((w_mm >> 8) << 4) | (h_mm >> 8)
        return bytes(data)

    def test_detailed_descriptor_in_mm(self):
        self.assertEqual(parse_edid_size_mm(self.edid(597, 336)), (597.0, 336.0))

    def test_fallback_to_centimetres(self):
        self.assertEqual(parse_edid_size_mm(self.edid(0, 0, cm=(53, 30))), (530.0, 300.0))

    def test_invalid_edid(self):
        self.assertIsNone(parse_edid_size_mm(b"garbage" * 30))
        self.assertIsNone(parse_edid_size_mm(None))

    def test_diagonal(self):
        self.assertAlmostEqual(diagonal_inches(597, 336), 27.0, places=0)


class PhysicalLayoutTests(unittest.TestCase):
    def test_pixel_mode_matches_virtual_desktop(self):
        mons = monitors_27_between_24s()
        self.assertEqual(apply_layout(mons, PhysicalSettings(enabled=False)), (6400, 1440))
        self.assertEqual(mons[0]["canvas"], (0, 0, 1920, 1080))
        self.assertEqual(mons[1]["canvas"], (1920, 0, 2560, 1440))

    def test_real_size_mode_uses_one_scale_and_bezel_gap(self):
        mons = monitors_27_between_24s()
        apply_layout(mons, PhysicalSettings(enabled=True, bezel_mm=20))
        density = [m["canvas"][2] / m["width_mm"] for m in mons]
        self.assertLess(max(density) / min(density), 1.01)
        left, center = mons[0]["canvas"], mons[1]["canvas"]
        gap_mm = (center[0] - (left[0] + left[2])) / density[0]
        self.assertAlmostEqual(gap_mm, 20, delta=0.5)
        # Les écrans sont centrés verticalement l'un sur l'autre.
        self.assertAlmostEqual(left[1] + left[3] / 2, center[1] + center[3] / 2, delta=2)
        # Aucun écran n'est agrandi : la densité est celle de l'écran le plus fin.
        self.assertGreaterEqual(min(m["canvas"][2] / m["width"] for m in mons), 0.999)

    def test_vertical_offset_override(self):
        mons = monitors_27_between_24s()
        apply_layout(mons, PhysicalSettings(enabled=True))
        y_before = mons[2]["canvas"][1]
        mons = monitors_27_between_24s()
        apply_layout(mons, PhysicalSettings(enabled=True, overrides={"R": {"offset_y_mm": 30}}))
        density = mons[1]["canvas"][2] / 597.0
        self.assertAlmostEqual((mons[2]["canvas"][1] - y_before) / density, 30, delta=1)

    def test_split_uses_canvas_rects_and_native_resolution(self):
        mons = monitors_27_between_24s()
        size = apply_layout(mons, PhysicalSettings(enabled=True, bezel_mm=20))
        with tempfile.TemporaryDirectory() as directory:
            results = split_wallpaper_by_monitors(Image.new("RGB", size), mons, directory, "t")
            for m, path in results:
                with Image.open(path) as piece:
                    self.assertEqual(piece.size, (m["width"], m["height"]))

    def test_signature_changes_with_screens(self):
        a = monitors_27_between_24s()
        self.assertEqual(layout_signature(a), layout_signature(list(reversed(monitors_27_between_24s()))))
        self.assertNotEqual(layout_signature(a), layout_signature(a[:2]))


def images(n, seed=3):
    import random
    r = random.Random(seed)
    return [LoadedImage(f"/photos/{i}.jpg", solid((r.choice([1920, 1080, 4000, 800]), r.choice([1080, 1920, 3000, 1200]))))
            for i in range(n)]


class LayoutTests(unittest.TestCase):
    def geometry(self, imgs):
        return [(round(i.x, 3), round(i.y, 3), i.w, i.h, i.crop_box_norm) for i in imgs]

    def test_layouts_are_deterministic(self):
        for mode in ("layout_optimal", "layout_mosaic", "layout_grid", "layout_lines"):
            a, b = images(6), images(6)
            AutoLayoutStrategy.apply(mode, 5760, 1080, a)
            AutoLayoutStrategy.apply(mode, 5760, 1080, b)
            self.assertEqual(self.geometry(a), self.geometry(b), mode)

    def test_fill_covers_whole_surface_without_distortion(self):
        for mode in ("layout_optimal", "layout_mosaic", "layout_grid", "layout_lines", "layout_v_strip"):
            imgs = images(5)
            for i in imgs:
                i.focus = (0.5, 0.5)
            AutoLayoutStrategy.apply(mode, 5760, 1080, imgs, fill=True)
            coverage = sum(i.w * i.h for i in imgs) / (5760 * 1080)
            self.assertGreater(coverage, 0.98, mode)
            for i in imgs:
                self.assertAlmostEqual(i.w / i.h, i.visible_aspect(), delta=0.03 * i.visible_aspect())

    def test_cover_crop_follows_focus(self):
        img = LoadedImage("x", solid((4000, 1000)))
        img.focus = (0.9, 0.5)
        AutoLayoutStrategy._apply_crop_cover(img, 0, 0, 1000, 1000)
        left, top, right, bottom = img.crop_box_norm
        self.assertAlmostEqual(right - left, 0.25)
        self.assertAlmostEqual(right, 1.0)  # la fenêtre reste dans l'image
        img.focus = (0.5, 0.5)
        AutoLayoutStrategy._apply_crop_cover(img, 0, 0, 1000, 1000)
        self.assertAlmostEqual(img.crop_box_norm[0], 0.375)

    def test_variants_are_distinct(self):
        placements = AutoLayoutStrategy.variants("layout_optimal", 5760, 1080, images(5), count=4)
        self.assertEqual(len(placements), 4)
        keys = {tuple((round(p[0]), round(p[1]), p[2], p[3]) for p in pl) for pl in placements}
        self.assertEqual(len(keys), 4)

    def test_place_on_screens(self):
        imgs = images(2)
        AutoLayoutStrategy.place_on_screens(imgs, [(0, 0, 1920, 1080), (1920, 0, 1080, 1920)], fill=True)
        self.assertEqual((imgs[1].x, imgs[1].w, imgs[1].h), (1920, 1080, 1920))


class FocusTests(unittest.TestCase):
    def test_focus_from_faces_weighted_by_size(self):
        fx, fy = facefocus.focus_from_faces([(100, 100, 100, 100), (700, 100, 20, 20)], (1000, 500))
        self.assertLess(abs(fx - 0.15), 0.05)
        self.assertLess(fy, 0.35)

    def test_detail_fallback_points_to_textured_area(self):
        img = Image.new("RGB", (400, 200), "black")
        for x in range(300, 400, 6):
            img.paste((255, 255, 255), (x, 0, x + 3, 200))
        fx, _ = facefocus.focus_from_detail(img)
        self.assertGreater(fx, 0.6)

    def test_find_focus_never_fails(self):
        fx, fy = facefocus.find_focus(Image.new("RGB", (64, 64), "gray"))
        self.assertTrue(0 <= fx <= 1 and 0 <= fy <= 1)

    def test_focus_is_saved_in_projects(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "a.png"
            solid((40, 20)).save(src)
            project = Path(directory) / "p.json"
            save_project_json(str(project), {"images": [{"path": str(src), "focus": [0.2, 0.7]}]})
            _meta, loaded = load_project_json(str(project))
            self.assertEqual(loaded[0]._focus, (0.2, 0.7))


class ServiceTests(unittest.TestCase):
    def test_config_store_roundtrip_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(directory)
            mons = monitors_27_between_24s()
            folder = store.dir_for(mons[:1])
            old = Path(folder) / "wallcraft_old_pos_00.png"
            solid((10, 10)).save(old)
            new = Path(folder) / "wallcraft_new_pos_00.png"
            solid((10, 10)).save(new)
            store.save(mons[:1], [(mons[0], str(new))], "wallcraft_new")
            self.assertFalse(old.exists())
            self.assertEqual(store.load(monitors_27_between_24s()), [])  # autre configuration
            loaded = store.load(mons[:1])
            self.assertEqual(Path(loaded[0][1]).name, new.name)
            manifest = json.loads((Path(store.dir_for(mons[:1])) / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["screens"][0]["width"], 1920)

    def test_wallpaper_replacement_detection(self):
        ours = [os.path.join("C:", "WallCraft", "a.png"), os.path.join("C:", "WallCraft", "b.png")]
        same = [{"path": ours[0]}, {"path": ours[1]}]
        theme = [{"path": ours[0]}, {"path": os.path.join("C:", "Windows", "img20.jpg")}]
        self.assertFalse(wallpaper_was_replaced(ours, same))
        self.assertTrue(wallpaper_was_replaced(ours, theme))
        self.assertFalse(wallpaper_was_replaced([], theme))

    def test_rotation_avoids_previous_images(self):
        import random
        files = [f"{i}.jpg" for i in range(6)]
        first = pick_rotation(files, 3, rng=random.Random(1))
        second = pick_rotation(files, 3, previous=first, rng=random.Random(2))
        self.assertFalse(set(first) & set(second))
        self.assertEqual(len(pick_rotation(files[:2], 3)), 2)


if __name__ == "__main__":
    unittest.main()
