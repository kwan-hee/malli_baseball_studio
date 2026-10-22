# 강의 소개 영상 — 최종 조립: render.py 무음 영상 + 나레이션(장면 wav 를 타임라인 위치에) + 효과음 + BGM + 자막
# 소리 칸 처리 (2026-10-22 결정): 원문 값(🎵 페이드·꺼짐, 효과음)은 그대로, [원문 공란]은 직전 상태 유지(BGM 계속)
# 자막: render.py 가 직접 굽는다(subs.py). 바닥 밀착 MarginV=10 상당.
# 최종 출력 1280x720, 완성본 파일명 앞에 ✅
import subprocess
import wave
from pathlib import Path

import numpy as np

from timeline import TIMELINE, TOTAL

BASE = Path(__file__).parent
ROOT = [_p for _p in BASE.resolve().parents if (_p / "AGENTS.md").is_file()][-1]
SR = 48000
BGM_VOLUME = 0.15
SFX_VOLUME = 0.9

# 콘티 소리 칸의 효과음 (장면, 효과음, 장면 내 시점 초)
SFX = [
    ("S01-02", "page", 0.1), ("S01-03", "bell", 0.0), ("S02-14", "bell", 0.0), ("S03-12", "bell", 0.0),
    ("S04-03", "swish", 0.2), ("S04-03", "swish", 1.6),
    ("S04-08", "box", 0.0), ("S04-10", "box", 0.0), ("S04-11", "box", 0.0),
    ("S06-09", "bell", 0.0), ("S06-13", "close", None),
]
# S05-07: 결과물 아이콘마다 "퐁" (render.py 와 같은 시점: 0.05 + i*0.075)
SFX += [("S05-07", "pop", ("frac", 0.05 + i * 0.075)) for i in range(11)]

T = {s["id"]: s for s in TIMELINE}


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(axis=1)
    if sr != SR:  # 선형 보간 리샘플
        n = int(len(x) * SR / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    return x


def add(track, x, t):
    i = int(t * SR)
    j = min(len(track), i + len(x))
    if j > i:
        track[i:j] += x[: j - i]


n = int((TOTAL + 0.5) * SR)
voice = np.zeros(n, np.float32)
fx = np.zeros(n, np.float32)

for s in TIMELINE:
    if s["wav"]:
        add(voice, read_wav(s["wav"]), s["start"])

for sid, name, at in SFX:
    s = T[sid]
    x = read_wav(BASE / "sfx" / f"{name}.wav")
    if at is None:  # 장면 끝에 맞춤 (책 닫히는 순간)
        t = s["start"] + s["length"] - len(x) / SR - 0.3
    elif isinstance(at, tuple):
        t = s["start"] + at[1] * s["length"]
    else:
        t = s["start"] + at
    add(fx, x * SFX_VOLUME, t)

# 완성작 클립 소리 (S03-08 한국어 / S03-10 영어 — 콘티: 🎵 꺼짐 / 클립 소리만)
for sid, name in (("S03-08", "harin_ko"), ("S03-10", "harin_en")):
    clip = BASE / "clips" / f"{name}.mp4"
    if clip.exists():
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(clip), "-vn", "-ac", "1", "-ar", str(SR),
                              "-f", "f32le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.float32)[: int(T[sid]["length"] * SR)]
        add(fx, x, T[sid]["start"])

# BGM: 동화용 b1→b2 반복 이어 붙이기 (3초 크로스페이드)
bgm_src = []
for name in ["b1", "b2"]:
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(ROOT / f"assets/bgm/storybook/{name}.mp3"),
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    bgm_src.append(np.frombuffer(raw, np.float32))
XF = int(3.0 * SR)
bgm = bgm_src[0].copy()
k = 1
while len(bgm) < n:
    nxt = bgm_src[k % 2]
    ramp = np.linspace(0, 1, XF, dtype=np.float32)
    bgm[-XF:] = bgm[-XF:] * (1 - ramp) + nxt[:XF] * ramp
    bgm = np.concatenate([bgm, nxt[XF:]])
    k += 1
bgm = bgm[:n]

# BGM 볼륨 곡선 (콘티 소리 칸)
env = np.ones(n, np.float32)
tt = np.arange(n) / SR


def ramp(t0, t1, v0, v1):
    m = (tt >= t0) & (tt < t1)
    env[m] = v0 + (v1 - v0) * (tt[m] - t0) / (t1 - t0)


# S01-01: 🎵 2초 페이드인
ramp(0, 2.0, 0, 1)
# S03-07: 장면 끝 1.5초 전부터 페이드아웃 → S03-08~S03-10 꺼짐 (클립 소리만)
s07 = T["S03-07"]
off0 = s07["start"] + s07["length"] - 1.5
ramp(off0, off0 + 1.5, 1, 0)
s11 = T["S03-11"]
env[(tt >= off0 + 1.5) & (tt < s11["start"] + 0.5)] = 0
# S03-11: 0.5초 지점부터 2초 페이드인
ramp(s11["start"] + 0.5, s11["start"] + 2.5, 0, 1)
# S06-14: 끝 5초 페이드아웃 → 0
ramp(TOTAL - 5.0, TOTAL + 1, 1, 0)
env[tt >= TOTAL] = 0

mix = voice + fx + bgm * env * BGM_VOLUME
peak = np.abs(mix).max()
if peak > 0.98:
    mix *= 0.98 / peak
mix_path = BASE / "_mix.wav"
with wave.open(str(mix_path), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print(f"mix: {len(mix)/SR:.1f}s peak={peak:.2f}")


# 자막은 render.py 가 프레임에 직접 굽는다 (subs.py — 맥 ffmpeg 에 libass 없음)
final = BASE / "✅강의소개_말리와_릴리_final.mp4"
r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "_video.mp4", "-i", "_mix.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", str(final.name)],
                   cwd=str(BASE), capture_output=True, text=True)
if r.returncode != 0:
    raise SystemExit(r.stderr[-1500:])
print(f"FINAL: (checkmark)_final.mp4 ({final.stat().st_size:,} bytes, {TOTAL:.1f}s)")
