"""Lógica geométrica pura, comprobable sin tener Pygame instalado."""
from __future__ import annotations
from dataclasses import dataclass
import math

from .config import FLOOR_Y, WIDTH, SIZE_RADIUS, SIZE_BOUNCE, SIZE_GRAVITY


@dataclass(slots=True)
class Platform:
    x1: float
    x2: float
    y: float


@dataclass(slots=True)
class Octopus:
    x: float
    y: float
    vx: float
    vy: float
    size: int
    hp: int = 1
    age: float = 0.0
    pulse: float = 0.0
    grace: float = 0.0  # pequeña protección al dividirse
    variant: str = "smile"  # sonriente o bandana (elite)

    @property
    def radius(self) -> float:
        return SIZE_RADIUS[self.size]


def move_octopus(o: Octopus, dt: float, platforms: tuple[Platform, ...] = (),
                 bounce_factor: float = 1.0) -> bool:
    """Actualiza un pulpo; devuelve True si ha rebotado en el suelo/plataforma."""
    r = o.radius
    old_bottom = o.y + r
    o.age += dt
    o.grace = max(0.0, o.grace - dt)
    o.x += o.vx * dt
    o.vy += SIZE_GRAVITY[o.size] * dt
    o.y += o.vy * dt
    bounced = False
    if o.x < r + 3:
        o.x = r + 3
        o.vx = abs(o.vx)
    if o.x > WIDTH - r - 3:
        o.x = WIDTH - r - 3
        o.vx = -abs(o.vx)
    if o.vy > 0:
        for p in platforms:
            # Solo si cae desde arriba: no hay teletransporte desde abajo.
            if old_bottom <= p.y + 2 and o.y + r >= p.y and o.x + r * .78 > p.x1 and o.x - r * .78 < p.x2:
                o.y = p.y - r
                o.vy = -SIZE_BOUNCE[o.size] * .77 * bounce_factor
                bounced = True
                break
    if o.y + r >= FLOOR_Y:
        o.y = FLOOR_Y - r
        o.vy = -SIZE_BOUNCE[o.size] * bounce_factor
        bounced = True
    # Seguridad: nada escapa por la franja superior.
    if o.y - r < 38:
        o.y = 38 + r
        o.vy = max(o.vy, 16.0)
    return bounced


def circle_hits_vertical_segment(cx: float, cy: float, radius: float,
                                 x: float, top: float, bottom: float) -> bool:
    nearest_y = min(max(cy, top), bottom)
    dx, dy = cx - x, cy - nearest_y
    return dx * dx + dy * dy <= radius * radius


def circle_hits_rectangle(cx: float, cy: float, radius: float,
                          left: float, top: float, right: float, bottom: float) -> bool:
    near_x = min(max(cx, left), right)
    near_y = min(max(cy, top), bottom)
    return (cx - near_x) ** 2 + (cy - near_y) ** 2 <= radius ** 2


def split_octopus(o: Octopus, speed_factor: float = 1.0) -> tuple[Octopus, Octopus] | tuple[()]:
    """Dos descendientes, hasta tamaño 3; el jefe -1 pasa a 0."""
    if o.size >= 3:
        return ()
    size = o.size + 1
    r = SIZE_RADIUS[size]
    speed = {0: 103.0, 1: 114.0, 2: 133.0, 3: 152.0}[size] * speed_factor
    y = max(45 + r, min(FLOOR_Y - r - 2, o.y - 3))
    left_x, right_x = o.x - r * .74, o.x + r * .74
    # Desplazar la pareja entera antes de limitar al escenario: si el pulpo
    # padre roza una pared, sus hijos nunca aparecen superpuestos.
    if left_x < r + 3:
        shift = r + 3 - left_x
        left_x += shift
        right_x += shift
    if right_x > WIDTH - r - 3:
        shift = right_x - (WIDTH - r - 3)
        left_x -= shift
        right_x -= shift
    return (
        Octopus(left_x, y, -speed, -128.0, size, grace=.12),
        Octopus(right_x, y, +speed, -128.0, size, grace=.12),
    )


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(round(u + (v - u) * t) for u, v in zip(a, b))
