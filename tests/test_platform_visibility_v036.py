"""La pista y las plataformas deben leerse por encima de los fondos HD."""
import unittest
from circo.art import Art, FLOOR_PALETTES, THEMES
from circo.levels import LEVELS
from circo.physics import Platform

class Pen:
    def __init__(self):
        self.calls = []
    def rect(self, *args, **kwargs):
        self.calls.append(('rect', args, kwargs))
    def line(self, *args, **kwargs):
        self.calls.append(('line', args, kwargs))

class PG:
    def __init__(self):
        self.draw = Pen()

class PlatformVisibilityTests(unittest.TestCase):
    def test_active_platforms_have_a_14px_high_body_all_worlds(self):
        art = Art.__new__(Art)
        art.pg = PG()
        for theme in THEMES:
            art.pg.draw.calls.clear()
            platform = Platform(130, 205, 179)
            art.platforms(None, (platform,), theme)
            calls = art.pg.draw.calls
            self.assertGreaterEqual(len(calls), 12, theme)
            self.assertIn(('rect', (None, (5, 9, 25), (128, 178, 79, 16)), {'border_radius': 3}), calls)
            top = ('line', (None, (246, 249, 253), (132, 179), (202, 179), 2), {})
            self.assertIn(top, calls, theme)
            self.assertTrue(any(kind == 'line' and args[1] == FLOOR_PALETTES[theme][1]
                                for kind, args, kwargs in calls), theme)

    def test_platforms_remain_unchanged_in_25_level_definitions(self):
        self.assertEqual(len(LEVELS), 25)
        self.assertTrue(all(not l.platforms for l in LEVELS[:5]))
        self.assertTrue(all(l.platforms for l in LEVELS[5:]))
        for level in LEVELS[5:]:
            for platform in level.platforms:
                self.assertGreater(platform.x2 - platform.x1, 50)
                self.assertLess(platform.y + 16, 263)

if __name__ == '__main__':
    unittest.main()
