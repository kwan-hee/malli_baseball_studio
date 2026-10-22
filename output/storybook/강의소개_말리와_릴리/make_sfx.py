# 강의 소개 영상 — 효과음 합성 (2026-10-22 결정: 무료·저작권 무관 합성음, 어색하면 검수 때 보고)
# 콘티 소리 칸: 🔔 신호음 / 책장 넘기는 / 상자 여는 / "퐁" / 살랑 / 책 닫는 효과음
import wave
from pathlib import Path

import numpy as np

BASE = Path(__file__).parent
OUT = BASE / "sfx"
OUT.mkdir(exist_ok=True)
SR = 44100
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(x, attack=0.005, decay=None):
    n = len(x)
    e = np.ones(n)
    a = max(1, int(SR * attack))
    e[:a] = np.linspace(0, 1, a)
    if decay:
        e *= np.exp(-np.arange(n) / SR / decay)
    return x * e


def noise(d, lo, hi):
    """대역 제한 노이즈 (FFT 마스크)."""
    n = int(SR * d)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n)
    return x / (np.abs(x).max() + 1e-9)


def save(name, x, gain=0.6):
    x = x / (np.abs(x).max() + 1e-9) * gain
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"{name}: {len(x)/SR:.2f}s")


# 🔔 신호음: 맑은 종 두 음 (E6 → A6)
tt = t(1.2)
bell = sum(env(np.sin(2 * np.pi * f * tt) * a, decay=dc) for f, a, dc in [(1318.5, 1, .45), (2637, .3, .2), (3950, .12, .12)])
tt2 = t(1.2)
bell2 = sum(env(np.sin(2 * np.pi * f * tt2) * a, decay=dc) for f, a, dc in [(1760, 1, .5), (3520, .3, .2)])
x = np.zeros(int(SR * 1.4))
x[:len(bell)] += bell
x[int(SR * .12):int(SR * .12) + len(bell2)] += bell2
save("bell", x, 0.45)

# 책장 넘기기: 종이 스치는 대역 노이즈 스윕
d = 0.55
n = noise(d, 1500, 9000)
shape = np.sin(np.pi * np.clip(t(d) / d, 0, 1)) ** 1.5
save("page", n * shape * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t(d))), 0.35)

# 상자 여는 소리: 짧은 '퐁' + 위로 올라가는 반짝 세 음
pop = env(np.sin(2 * np.pi * (500 + 900 * t(.12)) * t(.12)), decay=.05)
x = np.zeros(int(SR * .7))
x[:len(pop)] += pop
for i, f in enumerate([1568, 2093, 2637]):
    s = env(np.sin(2 * np.pi * f * t(.35)), decay=.12) * .5
    o = int(SR * (.1 + .07 * i))
    x[o:o + len(s)] += s
save("box", x, 0.45)

# 퐁: 짧은 상승 사인
save("pop", env(np.sin(2 * np.pi * (700 + 2500 * t(.14)) * t(.14)), decay=.05), 0.4)

# 살랑: 부드러운 바람 스윕 두 번
d = 0.7
n = noise(d, 300, 3000)
shape = np.abs(np.sin(2 * np.pi * 1.5 * t(d))) * np.hanning(len(n))
save("swish", n * shape, 0.3)

# 책 닫기: 낮은 '툭' + 짧은 종이 소리
thud = env(np.sin(2 * np.pi * 85 * t(.35)), decay=.08) + env(noise(.35, 100, 1200), decay=.04) * .6
x = np.zeros(int(SR * .5))
x[int(SR * .05):int(SR * .05) + len(thud)] += thud
x[:int(SR * .15)] += noise(.15, 2000, 8000) * np.hanning(int(SR * .15)) * .25
save("close", x, 0.6)
