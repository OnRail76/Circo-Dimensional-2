from pathlib import Path
import wave, math, random, struct
ROOT=Path(__file__).resolve().parents[1] / 'assets' / 'sfx'
SR=32000
N=int(SR*1.13)
rng=random.Random(20261118)
buffer=[]
noise_lp=0.0
for n in range(N):
    t=n/SR
    # 1.13s de explosión cómica, golpe + fizz digital + glissando de circo.
    envelope=(min(1.0, t*100) * math.exp(-t*3.15))
    raw=rng.uniform(-1,1)
    noise_lp=.77*noise_lp+.23*raw
    rumble=math.sin(math.tau*(92*t-34*t*t))*math.exp(-t*2.7)
    bloop=math.sin(math.tau*(390*t-180*t*t))*math.exp(-t*6)
    shimmer=(math.sin(math.tau*1390*t) + .4*math.sin(math.tau*1730*t))*math.exp(-t*8)
    circus=0
    for start,freq in ((.30,680),(.39,845),(.47,1020),(.56,1280)):
        q=t-start
        if q>=0:
            circus+=.11*math.sin(math.tau*freq*q)*math.exp(-q*23)
    s=(.73*noise_lp+.46*rumble+.20*bloop+.10*shimmer)*envelope+circus
    s=max(-1.,min(1.,s*.8))
    buffer.append(struct.pack('<h',round(s*32767)))
path=ROOT/'dom_boom.wav'
with wave.open(str(path),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(b''.join(buffer))
print(path,path.stat().st_size)
