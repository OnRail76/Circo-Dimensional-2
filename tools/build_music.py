"""Banda sonora ORIGINAL de CIRCO DIMENSIONAL 2.

Herramienta de produccion opcional: requiere numpy, soundfile, ffmpeg.
Las ocho pistas OGG ya vienen incluidas con el juego: no hay que ejecutar esto.
Musica original de feria espacial, sintetizadores FM, percusion arcade.
No utiliza ni reproduce melodias de obras existentes.
"""
from __future__ import annotations
from pathlib import Path
import subprocess
import tempfile
import math
import numpy as np
import soundfile as sf

SR = 32000
RNG = np.random.default_rng(20261118)
HERE = Path(__file__).resolve().parents[1]
OUT = HERE / 'assets' / 'music'
OUT.mkdir(parents=True, exist_ok=True)

# Nombre, BPM, tonic MIDI, modo, compases y semilla de la melodía (grados de escala).
# Cada pieza desarrolla una frase distinta, variaciones armónicas y cambios de registro.
TRACKS = [
    ('titulo', 132, 62, 'major', 8, (0,4,5,7, 4,2,1,4, 7,9,7,5, 4,2,1,0)),
    ('mundo_01', 126, 60, 'major', 16, (0,2,4,5, 7,5,4,2, 4,7,9,7, 5,4,2,0)),
    ('mundo_02', 138, 67, 'major', 16, (4,2,0,4, 7,9,7,4, 5,4,2,0, 2,4,5,7)),
    ('mundo_03', 144, 62, 'major', 16, (7,9,12,9, 7,5,4,2, 0,4,7,9, 12,9,7,5)),
    ('mundo_04', 150, 57, 'minor', 16, (0,3,7,10, 7,5,3,0, 12,10,7,5, 3,5,7,3)),
    ('mundo_05', 158, 64, 'minor', 16, (7,5,3,0, 3,7,10,12, 15,12,10,7, 5,3,0,3)),
    ('pulpo_primordial', 164, 60, 'minor', 16, (0,0,3,7, 6,7,10,12, 15,12,10,7, 6,3,0,7)),
    ('victoria', 128, 65, 'major', 4, (0,4,7,12, 11,12,14,12, 7,9,11,12, 12,12,12,12)),
]

MAJOR = (0,2,4,5,7,9,11,12,14,16,17,19,21,23,24)
MINOR = (0,2,3,5,7,8,10,12,14,15,17,19,20,22,24)
PROG_MAJOR = (0, 5, 3, 4, 0, 3, 5, 4)
PROG_MINOR = (0, 5, 6, 4, 0, 6, 3, 4)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def instrument(kind, midi, seconds):
    n = max(48, int(SR * seconds))
    t = np.arange(n, dtype=np.float32) / SR
    f = hz(midi)
    phase = (2 * np.pi * f * t).astype(np.float32)
    if kind == 'lead':
        vibrato = .008 * np.sin(2*np.pi*5.2*t)
        p = phase + .008 * f * np.sin(2*np.pi*5.2*t)
        wave = .60 * np.sin(p + .12*np.sin(2*p)) + .29*np.sin(2*p) + .11*np.sin(3*p)
        attack, release = .009, .125
    elif kind == 'bell':
        wave = .58*np.sin(phase + 2.8*np.sin(2.01*phase)) + .22*np.sin(3.01*phase)
        wave *= np.exp(-5*t / max(.08, seconds))
        attack, release = .005, .09
    elif kind == 'bass':
        wave = .78*np.sin(phase + 1.8*np.exp(-8*t)*np.sin(2*phase)) + .20*np.sin(2*phase)
        attack, release = .004, .07
    elif kind == 'organ':
        wave = .64*np.sin(phase) + .20*np.sin(2*phase) + .10*np.sin(3*phase) + .06*np.sin(4*phase)
        attack, release = .010, .065
    elif kind == 'arp':
        wave = .56*np.sin(phase) + .30*np.sin(2*phase) + .13*np.sin(3*phase)
        wave *= np.exp(-3*t/max(.1,seconds))
        attack, release = .003, .065
    else:
        raise ValueError(kind)
    env = np.minimum(1.0, t / attack)
    env *= np.minimum(1.0, (seconds - t) / release).clip(0,1)
    return (wave * env).astype(np.float32)


def add(samples, pos, note, kind, gain, pan=0.0):
    at = int(pos * SR)
    if at >= len(samples):
        return
    n = min(len(note), len(samples)-at)
    if n <= 0:
        return
    left = np.sqrt((1-pan)*.5)*gain
    right = np.sqrt((1+pan)*.5)*gain
    samples[at:at+n,0] += note[:n]*left
    samples[at:at+n,1] += note[:n]*right


def drum(kind):
    if kind == 'kick':
        t = np.arange(int(SR*.24)) / SR
        f = 53 + 115*np.exp(-38*t)
        a = np.cumsum(f) * 2*np.pi / SR
        return (np.sin(a)*np.exp(-17*t)).astype(np.float32)
    if kind == 'snare':
        t = np.arange(int(SR*.17)) / SR
        n = RNG.normal(size=len(t))
        low = np.sin(2*np.pi*165*t)
        return ((.7*n+.3*low)*np.exp(-23*t)).astype(np.float32)
    if kind == 'hat':
        t = np.arange(int(SR*.075)) / SR
        n = RNG.normal(size=len(t))
        high = n - np.convolve(n, np.ones(11)/11, mode='same')
        return (high*np.exp(-54*t)).astype(np.float32)
    if kind == 'tom':
        t = np.arange(int(SR*.18)) / SR
        return (np.sin(2*np.pi*(205*t-110*t*t))*np.exp(-19*t)).astype(np.float32)


