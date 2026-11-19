"""Sprites arcade de Dom y los pulpos; sin decorados procedimentales."""
from __future__ import annotations
import math
import random
from .config import WIDTH, HEIGHT, HUD_HEIGHT, FLOOR_Y, COLORS, SIZE_RADIUS
from .physics import blend
from .sprites import load_octopus_frames

THEMES = {
    "circus": ((16, 19, 51), (72, 32, 78), (250, 98, 150), (86, 221, 216)),
    "inverted": ((8, 34, 58), (22, 81, 109), (126, 248, 211), (250, 121, 169)),
    "saturn": ((23, 19, 56), (91, 45, 105), (237, 190, 106), (151, 151, 254)),
    "phantom": ((9, 23, 43), (20, 65, 76), (130, 235, 177), (179, 116, 230)),
    "core": ((30, 10, 49), (108, 27, 71), (255, 103, 114), (100, 220, 255)),
}

# Colores de la pista de juego (bajo los pies de Dom). El suelo queda
# separado del paisaje HD y cambia de ambiente con cada mundo.
FLOOR_PALETTES = {
    "circus":   ((30, 21, 52), (232, 104, 161), (113, 209, 235)),
    "inverted": ((18, 27, 53), (108, 221, 219), (164, 125, 243)),
    "saturn":   ((39, 26, 52), (235, 178, 125), (134, 193, 247)),
    "phantom":  ((19, 26, 45), (152, 218, 191), (178, 135, 246)),
    "core":     ((32, 20, 49), (233, 109, 173), (130, 210, 252)),
}




