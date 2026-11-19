"""Campaña de 25 fases: cinco mundos de cinco fases, con dificultad gradual.

Principios de diseño:
- En los primeros compases, todos los pulpos aparecen lejos de Dom,
  a izquierda/derecha, y avanzan inicialmente hacia las paredes.
- Los primeros cinco niveles enseñan las divisiones sin pulpos gigantes.
- El pulpo con bandana es élite: aguanta un impacto más y, al partirse,
  sus descendientes vuelven a ser pulpos normales.
"""
from __future__ import annotations
from dataclasses import dataclass
from .config import WIDTH, SIZE_RADIUS
from .physics import Platform


@dataclass(frozen=True, slots=True)
class Spawn:
    x: int
    y: int
    size: int
    direction: int = 1
    hp: int = 1
    variant: str = "smile"


@dataclass(frozen=True, slots=True)
class Level:
    title: str
    subtitle: str
    theme: str
    time_limit: int
    enemies: tuple[Spawn, ...]
    platforms: tuple[Platform, ...] = ()
    speed_factor: float = 1.0
    bounce_factor: float = 1.0


S = Spawn
P = Platform

WORLD_NAMES = (
    ("LA CARPA ERRANTE", "circus"),
    ("EL CIRCO INVERTIDO", "inverted"),
    ("JARDINES DE SATURNO", "saturn"),
    ("EL TEATRO FANTASMA", "phantom"),
    ("CORAZON DIMENSIONAL", "core"),
)

