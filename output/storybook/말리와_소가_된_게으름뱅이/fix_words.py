# 말리와 소가 된 게으름뱅이 — word_timestamps.json 환각 구간(48~92s) 교체
# 전체 오디오 전사에서 whisper 가 54~85s 를 환각(chronoscmd 등) → compose 자막 비례 폴백이 0.5s 큐로 붕괴
# 해당 구간만 잘라 재전사(condition_on_previous_text=False)하면 정상 → 단어 타임스탬프를 오프셋 보정해 끼워 넣음
import json
import sys
import wave

import whisper

from make_narration import FULL_WAV, OUT, SR, BITS, CH, write_wav

T0, T1 = 48.0, 92.0
WORDS = OUT / "word_timestamps.json"
SEG = OUT / "_seg_48_92.wav"

with wave.open(str(FULL_WAV), "rb") as wf:
    wf.setpos(int(T0 * SR))
    write_wav(wf.readframes(int((T1 - T0) * SR)), SEG)

res = whisper.load_model("large-v3").transcribe(
    str(SEG), language="ko", word_timestamps=True, condition_on_previous_text=False)
new = [{"word": w["word"], "start": T0 + w["start"], "end": T0 + w["end"]}
       for s in res["segments"] for w in s["words"]]
if not new:
    sys.exit("re-transcription returned no words")
print("".join(w["word"] for w in new))

old = json.loads(WORDS.read_text(encoding="utf-8"))
WORDS.with_suffix(".orig.json").write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
merged = [w for w in old if w["start"] < T0] + new + [w for w in old if w["start"] >= T1]
WORDS.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
print(f"words: {len(old)} -> {len(merged)} (replaced {T0}-{T1}s with {len(new)})")
SEG.unlink()
