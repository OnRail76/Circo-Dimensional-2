"""Comprobaciones puras de campaña, sin abrir ventana ni importar Pygame."""
import unittest
from pathlib import Path
from circo.levels import LEVELS, validate_levels, WORLD_NAMES
from circo.physics import Octopus, split_octopus, move_octopus
from circo.config import SIZE_RADIUS, SIZE_SPEED


class CampaignTests(unittest.TestCase):
    def test_twenty_five_stages_in_five_worlds(self):
        self.assertEqual(len(LEVELS), 25)
        for world_index, (name, theme) in enumerate(WORLD_NAMES):
            for level in LEVELS[world_index * 5:(world_index + 1) * 5]:
                self.assertEqual(level.theme, theme)
                self.assertEqual(level.title, name)

    def test_safe_opening_all_25_levels(self):
        validate_levels()
        for i, level in enumerate(LEVELS):
            for sp in level.enemies:
                vx = SIZE_SPEED[sp.size] * level.speed_factor * sp.direction
                self.assertTrue((sp.x - 240) * vx > 0, (i + 1, sp))

    def test_progressive_physics(self):
        speeds = [lvl.speed_factor for lvl in LEVELS]
        bounces = [lvl.bounce_factor for lvl in LEVELS]
        self.assertEqual(speeds, sorted(speeds))
        self.assertEqual(bounces, sorted(bounces))
        self.assertLess(speeds[0], speeds[5])
        self.assertLess(speeds[5], speeds[-1])
        self.assertLess(bounces[0], 1.0)

    def test_easy_first_world_no_large_enemies(self):
        self.assertEqual(len(LEVELS[0].enemies), 1)
        self.assertEqual(LEVELS[0].enemies[0].size, 2)
        for level in LEVELS[:5]:
            self.assertTrue(all(sp.size >= 1 for sp in level.enemies))
            self.assertTrue(all(sp.hp == 1 for sp in level.enemies))

    def test_bandana_reinforcements_start_later(self):
        self.assertFalse(any(sp.variant == 'bandana' for level in LEVELS[:14] for sp in level.enemies))
        self.assertTrue(any(sp.variant == 'bandana' for level in LEVELS[14:] for sp in level.enemies))
        for level in LEVELS:
            for sp in level.enemies:
                if sp.variant == 'bandana':
                    self.assertGreater(sp.hp, 1)

    def test_final_boss_only_at_end(self):
        self.assertFalse(any(sp.size == -1 for level in LEVELS[:-1] for sp in level.enemies))
        self.assertTrue(any(sp.size == -1 and sp.hp == 4 for sp in LEVELS[-1].enemies))

    def test_no_initial_sprite_overlap(self):
        for number, level in enumerate(LEVELS, 1):
            for i, a in enumerate(level.enemies):
                for b in level.enemies[i+1:]:
                    dist_squared = (a.x - b.x) ** 2 + (a.y - b.y) ** 2
                    min_sep = SIZE_RADIUS[a.size] + SIZE_RADIUS[b.size]
                    self.assertGreaterEqual(dist_squared, min_sep ** 2,
                                            f'Overlap initial in stage {number}: {a}, {b}')

    def test_bandana_splits_into_smiling_children(self):
        enemy = Octopus(130, 125, -100, 0, 0, hp=1, variant='bandana')
        children = split_octopus(enemy, .73)
        self.assertEqual(len(children), 2)
        self.assertTrue(all(child.variant == 'smile' for child in children))
        self.assertAlmostEqual(abs(children[0].vx), 114 * .73)

    def test_bounce_factor_changes_vertical_speed(self):
        o = Octopus(120, 263 - 19 - .5, 0, 250, 1)
        self.assertTrue(move_octopus(o, 1/60, bounce_factor=.85))
        self.assertAlmostEqual(o.vy, -350 * .85)

    def test_actual_png_assets_are_bundled(self):
        root = Path(__file__).resolve().parent.parent / 'assets' / 'sprites'
        for name in ('pulpo_sonriente.png', 'pulpo_bandana.png'):
            f = root / name
            self.assertTrue(f.is_file())
            with f.open('rb') as fp:
                self.assertEqual(fp.read(8), bytes.fromhex('89504E470D0A1A0A'))


if __name__ == '__main__':
    unittest.main()
