# 말리와 소가 된 게으름뱅이 — s03/s04 경계 수동 보정
# whisper 가 54~85s 구간을 환각 전사(chronoscmd 등) → s04 접두어 매칭 실패, 비례 폴백 64.23s 로 잘못 잡힘
# 구간만 잘라 재전사하면 정상: "나도 소가 되면 좋겠다"(64.5~66.4s) / "바로 그때"(67.4s~) → 그 사이 최장 무음으로 경계 이동
import wave

from make_narration import FULL_WAV, OUT, SR, BITS, find_silences, write_wav

S03_START, S04_END = 44.09, 97.37  # make_narration 로그의 기존 경계 (s03 시작 / s05 시작)
LO, HI = 66.4, 67.4                 # 재전사로 확인한 s03 끝 ~ s04 시작

with wave.open(str(FULL_WAV), "rb") as wf:
    pcm = wf.readframes(wf.getnframes())
bps = SR * BITS // 8
near = [(s1 - s0, (s0 + s1) / 2) for s0, s1 in find_silences(pcm) if s1 > LO and s0 < HI]
b = max(near)[1] if near else (LO + HI) / 2
print(f"s03/s04 boundary -> {b:.2f}s ({'silence' if near else 'midpoint'})")

for sid, start, end in [("s03", S03_START, b), ("s04", b, S04_END)]:
    write_wav(pcm[int(start * bps) // 2 * 2:int(end * bps) // 2 * 2], OUT / f"{sid}.wav")
    print(f"{sid}: {start:.2f}s ~ {end:.2f}s ({end - start:.1f}s)")
