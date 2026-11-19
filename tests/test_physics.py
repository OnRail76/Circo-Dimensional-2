import unittest
from circo.config import FLOOR_Y, SIZE_RADIUS
from circo.physics import (
    Octopus, Platform, move_octopus, split_octopus,
    circle_hits_rectangle, circle_hits_vertical_segment,
)


class PhysicsTests(unittest.TestCase):
    def test_split_tree(self):
        def count(o):
            kids = split_octopus(o)
            return 1 + sum(count(k) for k in kids)
        self.assertEqual(count(Octopus(210, 130, 80, 0, 0)), 15)
        self.assertEqual(count(Octopus(210, 130, 80, 0, -1)), 31)
        self.assertEqual(split_octopus(Octopus(200, 70, 80, 0, 3)), ())

    def test_children_are_safe_and_separated(self):
        for size in (-1, 0, 1, 2):
            for x in (5, 240, 475):
                o = Octopus(x, 110, 40, 0, size)
                l, r = split_octopus(o)
                self.assertLess(l.x, r.x)
                self.assertLess(l.vx, 0)
                self.assertGreater(r.vx, 0)
                self.assertGreaterEqual(l.x - l.radius, 0)
                self.assertLessEqual(r.x + r.radius, 480)
                self.assertGreater(l.grace, 0)

    def test_wall_rebound(self):
        o = Octopus(30, 130, -140, 0, 0)
        for i in range(20):
            move_octopus(o, 1 / 60)
        self.assertGreater(o.vx, 0)
        self.assertGreaterEqual(o.x - o.radius, 0)

    def test_floor_rebound(self):
        o = Octopus(200, FLOOR_Y - SIZE_RADIUS[1] - 1, 80, 220, 1)
        self.assertTrue(move_octopus(o, 1 / 60))
        self.assertLess(o.vy, 0)
        self.assertLessEqual(o.y + o.radius, FLOOR_Y)

    def test_platform_rebound_only_from_above(self):
        p = Platform(100, 180, 185)
        o = Octopus(130, 185 - 19 - 1, 0, 120, 1)
        self.assertTrue(move_octopus(o, 1 / 60, (p,)))
        self.assertEqual(o.y + o.radius, 185)
        self.assertLess(o.vy, 0)
        o = Octopus(130, 210, 0, -300, 1)
        self.assertFalse(move_octopus(o, 1 / 60, (p,)))

    def test_beam(self):
        self.assertTrue(circle_hits_vertical_segment(110, 120, 12, 100, 30, 230))
        self.assertFalse(circle_hits_vertical_segment(130, 120, 12, 100, 30, 230))
        self.assertTrue(circle_hits_vertical_segment(102, 22, 12, 100, 30, 230))
        self.assertFalse(circle_hits_vertical_segment(102, 7, 12, 100, 30, 230))

    def test_dom_collision(self):
        self.assertTrue(circle_hits_rectangle(246, 239, 10, 235, 234, 245, 261))
        self.assertFalse(circle_hits_rectangle(279, 190, 10, 235, 234, 245, 261))


if __name__ == "__main__":
    unittest.main()

class ArcadePhysicsIntegrationTests(unittest.TestCase):
    def test_all_scenes_keep_enemies_inside_arena(self):
        from circo.levels import LEVELS
        from circo.config import WIDTH, HUD_HEIGHT
        for scene in LEVELS:
            for sp in scene.enemies:
                o = Octopus(sp.x, sp.y, 95 * sp.direction, -92, sp.size, hp=sp.hp)
                floor_bounces = 0
                for _ in range(900):  # 15 segundos de simulación física
                    if move_octopus(o, 1/60, scene.platforms):
                        floor_bounces += 1
                    self.assertGreaterEqual(o.x - o.radius, 0)
                    self.assertLessEqual(o.x + o.radius, WIDTH)
                    self.assertGreaterEqual(o.y - o.radius, HUD_HEIGHT)
                    self.assertLessEqual(o.y + o.radius, FLOOR_Y)
                self.assertGreater(floor_bounces, 2)

    def test_large_octopus_bounces_high(self):
        from circo.config import SIZE_BOUNCE
        o = Octopus(200, FLOOR_Y - 25, 0, -SIZE_BOUNCE[0], 0)
        lowest_y = o.y
        for _ in range(60):
            move_octopus(o, 1 / 60)
            lowest_y = min(lowest_y, o.y)
        self.assertLess(lowest_y, FLOOR_Y - 25 - 95)
