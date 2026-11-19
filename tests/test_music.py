"""La banda sonora no requiere abrir pantalla ni cargar Pygame en las pruebas."""
import unittest
from pathlib import Path
from circo.audio import SoundBank

ROOT = Path(__file__).resolve().parents[1]

class FakeSound:
    def set_volume(self, level):
        pass
    def play(self):
        pass

class FakeMusic:
    def __init__(self):
        self.events = []
        self.volume = None
    def load(self, path):
        self.events.append(('load', Path(path).name))
    def play(self, **opts):
        self.events.append(('play', opts))
    def set_volume(self, level):
        self.volume = level
    def pause(self):
        self.events.append('pause')
    def unpause(self):
        self.events.append('unpause')
    def fadeout(self, ms):
        self.events.append(('fadeout', ms))

class FakeMixer:
    def __init__(self):
        self.music = FakeMusic()
    def get_init(self):
        return True
    def Sound(self, path):
        return FakeSound()
    def stop(self):
        pass

class FakePygame:
    error = RuntimeError
    def __init__(self):
        self.mixer = FakeMixer()

class MusicTests(unittest.TestCase):
    def setUp(self):
        self.pg = FakePygame()
        self.audio = SoundBank(self.pg, ROOT)

    def test_all_eight_ogg_files_exist(self):
        for name in self.audio.TRACKS:
            with self.subTest(track=name):
                path = self.audio.music_paths[name]
                self.assertGreater(path.stat().st_size, 25000)
                self.assertEqual(path.read_bytes()[:4], b'OggS')

    def test_one_song_per_world_and_special_tracks(self):
        self.assertEqual(self.audio.track_for('TITLE', 0), 'titulo')
        self.assertEqual(self.audio.track_for('HELP', 3), 'titulo')
        for idx in range(24):
            self.assertEqual(self.audio.track_for('PLAY', idx), f'mundo_{idx // 5 + 1:02d}')
        self.assertEqual(self.audio.track_for('READY', 24), 'pulpo_primordial')
        self.assertEqual(self.audio.track_for('VICTORY', 24), 'victoria')
        self.assertIsNone(self.audio.track_for('GAME_OVER', 7))

    def test_music_does_not_restart_when_entering_another_phase_of_same_world(self):
        self.audio.sync_music('TITLE', 0)
        self.audio.sync_music('READY', 0)
        self.audio.sync_music('PLAY', 0)
        self.audio.sync_music('CLEAR', 0)
        self.audio.sync_music('READY', 1)
        loads = [ev for ev in self.pg.mixer.music.events if isinstance(ev, tuple) and ev[0]=='load']
        self.assertEqual([x[1] for x in loads], ['titulo.ogg','mundo_01.ogg'])

    def test_pause_and_resume_without_rewinding(self):
        self.audio.sync_music('PLAY', 4)
        self.audio.sync_music('PAUSE', 4)
        self.audio.sync_music('PLAY', 4)
        events = self.pg.mixer.music.events
        self.assertIn('pause', events)
        self.assertIn('unpause', events)
        self.assertEqual(len([x for x in events if isinstance(x, tuple) and x[0]=='load']), 1)

    def test_mute_music_only_and_volume(self):
        self.audio.sync_music('PLAY', 6)
        self.audio.toggle_music()
        self.assertEqual(self.pg.mixer.music.volume, 0.0)
        self.audio.toggle_music()
        self.assertEqual(self.pg.mixer.music.volume, .24)
        self.audio.adjust_music_volume(.05)
        self.assertEqual(self.pg.mixer.music.volume, .29)
        self.audio.toggle()
        self.assertEqual(self.pg.mixer.music.volume, 0.0)
        self.audio.toggle()
        self.assertEqual(self.pg.mixer.music.volume, .29)

    def test_victory_fanfare_plays_once(self):
        self.audio.sync_music('VICTORY', 24)
        plays = [x for x in self.pg.mixer.music.events if isinstance(x, tuple) and x[0]=='play']
        self.assertEqual(len(plays), 1)
        self.assertEqual(plays[0][1]['loops'], 0)

if __name__ == '__main__':
    unittest.main()
