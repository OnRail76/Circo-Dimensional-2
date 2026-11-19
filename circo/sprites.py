"""Carga y prepara los PNG aprobados: sonriente y bandana.

El arte procede de la hoja de sprites creada para Circo Dimensional 2.
Se escalona una sola vez al arrancar, sin transformaciones costosas en el bucle.
"""
from __future__ import annotations
from pathlib import Path

from .config import SIZE_RADIUS


SPRITE_PATHS = {
    "smile": "pulpo_sonriente.png",
    "bandana": "pulpo_bandana.png",
}


def load_octopus_frames(pg, level_index: int = 0) -> dict[tuple[str, int, int], object]:
    """Carga poses de ambos pulpos, usando el color de la fase actual.

    El modelo original es el mismo; se usan PNG ya recoloreados para evitar
    filtros por píxel durante el juego (y cualquier caída de FPS).
    """
    root = Path(__file__).resolve().parent.parent / "assets" / "sprites"
    frames = {}
    for variant, filename in SPRITE_PATHS.items():
        themed = root / "fases" / f"fase_{level_index + 1:02d}_{variant}.png"
        source_path = themed if themed.is_file() else root / filename
        source = pg.image.load(str(source_path)).convert_alpha()
        for size, radius in SIZE_RADIUS.items():
            # 4 poses de squash/stretch: movimiento de bote, sin cambiar la silueta
            # ni el color aprobado por el autor.
            dim = 2 * radius + 9
            poses = ((0, 0), (2, -2), (-2, 3), (1, -1))
            for frame, (dw, dh) in enumerate(poses):
                w, h = max(14, dim + dw), max(14, dim + dh)
                frames[(variant, size, frame)] = pg.transform.smoothscale(source, (w, h))
    return frames
