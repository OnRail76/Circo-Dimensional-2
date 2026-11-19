"""Constantes de Circo Dimensional 2 — mundo lógico de 480×300."""
from __future__ import annotations

TITLE = "CIRCO DIMENSIONAL 2"
VERSION = "1.0.0"
AUTHOR = "Tony C. Ware"
WIDTH, HEIGHT, SCALE = 480, 300, 2
FPS = 60
HUD_HEIGHT = 34
FLOOR_Y = 263
PLAYER_SPEED = 145.0
PLAYER_HALF_WIDTH = 8
PLAYER_HEIGHT = 29
START_LIVES = 3
MAX_LIVES = 5
SHOT_COOLDOWN = 0.32
SHOT_SPEED = 620.0
SHOT_HOLD = 0.33
SHOT_LIMIT = 2
DOUBLE_WHIP_DURATION = 10.0  # Segundos efectivos, solo en la fase en que se recoge
STAGE_READY_SECS = 2.35
STAGE_CLEAR_SECS = 2.65
END_MIN_SECS = 3.0
HIT_INVULN_SECS = 2.0
DEATH_ANIMATION_SECS = 1.15
SIZE_RADIUS = {-1: 34, 0: 25, 1: 19, 2: 13, 3: 8}
SIZE_SPEED = {-1: 67.0, 0: 76.0, 1: 90.0, 2: 113.0, 3: 139.0}
SIZE_GRAVITY = {-1: 465.0, 0: 535.0, 1: 580.0, 2: 655.0, 3: 725.0}
SIZE_BOUNCE = {-1: 350.0, 0: 345.0, 1: 350.0, 2: 355.0, 3: 350.0}
SCORE_BY_SIZE = {-1: 700, 0: 100, 1: 150, 2: 200, 3: 300}
COLORS = {
    "ink": (9, 12, 28), "white": (242, 248, 251), "gold": (255, 212, 104),
    "cyan": (76, 237, 244), "pink": (252, 102, 165), "violet": (174, 115, 248),
    "green": (126, 240, 166), "red": (252, 109, 123),
}
