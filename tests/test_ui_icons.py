"""Revisión del selector con pulpo auténtico y del icono de aplicación."""
import struct
import unittest
from pathlib import Path
from circo.art import Art

ROOT=Path(__file__).resolve().parents[1]

class FakeSprite:
    def __init__(self,w,h):
        self.w,self.h=w,h
    def get_width(self): return self.w
    def get_height(self): return self.h

class FakeCanvas:
    def __init__(self): self.drawn=[]
    def blit(self,sprite,at): self.drawn.append((sprite,at))

class UIIconTests(unittest.TestCase):
    def test_menu_cursor_uses_genuine_smiling_octopus_frames(self):
        art=Art.__new__(Art)
        frames={}
        for n in range(4):
            frames[('smile',3,n)]=FakeSprite(25+n%3,24+n%3)
        art.sprite_images=frames
        can=FakeCanvas()
        for t in [0.00,0.12,0.23,0.35]:
            art.pulpo_menu_selector(can,85,100,t)
        self.assertEqual(len(can.drawn),4)
        for drawn,_pos in can.drawn:
            self.assertIn(drawn,frames.values())
        self.assertTrue(any(y<88 for _spr,(_x,y) in can.drawn))

    def test_real_octopus_icon_png_and_ico_are_present(self):
        folder=ROOT/'assets'/'icons'
        for size in (32,48,64,128,256,512):
            with self.subTest(size=size):
                png=(folder/f'pulpo_normal_{size}.png').read_bytes()
                self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
                self.assertEqual(struct.unpack('>II',png[16:24]),(size,size))
        ico=(folder/'pulpo_normal.ico').read_bytes()
        self.assertEqual(ico[:4],b'\x00\x00\x01\x00')
        self.assertGreater(struct.unpack('<H',ico[4:6])[0],3)

if __name__=='__main__': unittest.main()
