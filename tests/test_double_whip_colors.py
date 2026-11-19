"""Regresión del doble látigo de 10 s, transición de fases y paletas."""
import importlib
import importlib.util
import random
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from circo.levels import LEVELS
from circo.stage_colors import STAGE_COLORS, color_for
from circo.config import FLOOR_Y, SHOT_LIMIT


class DoubleWhipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_pg = types.ModuleType('pygame')
        with patch.dict(sys.modules, {'pygame': fake_pg}):
            cls.game_module = importlib.import_module('circo.game')
        cls.previous_pg = cls.game_module.pg
        cls.game_module.pg = fake_pg

    @classmethod
    def tearDownClass(cls):
        cls.game_module.pg = cls.previous_pg

    def make_game(self):
        g = self.game_module.Game.__new__(self.game_module.Game)
        g.state = 'PLAY'
        g.level_idx = 0
        g.player_x = 240
        g.cooldown = 0.0
        g.beams = []
        g.multishot_timer = 0
        g.float_texts = []
        g.pickups = []
        g.audio = types.SimpleNamespace(play=lambda _: None, sync_music=lambda *args: None)
        return g

    def test_regular_shot_has_one_whip_and_same_limit(self):
        g = self.make_game()
        g.fire()
        self.assertEqual(len(g.beams), 1)
        self.assertEqual(g.beams[0].x, 252)
        self.assertEqual(g.beams[0].bottom, FLOOR_Y - 15)
        g.cooldown = 0
        g.fire()
        self.assertEqual(len(g.beams), SHOT_LIMIT)
        g.cooldown = 0
        g.fire()
        self.assertEqual(len(g.beams), SHOT_LIMIT)

    def test_double_bonus_shoots_from_both_hands_simultaneously(self):
        g = self.make_game()
        g.multishot_timer = 10.0
        g.fire()
        self.assertEqual([b.x for b in g.beams], [228, 252])
        self.assertEqual([b.bottom for b in g.beams], [FLOOR_Y - 9, FLOOR_Y - 15])
        self.assertEqual(g.beams[0].top, g.beams[0].bottom)
        self.assertEqual(g.beams[1].top, g.beams[1].bottom)
        g.cooldown = 0
        g.fire()
        self.assertEqual(len(g.beams), 4)
        g.cooldown = 0
        g.fire()
        self.assertEqual(len(g.beams), 4)  # nunca una pareja incompleta

    def test_double_bonus_cannot_fire_half_pair(self):
        g = self.make_game()
        g.multishot_timer = 8
        g.beams = [self.game_module.Beam(70 + i, 165) for i in range(3)]
        g.fire()
        self.assertEqual(len(g.beams), 3)

    def test_collecting_double_resets_duration_to_ten_seconds(self):
        g = self.make_game()
        g.multishot_timer = 5.0
        p = self.game_module.Pickup(240, 245, 'DOUBLE')
        g.pickups = [p]
        g.collect_pickup(p)
        self.assertEqual(g.multishot_timer, 10.0)
        self.assertFalse(g.pickups)
        self.assertIn('10s', g.float_texts[-1].caption)

    def test_bonus_ends_and_shooting_returns_to_one_whip(self):
        g = self.make_game()
        g.multishot_timer = 0.0
        g.fire()
        self.assertEqual(len(g.beams), 1)

    def test_ten_seconds_count_only_during_actual_play(self):
        g = self.make_game()
        from circo.physics import Octopus
        g.multishot_timer = 10.0
        g.timer = 100.0
        g.invulnerable = 0.0
        g.shield_timer = 0.0
        g.walk_frame = 0.0
        g.enemies = [Octopus(68, 110, -40, -25, 2, grace=0.5)]
        g.rng = random.Random(4)
        g.score = 0
        g.high_score = 0
        g.state_age = 0.0
        g.t = 0.0
        g.shake = 0.0
        g.particles = []
        g.death_fragments = []
        with patch.object(self.game_module.Game, 'controls', return_value=(0, False)):
            g.update(.25)
        self.assertAlmostEqual(g.multishot_timer, 9.75)
        g.state = 'PAUSE'
        g.update(4.0)
        self.assertAlmostEqual(g.multishot_timer, 9.75)
        g.state = 'PLAY'
        with patch.object(self.game_module.Game, 'controls', return_value=(0, False)):
            g.update(.25)
        self.assertAlmostEqual(g.multishot_timer, 9.5)

    def test_finishing_stage_immediately_cancels_every_timed_item(self):
        g = self.make_game()
        g.enemies = []
        g.timer = 80.0
        g.shield_timer = 6.0
        g.multishot_timer = 7.0
        g.invulnerable = 0.0
        g.walk_frame = 0.0
        g.beams = [self.game_module.Beam(240, 160)]
        g.pickups = [self.game_module.Pickup(40, 110, 'DOUBLE')]
        g.rng = random.Random(17)
        g.score = 0
        g.high_score = 0
        g.lives = 3
        g.world_bonus_life = False
        g.state_age = 0.0
        with patch.object(self.game_module.Game, 'controls', return_value=(0, False)):
            g.update_play(0.10)
        self.assertEqual(g.state, 'CLEAR')
        self.assertEqual(g.shield_timer, 0.0)
        self.assertEqual(g.multishot_timer, 0.0)
        self.assertEqual(g.beams, [])
        self.assertEqual(g.pickups, [])
        self.assertEqual(g.lives, 3)

    def test_new_stage_resets_timed_items_but_keeps_extra_lives(self):
        g = self.make_game()
        g.art = types.SimpleNamespace(set_level_palette=lambda _: None)
        g.shield_timer = 4.25
        g.multishot_timer = 9.0
        g.level_idx = 1
        g.invulnerable = 0.0
        g.lives = 4
        g.score = 9000
        g.particles = []
        g.cooldown = 2.0
        g.beams = [self.game_module.Beam(240, 190)]
        g.pickups = [self.game_module.Pickup(50, 100, 'SHIELD')]
        g.start_level()
        self.assertEqual(g.state, 'READY')
        self.assertEqual(g.shield_timer, 0.0)
        self.assertEqual(g.multishot_timer, 0.0)
        self.assertEqual(g.beams, [])
        self.assertEqual(g.pickups, [])
        self.assertEqual(g.lives, 4)
        self.assertEqual(g.score, 9000)
        self.assertEqual(g.timer, float(LEVELS[1].time_limit))
        self.assertEqual(g.cooldown, 0.0)

    def test_time_pickup_applies_to_current_screen_only(self):
        g = self.make_game()
        g.timer = 56.0
        g.particles = []
        g.lives = 3
        g.shield_timer = 0.0
        g.invulnerable = 0.0
        g.art = types.SimpleNamespace(set_level_palette=lambda _: None)
        pickup = self.game_module.Pickup(240, 240, 'TIME')
        g.pickups = [pickup]
        g.collect_pickup(pickup)
        self.assertEqual(g.timer, 71.0)
        g.level_idx = 1
        g.start_level()
        self.assertEqual(g.timer, float(LEVELS[1].time_limit))
        self.assertEqual(g.lives, 3)

    def test_shield_bonus_still_works_during_its_own_stage(self):
        g = self.make_game()
        g.shield_timer = 0.0
        g.lives = 3
        pickup = self.game_module.Pickup(240, 240, 'SHIELD')
        g.pickups = [pickup]
        g.collect_pickup(pickup)
        self.assertEqual(g.shield_timer, 8.0)
        self.assertEqual(g.lives, 3)

    def test_particles_match_the_respective_octopus_color(self):
        g = self.make_game()
        g.level_idx = 14
        self.assertEqual(g.burst_color(types.SimpleNamespace(variant='smile')),
                         color_for(14, 'smile'))
        self.assertEqual(g.burst_color(types.SimpleNamespace(variant='bandana')),
                         color_for(14, 'bandana'))