def render_track(spec):
    name, bpm, tonic, mode, bars, motif = spec
    beat = 60 / bpm
    seconds = bars * 4 * beat
    total = int(round(SR*seconds))
    data = np.zeros((total,2), np.float32)
    notes = MAJOR if mode == 'major' else MINOR
    progression = PROG_MAJOR if mode == 'major' else PROG_MINOR
    kick, snare, hat, tom = (drum(x) for x in ('kick','snare','hat','tom'))
    is_boss = name=='pulpo_primordial'
    is_victory = name=='victoria'
    is_title = name=='titulo'
    for bar in range(bars):
        chord_degree = progression[bar % len(progression)]
        chord_root = tonic + notes[chord_degree]
        bar_start = bar*4*beat
        turnaround = (bar%4)==3
        # Bajo walking con contratiempos funk que dan sensacion de feria.
        for b, degree, duration, volume in [(0,0,.73,.43),(1.5,0,.42,.23),(2,7,.63,.35),(3.5,0,.38,.27)]:
            note = chord_root - 24 + degree
            add(data,bar_start+b*beat,instrument('bass',note,duration*beat),'bass',volume,-.04)
        # Acordes cortos de organo casi honky-tonk en contratiempos.
        chord_intervals = (0, 3 if mode=='minor' else 4, 7)
        for pulse in (0.5,1.5,2.5,3.5):
            if is_boss and pulse==.5 and bar%2: continue
            for idx, inte in enumerate(chord_intervals):
                add(data,bar_start+pulse*beat,instrument('organ',chord_root-12+inte,.30*beat),
                    'organ',.12,(-.38,0,.38)[idx])
        # Percusion sintetica original: bombo, caja y charles.
        for step in range(8):
            pos = bar_start+step*.5*beat
            if step%2==0:
                add(data,pos,hat,'hat',.065 if step%4 else .045,.50)
            else:
                add(data,pos,hat,'hat',.026,.50)
        for b in (0,2):
            add(data,bar_start+b*beat,kick,'kick',.36,-.12)
        for b in (1,3):
            add(data,bar_start+b*beat,snare,'snare',.17,.04)
        if bar%4==3:
            for k in range(4):
                add(data,bar_start+(3+k*.25)*beat,tom,'tom',.12+.02*k,.12)
        # Melodía principal: 8 notas por compás. Frases de respuesta con variación.
        for step in range(8):
            idx = (bar%2)*8+step
            degree = motif[idx]
            # Cada 4 compases, un pequeño remate que usa cromatismos propios.
            variation = (12 if bar%8 in (4,5) and step in (0,4) else 0)
            if step==7 and turnaround:
                degree = 11 if mode=='major' else 10
            if not is_victory and step in (3,7) and bar%4==1:
                continue
            pitch = tonic+degree+12+variation
            length = .42 if step not in (0,4) else .72
            gain = .23 if not is_boss else .30
            add(data,bar_start+step*.5*beat,instrument('lead',pitch,length*beat),
                'lead',gain,-.08)
        # Respuestas de xilófono FM: ritmo sincopado, especialmente niveles altos.
        for ix, pulse in enumerate((.75,1.75,2.75,3.75)):
            if is_title and ix%2: continue
            degree = (0, 4 if mode=='major' else 3, 7, 12)[(bar+ix)%4]
            add(data,bar_start+pulse*beat,instrument('bell',chord_root+12+degree,.32*beat),
                'bell',.10 if name.startswith('mundo_0') else .14,.58)
        # Arpegio brillante oculto tras la melodia, diferencial por mundo.
        if not is_victory:
            for pulse, offset in ((.25,0),(1.25,7),(2.25,12),(3.25,7)):
                add(data,bar_start+pulse*beat,instrument('arp',chord_root+offset,.25*beat),
                    'arp',.075 if is_title else .09,.65)
    # Eco muy corto con feedback circular para que el loop quede continuo.
    delayed = np.roll(data, int(SR*.113), axis=0)*.093
    delayed2 = np.roll(data, int(SR*.223), axis=0)*.055
    data = data+delayed+delayed2
    peak = float(np.max(np.abs(data)))
    if peak>.85: data *= .85/peak
    data = np.tanh(data*1.16)/1.16
    # Una cruzada casi imperceptible en el punto de loop elimina clics.
    n = int(.012*SR)
    fade = np.linspace(0,1,n,dtype=np.float32)[:,None]
    data[:n] *= fade
    data[-n:] *= (1-fade)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp)/'source.wav'
        sf.write(wav,data,samplerate=SR,subtype='PCM_16')
        out = OUT / (name+'.ogg')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(wav),
                        '-codec:a','libvorbis','-qscale:a','4',str(out)],check=True)
    return name, seconds, out.stat().st_size


if __name__=='__main__':
    for spec in TRACKS:
        name,duration,size = render_track(spec)
        print(f'{name}: {duration:.1f}s, {size//1024} KiB')
