# 장면 경계 보정 — 템플릿 CH2-1. (2026-10-30, check_boundaries.py 재전사 대조 + audio/words_*.json 단어 시각으로 확인)
# → 새 시작점을 주고, ±0.4s 안의 가장 긴 실측 무음 가운데로 스냅해 그 화자 장면 전부 다시 자른다.
import wave
from pathlib import Path

from make_narration import SCENES, SPEAKER, find_silences

BASE = Path(__file__).parent
AUD = BASE / "audio"
# CH2-2 (2026-10-30)
#   릴리: "하나 더요."(191.94~192.70)가 S03-10 끝에 붙음 / "새 창에서"(270.04~271.18)가 S04-05 끝에 붙음(S04-07 비례 폴백)
#   말리: "외웠어요."(13.18~14.20)가 S03-09 앞으로 넘어감
FIX = {
    "lily": {"S03-11": 191.60, "S04-07": 269.36},
    "malli": {"S03-09": 14.37},
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
