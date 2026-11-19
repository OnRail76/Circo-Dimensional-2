"""Pruebas sin pantalla para el nuevo ciclo de muerte y menús."""
import importlib
import json
import math
import random
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from circo.config import HIT_INVULN_SECS, DEATH_ANIMATION_SECS


class FakeImage:
    def subsurface(self, rect):
        return self

    def copy(self):
        return self


class FakeMask:
    def count(self):
        return 1


class FakeAudio:
    def __init__(self):
        self.music_enabled = True
        self.effects_enabled = True
        self.music_volume = .24
        self.effects_volume = .75
        self.sounds = {'dom_boom': True}
        self.actions = []

    def sync_music(self, state, idx):
        self.actions.append(('sync', state, idx))

    def play(self, name):
        self.actions.append(('play', name))

    def toggle_music(self):
        self.music_enabled = not self.music_enabled

    def toggle_effects(self):
        self.effects_enabled = not self.effects_enabled

    def adjust_music_volume(self, delta):
        self.music_volume = round(min(1., max(0., self.music_volume + delta)), 2)

    def adjust_effects_volume(self, delta):
        self.effects_volume = round(min(1., max(0., self.effects_volume + delta)), 2)


class DomFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # La lógica se prueba también en entornos sin Pygame/SDL, con máscaras
        # mínimas únicamente para fragmentar el sprite.
        mock_pg = types.ModuleType('pygame')
        mock_pg.Rect = lambda *args: args
        mock_pg.mask = types.SimpleNamespace(from_surface=lambda s: FakeMask())
        with patch.dict(sys.modules, {'pygame': mock_pg}):
            cls.mod = importlib.import_module('circo.game')
        cls.old_pg = cls.mod.pg
        cls.mod.pg = mock_pg

    @classmethod
    def tearDownClass(cls):
        cls.mod.pg = cls.old_pg

    def create_game(self):
        g = self.mod.Game.__new__(self.mod.Game)
        g.art = types.SimpleNamespace(hero_images={0: FakeImage()})
        g.audio = FakeAudio()
        g.lives = 3
        g.player_x = 240
        g.shake = 0
        g.invulnerable = 0
        g.shield_timer = 0
        g.beams = []
        g.death_fragments = []
        g.enemies = [types.SimpleNamespace(x=240, y=245, radius=17)]
        g.particles = []
        g.float_texts = []
        g.rng = random.Random(31)
        g.state = 'PLAY'
        g.state_age = 0
        g.t = 0
        g.level_idx = 0
        g.options_origin = 'TITLE'
        g.title_selected = 0
        g.pause_selected = 0
        g.options_selected = 0
        return g

    def test_dom_explodes_and_only_respawns_after_animation(self):
        g = self.create_game()
        g.take_damage()
        self.assertEqual(g.lives, 2)
        self.assertEqual(g.state, 'DEATH')
        self.assertEqual(g.invulnerable, 0)
        self.assertGreater(len(g.death_fragments), 10)
        self.assertGreater(len(g.particles), 65)
        self.assertIn(('play', 'dom_boom'), g.audio.actions)
        g.update(.55)
        self.assertEqual(g.state, 'DEATH')
        g.update(DEATH_ANIMATION_SECS - .55 + .002)
        self.assertEqual(g.state, 'PLAY')
        self.assertAlmostEqual(g.invulnerable, 2.0)
        self.assertNotEqual(g.player_x, 240)  # reaparecer lejos del pulpo central
        old_lives = g.lives
        g.take_damage()
        self.assertEqual(g.lives, old_lives)  # protegidos los dos segundos

    def test_last_life_finishes_explosion_before_game_over(self):
        g = self.create_game()
        g.lives = 1
        g.take_damage()
        self.assertEqual(g.state, 'DEATH')
        g.update(DEATH_ANIMATION_SECS + .02)
        self.assertEqual(g.state, 'GAME_OVER')
        self.assertEqual(g.state_age, 0)

    def test_audio_menu_changes_both_channels_and_saves(self):
        g = self.create_game()
        g.state = 'OPTIONS'
        g.options_selected = 0
        with tempfile.TemporaryDirectory() as tmp:
            g.settings_path = Path(tmp) / 'config.json'
            g.change_option(1)
            self.assertFalse(g.audio.music_enabled)
            g.options_selected = 1
            g.change_option(1)
            self.assertFalse(g.audio.effects_enabled)
            g.options_selected = 2
            g.change_option(1)
            self.assertEqual(g.audio.music_volume, .29)
            g.options_selected = 3
            g.change_option(-1)
            self.assertEqual(g.audio.effects_volume, .70)
            saved = json.loads(g.settings_path.read_text())
            self.assertEqual(saved['music_volume'], .29)
            self.assertFalse(saved['effects'])

    def test_gamepad_start_and_main_button_navigate_pause(self):
        g = self.create_game()
        pg = self.mod.pg
        pg.QUIT = 401
        pg.KEYDOWN = 402
        pg.JOYBUTTONDOWN = 403
        pg.JOYHATMOTION = 404
        pg.JOYAXISMOTION = 405
        pg.JOYDEVICEADDED = 406
        pg.JOYDEVICEREMOVED = 407
        pg.event = types.SimpleNamespace(get=lambda: [types.SimpleNamespace(type=403, button=7)])
        g.pause_selected = 0
        g.handle_events()
        self.assertEqual(g.state, 'PAUSE')
        pg.event = types.SimpleNamespace(get=lambda: [types.SimpleNamespace(type=404, value=(0, -1))])
        g.handle_events()
        self.assertEqual(g.pause_selected, 1)
        pg.event = types.SimpleNamespace(get=lambda: [types.SimpleNamespace(type=403, button=0)])
        g.handle_events()
        self.assertEqual(g.state, 'OPTIONS')
        self.assertEqual(g.options_origin, 'PAUSE')
        pg.event = types.SimpleNamespace(get=lambda: [types.SimpleNamespace(type=403, button=1)])
        g.handle_events()
        self.assertEqual(g.state, 'PAUSE')
        pg.event = types.SimpleNamespace(get=lambda: [types.SimpleNamespace(type=403, button=7)])
        g.handle_events()
        self.assertEqual(g.state, 'PLAY')

    def test_menu_navigation_and_gamepad_menu_shape(self):
        g = self.create_game()
        g.state = 'TITLE'
        g.title_selected = 0
        self.assertEqual(g.menu_items(), ['JUGAR', 'OPCIONES', 'CONTROLES', 'SALIR'])
        g.navigate(-1)
        self.assertEqual(g.title_selected, 3)
        g.navigate(1)
        self.assertEqual(g.title_selected, 0)
        g.title_selected = 1
        g.select_menu()
        self.assertEqual(g.state, 'OPTIONS')
        self.assertEqual(g.options_origin, 'TITLE')
        g.go_back()
        self.assertEqual(g.state, 'TITLE')


if __name__ == '__main__':
    unittest.main()
