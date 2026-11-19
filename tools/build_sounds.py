"""Construye los efectos originales del juego sin dependencias externas."""
from __future__ import annotations
import math, random, struct, wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(260226)


def save(name: str, values: list[float]) -> None:
    with wave.open(str(OUT / (name + ".wav")), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(v * 21500)))) for v in values))


def effect(name, duration, func):
    n = int(RATE * duration)
    save(name, [func(i / RATE, i / n) for i in range(n)])


# Látigo: chispa inicial + barrido de frecuencia + ruido seco.
effect("laser", .23, lambda t, p: (math.sin(2 * math.pi * (1250 * t - 2900 * t*t)) * .65 + rng.uniform(-.55, .55)) * (1-p)**2.9)
effect("pop", .18, lambda t, p: (rng.uniform(-1, 1) * .9 + math.sin(2 * math.pi * (190*t + 450*t*t)) * .25) * (1-p)**2.5)
effect("split", .29, lambda t, p: (rng.uniform(-.65, .65) + math.sin(2 * math.pi * (190*t - 70*t*t)) * .62) * (1-p)**1.8)
effect("damage", .51, lambda t, p: (math.sin(2 * math.pi * (210*t - 145*t*t)) + rng.uniform(-.55, .55)) * (1-p)**1.6)
effect("bounce", .075, lambda t, p: math.sin(2 * math.pi * (170*t + 230*t*t)) * (1-p)**3)
effect("ui", .13, lambda t, p: math.sin(2 * math.pi * 670*t) * (1-p)**1.2)
NOTES = (660, 830, 990, 1320, 990, 1320, 1660)
effect("bonus", .48, lambda t, p: math.sin(2*math.pi*NOTES[min(len(NOTES)-1, int(p*len(NOTES)))]*t) * (1-p)**1.3 * .78)
MELODY = (523, 659, 784, 1046, 784, 1046, 1318, 1568)
effect("victory", 2.30, lambda t, p: (math.sin(2*math.pi*MELODY[min(7, int(p*8))]*t) * .55 + math.sin(2*math.pi*MELODY[min(7, int(p*8))]*2*t)*.19) * min(1, t*9) * (1-p)**.6)
print(f"Generados {len(list(OUT.glob('*.wav')))} sonidos en {OUT}")
