import random
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from image_tools import (AutoLayoutStrategy, LoadedImage, compose_wallpaper_contain,
                         load_project_json, save_project_json)


class ImageToolsTests(unittest.TestCase):
    def make_images(self):
        return [LoadedImage(str(i), Image.new("RGB", size, "red"))
                for i, size in enumerate([(200, 100), (80, 160), (120, 120), (300, 100)])]

    def test_layouts_preserve_full_images_and_stay_in_bounds(self):
        for mode in ("layout_grid", "layout_lines", "layout_mosaic", "layout_v_strip",
                     "layout_h_strip", "layout_optimal"):
            with self.subTest(mode=mode):
                random.seed(42)
                images = self.make_images()
                AutoLayoutStrategy.apply(mode, 1920, 1080, images)
                for image in images:
                    self.assertGreater(image.w, 0)
                    self.assertGreater(image.h, 0)
                    self.assertGreaterEqual(image.x, -0.001)
                    self.assertGreaterEqual(image.y, -0.001)
                    self.assertLessEqual(image.x + image.w, 1920.001)
                    self.assertLessEqual(image.y + image.h, 1080.001)
                    self.assertEqual(image.crop_box_norm, (0, 0, 1, 1))
                    self.assertLessEqual(abs(image.w - image.h * image.current_aspect()),
                                         1 + image.current_aspect())
                for i, first in enumerate(images):
                    for second in images[i + 1:]:
                        overlap_w = min(first.x + first.w, second.x + second.w) - max(first.x, second.x)
                        overlap_h = min(first.y + first.h, second.y + second.h) - max(first.y, second.y)
                        self.assertFalse(overlap_w > 0.001 and overlap_h > 0.001)

    def test_empty_layout_is_supported(self):
        AutoLayoutStrategy.apply("layout_optimal", 1920, 1080, [])

    def test_rotation_updates_ratio_and_clears_preview_cache(self):
        image = self.make_images()[0]
        image._preview_cache["old"] = object()
        image.rotate_cw()
        self.assertEqual(image.current_aspect(), 0.5)
        self.assertEqual(image._preview_cache, {})

    def test_clone_preserves_edits_without_sharing_preview_cache(self):
        image = self.make_images()[0]
        image.brightness = 0.8
        clone = image.clone()
        clone._preview_cache["new"] = object()
        clone.x = 42
        self.assertEqual(image.x, 0)
        self.assertEqual(image._preview_cache, {})
        self.assertEqual(clone.brightness, 0.8)
        self.assertIs(clone.original_image, image.original_image)

    def test_project_round_trip_restores_geometry_and_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "source.png"
            Image.new("RGB", (200, 100), "blue").save(source)
            project = folder / "project.json"
            save_project_json(str(project), {"meta": {"name": "Test"}, "images": [
                {"path": str(source), "x": 12, "y": 34, "w": 100, "h": 50,
                 "angle": 90, "brightness": 0.8}]})
            metadata, images = load_project_json(str(project))
            self.assertEqual(metadata["name"], "Test")
            self.assertEqual(len(images), 1)
            self.assertEqual((images[0].x, images[0].y, images[0].angle), (12, 34, 90))
            self.assertEqual(images[0].brightness, 0.8)

    def test_export_uses_original_pixels_and_keeps_background(self):
        original = Image.new("RGB", (40, 20), "red")
        original.putpixel((0, 0), (0, 0, 255))
        image = LoadedImage("test", original)
        image.x, image.y, image.w, image.h = 5, 6, 40, 20
        # Corrupting the UI proxy must not affect a full-quality export.
        image.display_image = Image.new("RGBA", (40, 20), "green")
        result = compose_wallpaper_contain((60, 40), [image], "black")
        self.assertEqual(result.size, (60, 40))
        self.assertEqual(result.getpixel((5, 6)), (0, 0, 255))
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0))
