"""Muestrario PNG hecho con los sprites auténticos incluidos en el juego.

    python tools/muestrario_colores.py
Requiere Pillow solo para crear la lámina (no durante el juego).
"""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from circo.levels import LEVELS


def make_preview():
    from PIL import Image, ImageDraw, ImageFont
    sprite_path = ROOT / 'assets' / 'sprites' / 'fases'
    output = ROOT / 'docs' / 'muestrario_25_fases_sprites.png'
    output.parent.mkdir(exist_ok=True)
    image = Image.new('RGB', (1210, 920), (11, 14, 33))
    draw = ImageDraw.Draw(image)
    fontpath = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    smallpath = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    headline = ImageFont.truetype(str(fontpath), 15) if fontpath.is_file() else ImageFont.load_default()
    small = ImageFont.truetype(str(smallpath), 11) if smallpath.is_file() else ImageFont.load_default()
    draw.text((30, 14), 'CIRCO DIMENSIONAL 2 · COLORES REALES DE LAS 25 FASES',
              font=headline, fill=(254, 214, 114))
    draw.text((31, 40),
              'Sprites originales coloreados, sin modelos inventados. Bandana solo cuando aparece en esa fase.',
              font=small, fill=(172, 210, 232))
    for idx, level in enumerate(LEVELS):
        col, row = idx % 5, idx // 5
        x, y = 12 + col * 240, 68 + row * 168
        draw.rounded_rectangle((x, y, x + 229, y + 159), radius=12,
                               fill=(34, 29, 64), outline=(95, 79, 136), width=2)
        draw.text((x + 12, y + 8), f'FASE {idx+1:02d}', font=headline, fill=(255, 211, 96))
        smile = Image.open(sprite_path / f'fase_{idx+1:02d}_smile.png').convert('RGBA')
        if any(sp.variant == 'bandana' for sp in level.enemies):
            bandana = Image.open(sprite_path / f'fase_{idx+1:02d}_bandana.png').convert('RGBA')
            smile.thumbnail((95, 95), Image.Resampling.LANCZOS)
            bandana.thumbnail((95, 95), Image.Resampling.LANCZOS)
            image.paste(smile, (x + 9, y + 39), smile)
            image.paste(bandana, (x + 123, y + 39), bandana)
            draw.text((x + 21, y + 138), 'NORMAL', font=small, fill=(208, 217, 239))
            draw.text((x + 133, y + 138), 'BANDANA', font=small, fill=(208, 217, 239))
        else:
            smile.thumbnail((112, 110), Image.Resampling.LANCZOS)
            image.paste(smile, (x + 55, y + 32), smile)
            draw.text((x + 84, y + 139), 'NORMAL', font=small, fill=(208, 217, 239))
    image.save(output, optimize=True)
    return output


if __name__ == '__main__':
    print(make_preview())
