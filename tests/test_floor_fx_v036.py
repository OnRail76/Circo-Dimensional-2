"""Regresiones v0.3.6: suelo, transparencia, oscurecimiento y sin sombras."""
from __future__ import annotations
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from circo.art import Art, THEMES, FLOOR_PALETTES
from circo.backgrounds import BACKGROUND_FILES, HD_DIM_ALPHA, HDBackdrops
from circo.config import FLOOR_Y, HEIGHT, WIDTH, VERSION
from circo.levels import LEVELS


class RecordingSurface:
    def __init__(self, size):
        self.size = size
        self.fills = []
        self.blits = []
        self.original = True

    def fill(self, color):
        self.fills.append(color)

    def blit(self, source, pos):
        self.blits.append((source, pos))


class RecordingDraw:
    def __init__(self):
        self.calls = []

    def rect(self, *args):
        self.calls.append(('rect', args))

    def line(self, *args):
        self.calls.append(('line', args))

    def circle(self, *args):
        self.calls.append(('circle', args))

    def arc(self, *args):
        self.calls.append(('arc', args))


class RecordingPG:
    SRCALPHA = 1

    def __init__(self):
        self.draw = RecordingDraw()

    def Surface(self, size, flags=0):
        return RecordingSurface(size)

    def Rect(self, *args):
        return tuple(args)


class FloorTests(unittest.TestCase):
    def test_five_floors_match_five_existing_worlds(self):
        self.assertEqual(set(THEMES), set(FLOOR_PALETTES))
        self.assertEqual(set(THEMES), set(BACKGROUND_FILES))
        self.assertEqual(VERSION, '1.0.0')
        for i, level in enumerate(LEVELS):
            self.assertIn(level.theme, FLOOR_PALETTES)
            self.assertEqual(level.theme, list(THEMES)[i // 5])

    def test_floor_starts_at_physics_line_and_fills_remaining_height(self):
        art = Art.__new__(Art)
        art.pg = RecordingPG()
        art.floor_images = {name: art.make_floor(name) for name in THEMES}
        for theme in THEMES:
            surf = art.floor_images[theme]
            self.assertEqual(surf.size, (WIDTH, HEIGHT - FLOOR_Y))
            self.assertEqual(surf.fills[0][-1], 245)
            target = RecordingSurface((WIDTH, HEIGHT))
            art.floor(target, theme, 0.0)
            self.assertIs(target.blits[0][0], surf)
            self.assertEqual(target.blits[0][1], (0, FLOOR_Y))

    def test_floor_has_bright_edge_but_no_figures_or_background_repainting(self):
        art = Art.__new__(Art)
        art.pg = RecordingPG()
        art.make_floor('circus')
        strokes = art.pg.draw.calls
        self.assertGreater(sum(kind == 'line' for kind, _ in strokes), 5)
        self.assertFalse(any(kind in ('ellipse', 'polygon', 'circle') for kind, _ in strokes))


class FXTests(unittest.TestCase):
    def test_stars_and_portal_are_translucent_and_not_opaque_shapes(self):
        art = Art.__new__(Art)
        art.pg = RecordingPG()
        art._fx_layer = RecordingSurface((WIDTH, HEIGHT))
        art._star_field = {name: [(80, 75, 1.0, 1.1, True)] * 30 for name in THEMES}
        target = RecordingSurface((WIDTH, HEIGHT))
        art.star_glints(target, 'saturn', 7.0)
        self.assertEqual(art._fx_layer.fills[-1], (0, 0, 0, 0))
        self.assertEqual(target.blits[-1][0], art._fx_layer)
        calls = art.pg.draw.calls
        self.assertTrue(any(k == 'circle' for k, _ in calls))
        self.assertTrue(any(k == 'arc' for k, _ in calls))
        for _, args in calls:
            color = args[1]
            self.assertEqual(len(color), 4)
            self.assertLess(color[3], 255)

    def test_opaque_background_is_darkened_only_after_scaling(self):
        self.assertTrue(25 <= HD_DIM_ALPHA <= 55)
        source = (Path(__file__).parent.parent / 'circo/backgrounds.py').read_text()
        self.assertLess(source.index('smoothscale(source'), source.index('veil.fill('))
        self.assertLess(source.index('veil.fill('), source.index('self._cache_image.blit(veil'))

    def test_no_pulpo_shadows_are_drawn_in_action(self):
        game_file = Path(__file__).parent.parent / 'circo/game.py'
        tree = ast.parse(game_file.read_text(encoding='utf-8'))
        game = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Game')
        action = next(n for n in game.body if isinstance(n, ast.FunctionDef) and n.name == 'draw_action')
        calls = [n for n in ast.walk(action) if isinstance(n, ast.Call)]
        def name(call):
            try:
                return ast.unparse(call.func)
            except Exception:
                return ''
        methods = [name(call) for call in calls]
        self.assertIn('self.art.floor', methods)
        self.assertIn('self.art.octopus', methods)
        self.assertNotIn('pg.draw.ellipse', methods)
        floor_call = next(n for n in calls if name(n) == 'self.art.floor')
        octo_call = next(n for n in calls if name(n) == 'self.art.octopus')
        self.assertLess(floor_call.lineno, octo_call.lineno)


if __name__ == '__main__':
    unittest.main()
