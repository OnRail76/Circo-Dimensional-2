"""Genera PNG de cuerpos recoloreados SIN redibujar las siluetas.

Se ejecuta al preparar la distribución. Solo necesita Pillow para editar PNG;
el videojuego utiliza Pygame CE y NO depende de Pillow para ejecutarse.

    python -m pip install Pillow
    python tools/recolorear_pulpos.py
"""
from __future__ import annotations
import colorsys
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from circo.stage_colors import STAGE_COLORS, color_for


def recolor_pixel(pixel: tuple[int, int, int, int], target: tuple[int, int, int]):
    """Recolorea pigmento rosa conservando brillos, ojos, contornos y alfa.

    Los sprites originales tienen el cuerpo magenta (hue ~0.86); lo rotamos
    dentro del intervalo magenta-violeta. Blancos, negros y ornamentos que
    estén fuera de ese rango permanecen idénticos píxel a píxel.
    """
    r, g, b, a = pixel
    if a == 0:
        return pixel
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if not (0.72 <= h <= 0.965 and s >= 0.29 and v >= 0.17):
        return pixel
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in target))
    # Mantener brillo relativo del sombreado original y su expresividad.
    h2 = (th + (h - 0.865) * .19) % 1.0
    s2 = min(1.0, max(0.35, s * (0.85 + ts * .15)))
    v2 = min(1.0, v * (0.87 + tv * .13))
    rr, gg, bb = colorsys.hsv_to_rgb(h2, s2, v2)
    return (round(rr * 255), round(gg * 255), round(bb * 255), a)


def recolor_image(source, target, variant="smile"):
    from PIL import Image
    image = source.convert('RGBA')
    result = Image.new('RGBA', image.size)
    width, _ = image.size
    pixels = []
    for n, original in enumerate(image.getdata()):
        x, y = n % width, n // width
        # El logotipo rojo/rosa bordado sobre la bandana es parte del vestuario,
        # no del cuerpo. Su tinta debe mantenerse idéntica en las 25 fases.
        if variant == 'bandana' and 69 <= x <= 102 and 28 <= y <= 47:
            pixels.append(original)
        else:
            pixels.append(recolor_pixel(original, target))
    result.putdata(pixels)
    return result


def build(root: Path = ROOT):
    from PIL import Image
    sprites = root / 'assets' / 'sprites'
    out = sprites / 'fases'
    out.mkdir(parents=True, exist_ok=True)
    for variant, filename in (("smile", "pulpo_sonriente.png"),
                              ("bandana", "pulpo_bandana.png")):
        original = Image.open(sprites / filename).convert('RGBA')
        for i in range(len(STAGE_COLORS)):
            recolor_image(original, color_for(i, variant), variant).save(
                out / f"fase_{i + 1:02d}_{variant}.png", optimize=True)
    return out


if __name__ == '__main__':
    print('Variantes PNG generadas en:', build())
