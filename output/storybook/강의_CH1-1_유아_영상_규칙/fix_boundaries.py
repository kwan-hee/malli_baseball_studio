# 말리 트랙 장면 경계 보정 (2026-10-29)
# whisper large-v3 접두어 매칭이 짧은 대사("네!"·"안 꿔요!")와 의성어("하암", "음매~")에서 어긋나
# S03-05·S03-08·S04-11·S04-14·S05-03~S06-04 경계가 밀림. 원음은 대본대로 정상(whisper small 재전사로 확인).
# → 재전사 시각을 대략적인 시작점으로 주고, ±0.35s 안의(앞 경계보다 0.3s 이상 뒤) 가장 긴 실측 무음 가운데로 스냅해 말리 장면 전부 다시 자른다.
import wave
from pathlib import Path

from make_narration import find_silences

BASE = Path(__file__).parent
SRC = BASE / "audio" / "narration_malli.wav"

# 장면 시작 대략값(초, whisper small 재전사 기준)
STARTS = {
    "S01-03": 0.0, "S01-05": 3.4, "S02-02": 7.8, "S03-02": 13.9, "S03-03b": 18.3, "S03-05": 23.7,
    "S03-08": 29.8, "S04-02": 32.9, "S04-04": 35.8, "S04-07": 39.0, "S04-11": 43.3, "S04-14": 46.3,
    "S04-16": 50.7, "S05-A2": 54.5, "S05-03": 57.5, "S05-05": 58.65, "S05-07": 59.75, "S06-02": 61.9,
    "S06-04": 65.1,
}

with wave.open(str(SRC), "rb") as w:
    sr, sw, ch = w.getframerate(), w.getsampwidth(), w.getnchannels()
    pcm = w.readframes(w.getnframes())
bps = sr * sw * ch
total = len(pcm) / bps
sil = find_silences(pcm, min_len=0.12)

cuts = []
for sid, t in STARTS.items():
    if t > 0:
        prev = cuts[-1][1]
        near = [(s1 - s0, (s0 + s1) / 2) for s0, s1 in sil
                if s1 > t - 0.35 and s0 < t + 0.35 and (s0 + s1) / 2 > prev + 0.3]
        if near:
            t = max(near)[1]
    cuts.append((sid, t))
for i, (sid, a) in enumerate(cuts):
    b = cuts[i + 1][1] if i + 1 < len(cuts) else total
    seg = pcm[int(a * bps) // 2 * 2: int(b * bps) // 2 * 2]
    with wave.open(str(BASE / "audio" / f"{sid}.wav"), "wb") as o:
        o.setnchannels(ch)
        o.setsampwidth(sw)
        o.setframerate(sr)
        o.writeframes(seg)
    print(f"{sid}: {a:.2f}s ~ {b:.2f}s ({b - a:.1f}s)")

# 릴리 트랙: 다음 장면 첫 단어가 앞 장면 끝에 붙은 4곳 (whisper small 재전사 + 단어 시각 + 실측 무음으로 확인)
# 새 경계 = 그 단어 앞 무음 구간 가운데. (장면, 시작, 끝) — 끝 장면의 원래 끝은 make_narration 로그 값
LILY_SRC = BASE / "audio" / "narration_lily.wav"
LILY_CUTS = {
    "S02-01": (30.79, 44.58), "S02-03": (44.58, 62.61),    # "그렇죠." 앞 무음 44.42~44.74
    "S03-06": (113.97, 123.54), "S03-07": (123.54, 143.15),  # "셋째," 앞 무음 123.36~123.72
    "S04-03": (160.12, 184.92), "S04-05": (184.92, 199.07),  # "다섯째," 앞 무음 184.66~185.18
    "S05-01": (336.48, 344.52), "S05-02": (344.52, 349.28),  # "하나," 앞 무음 344.18~344.86
}
with wave.open(str(LILY_SRC), "rb") as w:
    lpcm = w.readframes(w.getnframes())
for sid, (a, b) in LILY_CUTS.items():
    with wave.open(str(BASE / "audio" / f"{sid}.wav"), "wb") as o:
        o.setnchannels(ch)
        o.setsampwidth(sw)
        o.setframerate(sr)
        o.writeframes(lpcm[int(a * bps) // 2 * 2: int(b * bps) // 2 * 2])
    print(f"{sid}: {a:.2f}s ~ {b:.2f}s ({b - a:.1f}s) [lily]")
