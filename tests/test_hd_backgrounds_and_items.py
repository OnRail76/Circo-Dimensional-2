"""Verificaciones de los cinco fondos oficiales y el retorno de los ítems."""
from pathlib import Path
import importlib
import importlib.util
import random
import sys
import types
import unittest
from unittest.mock import patch

from circo.backgrounds import BACKGROUND_FILES, cover_crop_dimensions
from circo.levels import LEVELS

ROOT = Path(__file__).resolve().parent.parent
BACKGROUNDS = ROOT / 'assets' / 'backgrounds'


class BackgroundTests(unittest.TestCase):
    def test_five_original_images_are_shipped_as_png(self):
        self.assertEqual(set(BACKGROUND_FILES), {'circus', 'inverted', 'saturn', 'phantom', 'core'})
        for theme, filename in BACKGROUND_FILES.items():
            png = BACKGROUNDS / filename
            self.assertTrue(png.is_file(), theme)
            self.assertEqual(png.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')

    def test_all_levels_use_their_world_background(self):
        for idx, level in enumerate(LEVELS):
            expected = ['circus', 'inverted', 'saturn', 'phantom', 'core'][idx // 5]
            self.assertEqual(level.theme, expected)
            self.assertTrue((BACKGROUNDS / BACKGROUND_FILES[expected]).is_file())

    def test_crop_preserves_aspect_and_bounds(self):
        for source in ((1648, 928), (1920, 1080), (1000, 1000)):
            x, y, w, h = cover_crop_dimensions(*source, 960, 600)
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x+w, source[0])
            self.assertLessEqual(y+h, source[1])
            self.assertAlmostEqual(w/h, 960/600, delta=0.004)

    def test_invalid_image_size_is_rejected(self):
        with self.assertRaises(ValueError):
            cover_crop_dimensions(0, 100, 960, 600)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow opcional para comprobación HD")
    def test_pngs_keep_original_resolution(self):
        from PIL import Image
        import json
        import hashlib
        manifest = json.loads((BACKGROUNDS / 'MANIFIESTO.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest), 5)
        for data in manifest:
            file = BACKGROUNDS / data['archivo']
            with Image.open(file) as image:
                self.assertGreaterEqual(image.width, 1600)
                self.assertGreaterEqual(image.height, 900)
                self.assertEqual(f"{image.width}x{image.height}", data['resolucion'])
            self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), data['sha256_png'])


class PickupRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(sys.modules, {'pygame': types.ModuleType('pygame')}):
            cls.module = importlib.import_module('circo.game')

    def game(self, level_idx=0):
        g = self.module.Game.__new__(self.module.Game)
        g.level_idx = level_idx
        g.pickups = []
        g.pickups_spawned_this_stage = 0
        g.pickup_kills_since_drop = 0
        g.rng = random.Random(41)
        g.enemies = [object()]
        return g

    def test_first_eligible_kill_guarantees_an_item(self):
        g = self.game()
        spawn = types.SimpleNamespace(x=64, y=108)
        self.assertTrue(g.try_drop_pickup(spawn))
        self.assertEqual(len(g.pickups), 1)
        self.assertEqual(g.pickups[0].vy, 92)
        self.assertEqual(g.pickups_spawned_this_stage, 1)

    def test_no_useless_item_after_last_kill(self):
        g = self.game()
        g.enemies = []
        self.assertFalse(g.try_drop_pickup(types.SimpleNamespace(x=64, y=108)))
        self.assertFalse(g.pickups)

    def test_limits_stages_one_to_five_to_one_drop(self):
        g = self.game(level_idx=0)
        enemy = types.SimpleNamespace(x=68, y=95)
        g.try_drop_pickup(enemy)
        g.pickups.clear()
        for _ in range(20):
            self.assertFalse(g.try_drop_pickup(enemy))
        self.assertEqual(g.pickups_spawned_this_stage, 1)

    def test_later_stages_allow_two_but_never_more(self):
        g = self.game(level_idx=17)
        enemy = types.SimpleNamespace(x=416, y=107)
        self.assertTrue(g.try_drop_pickup(enemy))
        g.pickups.clear()
        g.rng = types.SimpleNamespace(random=lambda: 0.0, choices=lambda *args: ['SHIELD'])
        for _ in range(6):
            g.try_drop_pickup(enemy)
        self.assertEqual(g.pickups_spawned_this_stage, 2)
        g.pickups.clear()
        for _ in range(20):
            self.assertFalse(g.try_drop_pickup(enemy))
        self.assertEqual(g.pickups_spawned_this_stage, 2)

    def test_drop_stays_inside_playable_area(self):
        g = self.game()
        g.try_drop_pickup(types.SimpleNamespace(x=-20, y=-30))
        self.assertEqual(g.pickups[0].x, 18)
        self.assertEqual(g.pickups[0].y, 48)


if __name__ == '__main__':
    unittest.main()
