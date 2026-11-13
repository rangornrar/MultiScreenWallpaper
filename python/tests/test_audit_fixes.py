"""Tests des corrections issues de l'audit de novembre 2026."""
import json
import random
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from image_tools import (AutoLayoutStrategy, LoadedImage, compose_wallpaper_contain,
                         load_images_from_paths, load_project_json, save_project_json)
from screen_splitter import match_monitors, split_wallpaper_by_monitors, virtual_desktop_bbox


def solid(size, color="red"):
    return Image.new("RGB", size, color)


class LoadingTests(unittest.TestCase):
    def test_exif_orientation_is_applied(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "portrait.jpg"
            exif = Image.Exif()
            exif[0x0112] = 6  # capteur en paysage, photo prise en portrait
            solid((400, 300)).save(path, "JPEG", exif=exif)
            image = load_images_from_paths([str(path)])[0]
            self.assertEqual(image.original_size, (300, 400))
            self.assertAlmostEqual(image.current_aspect(), 0.75)
            self.assertEqual(image.original_image.size, (300, 400))

    def test_file_backed_original_is_not_kept_in_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "big.png"
            solid((2000, 1000)).save(path)
            image = load_images_from_paths([str(path)])[0]
            self.assertIsNone(image._original)
            self.assertLessEqual(max(image.low_res_image.size), 1024)
            self.assertEqual(image.original_image.size, (2000, 1000))

    def test_load_errors_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.jpg"
            bad.write_bytes(b"not an image")
            errors = []
            self.assertEqual(load_images_from_paths([str(bad)], errors), [])
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0][0], str(bad))


class GeometryTests(unittest.TestCase):
    def test_visible_aspect_follows_crop(self):
        image = LoadedImage("x", solid((200, 100)))
        image.crop_box_norm = (0.0, 0.0, 0.5, 1.0)
        self.assertAlmostEqual(image.visible_aspect(), 1.0)
        AutoLayoutStrategy._apply_fit_inside(image, 0, 0, 1000, 500)
        self.assertEqual((image.w, image.h), (500, 500))
        self.assertEqual(image.crop_box_norm, (0.0, 0.0, 0.5, 1.0))

    def test_optimal_layout_avoids_tiny_images(self):
        random.seed(7)
        images = [LoadedImage(str(i), solid((random.choice([1920, 1080, 4000, 800]),
                                             random.choice([1080, 1920, 3000, 1200]))))
                  for i in range(12)]
        AutoLayoutStrategy._optimal_fit(5760, 1080, images, max_time=0.3)
        areas = [i.w * i.h for i in images]
        self.assertGreater(min(areas) / max(areas), 0.05)
        self.assertGreater(sum(areas) / (5760 * 1080), 0.85)

    def test_export_has_no_gap_between_adjacent_images(self):
        left = LoadedImage("l", solid((10, 10), "red"))
        right = LoadedImage("r", solid((10, 10), "blue"))
        left.x, left.y, left.w, left.h = 0.6, 0, 10, 10
        right.x, right.y, right.w, right.h = 10.6, 0, 10, 10
        result = compose_wallpaper_contain((25, 10), [left, right], "black")
        row = [result.getpixel((x, 5)) for x in range(1, 21)]
        self.assertNotIn((0, 0, 0), row)

    def test_slice_preview_matches_logical_region(self):
        image = LoadedImage("x", solid((400, 100), "red"))
        image.low_res_image.paste((0, 0, 255), (200, 0, 400, 100))
        image.w, image.h = 4000, 1000
        piece = image.get_slice_image(2000, 0, 4000, 1000, 50, 20)
        self.assertEqual(piece.getpixel((25, 10))[:3], (0, 0, 255))


class MonitorTests(unittest.TestCase):
    def setUp(self):
        # Écran principal, un écran à gauche en coordonnées négatives et un écran posé au-dessus.
        self.monitors = [
            {"x": -1920, "y": 0, "width": 1920, "height": 1080, "name": "L", "device_id": "L"},
            {"x": 0, "y": 0, "width": 2560, "height": 1440, "name": "M", "device_id": "M"},
            {"x": 0, "y": -1080, "width": 1920, "height": 1080, "name": "T", "device_id": "T"},
        ]

    def test_split_produces_one_image_per_monitor_at_native_size(self):
        x0, y0, x1, y1 = virtual_desktop_bbox(self.monitors)
        canvas = Image.new("RGB", (x1 - x0, y1 - y0), "black")
        with tempfile.TemporaryDirectory() as directory:
            results = split_wallpaper_by_monitors(canvas, self.monitors, directory, "t")
            self.assertEqual(len(results), 3)
            for monitor, path in results:
                with Image.open(path) as piece:
                    self.assertEqual(piece.size, (monitor["width"], monitor["height"]))

    def test_stacked_monitors_are_matched_by_rectangle(self):
        split = [(m, f"{m['name']}.png") for m in self.monitors]
        # Windows énumère dans un autre ordre ; T et M partagent la même abscisse.
        windows = [
            {"id": "\\\\?\\DISPLAY#M", "rect": (0, 0, 2560, 1440)},
            {"id": "\\\\?\\DISPLAY#T", "rect": (0, -1080, 1920, 0)},
            {"id": "\\\\?\\DISPLAY#L", "rect": (-1920, 0, 0, 1080)},
        ]
        pairs, unmatched = match_monitors(split, windows)
        self.assertEqual(unmatched, [])
        self.assertEqual(dict((path, mid) for mid, path in pairs), {
            "L.png": "\\\\?\\DISPLAY#L", "M.png": "\\\\?\\DISPLAY#M", "T.png": "\\\\?\\DISPLAY#T"})

    def test_image_without_matching_screen_is_reported(self):
        split = [(m, f"{m['name']}.png") for m in self.monitors]
        windows = [{"id": "M", "rect": (0, 0, 2560, 1440)}]
        pairs, unmatched = match_monitors(split, windows)
        self.assertEqual(pairs, [("M", "M.png")])
        self.assertEqual(sorted(unmatched), ["L.png", "T.png"])


class ProjectTests(unittest.TestCase):
    def test_save_does_not_modify_input_and_writes_version(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "a.png"
            solid((20, 10)).save(source)
            data = {"meta": {}, "images": [{"path": str(source), "x": 0, "y": 0, "w": 20, "h": 10}]}
            project = Path(directory) / "p.json"
            save_project_json(str(project), data)
            self.assertEqual(data["images"][0]["path"], str(source))
            saved = json.loads(project.read_text(encoding="utf-8"))
            self.assertEqual(saved["version"], 1)
            self.assertEqual(saved["images"][0]["path"], "a.png")

    def test_missing_and_invalid_images_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / "good.png"
            solid((20, 10)).save(good)
            project = Path(directory) / "p.json"
            project.write_text(json.dumps({"version": 1, "images": [
                {"path": "good.png", "x": 1, "y": 2, "w": 20, "h": 10},
                {"path": "missing.png"},
                {"path": "good.png", "w": "large"},
            ]}), encoding="utf-8")
            errors = []
            _meta, images = load_project_json(str(project), errors)
            self.assertEqual(len(images), 1)
            self.assertEqual([e[0] for e in errors], ["missing.png", "good.png"])

    def test_future_schema_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "p.json"
            project.write_text(json.dumps({"version": 99, "images": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_project_json(str(project))


if __name__ == "__main__":
    unittest.main()
