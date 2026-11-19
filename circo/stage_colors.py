"""25 combinaciones cromáticas: solo cambia el pigmento del cuerpo.

El modelo, los ojos, la bandana, las animaciones y las colisiones permanecen
idénticos. Cada fase utiliza el primer color para pulpos sonrientes y, cuando
hay pulpos de bandana, el segundo color, claramente diferente.
"""
from __future__ import annotations

# (sonriente, bandana) RGB. Siempre dos tonos definidos, aunque haya un solo
# tipo en la fase. Esto facilita añadir Bandanas posteriormente sin romper nada.
STAGE_COLORS: tuple[tuple[tuple[int, int, int], tuple[int, int, int]], ...] = (
    ((249,   1, 198), ( 48, 218, 232)),  # 01: magenta clásico
    (( 34, 218, 204), (247, 130, 106)),  # 02: turquesa
    ((255, 171,  65), (110, 148, 255)),  # 03: naranja
    ((168, 105, 247), (124, 239, 120)),  # 04: violeta
    ((135, 235,  89), (247, 115, 192)),  # 05: verde lima
    (( 81, 169, 255), (255, 196,  77)),  # 06: azul cielo
    ((255, 131, 113), ( 82, 214, 224)),  # 07: coral
    (( 84, 229, 164), (235, 121, 240)),  # 08: menta
    ((255,  95, 183), ( 96, 222, 124)),  # 09: chicle
    ((252, 219,  72), (133, 114, 252)),  # 10: limón
    ((204, 143, 254), ( 83, 238, 189)),  # 11: lila
    (( 63, 192, 247), (253, 153,  95)),  # 12: azul eléctrico
    ((255,  87, 120), (121, 235, 144)),  # 13: cereza
    ((151, 237, 103), (244, 137, 212)),  # 14: manzana
    ((255, 159,  89), ( 58, 201, 252)),  # 15: mandarina / bandana azul
    ((234,  90, 203), (177, 235,  75)),  # 16: fucsia / lima
    (( 92, 142, 255), (255, 120, 109)),  # 17: índigo / coral
    (( 92, 229, 174), (178, 115, 253)),  # 18: menta / violeta
    ((255, 180,  82), ( 77, 189, 250)),  # 19: oro / azul
    ((195, 114, 244), (156, 233,  80)),  # 20: púrpura / manzana
    (( 79, 223, 229), (255, 103, 120)),  # 21: aguamarina / rojo
    ((165, 125, 251), (255, 168,  91)),  # 22: amatista / melocotón
    ((252, 204,  82), ( 79, 180, 252)),  # 23: dorado (un solo modelo)
    ((158, 235,  84), (252,  98, 161)),  # 24: lima / rosa
    (( 66, 230, 180), (255,  84, 194)),  # 25: jade / Primordial fucsia
)


def color_for(level_index: int, variant: str) -> tuple[int, int, int]:
    """Tono del cuerpo sin alterar el modelo del personaje."""
    if not 0 <= level_index < len(STAGE_COLORS):
        raise IndexError(f"Fase inexistente: {level_index + 1}")
    if variant not in ("smile", "bandana"):
        raise ValueError(f"Tipo de pulpo no previsto: {variant}")
    return STAGE_COLORS[level_index][int(variant == "bandana")]
