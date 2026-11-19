"""Sonidos WAV y banda sonora OGG originales. Silencioso si falla el audio."""
from __future__ import annotations
from pathlib import Path


class SoundBank:
    """Canal de efectos y canal de música independientes (SDL_mixer)."""

    TRACKS = (
        "titulo", "mundo_01", "mundo_02", "mundo_03", "mundo_04", "mundo_05",
        "pulpo_primordial", "victoria",
    )

    def __init__(self, pygame_module, root: Path):
        self.pg = pygame_module
        self.enabled = False
        self.muted = False
        self.music_enabled = True
        self.effects_enabled = True
        self.music_volume = 0.24
        self.effects_volume = 0.75
        self.music_paused = False
        self.current_music: str | None = None
        self.sounds = {}
        self.music_paths = {name: root / 'assets' / 'music' / f'{name}.ogg'
                            for name in self.TRACKS}
        try:
            if not self.pg.mixer.get_init():
                self.pg.mixer.init(frequency=32000, size=-16, channels=2, buffer=512)
            self.enabled = True
            for filename in ("laser", "pop", "split", "damage", "dom_boom", "bonus", "ui", "victory", "bounce"):
                path = root / "assets" / "sfx" / f"{filename}.wav"
                if path.exists():
                    self.sounds[filename] = self.pg.mixer.Sound(str(path))
            self.set_volumes()
            self._apply_music_volume()
        except (self.pg.error, OSError):
            self.enabled = False

    def set_volumes(self):
        for name, snd in self.sounds.items():
            base = (.19 if name == "bounce" else
                    .34 if name in ("pop", "laser") else .60 if name == "dom_boom" else .49)
            snd.set_volume(min(1.0, base * self.effects_volume / .75))

    def play(self, name: str):
        if self.enabled and self.effects_enabled and not self.muted and name in self.sounds:
            self.sounds[name].play()

    def toggle_effects(self):
        self.effects_enabled = not self.effects_enabled
        if not self.effects_enabled and self.enabled:
            self.pg.mixer.stop()

    def adjust_effects_volume(self, delta: float):
        self.effects_volume = round(max(0.0, min(1.0, self.effects_volume + delta)), 2)
        self.set_volumes()

    def _apply_music_volume(self):
        if not self.enabled:
            return
        try:
            self.pg.mixer.music.set_volume(self.music_volume if self.music_enabled and not self.muted else 0.0)
        except (self.pg.error, OSError):
            pass

    def toggle(self):
        """M: interruptor maestro, conserva el estado previo de música/efectos."""
        if not self.enabled:
            return
        self.muted = not self.muted
        if self.muted:
            try:
                self.pg.mixer.stop()
            except self.pg.error:
                pass
        self._apply_music_volume()

    def toggle_music(self):
        """N: solo música; los efectos siguen sonando."""
        self.music_enabled = not self.music_enabled
        self._apply_music_volume()

    def adjust_music_volume(self, delta: float):
        self.music_volume = round(max(0.0, min(1.0, self.music_volume + delta)), 2)
        self._apply_music_volume()

    @staticmethod
    def track_for(state: str, level_idx: int) -> str | None:
        if state in ('TITLE', 'HELP'):
            return 'titulo'
        if state in ('GAME_OVER',):
            return None
        if state == 'VICTORY':
            return 'victoria'
        if state in ('READY', 'PLAY', 'CLEAR', 'TIMEOUT', 'DEATH'):
            return 'pulpo_primordial' if level_idx == 24 else f'mundo_{level_idx // 5 + 1:02d}'
        return None

    def sync_music(self, state: str, level_idx: int):
        """Cambia pista solo cuando cambia el mundo. PAUSE conserva posición."""
        if not self.enabled:
            return
        try:
            if state == 'PAUSE':
                if not self.music_paused:
                    self.pg.mixer.music.pause()
                    self.music_paused = True
                return
            if self.music_paused:
                self.pg.mixer.music.unpause()
                self.music_paused = False
            target = self.track_for(state, level_idx)
            if target == self.current_music:
                return
            if target is None:
                self.pg.mixer.music.fadeout(300)
                self.current_music = None
                return
            path = self.music_paths[target]
            if not path.is_file():
                self.current_music = None
                return
            self.pg.mixer.music.load(str(path))
            self._apply_music_volume()
            self.pg.mixer.music.play(loops=0 if target == 'victoria' else -1,
                                     fade_ms=350)
            self.current_music = target
        except (self.pg.error, OSError):
            # Pygame continúa sin música incluso si SDL_mixer rechaza OGG.
            self.current_music = None

    def has_victory_music(self) -> bool:
        return self.enabled and self.current_music == 'victoria'
