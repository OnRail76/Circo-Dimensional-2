"""Circo Dimensional 2: campaña de 25 fases y cinco mundos de pulpos."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import math
import random
import json

import pygame as pg

from .art import Art, THEMES
from .backgrounds import HDBackdrops
from .audio import SoundBank
from .config import (
    TITLE, VERSION, WIDTH, HEIGHT, SCALE, FPS, HUD_HEIGHT, FLOOR_Y,
    PLAYER_SPEED, PLAYER_HALF_WIDTH, PLAYER_HEIGHT, START_LIVES, MAX_LIVES,
    SHOT_COOLDOWN, SHOT_HOLD, SHOT_SPEED, SHOT_LIMIT, STAGE_READY_SECS,
    STAGE_CLEAR_SECS, END_MIN_SECS, HIT_INVULN_SECS, DEATH_ANIMATION_SECS, SIZE_RADIUS, SIZE_SPEED,
    SCORE_BY_SIZE, COLORS, DOUBLE_WHIP_DURATION,
)
from .levels import LEVELS
from .stage_colors import color_for
from .physics import (
    Octopus, move_octopus, circle_hits_vertical_segment,
    circle_hits_rectangle, split_octopus,
)


@dataclass(slots=True)
class Beam:
    x: float
    top: float
    age_top: float = 0.0
    bottom: float = FLOOR_Y - 15  # nacimiento exacto desde la mano de Dom


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    total: float
    color: tuple[int, int, int]
    radius: int = 2


@dataclass(slots=True)
class DomFragment:
    image: object
    x: float
    y: float
    vx: float
    vy: float
    rotation: float
    rotation_speed: float
    life: float


@dataclass(slots=True)
class Pickup:
    x: float
    y: float
    kind: str
    vy: float = 92.0  # Los bonus llegan al suelo antes y son alcanzables
    age: float = 0.0


@dataclass(slots=True)
class FloatText:
    x: float
    y: float
    caption: str
    color: tuple[int, int, int]
    age: float = 0.0


class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption("Circo Dimensional 2 — Tony C. Ware")
        # Icono de ventana: el mismo pulpo sonriente PNG usado dentro del juego.
        icon = Path(__file__).resolve().parent.parent / "assets" / "icons" / "pulpo_normal_64.png"
        if icon.is_file():
            try:
                pg.display.set_icon(pg.image.load(str(icon)))
            except (pg.error, OSError):
                pass
        self.fullscreen = False
        self.window = pg.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
        self.canvas = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA).convert_alpha()
        self.clock = pg.time.Clock()
        self.art = Art(pg)
        self.hd_backdrops = HDBackdrops(pg)
        self.audio = SoundBank(pg, Path(__file__).resolve().parent.parent)
        self.rng = random.Random()
        self.alive = True
        self.state = "TITLE"
        self.state_age = 0.0
        self.t = 0.0
        self.level_idx = 0
        self.lives = START_LIVES
        self.score = 0
        self.high_score = 0
        self.player_x = WIDTH / 2
        self.walk_frame = 0.0
        self.enemies: list[Octopus] = []
        self.beams: list[Beam] = []
        self.particles: list[Particle] = []
        self.pickups: list[Pickup] = []
        self.pickup_kills_since_drop = 0
        self.pickups_spawned_this_stage = 0
        self.float_texts: list[FloatText] = []
        self.cooldown = 0.0
        self.invulnerable = 0.0
        self.shield_timer = 0.0
        self.multishot_timer = 0.0
        self.combo = 0
        self.world_bonus_life = False
        self.last_hit_t = -100.0
        self.timer = 0.0
        self.shake = 0.0
        self.joystick = None
        self.title_selected = 0
        self.pause_selected = 0
        self.options_selected = 0
        self.options_origin = "TITLE"
        self.last_menu_axis = -100.0
        self.death_fragments: list[DomFragment] = []
        self.death_x = self.player_x
        self.death_y = FLOOR_Y - 19
        self.death_reason = "hit"
        self.settings_path = Path.home() / '.config' / 'circo-dimensional-2' / 'settings.json'
        self.load_settings()
        try:
            pg.joystick.init()
            self.refresh_joystick()
        except pg.error:
            pass
        self.demo = [Octopus(341, 173, 64, -164, 0),
                     Octopus(96, 177, -85, -112, 1, variant="bandana")]
        self.audio.sync_music("TITLE", self.level_idx)

    def set_state(self, state: str):
        self.state = state
        self.state_age = 0.0
        music_state = ("PAUSE" if self.options_origin == "PAUSE" else "TITLE") if state == "OPTIONS" else state
        self.audio.sync_music(music_state, self.level_idx)

    def load_settings(self):
        try:
            values = json.loads(self.settings_path.read_text(encoding='utf-8'))
            self.audio.music_enabled = bool(values.get('music', True))
            self.audio.effects_enabled = bool(values.get('effects', True))
            self.audio.music_volume = max(0.0, min(1.0, float(values.get('music_volume', .24))))
            self.audio.effects_volume = max(0.0, min(1.0, float(values.get('effects_volume', .75))))
            self.audio.set_volumes()
            self.audio._apply_music_volume()
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def save_settings(self):
        data = {
            'music': self.audio.music_enabled,
            'effects': self.audio.effects_enabled,
            'music_volume': self.audio.music_volume,
            'effects_volume': self.audio.effects_volume,
        }
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except OSError:
            pass

    def new_game(self):
        self.score = 0
        self.lives = START_LIVES
        self.level_idx = 0
        self.combo = 0
        self.death_fragments.clear()
        self.invulnerable = 0
        self.shield_timer = 0
        self.multishot_timer = 0
        self.start_level()

    def clear_temporary_powerups(self):
        """Cancelar efectos de bonus al cerrar o abrir cualquier pantalla.

        La vida extra es permanente, y +TIEMPO solo modifica el reloj de
        la pantalla actual (que start_level reinicia al valor propio de fase).
        """
        self.shield_timer = 0.0
        self.multishot_timer = 0.0

    def start_level(self):
        # No heredar escudo ni doble látigo de fases superadas o reintentadas.
        self.clear_temporary_powerups()
        level = LEVELS[self.level_idx]
        # Un único modelo por tipo, nuevos pigmentos cada una de las 25 fases.
        self.art.set_level_palette(self.level_idx)
        self.enemies = []
        self.player_x = WIDTH / 2
        self.walk_frame = 0
        self.cooldown = 0
        self.beams.clear()
        self.pickups.clear()
        self.pickup_kills_since_drop = 0
        self.pickups_spawned_this_stage = 0
        self.particles.clear()
        self.float_texts.clear()
        self.timer = float(level.time_limit)
        self.combo = 0
        self.world_bonus_life = False
        # Más margen de reacción en el aprendizaje inicial.
        self.invulnerable = max(self.invulnerable, 1.75 if self.level_idx < 5 else 1.15)
        for sp in level.enemies:
            speed = SIZE_SPEED[sp.size]
            obj = Octopus(float(sp.x), float(sp.y), speed * level.speed_factor * sp.direction,
                          -92.0 * level.bounce_factor, sp.size, hp=sp.hp, grace=.5,
                          variant=sp.variant)
            self.enemies.append(obj)
        self.set_state("READY")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pg.display.set_mode((0, 0), pg.FULLSCREEN)
        else:
            self.window = pg.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))

    def refresh_joystick(self):
        try:
            self.joystick = None
            pg.joystick.init()
            if pg.joystick.get_count():
                self.joystick = pg.joystick.Joystick(0)
                self.joystick.init()
        except (pg.error, AttributeError):
            self.joystick = None

    def joystick_direction_fire(self):
        if not self.joystick:
            return 0, False
        try:
            direction = 0
            if self.joystick.get_numaxes():
                axis = self.joystick.get_axis(0)
                if abs(axis) > .25:
                    direction = -1 if axis < 0 else 1
            if self.joystick.get_numhats():
                hatx = self.joystick.get_hat(0)[0]
                if hatx:
                    direction = hatx
            shoot = any(self.joystick.get_button(i) for i in range(min(3, self.joystick.get_numbuttons())))
            return direction, bool(shoot)
        except pg.error:
            self.joystick = None
            return 0, False

    def gamepad_name(self):
        try:
            return self.joystick.get_name() if self.joystick else "NO DETECTADO"
        except (pg.error, AttributeError):
            return "NO DETECTADO"

    def menu_items(self):
        if self.state == "TITLE":
            return ["JUGAR", "OPCIONES", "CONTROLES", "SALIR"]
        if self.state == "PAUSE":
            return ["CONTINUAR", "OPCIONES", "REINICIAR PARTIDA", "VOLVER AL TITULO"]
        if self.state == "OPTIONS":
            return ["MUSICA", "EFECTOS", "VOLUMEN MUSICA", "VOLUMEN EFECTOS", "VOLVER"]
        return []

    def selected_index(self):
        return {"TITLE": self.title_selected, "PAUSE": self.pause_selected,
                "OPTIONS": self.options_selected}.get(self.state, 0)

    def navigate(self, step):
        items = self.menu_items()
        if not items:
            return
        idx = (self.selected_index() + step) % len(items)
        if self.state == 'TITLE':
            self.title_selected = idx
        elif self.state == 'PAUSE':
            self.pause_selected = idx
        elif self.state == 'OPTIONS':
            self.options_selected = idx
        self.audio.play('ui')

    def open_options(self):
        self.options_origin = self.state
        self.options_selected = 0
        self.set_state('OPTIONS')

    def go_back(self):
        if self.state == 'OPTIONS':
            self.set_state(self.options_origin)
        elif self.state == 'HELP':
            self.set_state('TITLE')
        elif self.state == 'PAUSE':
            self.set_state('PLAY')
        elif self.state == 'TITLE':
            self.alive = False
        elif self.state == 'PLAY':
            self.pause_selected = 0
            self.set_state('PAUSE')

    def select_menu(self):
        if self.state == 'TITLE':
            choice = self.title_selected
            if choice == 0:
                self.new_game()
            elif choice == 1:
                self.open_options()
            elif choice == 2:
                self.set_state('HELP')
            else:
                self.alive = False
        elif self.state == 'PAUSE':
            choice = self.pause_selected
            if choice == 0:
                self.set_state('PLAY')
            elif choice == 1:
                self.open_options()
            elif choice == 2:
                self.new_game()
            else:
                self.set_state('TITLE')
        elif self.state == 'OPTIONS':
            if self.options_selected == 4:
                self.go_back()
            else:
                self.change_option(1)
        elif self.state == 'HELP':
            self.go_back()

    def change_option(self, step):
        if self.state != 'OPTIONS':
            return
        choice = self.options_selected
        if choice == 0:
            self.audio.toggle_music()
        elif choice == 1:
            self.audio.toggle_effects()
        elif choice == 2:
            self.audio.adjust_music_volume(.05 * step)
        elif choice == 3:
            self.audio.adjust_effects_volume(.05 * step)
        else:
            return
        self.save_settings()
        self.audio.play('ui')

    def handle_events(self):
        navstates = ('TITLE', 'PAUSE', 'OPTIONS', 'HELP')
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                self.alive = False
                return
            if ev.type in (getattr(pg, 'JOYDEVICEADDED', -91), getattr(pg, 'JOYDEVICEREMOVED', -92)):
                self.refresh_joystick()
                continue
            if ev.type == getattr(pg, 'JOYHATMOTION', -93) and self.state in navstates:
                if ev.value[1]:
                    self.navigate(-int(ev.value[1]))
                if ev.value[0]:
                    self.change_option(int(ev.value[0]))
                continue
            if ev.type == getattr(pg, 'JOYAXISMOTION', -94) and self.state in navstates:
                # Evita saltar varias opciones por un único movimiento del stick.
                if self.t - self.last_menu_axis >= .22 and abs(ev.value) >= .65:
                    if ev.axis == 1:
                        self.navigate(1 if ev.value > 0 else -1)
                        self.last_menu_axis = self.t
                    elif ev.axis == 0:
                        self.change_option(1 if ev.value > 0 else -1)
                        self.last_menu_axis = self.t
                continue
            if ev.type == getattr(pg, 'JOYBUTTONDOWN', -95):
                if ev.button in (7, 9):
                    if self.state == 'PLAY':
                        self.pause_selected = 0
                        self.set_state('PAUSE')
                    elif self.state == 'PAUSE':
                        self.set_state('PLAY')
                    elif self.state in ('TITLE', 'HELP', 'OPTIONS'):
                        self.select_menu()
                    elif self.state in ('GAME_OVER', 'VICTORY') and self.state_age >= END_MIN_SECS:
                        self.set_state('TITLE')
                elif ev.button == 0:
                    if self.state in navstates:
                        self.select_menu()
                    elif self.state in ('GAME_OVER', 'VICTORY') and self.state_age >= END_MIN_SECS:
                        self.set_state('TITLE')
                elif ev.button == 1 and self.state in navstates:
                    self.go_back()
                continue
            if ev.type != pg.KEYDOWN:
                continue
            if ev.key == pg.K_F11:
                self.toggle_fullscreen()
                continue
            if ev.key == pg.K_m:
                self.audio.toggle()
                continue
            if ev.key == pg.K_n:
                self.audio.toggle_music()
                self.save_settings()
                continue
            if ev.key in (pg.K_MINUS, pg.K_KP_MINUS):
                self.audio.adjust_music_volume(-.05)
                self.save_settings()
                continue
            if ev.key in (pg.K_EQUALS, getattr(pg, 'K_PLUS', pg.K_EQUALS), pg.K_KP_PLUS):
                self.audio.adjust_music_volume(.05)
                self.save_settings()
                continue
            if ev.key == pg.K_ESCAPE:
                self.go_back()
                continue
            if ev.key == pg.K_F1 and self.state in ('TITLE', 'HELP'):
                self.set_state('HELP' if self.state == 'TITLE' else 'TITLE')
                continue
            if self.state in ('TITLE', 'PAUSE', 'OPTIONS'):
                if ev.key in (pg.K_UP, pg.K_w):
                    self.navigate(-1)
                elif ev.key in (pg.K_DOWN, pg.K_s):
                    self.navigate(1)
                elif ev.key == pg.K_LEFT:
                    self.change_option(-1)
                elif ev.key == pg.K_RIGHT:
                    self.change_option(1)
                elif ev.key in (pg.K_SPACE, pg.K_RETURN):
                    self.select_menu()
                continue
            if ev.key in (pg.K_SPACE, pg.K_RETURN):
                if self.state == 'HELP':
                    self.set_state('TITLE')
                elif self.state in ('GAME_OVER', 'VICTORY') and self.state_age >= END_MIN_SECS:
                    self.audio.play('ui')
                    self.set_state('TITLE')
                elif self.state == 'PLAY' and ev.key == pg.K_SPACE:
                    self.fire()

    def controls(self):
        key = pg.key.get_pressed()
        direction = (1 if key[pg.K_RIGHT] or key[pg.K_d] or key[pg.K_p] else 0) - (
            1 if key[pg.K_LEFT] or key[pg.K_a] or key[pg.K_o] else 0)
        joy_dir, joy_fire = self.joystick_direction_fire()
        if joy_dir:
            direction = joy_dir
        return direction, bool(key[pg.K_SPACE] or joy_fire)

    def fire(self):
        if self.state != "PLAY" or self.cooldown > 0:
            return
        twin = self.multishot_timer > 0
        # Bonus DOBLE: dos látigos simultáneos, uno por mano. Hasta dos parejas
        # en pantalla; la normal sigue permitiendo hasta dos látigos sueltos.
        required = 2 if twin else 1
        limit = SHOT_LIMIT * (2 if twin else 1)
        if len(self.beams) + required > limit:
            return  # nunca sale una pareja incompleta
        # Misma silueta de Dom. Solo cambian los orígenes de los rayos.
        # Sprite 32x38 situado en (player_x-16, FLOOR_Y-37).
        right_y = FLOOR_Y - 15   # guante derecho a la altura de la mano
        if twin:
            left_y = FLOOR_Y - 9
            self.beams.append(Beam(self.player_x - 12, left_y, bottom=left_y))
        self.beams.append(Beam(self.player_x + 12, right_y, bottom=right_y))
        self.cooldown = SHOT_COOLDOWN * (.70 if twin else 1.0)
        self.audio.play("laser")

    def spawn_burst(self, x, y, size, color, amount=12):
        for i in range(amount):
            angle = math.tau * (i / amount) + self.rng.uniform(-.27, .27)
            velocity = self.rng.uniform(37, 112) * (1.0 + (size <= 0) * .30)
            life = self.rng.uniform(.32, .77)
            self.particles.append(Particle(
                x, y, math.cos(angle) * velocity, math.sin(angle) * velocity,
                life, life, color, radius=self.rng.choice((1, 2, 2, 3))
            ))
        if len(self.particles) > 220:
            del self.particles[:len(self.particles) - 220]

    def burst_color(self, enemy):
        # Las partículas tienen el mismo pigmento que el pulpo destruido.
        return color_for(self.level_idx, enemy.variant)

    def hit_enemy(self, enemy):
        self.spawn_burst(enemy.x, enemy.y, enemy.size, self.burst_color(enemy),
                         amount=24 if enemy.size <= 0 else 13)
        self.shake = max(self.shake, .16 if enemy.size <= 0 else .07)
        # Los Bandana resisten dos impactos; el Primordial requiere cuatro.
        if enemy.hp > 1:
            enemy.hp -= 1
            enemy.vx *= -1
            enemy.vy = -185.0
            enemy.grace = .21
            self.audio.play("split")
            self.float_texts.append(FloatText(enemy.x, enemy.y - 37, "¡IMPACTO!", COLORS["gold"]))
            return
        if self.t - self.last_hit_t <= 1.35:
            self.combo = min(self.combo + 1, 5)
        else:
            self.combo = 1
        self.last_hit_t = self.t
        earned = SCORE_BY_SIZE[enemy.size] * self.combo
        self.score += earned
        self.high_score = max(self.high_score, self.score)
        self.float_texts.append(FloatText(enemy.x, enemy.y - enemy.radius - 5,
                                          f"+{earned}", COLORS["gold"]))
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        children = split_octopus(enemy, LEVELS[self.level_idx].speed_factor)
        self.enemies.extend(children)
        self.audio.play("split" if children else "pop")
        self.try_drop_pickup(enemy)

    def try_drop_pickup(self, enemy):
        """Primer premio temprano; otros espaciados, sin lluvia de bonus.

        Nunca generar bonus en la baja final, porque el cierre de pantalla
        los retiraría antes de poder recogerlos.
        """
        if not self.enemies:
            return False
        self.pickup_kills_since_drop += 1
        # Uno accesible por fase; máximo dos en fases intermedias y avanzadas.
        maximum = 1 if self.level_idx < 5 else 2
        if self.pickups_spawned_this_stage >= maximum or self.pickups:
            return False
        first = self.pickups_spawned_this_stage == 0
        if not first and (self.pickup_kills_since_drop < 6 or self.rng.random() >= .23):
            return False
        kind = self.rng.choices(['SHIELD', 'DOUBLE', 'TIME', 'LIFE'], [35, 30, 31, 4])[0]
        # Limitar el nacimiento al campo jugable y dar un margen de 2 s de caída.
        x = max(18, min(WIDTH - 18, enemy.x))
        y = max(HUD_HEIGHT + 14, min(FLOOR_Y - 50, enemy.y))
        self.pickups.append(Pickup(x, y, kind))
        self.pickup_kills_since_drop = 0
        self.pickups_spawned_this_stage += 1
        return True

    def collect_pickup(self, pickup):
        if pickup.kind == "SHIELD":
            self.shield_timer = max(self.shield_timer, 8.0)
            label = "¡ESCUDO!"
        elif pickup.kind == "DOUBLE":
            # Diez segundos efectivos; la pausa no descuenta duración.
            # Otro doble látigo reinicia el contador, nunca acumula tiempo.
            self.multishot_timer = DOUBLE_WHIP_DURATION
            label = f"¡DOBLE LATIGO! {int(DOUBLE_WHIP_DURATION)}s"
        elif pickup.kind == "TIME":
            self.timer += 15.0
            label = "+15 SEGUNDOS"
        else:
            self.lives = min(MAX_LIVES, self.lives + 1)
            label = "¡VIDA EXTRA!"
        self.float_texts.append(FloatText(self.player_x, FLOOR_Y - 42, label, COLORS["green"]))
        self.pickups.remove(pickup)
        self.audio.play("bonus")

    def explode_dom(self, reason='hit'):
        """Secuencia de muerte de dibujos animados, sin respawn durante el fogonazo."""
        self.lives -= 1
        self.death_reason = reason
        self.death_x, self.death_y = self.player_x, FLOOR_Y - 19
        self.beams.clear()
        self.death_fragments.clear()
        self.shake = .85
        self.invulnerable = 0.0  # los dos segundos empiezan al reaparecer
        sprite = self.art.hero_images[0]
        # Sombrero completo sale volando; el resto de Dom se desarma en pedazos.
        pieces = [(4, 0, 24, 17)]
        pieces.extend((x, y, min(8, 32 - x), min(7, 38 - y))
                      for y in (17, 24, 31) for x in (0, 8, 16, 24))
        for x, y, w, h in pieces:
            fragment = sprite.subsurface(pg.Rect(x, y, w, h)).copy()
            if not pg.mask.from_surface(fragment).count():
                continue
            cx = self.player_x - 16 + x + w / 2
            cy = FLOOR_Y - 37 + y + h / 2
            direction = self.rng.uniform(-1.0, 1.0)
            self.death_fragments.append(DomFragment(
                fragment, cx, cy, direction * 190, -self.rng.uniform(105, 255),
                0, self.rng.uniform(-650, 650), 1.22))
        # Una nube de confeti y chispas mucho más grande que la de los pulpos.
        palette = [COLORS['gold'], COLORS['cyan'], COLORS['pink'], COLORS['red'],
                   (255, 255, 247), COLORS['violet'], COLORS['green']]
        for _ in range(75):
            angle = self.rng.uniform(0, math.tau)
            speed = self.rng.uniform(55, 265)
            life = self.rng.uniform(.48, 1.15)
            self.particles.append(Particle(
                self.death_x, self.death_y,
                math.cos(angle) * speed, math.sin(angle) * speed - 52,
                life, life, self.rng.choice(palette), self.rng.choice((1, 2, 3, 4))))
        self.audio.play('dom_boom' if 'dom_boom' in self.audio.sounds else 'damage')
        self.set_state('DEATH')

    def safest_respawn_x(self):
        """Elegir el punto de suelo menos peligroso antes de los 2 s de parpadeo."""
        positions = [WIDTH / 2, WIDTH / 2 - 70, WIDTH / 2 + 70,
                     WIDTH / 2 - 135, WIDTH / 2 + 135, 32, WIDTH - 32]
        def margin(x):
            if not self.enemies:
                return 10000
            return min(math.hypot(e.x - x, (e.y - (FLOOR_Y - 19)) * 1.25) - e.radius
                       for e in self.enemies)
        return max(positions, key=margin)

    def take_damage(self):
        if self.state != 'PLAY' or self.invulnerable > 0 or self.shield_timer > 0:
            return
        self.explode_dom('hit')

    def timeout(self):
        self.explode_dom('timeout')

    def update_play(self, dt):
        level = LEVELS[self.level_idx]
        self.cooldown = max(0.0, self.cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.multishot_timer = max(0.0, self.multishot_timer - dt)
        self.timer -= dt
        if self.timer <= 0:
            self.timer = 0
            self.timeout()
            return
        direction, trigger = self.controls()
        self.player_x = max(10, min(WIDTH - 13, self.player_x + direction * PLAYER_SPEED * dt))
        if direction:
            self.walk_frame += dt * 10
        else:
            self.walk_frame = 0
        if trigger:
            self.fire()
        for beam in self.beams[:]:
            if beam.top > HUD_HEIGHT + 4:
                beam.top = max(HUD_HEIGHT + 4, beam.top - SHOT_SPEED * dt)
            else:
                beam.age_top += dt
            if beam.age_top >= SHOT_HOLD:
                self.beams.remove(beam)
        for enemy in self.enemies[:]:
            bounced = move_octopus(enemy, dt, level.platforms, level.bounce_factor)
            if bounced and enemy.size <= 0 and self.rng.random() < .18:
                self.audio.play("bounce")
        # Impactos: revisar cada látigo con cada enemigo en el mismo fotograma.
        for beam in self.beams[:]:
            for enemy in self.enemies[:]:
                if enemy.grace > 0:
                    continue
                if circle_hits_vertical_segment(enemy.x, enemy.y, enemy.radius * .85,
                                                beam.x, beam.top, beam.bottom):
                    if beam in self.beams:
                        self.beams.remove(beam)
                    self.hit_enemy(enemy)
                    break
        for pickup in self.pickups[:]:
            pickup.age += dt
            pickup.y = min(FLOOR_Y - 10, pickup.y + pickup.vy * dt)
            if (abs(pickup.x - self.player_x) <= 13 and pickup.y >= FLOOR_Y - PLAYER_HEIGHT - 8):
                self.collect_pickup(pickup)
            elif pickup.age > 14:
                self.pickups.remove(pickup)
        for enemy in self.enemies:
            if circle_hits_rectangle(enemy.x, enemy.y, enemy.radius * .75,
                                     self.player_x - 6, FLOOR_Y - PLAYER_HEIGHT + 2,
                                     self.player_x + 6, FLOOR_Y - 2):
                self.take_damage()
                if self.state != "PLAY":
                    return
                break
        if not self.enemies:
            # Termina el efecto AL SUPERAR la fase, no en el primer
            # fotograma de la siguiente. Tampoco quedan objetos ni rayos.
            self.clear_temporary_powerups()
            self.beams.clear()
            self.pickups.clear()
            self.score += max(0, int(self.timer)) * 15
            self.high_score = max(self.high_score, self.score)
            # Al cerrar cada mundo se regala una vida (hasta el maximo de 5).
            if self.level_idx in (4, 9, 14, 19) and self.lives < MAX_LIVES:
                self.lives += 1
                self.world_bonus_life = True
            self.audio.play("bonus")
            self.set_state("CLEAR")

    def update_particles(self, dt):
        for part in self.death_fragments[:]:
            part.x += part.vx * dt
            part.y += part.vy * dt
            part.vy += 380 * dt
            part.rotation += part.rotation_speed * dt
            part.life -= dt
            if part.life <= 0:
                self.death_fragments.remove(part)
        for particle in self.particles[:]:
            particle.life -= dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += dt * 128
            if particle.life <= 0:
                self.particles.remove(particle)
        for ft in self.float_texts[:]:
            ft.age += dt
            ft.y -= dt * 26
            if ft.age > 1.10:
                self.float_texts.remove(ft)

    def update(self, dt):
        self.t += dt
        self.state_age += dt
        self.shake = max(0.0, self.shake - dt)
        if self.state == "TITLE":
            for octo in self.demo:
                move_octopus(octo, dt)
        elif self.state == "READY":
            if self.state_age >= STAGE_READY_SECS:
                self.set_state("PLAY")
        elif self.state == "PLAY":
            self.update_play(dt)
        elif self.state == "CLEAR":
            if self.state_age >= STAGE_CLEAR_SECS:
                if self.level_idx >= len(LEVELS) - 1:
                    self.set_state("VICTORY")
                    if not self.audio.has_victory_music():
                        self.audio.play("victory")
                else:
                    self.level_idx += 1
                    self.start_level()
        elif self.state == 'DEATH':
            if self.state_age >= DEATH_ANIMATION_SECS:
                self.death_fragments.clear()
                if self.lives <= 0:
                    self.set_state('GAME_OVER')
                elif self.death_reason == 'timeout':
                    self.set_state('TIMEOUT')
                else:
                    self.player_x = self.safest_respawn_x()
                    self.invulnerable = HIT_INVULN_SECS
                    self.set_state('PLAY')
        elif self.state == "TIMEOUT":
            if self.state_age >= 2.15:
                self.start_level()
                self.invulnerable = HIT_INVULN_SECS
        if self.state != "PAUSE":
            self.update_particles(dt)

    def draw_hud(self):
        pg.draw.rect(self.canvas, (7, 11, 29), (0, 0, WIDTH, HUD_HEIGHT))
        self.art.text(self.canvas, f"PUNTOS {self.score:07d}", 9, 8,
                      size=13, center=False, color=COLORS["white"])
        self.art.text(self.canvas, "VIDAS", 183, 8, size=12, center=False,
                      color=COLORS["gold"])
        # Firma Tony C. Ware: smileys AMARILLOS llenos, ojos/sonrisa NEGROS.
        # Centrado perfecto dentro de la zona de vidas, también con 1 o 5.
        for i in range(self.lives):
            self.art.smiley(self.canvas, round(252 + (i - (self.lives - 1) / 2) * 14), 15, 6)
        self.art.text(self.canvas, f"FASE {self.level_idx+1:02d}/{len(LEVELS)}", 299, 8,
                      size=12, center=False, color=COLORS["cyan"])
        timer_col = COLORS["red"] if self.timer < 15 else COLORS["white"]
        self.art.text(self.canvas, f"{max(0, math.ceil(self.timer)):03d}", 450, 7,
                      size=15, center=False, color=timer_col)
        progress = max(0, min(1, self.timer / LEVELS[self.level_idx].time_limit))
        pg.draw.rect(self.canvas, (33, 40, 66), (0, HUD_HEIGHT - 3, WIDTH, 2))
        pg.draw.rect(self.canvas, COLORS["pink"] if progress < .2 else COLORS["cyan"],
                     (0, HUD_HEIGHT - 3, round(WIDTH * progress), 2))

    def draw_pickups(self):
        colors = {"SHIELD": COLORS["cyan"], "DOUBLE": COLORS["pink"],
                  "TIME": COLORS["gold"], "LIFE": COLORS["green"]}
        symbols = {"SHIELD": "S", "TIME": "+", "LIFE": "1"}
        for p in self.pickups:
            x, y = round(p.x), round(p.y)
            col = colors[p.kind]
            # Medallón oscuro para que el objeto se distinga sobre cualquier fondo HD.
            halo = 1 if (self.t * 4) % 2 < 1 else 0
            pg.draw.circle(self.canvas, (9, 12, 28), (x, y), 11)
            pg.draw.circle(self.canvas, col, (x, y), 9 + halo, 2)
            pg.draw.circle(self.canvas, (255, 255, 240), (x - 3, y - 4), 1)
            if p.kind == "DOUBLE":
                # Dos mini-látigos, reconocibles sin depender de la letra D.
                for dx, laser_color in ((-3, COLORS["cyan"]), (3, COLORS["gold"])):
                    pg.draw.line(self.canvas, laser_color, (x + dx, y - 5),
                                 (x + dx, y + 5), 2)
                    pg.draw.circle(self.canvas, (255, 252, 235), (x + dx, y - 5), 2)
            else:
                self.art.text(self.canvas, symbols[p.kind], x, y - 7, size=13,
                              color=col)

    def draw_action(self):
        level = LEVELS[self.level_idx]
        self.art.star_glints(self.canvas, level.theme, self.t)
        # La pista comienza en FLOOR_Y: Dom apoya sus pies en un plano de
        # juego visible, independiente de la fotografía del escenario.
        self.art.floor(self.canvas, level.theme, self.t)
        self.art.platforms(self.canvas, level.platforms, level.theme)
        for o in self.enemies:
            # Pulpos flotantes: SIN sombras proyectadas sobre el suelo.
            self.art.octopus(self.canvas, o, self.t)
        for b in self.beams:
            self.art.laser(self.canvas, b, self.t)
        self.draw_pickups()
        if self.state not in ('DEATH', 'GAME_OVER', 'TIMEOUT'):
            self.art.dom(self.canvas, self.player_x, int(self.walk_frame) % 4,
                         self.invulnerable, self.t, self.shield_timer)
        for part in self.death_fragments:
            sprite = pg.transform.rotate(part.image, part.rotation)
            rect = sprite.get_rect(center=(round(part.x), round(part.y)))
            self.canvas.blit(sprite, rect)
        if self.state == 'DEATH':
            # Doble onda expansiva con un núcleo blanco y texto muy exagerado.
            pulse = self.state_age
            for delay, col in ((0.0, COLORS['gold']), (.16, COLORS['cyan']), (.30, COLORS['pink'])):
                age = pulse - delay
                if 0 <= age < .62:
                    radius = round(8 + age * 99)
                    pg.draw.circle(self.canvas, col, (round(self.death_x), round(self.death_y)),
                                   radius, max(1, round(5 * (1 - age / .62))))
            if pulse < .20:
                pg.draw.circle(self.canvas, (255, 252, 245),
                               (round(self.death_x), round(self.death_y)),
                               max(1, round(19 * (1 - pulse / .2))))
            self.art.text(self.canvas, '¡BOOOOM!', max(92, min(WIDTH - 92, self.death_x)),
                          max(58, self.death_y - 78),
                          size=29, color=COLORS['gold'])
        for p in self.particles:
            pg.draw.circle(self.canvas, p.color, (round(p.x), round(p.y)),
                           max(1, round(p.radius * p.life / max(.01, p.total))))
        for ft in self.float_texts:
            self.art.text(self.canvas, ft.caption, ft.x, ft.y, size=12,
                          color=ft.color, alpha=max(20, int(255 * (1.0 - ft.age / 1.1))))
        self.draw_hud()
        if self.state in ("PLAY", "READY"):
            if self.shield_timer > 0:
                self.art.text(self.canvas, f"ESCUDO {math.ceil(self.shield_timer)}s", 72, 276,
                              size=10, color=COLORS["cyan"])
            if self.multishot_timer > 0:
                self.art.text(self.canvas, f"DOBLE LATIGO {math.ceil(self.multishot_timer)}s", 229, 276,
                              size=10, color=COLORS["pink"])
        if self.state == "READY":
            self.panel((8, 14, 36), (76, 94, 328, 105))
            self.art.text(self.canvas, f"FASE {self.level_idx + 1:02d} / {len(LEVELS)}", 240, 109,
                          size=17, color=COLORS["gold"])
            self.art.text(self.canvas, level.title, 240, 135, size=22, color=COLORS["white"])
            self.art.text(self.canvas, level.subtitle, 240, 167, size=11, color=COLORS["cyan"])
        elif self.state == "CLEAR":
            self.panel((8, 16, 38), (81, 97, 318, 103))
            self.art.text(self.canvas, "¡PORTAL LIMPIO!", 240, 116, size=29,
                          color=COLORS["green"])
            self.art.text(self.canvas, f"BONUS DE TIEMPO +{int(self.timer) * 15}",
                          240, 155, size=13, color=COLORS["gold"])
            if self.world_bonus_life:
                self.art.text(self.canvas, "+1 VIDA POR TERMINAR EL MUNDO",
                              240, 179, size=11, color=COLORS["green"])
        elif self.state == 'DEATH':
            pass  # se dibuja la explosión encima de la escena, sin menú de muerte
        elif self.state == "TIMEOUT":
            self.panel((20, 13, 34), (86, 98, 308, 99))
            self.art.text(self.canvas, "¡TIEMPO AGOTADO!", 240, 119, size=24,
                          color=COLORS["red"])
            self.art.text(self.canvas, "DOM VUELVE A INTENTARLO", 240, 158,
                          size=12, color=COLORS["white"])
        elif self.state == 'PAUSE':
            self.draw_pause_menu()
        elif self.state in ("GAME_OVER", "VICTORY"):
            self.draw_ending()

    def panel(self, color, rect):
        x, y, w, h = rect
        translucent = pg.Surface((w, h), pg.SRCALPHA)
        translucent.fill((*color, 231))
        self.canvas.blit(translucent, (x, y))
        pg.draw.rect(self.canvas, COLORS["cyan"], rect, 2)
        pg.draw.line(self.canvas, COLORS["pink"], (x + 9, y), (x + w - 9, y), 2)

    def draw_ending(self):
        self.panel((13, 11, 37), (58, 84, 364, 139))
        if self.state == "GAME_OVER":
            self.art.text(self.canvas, "GAME OVER", 240, 105, size=37,
                          color=COLORS["pink"])
            self.art.text(self.canvas, "LOS PULPOS GANAN ESTA VEZ", 240, 153,
                          size=13, color=COLORS["white"])
        else:
            self.art.text(self.canvas, "¡VICTORIA, DOM!", 240, 101,
                          size=31, color=COLORS["green"])
            self.art.text(self.canvas, "¡HAS SUPERADO LAS 25 FASES!", 240, 148,
                          size=12, color=COLORS["white"])
        self.art.text(self.canvas, f"PUNTUACION FINAL  {self.score:07d}", 240, 177,
                      size=12, color=COLORS["gold"])
        if self.state_age >= END_MIN_SECS:
            self.art.text(self.canvas, "ESPACIO PARA VOLVER AL TITULO", 240, 203,
                          size=11, color=COLORS["cyan"])
        else:
            remaining = max(1, math.ceil(END_MIN_SECS - self.state_age))
            self.art.text(self.canvas, f"UN MOMENTO... {remaining}", 240, 203,
                          size=11, color=COLORS["cyan"])

    def draw_title(self):
        # El escaparate del título vuelve al color clásico tras cada partida.
        self.art.set_level_palette(0)
        self.art.star_glints(self.canvas, "circus", self.t)
        self.art.floor(self.canvas, "circus", self.t)
        for o in self.demo:
            self.art.octopus(self.canvas, o, self.t)
        self.art.dom(self.canvas, 126, int(self.t * 4) % 4, 0, self.t, 0)
        pg.draw.rect(self.canvas, (12, 13, 35), (60, 37, 362, 107))
        pg.draw.rect(self.canvas, COLORS["pink"], (60, 37, 362, 107), 2)
        self.art.text(self.canvas, "CIRCO", 240, 40, size=48, color=COLORS["gold"])
        self.art.text(self.canvas, "DIMENSIONAL 2", 240, 91, size=34,
                      color=COLORS["cyan"])
        self.art.text(self.canvas, "DOM Y LOS PULPOS REBOTADORES", 240, 152,
                      size=13, color=COLORS['white'])
        self.draw_menu_entries(self.menu_items(), self.title_selected,
                               top=177, spacing=23, font_size=17)
        self.art.text(self.canvas, "2026 TONY C. WARE  ·  O/P / MANDO  ·  V" + VERSION,
                      240, 281, size=10, color=COLORS['gold'])

    def draw_menu_entries(self, entries, selected, top, spacing, font_size=15):
        for index, title in enumerate(entries):
            y = top + index * spacing
            if index == selected:
                pg.draw.rect(self.canvas, (54, 32, 84),
                             (105, y - 3, 270, spacing - 1), border_radius=4)
                pg.draw.rect(self.canvas, COLORS['pink'],
                             (105, y - 3, 270, spacing - 1), 1, border_radius=4)
                selector_frame = int(self.t * 7) % 4
                self.art.dom_menu_selector(self.canvas, 114, y - 1, selector_frame)
            self.art.text(self.canvas, title,
                          240, y, size=font_size,
                          color=COLORS['gold'] if index == selected else COLORS['white'])

    def draw_pause_menu(self):
        self.panel((11, 15, 34), (85, 51, 310, 214))
        self.art.text(self.canvas, 'PAUSA', 240, 66, size=31, color=COLORS['gold'])
        self.draw_menu_entries(self.menu_items(), self.pause_selected,
                               top=118, spacing=30, font_size=15)
        self.art.text(self.canvas, 'ESC / START: CONTINUAR', 240, 245,
                      size=10, color=COLORS['cyan'])

    def draw_options(self):
        self.art.star_glints(self.canvas, self.background_theme(), self.t)
        self.panel((10, 13, 32), (48, 22, 384, 261))
        self.art.text(self.canvas, 'OPCIONES', 240, 37, size=32, color=COLORS['gold'])
        options = [
            ('MUSICA', 'SI' if self.audio.music_enabled else 'NO'),
            ('EFECTOS', 'SI' if self.audio.effects_enabled else 'NO'),
            ('VOLUMEN MUSICA', f'{round(self.audio.music_volume * 100)}%'),
            ('VOLUMEN EFECTOS', f'{round(self.audio.effects_volume * 100)}%'),
            ('VOLVER', ''),
        ]
        for idx, (caption, val) in enumerate(options):
            y = 89 + idx * 34
            if idx == self.options_selected:
                pg.draw.rect(self.canvas, (58, 30, 86), (68, y - 6, 344, 31), border_radius=4)
                pg.draw.rect(self.canvas, COLORS['pink'], (68, y - 6, 344, 31), 1, border_radius=4)
                self.art.pulpo_menu_selector(self.canvas, 85, y + 9, self.t)
            col = COLORS['gold'] if idx == self.options_selected else COLORS['white']
            self.art.text(self.canvas, caption, 109, y, size=14, center=False, color=col)
            if idx in (2, 3):
                value = self.audio.music_volume if idx == 2 else self.audio.effects_volume
                pg.draw.rect(self.canvas, (29, 42, 68), (283, y + 2, 76, 10))
                pg.draw.rect(self.canvas, COLORS['cyan'], (283, y + 2, round(76 * value), 10))
                self.art.text(self.canvas, val, 393, y, size=13, color=col)
            else:
                self.art.text(self.canvas, val, 376, y, size=14, color=col)
        name = self.gamepad_name()
        if len(name) > 28:
            name = name[:27] + '…'
        self.art.text(self.canvas, 'MANDO: ' + name, 240, 264, size=10, color=COLORS['cyan'])
        self.art.text(self.canvas, 'FLECHAS / CRUCETA: ELEGIR Y AJUSTAR', 240, 288,
                      size=10, color=COLORS['white'])

    def draw_help(self):
        self.art.star_glints(self.canvas, 'inverted', self.t)
        self.panel((11, 16, 36), (34, 23, 412, 261))
        self.art.text(self.canvas, 'CONTROLES', 240, 40, size=30, color=COLORS['gold'])
        items = [
            ('MOVER', 'O / P, A / D, flechas, stick / cruceta'),
            ('LATIGO LASER', 'ESPACIO o boton principal del mando'),
            ('ACEPTAR', 'INTRO / ESPACIO / boton principal'),
            ('MENU', 'Flechas, cruceta o stick izquierdo'),
            ('PAUSA', 'ESC / START del mando'),
            ('VOLVER', 'ESC / boton secundario'),
            ('MUSICA', 'N activa/desactiva, +/- volumen'),
            ('TODO EL AUDIO', 'M para silenciar temporalmente'),
            ('PANTALLA', 'F11 alterna pantalla completa'),
        ]
        for idx, (a, b) in enumerate(items):
            y = 86 + idx * 19
            self.art.text(self.canvas, a, 53, y, size=11, center=False, color=COLORS['cyan'])
            self.art.text(self.canvas, b, 198, y, size=10, center=False, color=COLORS['white'])
        self.art.text(self.canvas, 'MANDO: ' + self.gamepad_name()[:38], 240, 262,
                      size=10, color=COLORS['pink'])
        self.art.text(self.canvas, 'ESC / B / ESPACIO: VOLVER AL TITULO', 240, 285,
                      size=10, color=COLORS['gold'])

    def background_theme(self):
        """Un único fondo HD oficial por mundo, incluso en pausa y menús."""
        if self.state == 'TITLE':
            return 'circus'
        if self.state == 'HELP':
            return 'inverted'
        if self.state == 'OPTIONS' and self.options_origin != 'PAUSE':
            return 'circus'
        return LEVELS[self.level_idx].theme

    def render(self):
        # Los gráficos arcade se dibujan SOLO sobre una capa transparente.
        # Así los fondos HD nunca sufren pixelación al ampliar de 480x300.
        self.canvas.fill((0, 0, 0, 0))
        if self.state == "TITLE":
            self.draw_title()
        elif self.state == 'HELP':
            self.draw_help()
        elif self.state == 'OPTIONS':
            self.draw_options()
        else:
            self.draw_action()
        self.art.vignette(self.canvas)
        display_w, display_h = self.window.get_size()
        scale = min(display_w / WIDTH, display_h / HEIGHT)
        out_w, out_h = max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale))
        self.window.fill((2, 3, 12))
        offset_x = (display_w - out_w) // 2
        offset_y = (display_h - out_h) // 2
        if self.shake > 0:
            dx = round(self.rng.randint(-2, 2) * min(3, scale))
            dy = round(self.rng.randint(-2, 2) * min(3, scale))
            offset_x += dx
            offset_y += dy
        self.window.blit(self.hd_backdrops.frame(self.background_theme(), out_w, out_h),
                         (offset_x, offset_y))
        # Nearest-neighbor conserva el pixel-art de Dom, pulpos, smileys y HUD.
        overlay = pg.transform.scale(self.canvas, (out_w, out_h))
        self.window.blit(overlay, (offset_x, offset_y))
        pg.display.flip()

    def run(self):
        while self.alive:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 30)
            self.handle_events()
            if not self.alive:
                break
            self.update(dt)
            self.render()
        pg.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
