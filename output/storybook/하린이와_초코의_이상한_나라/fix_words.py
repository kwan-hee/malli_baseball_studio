# 하린이와 초코의 이상한 나라 — whisper 환각 단어 제거 (2026-10-20)
# 230.64s 에 길이 0 단어 5개("그 침대에 누워 있었어요. 하린이는") 환각 → s09 마지막 자막이 1.2s 로 붕괴
# 길이 0 단어가 3개 이상 연속된 구간만 환각으로 보고 제거 (단독 길이 0 단어는 실제 발화라 유지 — 글자 정렬 보존)
# 원본은 word_timestamps.orig.json 백업
import json
import shutil
import sys
from pathlib import Path

# 인자: 오디오 폴더 이름 (기본 audio, 영어는 audio_en — 영어도 148.36s 에 "The Queen was in a state of defeat." 환각)
P = Path(__file__).parent / (sys.argv[1] if len(sys.argv) > 1 else "audio") / "word_timestamps.json"
BAK = P.with_name("word_timestamps.orig.json")
if not BAK.exists():
    shutil.copy(P, BAK)
words = json.loads(BAK.read_text(encoding="utf-8"))
zero = [w["end"] <= w["start"] for w in words]
drop = set()
i = 0
while i < len(words):
    j = i
    while j < len(words) and zero[j]:
        j += 1
    if j - i >= 3:
        drop.update(range(i, j))
    i = max(j, i + 1)
kept = [w for k, w in enumerate(words) if k not in drop]
print(f"removed {len(drop)} hallucinated words: {[words[k]['word'] for k in sorted(drop)]}")
P.write_text(json.dumps(kept, ensure_ascii=False), encoding="utf-8")