class StageColorsTests(unittest.TestCase):
    def test_all_twenty_five_stages_have_distinct_type_colors(self):
        self.assertEqual(len(STAGE_COLORS), 25)
        for i in range(25):
            self.assertNotEqual(color_for(i, 'smile'), color_for(i, 'bandana'))
        self.assertEqual(len(set(color_for(i, 'smile') for i in range(25))), 25)

    def test_only_one_visible_color_when_all_enemies_are_same_type(self):
        for idx, level in enumerate(LEVELS):
            variants = {s.variant for s in level.enemies}
            colors_used = {color_for(idx, variant) for variant in variants}
            self.assertEqual(len(colors_used), len(variants), f'Fase {idx+1}')

    def test_generated_sprites_exist_for_each_stage_and_both_types(self):
        root = Path(__file__).resolve().parent.parent / 'assets' / 'sprites' / 'fases'
        for i in range(1, 26):
            for v in ('smile', 'bandana'):
                p = root / f'fase_{i:02d}_{v}.png'
                self.assertTrue(p.is_file(), str(p))
                self.assertEqual(p.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')

    @unittest.skipUnless(importlib.util.find_spec('PIL'), 'Pillow solo para pruebas de arte')
    def test_model_alpha_and_eyes_are_identical_through_all_recolors(self):
        from PIL import Image
        root = Path(__file__).resolve().parent.parent / 'assets' / 'sprites'
        for variant, source_name in (('smile', 'pulpo_sonriente.png'),
                                     ('bandana', 'pulpo_bandana.png')):
            source = Image.open(root / source_name).convert('RGBA')
            base = list(source.getdata())
            for i in range(1, 26):
                current = Image.open(root / 'fases' / f'fase_{i:02d}_{variant}.png').convert('RGBA')
                pixels = list(current.getdata())
                self.assertEqual(current.size, source.size)
                self.assertEqual([p[3] for p in pixels], [p[3] for p in base])
                if variant == 'bandana':
                    # Bordado de la bandana preservado píxel por píxel.
                    for y in range(28, 48):
                        for x in range(69, 103):
                            self.assertEqual(current.getpixel((x, y)),
                                             source.getpixel((x, y)))
                # Ojos blancos y elementos negros nunca se colorean.
                for previous, new in zip(base, pixels):
                    if previous[3] > 128 and (max(previous[:3]) - min(previous[:3]) < 12):
                        self.assertEqual(previous, new)


if __name__ == '__main__':
    unittest.main()
