"""Noms lisibles des écrans et détection des images trop petites."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from display_geometry import monitor_labels, monitor_vendor, upscale_factor
from image_tools import LoadedImage

WORDS = {"left": "Gauche", "center": "Centre", "right": "Droite", "top": "Haut", "bottom": "Bas", "screen": "Écran {}"}


def screen(x, y, hw="", mm=None, w=1920, h=1080):
    m = {"name": "\\\\.\\DISPLAY", "x": x, "y": y, "width": w, "height": h, "hw_id": hw}
    if mm:
        m["width_mm"], m["height_mm"] = mm
    return m


class MonitorLabelTest(unittest.TestCase):
    def test_three_in_a_row_named_left_to_right(self):
        # Ordre Windows : DISPLAY2 à gauche, DISPLAY3 au centre, DISPLAY1 à droite.
        ms = [screen(0, 0, "IVM6132#c", (544, 303)), screen(-3840, 0, "PHLC069#a", (509, 286)), screen(-1920, 0, "IVM6132#b", (544, 303))]
        self.assertEqual(monitor_labels(ms, WORDS), ["Droite · iiyama 24,5″", "Gauche · Philips 23″", "Centre · iiyama 24,5″"])

    def test_two_stacked(self):
        ms = [screen(0, 1080, "SAM0F00#x"), screen(0, 0, "DEL1234#y")]
        self.assertEqual(monitor_labels(ms, WORDS), ["Bas · Samsung", "Haut · Dell"])

    def test_single_screen_has_no_position(self):
        self.assertEqual(monitor_labels([screen(0, 0, "", (597, 336))], WORDS, decimal="."), ["27″"])

    def test_unknown_vendor_and_size_falls_back_to_resolution(self):
        self.assertEqual(monitor_labels([screen(0, 0), screen(1920, 0)], WORDS), ["Gauche · 1920 × 1080", "Droite · 1920 × 1080"])

    def test_four_screens_are_numbered(self):
        ms = [screen(i * 1920, 0) for i in (2, 0, 3, 1)]
        self.assertEqual([lab.split(" · ")[0] for lab in monitor_labels(ms, WORDS)], ["Écran 3", "Écran 1", "Écran 4", "Écran 2"])

    def test_vendor_code(self):
        self.assertEqual(monitor_vendor({"hw_id": "GSM5B7F#abc"}), "LG")
        self.assertEqual(monitor_vendor({"hw_id": "ZZZ0001#abc"}), "ZZZ")
        self.assertEqual(monitor_vendor({"hw_id": "\\\\.\\DISPLAY1"}), "")


class UpscaleTest(unittest.TestCase):
    def make(self, size):
        return LoadedImage("mem.png", Image.new("RGB", size, "red"))

    def test_small_image_on_large_area(self):
        img = self.make((600, 400))
        img.w, img.h = 1500, 1000
        self.assertAlmostEqual(upscale_factor(img), 2.5)

    def test_crop_increases_stretch(self):
        img = self.make((2000, 1000))
        img.crop_box_norm = (0.0, 0.0, 0.5, 1.0)  # moitié gauche : 1000 px de large
        img.w, img.h = 2000, 2000
        self.assertAlmostEqual(upscale_factor(img), 2.0)

    def test_rotation_swaps_axes(self):
        img = self.make((4000, 1000))
        img.rotate_cw()
        img.w, img.h = 1000, 4000
        self.assertAlmostEqual(upscale_factor(img), 1.0)


if __name__ == "__main__":
    unittest.main()
