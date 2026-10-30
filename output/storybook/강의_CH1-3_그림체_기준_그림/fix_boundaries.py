# 장면 경계 보정 (CH1-3, 2026-10-30 — check_boundaries.py 재전사 대조로 발견. 템플릿 = CH1-2 fix_boundaries.py)
# 릴리: S03-10 끝에 "그렇죠" 붙음 / S03-13 끝 "무덤은 꽃이 핀 풀 언덕으로요"가 S03-14 로 넘어감 / S04-01 끝에 "이 장면의 대사는" 붙음
# 말리: S03-04 "그건 너무 슬퍼요"가 S03-07 로 넘어감 / S05-09 "니까 괜찮아요"가 S06-02 로 넘어감
# → 실측 무음 가운데(whisper 단어 시각은 ~1s 이르게 찍힘)를 새 시작점으로, ±0.4s 안의 가장 긴 무음으로 스냅해 그 화자 장면 전부 다시 자른다.
# S03-14 는 143.96 으로 잡았다가 "다섯째"가 S03-13 끝에 남아 142.88 로 다시 옮김 (재검증으로 확인).
import wave
from pathlib import Path

from make_narration import SCENES, SPEAKER, find_silences

BASE = Path(__file__).parent
AUD = BASE / "audio"
FIX = {
    "malli": {"S03-07": 28.08, "S06-02": 94.49},
    "lily": {"S03-12": 119.58, "S03-14": 142.88, "S04-03": 156.20},
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
