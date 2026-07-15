# whisper 씬 경계 전면 재유도 v3 — 모든 씬(s02~s10) 시작을 단어 타임스탬프 접두어 퍼지 매칭으로 결정
# (부분 복구 시도에서 원래 whisper 경계 다수가 오염된 것으로 확인 → 전면 재유도가 안전)
import difflib
import json
import wave
from pathlib import Path

from make_narration import SCENES, norm

BASE = Path(__file__).parent
FULL = BASE / "audio" / "narration_full.wav"
WORDS = json.loads((BASE / "audio" / "word_timestamps.json").read_text(encoding="utf-8"))
SR, BITS = 24000, 16
MARGIN = 0.15
PREFIX_LEN = 14
SEARCH_WINDOW = 20.0  # 문자비율 추정 시각 ± 탐색 범위

with wave.open(str(FULL), "rb") as wf:
    pcm = wf.readframes(wf.getnframes())
TOTAL = len(pcm) / (SR * BITS // 8)
bps = SR * BITS // 8

# 단어 → 정규화 문자 스트림 (문자마다 해당 단어 시작시각)
stream_chars, stream_times = [], []
for w in WORDS:
    for ch in norm(w["word"]):
        stream_chars.append(ch)
        stream_times.append(w["start"])
S = "".join(stream_chars)

sids = list(SCENES.keys())
chars = {sid: len(norm(SCENES[sid])) for sid in sids}
total_c = sum(chars.values())

# 수동 오버라이드: whisper 가 s07 시작을 환각 전사(다국어 노이즈)해 접두어 매칭 불가.
# 신뢰 앵커 = s08 시작 "견우와 직녀는 오작교"(175.30, 깨끗 전사). s07 시작은 s06·s08 사이 글자수 비례.
MANUAL_ANCHOR = {"s08": 175.30}  # 깨끗 매칭된 s08 첫 단어 시작시각

bounds = {sids[0]: 0.0}
acc = 0
prev_b = 0.0
for k, sid in enumerate(sids[1:], start=1):
    acc += chars[sids[k - 1]]
    est = TOTAL * acc / total_c

    # s07: 접두어 환각 → s06(prev_b)와 s08 앵커 사이를 글자수 비례로 배치
    if sid == "s07":
        s08a = MANUAL_ANCHOR["s08"]
        b = prev_b + (s08a - prev_b) * chars["s06"] / (chars["s06"] + chars["s07"])
        print(f"{sid} start: MANUAL proportional = {b:.2f} (s06~s08 anchor)")
        bounds[sid] = b
        prev_b = b
        continue
    if sid in MANUAL_ANCHOR:
        b = max(prev_b + 1.0, MANUAL_ANCHOR[sid] - MARGIN)
        print(f"{sid} start: MANUAL anchor = {b:.2f}")
        bounds[sid] = b
        prev_b = b
        continue

    prefix = norm(SCENES[sid])[:PREFIX_LEN]
    # 후렴 반복 함정 방지: ratio 0.75+ 후보 중 추정치(est)에 가장 가까운 것을 선택
    # (전역 최고 ratio 는 씬 안의 반복 구절 두 번째 등장에 걸릴 수 있음 — 해와달 s03에서 확인)
    cands = []
    best_ratio, best_time = 0.0, None
    for i in range(len(S) - PREFIX_LEN):
        t = stream_times[i]
        if abs(t - est) > SEARCH_WINDOW or t <= prev_b + 1.0:
            continue
        ratio = difflib.SequenceMatcher(None, S[i:i + PREFIX_LEN], prefix).ratio()
        if ratio >= 0.75:
            cands.append((t, ratio))
        if ratio > best_ratio:
            best_ratio, best_time = ratio, t
    if cands:
        best_time, best_ratio = min(cands, key=lambda c: abs(c[0] - est))
    if best_time is None or best_ratio < 0.55:
        raise SystemExit(f"{sid}: prefix match failed (best={best_ratio:.2f} near est={est:.2f})")
    b = max(prev_b + 1.0, best_time - MARGIN)
    print(f"{sid} start: est={est:6.2f} matched={best_time:6.2f} (ratio {best_ratio:.2f})")
    bounds[sid] = b
    prev_b = b

for i, sid in enumerate(sids):
    start = bounds[sid]
    end = bounds[sids[i + 1]] if i + 1 < len(sids) else TOTAL
    b0 = int(start * bps) // 2 * 2
    b1 = int(end * bps) // 2 * 2
    with wave.open(str(BASE / "audio" / f"{sid}.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm[b0:b1])
    rate = chars[sid] / max(end - start, 0.1) * 60
    print(f"{sid}.wav: {start:.2f}~{end:.2f} ({end-start:.1f}s, {rate:.0f}자/분)")
print("FIX DONE")