def _inflate_rect(rect, dx: int, dy: int):
    """Compatibilidad con pygame.Rect y con dobles de prueba basados en tuplas."""
    if hasattr(rect, 'inflate'):
        return rect.inflate(dx, dy)
    x, y, w, h = rect
    return (x - dx // 2, y - dy // 2, w + dx, h + dy)


class Art:
    def __init__(self, pg):
        self.pg = pg
        self.fonts = {}
        self.octopus_images = {}
        for size in SIZE_RADIUS:
            for frame in range(4):
                self.octopus_images[(size, frame)] = self.make_octopus(size, frame)
        self.palette_stage = 0
        self.sprite_images = load_octopus_frames(pg, level_index=0)
        self.hero_images = {k: self.make_dom(k) for k in range(4)}
        # Se construyen una sola vez, sin coste de composición por fotograma.
        self.floor_images = {name: self.make_floor(name) for name in THEMES}
        self._fx_layer = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        self._star_field = {}
        for theme_index, name in enumerate(THEMES):
            rng = random.Random(2026 + theme_index * 137)
            # Estrellas únicas por mundo; predominan los puntos diminutos.
            self._star_field[name] = [
                (rng.randrange(14, WIDTH - 14), rng.randrange(HUD_HEIGHT + 9, 198),
                 rng.random() * math.tau, rng.uniform(.7, 1.9), i % 6 == 0)
                for i in range(38)
            ]

    def set_level_palette(self, level_index: int):
        """Solo reconstruye los fotogramas al cambiar de fase, nunca por frame."""
        if level_index != self.palette_stage:
            self.sprite_images = load_octopus_frames(self.pg, level_index)
            self.palette_stage = level_index

    def font(self, size: int, bold: bool = True):
        key = size, bold
        if key not in self.fonts:
            try:
                self.fonts[key] = self.pg.font.SysFont("consolas", size, bold=bold)
            except Exception:
                self.fonts[key] = self.pg.font.Font(None, size)
        return self.fonts[key]

    def text(self, dest, string: str, cx: float, y: float, *, size: int = 15,
             color=(255, 255, 255), center: bool = True, shadow: bool = True,
             alpha: int = 255):
        f = self.font(size)
        img = f.render(string, False, color)
        if alpha != 255:
            img.set_alpha(alpha)
        rect = img.get_rect()
        rect.topleft = (round(cx - rect.width / 2) if center else round(cx), round(y))
        if shadow:
            sh = f.render(string, False, (5, 7, 20))
            sh.set_alpha(alpha)
            dest.blit(sh, rect.move(1, 2))
        dest.blit(img, rect)
        return rect

    def make_floor(self, theme: str):
        """Pista frontal arcade: comienza EXACTAMENTE en la línea física del suelo.

        No sustituye ni modifica el fondo HD, simplemente le da a Dom un
        plano de apoyo inequívoco. La textura no incluye objetos figurativos.
        """
        pg = self.pg
        base, rim, glow = FLOOR_PALETTES[theme]
        height = HEIGHT - FLOOR_Y
        surf = pg.Surface((WIDTH, height), pg.SRCALPHA)
        surf.fill((*base, 245))
        # Canto de escenario: sombra, filo brillante y borde secundario.
        pg.draw.rect(surf, (7, 11, 25, 252), (0, 0, WIDTH, 2))
        pg.draw.line(surf, (*rim, 255), (0, 2), (WIDTH - 1, 2), 2)
        pg.draw.line(surf, (*glow, 179), (0, 4), (WIDTH - 1, 4))
        pg.draw.line(surf, (12, 14, 35, 180), (0, 7), (WIDTH - 1, 7))
        # Piezas de la pista de baja intensidad, sin nuevos decorados.
        for y in range(8, height):
            factor = (y - 7) / max(1, height - 7)
            col = tuple(max(0, int(c * (1 - .30 * factor))) for c in base)
            pg.draw.line(surf, (*col, 240), (0, y), (WIDTH - 1, y))
        for x in range(0, WIDTH + 1, 48):
            pg.draw.line(surf, (*glow, 74), (x, 9), (x - 9, height - 1))
            pg.draw.line(surf, (9, 12, 30, 128), (x + 2, 9), (x - 7, height - 1))
        pg.draw.line(surf, (*rim, 82), (0, height - 8), (WIDTH - 1, height - 8))
        for x in range(24, WIDTH, 48):
            pg.draw.line(surf, (*glow, 93), (x - 5, 15), (x + 5, 15))
        return surf

    def floor(self, dest, theme: str, tick: float):
        """Suelo estable de todas las fases; solo palpita una línea sutil."""
        dest.blit(self.floor_images[theme], (0, FLOOR_Y))
        # Breve reflejo de energía desplazándose por la arista frontal.
        phase = (tick * 42) % (WIDTH + 100) - 50
        x = round(phase)
        col = FLOOR_PALETTES[theme][2]
        self.pg.draw.line(dest, (*col, 155), (max(0, x - 10), FLOOR_Y + 3),
                          (min(WIDTH - 1, x + 10), FLOOR_Y + 3))

    def star_glints(self, dest, theme: str, tick: float):
        """Brillos estelares y portales visibles pero respetuosos con el HD.

        Refuerza la atmósfera cósmica con estrellas, estelas y arcos energéticos
        más notorios que en v0.3.6, pero sin introducir decorados extraños.
        """
        pg = self.pg
        fx = self._fx_layer
        fx.fill((0, 0, 0, 0))
        _, _, accent, glow = THEMES[theme]
        for x, y, phase, speed, cross in self._star_field[theme]:
            light = .5 + .5 * math.sin(tick * speed * 2.0 + phase)
            if light < .34:
                continue
            alpha = round(34 + 156 * light ** 2)
            pg.draw.circle(fx, (*glow, alpha), (x, y), 1)
            if light > .90:
                pg.draw.circle(fx, (245, 249, 255, round(alpha * .42)), (x, y), 2)
            if cross and light > .76:
                reach = 2 if light < .92 else 3
                pg.draw.line(fx, (*glow, round(alpha * .72)),
                             (x - reach, y), (x + reach, y))
                pg.draw.line(fx, (245, 249, 255, round(alpha * .75)),
                             (x, y - reach), (x, y + reach))
        # Tres estelas cortas, discretas, detrás de la acción principal.
        for i in range(3):
            travel = (tick * (25 + i * 8) + 170 * i) % 820
            if travel > WIDTH + 24:
                continue
            x = round(travel - 46)
            y = 42 + i * 36
            pg.draw.line(fx, (*glow, 84), (x - 16, y - 4), (x + 1, y))
            pg.draw.line(fx, (245, 249, 255, 42), (x - 10, y - 2), (x + 3, y + 1))
            pg.draw.circle(fx, (232, 244, 255, 150), (x + 2, y), 1)
        # Ecos de portal algo más visibles en los extremos. Siguen muy fuera
        # de la zona de juego, pero ahora se leen mejor sobre el fondo HD.
        edge = 0 if theme in ("inverted", "phantom") else WIDTH
        cx = 18 if edge == 0 else WIDTH - 18
        cy = 126 + list(THEMES).index(theme) * 7
        for i in range(3):
            r = 30 + i * 8 + 2.0 * math.sin(tick * 1.45 + i * .7)
            rect = pg.Rect(round(cx - r), round(cy - r * 1.38),
                           round(r * 2), round(r * 2.76))
            phase = (tick * .34 + i * 1.85) % math.tau
            # halo difuso
            pg.draw.arc(fx, (*accent, 24 + i * 7), _inflate_rect(rect, 10, 14),
                        phase + .16, phase + 1.15, 4)
            # arco principal
            pg.draw.arc(fx, (*accent, 66 + i * 14), rect,
                        phase, phase + 1.04, 3)
            # eco complementario
            pg.draw.arc(fx, (*glow, 74 + i * 12), _inflate_rect(rect, -4, -6),
                        phase + math.pi * .98, phase + math.pi * .98 + .90, 2)
            # pequeño núcleo de energía
            px = round(cx + (8 if edge == 0 else -8))
            py = round(cy + (i - 1) * 8)
            pg.draw.circle(fx, (*glow, 24 + i * 10), (px, py), 7 - i)
        dest.blit(fx, (0, 0))

    def platforms(self, dest, platforms, theme):
        """Plataformas arcade muy visibles sobre los cinco fondos HD.

        La arista blanca empieza justo en p.y, que es la superficie física de
        rebote: no se modifican plataformas ni colisiones, solo el dibujo.
        Cuerpo oscuro + doble franja luminosa + remates sólidos evitan que se
        confundan con las estructuras representadas en las ilustraciones.
        """
        pg = self.pg
        _, rim, glow = FLOOR_PALETTES[theme]
        ink = (5, 9, 25)
        body = (21, 28, 56)
        body_light = (47, 57, 87)
        light = (246, 249, 253)
        for p in platforms:
            x, y = round(p.x1), round(p.y)
            w = max(8, round(p.x2 - p.x1))
            right = x + w - 1
            # Contorno negro amplio y grosor real de 14 px.
            pg.draw.rect(dest, ink, (x - 2, y - 1, w + 4, 16), border_radius=3)
            pg.draw.rect(dest, body, (x, y + 2, w, 10))
            pg.draw.rect(dest, body_light, (x + 4, y + 5, max(1, w - 8), 4))
            # Superficie de colisión: blanca en el centro y neón por debajo.
            pg.draw.line(dest, light, (x + 2, y), (right - 2, y), 2)
            pg.draw.line(dest, rim, (x + 2, y + 2), (right - 2, y + 2), 2)
            pg.draw.line(dest, glow, (x + 5, y + 4), (right - 5, y + 4), 1)
            # Segundo canto que define la plataforma incluso en un fondo claro.
            pg.draw.line(dest, rim, (x + 3, y + 11), (right - 3, y + 11), 2)
            pg.draw.line(dest, ink, (x + 3, y + 13), (right - 3, y + 13), 1)
            # Bordes gruesos y marcas de ensamblaje discretas, no decorados.
            pg.draw.rect(dest, rim, (x, y + 2, 3, 10))
            pg.draw.rect(dest, rim, (right - 2, y + 2, 3, 10))
            pg.draw.line(dest, light, (x + 1, y + 4), (x + 1, y + 7))
            pg.draw.line(dest, light, (right - 1, y + 4), (right - 1, y + 7))
            for k in range(x + 13, right - 8, 20):
                pg.draw.rect(dest, ink, (k, y + 6, 3, 3))
                pg.draw.rect(dest, glow, (k + 1, y + 6, 2, 2))

    def make_octopus(self, size: int, frame: int):
        pg = self.pg
        r = SIZE_RADIUS[size]
        box = r * 2 + 12
        s = pg.Surface((box, box), pg.SRCALPHA)
        cx = cy = r + 6
        palette = {
            -1: ((235, 79, 161), (132, 37, 134), (255, 186, 153)),
            0: ((79, 226, 216), (28, 112, 158), (173, 253, 226)),
            1: ((181, 135, 250), (89, 75, 175), (240, 207, 255)),
            2: ((252, 177, 90), (209, 92, 105), (255, 231, 146)),
            3: ((251, 126, 162), (164, 63, 127), (255, 206, 215)),
        }
        col, dark, light = palette[size]
        leg_rad = max(2, round(r * .12))
        for i in range(8):
            px = cx + (i - 3.5) * (r * .205)
            shift = (1 if (i + frame) % 2 else -1) * (3 if size <= 1 else 2)
            end = (round(px + (i - 3.5) * r * .08 + shift), round(cy + r * .86))
            origin = (round(px), round(cy + r * .24))
            pg.draw.line(s, dark, origin, end, max(2, round(r * .26)))
            pg.draw.line(s, col, origin, end, leg_rad)
            pg.draw.circle(s, col, end, max(1, leg_rad))
        body_rect = pg.Rect(round(cx - r * .87), round(cy - r * .88), round(1.74 * r), round(1.65 * r))
        pg.draw.ellipse(s, dark, body_rect.inflate(3, 3))
        pg.draw.ellipse(s, col, body_rect)
        shine = pg.Rect(round(cx - r * .65), round(cy - r * .72), round(.88 * r), round(.61 * r))
        pg.draw.ellipse(s, light, shine)
        pg.draw.ellipse(s, col, (round(cx - r * .46), round(cy - r * .56), round(r * 1.14), round(.65 * r)))
        eye_y = round(cy - r * .20)
        eye_dx = round(r * .31)
        er = max(2, round(r * .22))
        for ex in (cx - eye_dx, cx + eye_dx):
            pg.draw.ellipse(s, (250, 249, 249), (round(ex - er), eye_y - er, 2 * er, 2 * er + 1))
            pg.draw.rect(s, (13, 23, 51), (round(ex - 1), eye_y - 1, max(2, r // 7), max(2, r // 5)))
        if size == -1:
            pg.draw.line(s, (255, 215, 154), (cx - 7, eye_y - 10), (cx - 2, eye_y - 7), 2)
            pg.draw.line(s, (255, 215, 154), (cx + 2, eye_y - 7), (cx + 7, eye_y - 10), 2)
            pg.draw.arc(s, (52, 8, 61), (cx - 9, cy + 1, 18, 12), 0, math.pi, 2)
            for i in range(3):
                pg.draw.rect(s, (255, 198, 101), (round(cx - 12 + i * 12), round(cy - r * .75), 3, 3))
        elif r >= 13:
            pg.draw.line(s, dark, (cx - 3, cy + 4), (cx + 3, cy + 4), 2)
        else:
            pg.draw.line(s, dark, (cx - 2, cy + 3), (cx + 2, cy + 3))
        return s

    def octopus(self, dest, obj, t):
        pg = self.pg
        frame = int(t * 10 + obj.x * .018) % 4
        sprite = self.sprite_images.get((obj.variant, obj.size, frame),
                                        self.octopus_images[(obj.size, frame)])
        if obj.size == -1:
            # Aura del jefe, también indica puntos de vida restantes.
            rad = obj.radius + 6 + int(math.sin(t * 5) * 2)
            pg.draw.circle(dest, (198, 65, 127), (round(obj.x), round(obj.y)), rad, 1)
            for j in range(obj.hp):
                pg.draw.rect(dest, (255, 188, 102), (round(obj.x - 12 + j * 7), round(obj.y - obj.radius - 9), 5, 3))
        dest.blit(sprite, (round(obj.x - sprite.get_width() // 2), round(obj.y - sprite.get_height() // 2)))

    def make_dom(self, frame):
        pg = self.pg
        s = pg.Surface((32, 38), pg.SRCALPHA)
        bob = frame % 2
        # Sombrero de copa + rostro + nariz + bigote.
        pg.draw.rect(s, (11, 17, 38), (9, 2 + bob, 14, 14))
        pg.draw.rect(s, (37, 25, 60), (10, 3 + bob, 12, 7))
        pg.draw.rect(s, (255, 90, 145), (10, 11 + bob, 12, 3))
        pg.draw.rect(s, (12, 16, 36), (5, 14 + bob, 23, 4))
        pg.draw.rect(s, (244, 188, 126), (11, 17 + bob, 11, 8))
        # Opcion DIBUJOS: dos ojos blancos grandes con pupilas negras.
        # Permanecen legibles al doble de escala y en los cuatro fotogramas.
        pg.draw.rect(s, (15, 17, 37), (11, 18 + bob, 5, 4))
        pg.draw.rect(s, (15, 17, 37), (17, 18 + bob, 5, 4))
        pg.draw.rect(s, (250, 252, 255), (12, 18 + bob, 4, 3))
        pg.draw.rect(s, (250, 252, 255), (18, 18 + bob, 4, 3))
        pg.draw.rect(s, (15, 17, 37), (14, 19 + bob, 2, 2))
        pg.draw.rect(s, (15, 17, 37), (19, 19 + bob, 2, 2))
        pg.draw.rect(s, (27, 22, 42), (13, 23 + bob, 8, 1))
        # Casaca domador, faldones, botones y guantes.
        pg.draw.polygon(s, (97, 35, 100), [(9, 24), (22, 24), (25, 34), (6, 34)])
        pg.draw.rect(s, (204, 62, 103), (10, 25, 12, 9))
        pg.draw.line(s, (246, 195, 87), (11, 25), (12, 33), 2)
        pg.draw.line(s, (246, 195, 87), (21, 25), (20, 33), 2)
        pg.draw.circle(s, (255, 225, 143), (16, 28), 1)
        pg.draw.circle(s, (255, 225, 143), (16, 32), 1)
        pg.draw.line(s, (204, 62, 103), (8, 26), (4, 29), 3)
        pg.draw.line(s, (204, 62, 103), (24, 26), (27, 24), 3)
        pg.draw.rect(s, (244, 188, 126), (26, 22, 4, 4))
        pg.draw.rect(s, (243, 220, 121), (28, 18, 2, 5))
        pg.draw.rect(s, (26, 25, 50), (10, 33, 5, 5))
        pg.draw.rect(s, (26, 25, 50), (19, 33, 5, 5))
        if frame >= 2:
            pg.draw.rect(s, (14, 18, 42), (8, 35, 7, 2))
            pg.draw.rect(s, (14, 18, 42), (20, 34, 7, 3))
        return s

    def dom(self, dest, player_x, frame, invulnerable, t, shield):
        if invulnerable > 0 and int(t * 11) % 3 == 0:
            return
        s = self.hero_images[frame]
        x, y = round(player_x) - 16, FLOOR_Y - 37
        if shield > 0:
            self.pg.draw.ellipse(dest, (99, 225, 247), (x - 3, y - 6, 38, 48), 2)
            self.pg.draw.ellipse(dest, (23, 72, 106), (x - 5, y - 7, 42, 50), 1)
        dest.blit(s, (x, y))

    def laser(self, dest, beam, tick):
        pg = self.pg
        x, top = round(beam.x), round(beam.top)
        base = round(beam.bottom)
        pg.draw.line(dest, (36, 80, 134), (x - 2, top), (x - 2, base), 5)
        pg.draw.line(dest, (81, 233, 255), (x, top), (x, base), 3)
        pg.draw.line(dest, (255, 251, 212), (x, top), (x, base), 1)
        pg.draw.polygon(dest, (255, 112, 194), [(x - 4, top + 5), (x, top - 5), (x + 4, top + 5)])
        for iy in range(top + 12, base, 17):
            jitter = 1 if int(tick * 26 + iy) % 2 else -1
            pg.draw.line(dest, (165, 242, 255), (x, iy), (x + jitter * 4, iy + 3))

    def smiley(self, dest, x, y, radius=6):
        pg = self.pg
        cx, cy = round(x), round(y)
        # Smiley retro legible en HUD: amarillo relleno, contorno oscuro,
        # ojos negros y sonrisa gruesa. Debe leerse incluso a 1x.
        pg.draw.circle(dest, (18, 21, 34), (cx, cy), radius + 1)
        pg.draw.circle(dest, (251, 216, 81), (cx, cy), radius)
        if radius >= 6:
            pg.draw.circle(dest, (255, 239, 151), (cx - 2, cy - 2), max(1, radius // 3))
        eye_w = 2 if radius >= 6 else 1
        eye_h = 2 if radius >= 6 else 1
        pg.draw.rect(dest, (18, 21, 34), (cx - 3, cy - 2, eye_w, eye_h))
        pg.draw.rect(dest, (18, 21, 34), (cx + 2, cy - 2, eye_w, eye_h))
        # Sonrisa en píxel-art, más nítida que un arco fino.
        mouth = [(cx - 4, cy + 1), (cx - 3, cy + 2), (cx - 2, cy + 3),
                 (cx - 1, cy + 3), (cx, cy + 4), (cx + 1, cy + 3),
                 (cx + 2, cy + 3), (cx + 3, cy + 2), (cx + 4, cy + 1)]
        for i in range(len(mouth) - 1):
            pg.draw.line(dest, (18, 21, 34), mouth[i], mouth[i + 1])

    def dom_menu_selector(self, dest, x, y, frame=0):
        pg = self.pg
        # Cabeza de Dom animada para menús: 16x16 aprox, con pequeño bote/parpadeo.
        bob = 1 if frame % 2 else 0
        wink = frame % 4 == 2
        # ala del sombrero
        pg.draw.rect(dest, (12, 16, 36), (x + 1, y + 6 + bob, 16, 3))
        # copa
        pg.draw.rect(dest, (11, 17, 38), (x + 4, y + 0 + bob, 10, 7))
        pg.draw.rect(dest, (38, 27, 67), (x + 5, y + 1 + bob, 8, 3))
        pg.draw.rect(dest, (255, 90, 145), (x + 5, y + 5 + bob, 8, 2))
        # cara
        pg.draw.rect(dest, (18, 21, 34), (x + 3, y + 9 + bob, 11, 8))
        pg.draw.rect(dest, (244, 188, 126), (x + 4, y + 9 + bob, 9, 7))
        # ojos tipo “dibujos”
        if wink:
            pg.draw.rect(dest, (15, 17, 37), (x + 5, y + 11 + bob, 3, 1))
            pg.draw.rect(dest, (250, 252, 255), (x + 9, y + 10 + bob, 3, 2))
            pg.draw.rect(dest, (15, 17, 37), (x + 10, y + 10 + bob, 1, 1))
        else:
            pg.draw.rect(dest, (250, 252, 255), (x + 5, y + 10 + bob, 3, 2))
            pg.draw.rect(dest, (250, 252, 255), (x + 9, y + 10 + bob, 3, 2))
            pg.draw.rect(dest, (15, 17, 37), (x + 6, y + 10 + bob, 1, 1))
            pg.draw.rect(dest, (15, 17, 37), (x + 10, y + 10 + bob, 1, 1))
        pg.draw.rect(dest, (225, 132, 108), (x + 8, y + 11 + bob, 1, 2))
        # bigote
        pg.draw.rect(dest, (27, 22, 42), (x + 5, y + 14 + bob, 7, 1))
        pg.draw.rect(dest, (27, 22, 42), (x + 4, y + 13 + bob, 2, 1))
        pg.draw.rect(dest, (27, 22, 42), (x + 11, y + 13 + bob, 2, 1))

    def pulpo_menu_selector(self, dest, x, y, t):
        """Pulpo sonriente auténtico, animado y ligeramente saltarín.

        Reutiliza los PNG y fotogramas del juego. Se mueve únicamente el
        selector resaltado; nunca se rasteriza el sprite cada fotograma.
        """
        frame = int(t * 9) % 4
        sprite = self.sprite_images[("smile", 3, frame)]
        # Rebote periódico de 4 px, con squash/stretch en el aterrizaje.
        bounce = max(0.0, math.sin(t * 8.0)) * 4.0
        dest.blit(sprite, (round(x - sprite.get_width() / 2),
                           round(y - sprite.get_height() / 2 - bounce)))

    def vignette(self, dest):
        pg = self.pg
        pg.draw.rect(dest, (17, 10, 30), (0, 0, WIDTH, HEIGHT), 3)
        for x in range(0, WIDTH, 5):
            pg.draw.rect(dest, (11, 14, 29), (x, HEIGHT - 2, 3, 2))
