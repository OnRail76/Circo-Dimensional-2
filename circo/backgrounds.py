"""Fondos HD oficiales: imágenes facilitadas por el autor, no decorados procedimentales.

Se dibujan por separado en la ventana (smoothscale); los sprites del juego
se renderizan encima en un canvas transparente 480 x 300 (scale pixel-art).
"""
from __future__ import annotations
from pathlib import Path

# 16 % de oscurecimiento suave sobre la capa HD; sprites, HUD y suelo
# se dibujan después, conservando completamente su brillo y legibilidad.
HD_DIM_ALPHA = 40

BACKGROUND_FILES = {
    "circus": "01_carpa_errante.png",
    "inverted": "02_circo_invertido.png",
    "saturn": "03_jardines_saturno.png",
    "phantom": "04_teatro_fantasma.png",
    "core": "05_corazon_dimensional.png",
}


def cover_crop_dimensions(source_width: int, source_height: int,
                          target_width: int, target_height: int) -> tuple[int, int, int, int]:
    """Encuadre central sin deformación; recorta solo el exceso de proporción."""
    if min(source_width, source_height, target_width, target_height) <= 0:
        raise ValueError('Dimensiones no válidas')
    if source_width * target_height > source_height * target_width:
        crop_w = max(1, round(source_height * target_width / target_height))
        crop_h = source_height
    else:
        crop_w = source_width
        crop_h = max(1, round(source_width * target_height / target_width))
    crop_w = min(source_width, crop_w)
    crop_h = min(source_height, crop_h)
    return ((source_width - crop_w)//2, (source_height - crop_h)//2,
            crop_w, crop_h)


class HDBackdrops:
    def __init__(self, pg, root: Path | None = None):
        self.pg = pg
        folder = root or (Path(__file__).resolve().parent.parent / 'assets' / 'backgrounds')
        self.originals = {}
        for theme, filename in BACKGROUND_FILES.items():
            path = folder / filename
            if not path.is_file():
                raise FileNotFoundError(f'Falta el fondo HD oficial del mundo {theme}: {path}')
            self.originals[theme] = pg.image.load(str(path)).convert()
        self._cache_key = None
        self._cache_image = None

    def frame(self, theme: str, width: int, height: int):
        key = theme, width, height
        if key != self._cache_key:
            original = self.originals[theme]
            x, y, w, h = cover_crop_dimensions(*original.get_size(), width, height)
            source = original.subsurface(self.pg.Rect(x, y, w, h))
            self._cache_image = self.pg.transform.smoothscale(source, (width, height))
            veil = self.pg.Surface((width, height), self.pg.SRCALPHA)
            veil.fill((5, 7, 17, HD_DIM_ALPHA))
            self._cache_image.blit(veil, (0, 0))
            self._cache_key = key
        return self._cache_image
