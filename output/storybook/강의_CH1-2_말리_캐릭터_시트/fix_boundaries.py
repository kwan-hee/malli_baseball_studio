# 장면 경계 보정 (2026-10-29, check_boundaries.py 재전사 대조로 발견)
# 말리: 짧은 대사 연속 구간(S04-07~S06-04)에서 접두어 매칭이 한 칸씩 밀림
# 릴리: S04-01 첫 문장 "이제 글 쪽이에요"가 S03-06 끝에 붙음 / S06-03 끝 "리본이 어디에 있죠?"가 S06-05로 넘어감(비례 폴백)
# → whisper small 단어 시각으로 새 시작점을 주고, ±0.4s 안의 가장 긴 실측 무음 가운데로 스냅해 그 화자 장면 전부 다시 자른다.
import wave
from pathlib import Path

from make_narration import SCENES, SPEAKER, find_silences

BASE = Path(__file__).parent
AUD = BASE / "audio"
FIX = {
    "malli": {"S05-04": 30.86, "S05-07": 34.42, "S06-02": 37.6, "S06-04": 39.67},  # 실측 무음 가운데 (whisper 단어 시각은 ~1s 이르게 찍힘),
    "lily": {"S04-01": 145.0, "S06-05": 395.6},
}

for spk, fix in FIX.items():
    with wave.open(str(AUD / f"narration_{spk}.wav"), "rb") as w:
        sr, sw, ch = w.getframerate(), w.getsampwidth(), w.getnchannels()
        pcm = w.readframes(w.getnframes())
    bps = sr * sw * ch
    total = len(pcm) / bps
    sil = find_silences(pcm, min_len=0.12)
    sids = [s for s in SCENES if SPEAKER[s] == spk]
    # 현재 경계 = 장면 wav 길이 누적
    starts, t = {}, 0.0
    for sid in sids:
        starts[sid] = t
        with wave.open(str(AUD / f"{sid}.wav")) as w:
            t += w.getnframes() / w.getframerate()
    for sid, t in fix.items():
        near = [(s1 - s0, (s0 + s1) / 2) for s0, s1 in sil if s1 > t - 0.4 and s0 < t + 0.4]
        starts[sid] = max(near)[1] if near else t
    for i, sid in enumerate(sids):
        a = starts[sid]
        b = starts[sids[i + 1]] if i + 1 < len(sids) else total
        with wave.open(str(AUD / f"{sid}.wav"), "wb") as o:
            o.setnchannels(ch)
            o.setsampwidth(sw)
            o.setframerate(sr)
            o.writeframes(pcm[int(a * bps) // 2 * 2: int(b * bps) // 2 * 2])
        if sid in fix or (i + 1 < len(sids) and sids[i + 1] in fix):
            print(f"{sid}: {a:.2f}s ~ {b:.2f}s ({b - a:.1f}s)")
