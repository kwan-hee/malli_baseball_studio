# 하린이와 초코의 이상한 나라 — 영어 s06/s07 경계 수동 보정 (2026-10-20)
# 무음 스냅이 경계를 150.09 → 148.78s 로 앞당겨 s06 마지막 대사 "Who made a mess of my garden?"(148.46~150.8s)가 s07 로 넘어감
# 대사 끝(150.8) ~ "The card soldiers"(151.04) 사이 최장 무음으로 경계 이동
import wave

from make_narration_en import FULL_WAV, OUT, SR, BITS, find_silences, write_wav

S06_START, S07_END = 129.12, 176.14  # make_narration_en 로그의 기존 경계 (s06 시작 / s08 시작)
LO, HI = 150.8, 151.04

with wave.open(str(FULL_WAV), "rb") as wf:
    pcm = wf.readframes(wf.getnframes())
bps = SR * BITS // 8
near = [(s1 - s0, (s0 + s1) / 2) for s0, s1 in find_silences(pcm) if s1 > LO and s0 < HI]
b = max(near)[1] if near else (LO + HI) / 2
print(f"s06/s07 boundary -> {b:.2f}s ({'silence' if near else 'midpoint'})")

for sid, start, end in [("s06", S06_START, b), ("s07", b, S07_END)]:
    write_wav(pcm[int(start * bps) // 2 * 2:int(end * bps) // 2 * 2], OUT / f"{sid}.wav")
    print(f"{sid}: {start:.2f}s ~ {end:.2f}s ({end - start:.1f}s)")