# Una fila por fase: subtítulo, enemigos, plataformas, segundos.
# Tiempos generosos al comienzo; las fases finales exigen dominar el látigo.
ENCOUNTERS = (
    # MUNDO 1: PRESENTACIÓN; nada de gigantes ni élites.
    ("UN PULPO, UN LATIGO", (S(65, 130, 2, -1),), (), 105),
    ("DOS SALTARINES", (S(65, 115, 2, -1), S(414, 129, 2, 1)), (), 108),
    ("APRENDE A PARTIRLOS", (S(72, 119, 1, -1),), (), 110),
    ("EL MAS PEQUENO", (S(71, 117, 1, -1), S(419, 148, 3, 1)), (), 112),
    ("PRIMERA GRAN FUNCION", (S(67, 110, 1, -1), S(386, 120, 2, 1), S(434, 168, 2, 1)), (), 120),
    # MUNDO 2: APARECEN LOS GRANDES Y LAS PLATAFORMAS.
    ("LLEGA EL GRANDULLON", (S(69, 107, 0, -1),), (P(168, 310, 185),), 123),
    ("REBOTES BAJO EL TECHO", (S(68, 101, 0, -1), S(416, 150, 3, 1)), (P(157, 227, 180),), 125),
    ("EL DOBLE DESAFIO", (S(70, 97, 0, -1), S(409, 129, 2, 1)), (P(150, 215, 189), P(267, 335, 189)), 128),
    ("NO PIERDAS EL RITMO", (S(71, 103, 0, -1), S(411, 130, 1, 1)), (P(124, 197, 193), P(281, 360, 193)), 132),
    ("LA CARPA SE COMPLICA", (S(70, 97, 0, -1), S(410, 108, 1, 1), S(430, 178, 2, 1)), (P(105, 189, 193), P(294, 378, 193)), 135),
    # MUNDO 3: PRIMERAS COMBINACIONES SERIAS; ÉLITE EN LA ÚLTIMA FASE.
    ("GRAVEDAD CAPRICHOSA", (S(69, 99, 0, -1), S(410, 118, 1, 1)), (P(157, 324, 178),), 135),
    ("EL ANILLO DE SATURNO", (S(68, 97, 0, -1), S(394, 103, 1, 1), S(435, 164, 2, 1)), (P(60, 145, 196), P(211, 284, 170), P(352, 431, 196)), 138),
    ("DOS PESOS PESADOS", (S(69, 105, 0, -1), S(410, 104, 0, 1)), (P(148, 210, 197), P(270, 333, 197)), 140),
    ("DANZA DE LOS OCHO BRAZOS", (S(65, 94, 0, -1), S(414, 103, 1, 1), S(373, 164, 1, 1)), (P(48, 126, 194), P(192, 292, 174), P(355, 432, 194)), 143),
    ("EL PRIMER BANDANA", (S(68, 94, 0, -1), S(415, 106, 1, 1, 2, "bandana"), S(373, 170, 1, 1), S(119, 184, 2, -1)), (P(164, 320, 184),), 145),
    # MUNDO 4: ELITE REGULAR Y MÁS PRESIÓN.
    ("EL PUBLICO SE REBELA", (S(70, 104, 0, -1), S(412, 99, 0, 1), S(402, 177, 2, 1, 2, "bandana")), (P(166, 311, 183),), 145),
    ("DOBLE FUNCIÓN", (S(67, 96, 0, -1), S(413, 114, 1, 1, 2, "bandana"), S(126, 169, 1, -1), S(378, 179, 2, 1)), (P(54, 149, 189), P(320, 414, 189)), 148),
    ("UN TEATRO A REVENTAR", (S(66, 102, 0, -1), S(413, 104, 0, 1), S(115, 182, 2, -1), S(369, 181, 2, 1, 2, "bandana")), (P(155, 231, 184), P(251, 330, 184)), 150),
    ("ATENCION A LA BANDANA", (S(70, 102, 0, -1), S(407, 97, 0, 1), S(360, 176, 1, 1, 2, "bandana")), (P(106, 173, 195), P(307, 376, 195)), 152),
    ("ULTIMO ACTO DEL TEATRO", (S(65, 97, 0, -1), S(414, 99, 0, 1), S(374, 176, 1, 1, 2, "bandana"), S(118, 186, 2, -1)), (P(158, 320, 179),), 155),
    # MUNDO 5: GRAN FINAL, AUN CON SALIDA SEGURA DESDE EL CENTRO.
    ("SE ABRE EL CORAZON", (S(68, 102, 0, -1), S(413, 107, 0, 1), S(365, 172, 1, 1, 2, "bandana"), S(122, 186, 2, -1)), (P(152, 232, 188), P(252, 331, 188)), 158),
    ("EL CIRCO IMPOSIBLE", (S(69, 97, 0, -1), S(412, 99, 0, 1), S(128, 177, 1, -1), S(359, 177, 1, 1, 2, "bandana")), (P(92, 177, 199), P(303, 387, 199)), 160),
    ("TRES GIGANTES", (S(67, 92, 0, -1), S(414, 98, 0, 1), S(122, 180, 0, -1)), (P(184, 294, 165),), 163),
    ("ANTES DEL APOCALIPSIS", (S(69, 99, 0, -1), S(409, 94, 0, 1), S(118, 175, 1, -1), S(361, 166, 1, 1, 2, "bandana"), S(435, 190, 2, 1)), (P(143, 215, 191), P(266, 339, 191)), 168),
    ("EL PULPO PRIMORDIAL", (S(81, 93, -1, -1, 4, "bandana"), S(403, 104, 0, 1), S(382, 180, 1, 1, 2, "bandana"), S(129, 185, 2, -1), S(436, 196, 2, 1)), (P(157, 218, 203), P(272, 339, 203)), 180),
)


def make_levels() -> tuple[Level, ...]:
    levels = []
    for i, (subtitle, enemies, platforms, seconds) in enumerate(ENCOUNTERS):
        title, theme = WORLD_NAMES[i // 5]
        levels.append(Level(
            title, subtitle, theme, seconds, enemies, platforms,
            speed_factor=round(.72 + .018 * i, 3),
            bounce_factor=round(.83 + .012 * i, 3),
        ))
    return tuple(levels)


LEVELS = make_levels()


def validate_levels() -> None:
    """Prueba simple de seguridad: inicio lejos de Dom y dentro del campo."""
    assert len(LEVELS) == 25
    for number, level in enumerate(LEVELS, 1):
        assert level.enemies, number
        for spawn in level.enemies:
            r = SIZE_RADIUS[spawn.size]
            assert r + 3 <= spawn.x <= WIDTH - r - 3, (number, spawn)
            assert abs(spawn.x - WIDTH / 2) >= 100, (number, spawn)
            assert spawn.direction == (-1 if spawn.x < WIDTH / 2 else 1), (number, spawn)
            assert spawn.variant in ("smile", "bandana"), (number, spawn)
            assert spawn.y - r >= 38 and spawn.y + r <= 263, (number, spawn)
