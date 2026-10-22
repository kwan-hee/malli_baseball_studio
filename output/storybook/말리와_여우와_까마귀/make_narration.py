# 말리와 여우와 까마귀 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
import base64
import os
import sys
import time
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FFMPEG_DIR = (
    "/opt/homebrew/bin:/usr/local/bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15

STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, "
    "여우가 아부하는 장면은 달콤하고 과장되게, "
    "까마귀가 우쭐해하는 장면은 뽐내듯 뿌듯하게, "
    "치즈가 떨어지는 장면은 놀라고 당황하게, "
    "여우가 사과하는 장면은 미안하고 진심 어리게, "
    "둘이 나눠 먹는 마지막은 따뜻하고 훈훈하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은 여우와 까마귀 이야기를 해 줄 거예요. 달콤한 말에 속으면 어떻게 될까요? 같이 알아봐요!",
    "s02": "어느 날, 까마귀 한 마리가 맛있는 치즈를 하나 주워 왔어요. 까마귀는 치즈를 꼭 물고 높은 나무 꼭대기에 올라가 앉았지요. 오늘은 정말 좋은 날이다! 까마귀는 아주아주 기분이 좋았어요.",
    "s03": "그때, 배고픈 여우 한 마리가 나무 아래를 지나가다 고개를 들었어요. 어? 저 치즈 정말 맛있겠다! 여우는 꿀꺽 침을 삼키며 궁리를 시작했어요.",
    "s04": "여우가 나무 아래에서 활짝 웃으며 말했어요. 까마귀 님, 깃털이 정말 아름다우시네요! 반짝반짝 윤이 나서 마치 보석 같아요! 까마귀는 슬쩍 기분이 좋아졌어요.",
    "s05": "여우가 더 달콤하게 말했어요. 이렇게 아름다운 분이라면 목소리도 분명 정말 예쁘시겠어요! 한 곡만 불러 주시면 안 될까요? 까마귀는 점점 우쭐해졌어요. 그래, 내 목소리를 들려줘야지!",
    "s06": "까마귀가 목을 쭉 빼고 입을 크게 벌렸어요. 까악! 그 순간, 물고 있던 치즈가 뚝, 아래로 떨어졌어요! 까마귀는 깜짝 놀라 아래를 내려다보았지요.",
    "s07": "여우가 재빨리 치즈를 낼름 물었어요. 히히, 너무 쉬웠어! 여우가 돌아서려는데, 나무 위에서 까마귀가 풀이 죽어 고개를 떨구고 있었어요. 내 치즈, 돌려 줘요. 까마귀의 목소리가 작게 떨렸어요.",
    "s08": "여우는 까마귀의 슬픈 모습을 보고 마음이 찔렸어요. 여우가 천천히 돌아와 말했지요. 미안해, 솔직하게 말했어야 했는데 빈말로 속인 거야. 여우는 치즈를 반으로 나눠 한쪽을 까마귀에게 내밀었어요.",
    "s09": "까마귀가 나무에서 내려와 치즈를 받았어요. 둘은 나란히 앉아 맛있게 나눠 먹었지요. 다음엔 솔직하게 말해 줘. 빈말 칭찬 말고 진짜 칭찬! 까마귀가 웃으며 말했어요. 여우도 고개를 끄덕이며 웃었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 달콤한 말로 칭찬하는 건 진짜 칭찬이 아니에요. 빈말에 우쭐하면 소중한 걸 잃을 수 있답니다. 여러분은 진짜 마음을 담은 칭찬을 하는 멋진 친구가 돼 주세요! 재미있었다면 구독이랑 좋아요 꾹 눌러 주세요. 다음에 또 만나요, 멍멍!",
}

FULL_WAV = OUT / "narration_full.wav"


def write_wav(pcm, path):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm)


def norm(text):
    return "".join(ch for ch in text if ch.isalnum())


def generate_full():
    if FULL_WAV.exists() and FULL_WAV.stat().st_size > 100000:
        print("full narration: cached")
        return
    pool = GeminiPool()
    client = pool.client()
    full_text = "\n\n".join(SCENES.values())
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL, contents=STYLE + full_text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE))),
                ),
            )
            data = resp.candidates[0].content.parts[0].inline_data.data
            pcm = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10
            if dur < min_dur:
                raise RuntimeError(f"truncated take: {dur:.1f}s < {min_dur:.1f}s expected — retry")
            write_wav(pcm, FULL_WAV)
            print(f"full narration: {len(pcm):,} PCM bytes ({dur:.1f}s)")
            return
        except Exception as e:
            err = str(e)
            print(f"full TTS attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit("all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    sys.exit("full TTS: all retries failed")


def split_scenes():
    import json, difflib, whisper
    print("loading whisper large-v3 ...")
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(FULL_WAV), language="ko", word_timestamps=True)
    words = [w for seg in result["segments"] for w in seg["words"]]
    if not words:
        sys.exit("whisper returned no words")
    (OUT / "word_timestamps.json").write_text(
        json.dumps([{"word": w["word"], "start": w["start"], "end": w["end"]} for w in words],
                   ensure_ascii=False), encoding="utf-8")
    print(f"word_timestamps.json: {len(words)} words")
    with wave.open(str(FULL_WAV), "rb") as wf:
        pcm = wf.readframes(wf.getnframes())
    total_dur = len(pcm) / (SR * BITS // 8)
    bps = SR * BITS // 8
    stream_times, stream_chars = [], []
    for w in words:
        for ch in norm(w["word"]):
            stream_chars.append(ch)
            stream_times.append(w["start"])
    S = "".join(stream_chars)
    sids = list(SCENES.keys())
    chars = {sid: len(norm(SCENES[sid])) for sid in sids}
    total_c = sum(chars.values())
    PREFIX_LEN, WINDOW = 14, 20.0
    boundaries = {sids[0]: 0.0}
    acc, prev_b = 0, 0.0
    for k, sid in enumerate(sids[1:], start=1):
        acc += chars[sids[k - 1]]
        est = total_dur * acc / total_c
        prefix = norm(SCENES[sid])[:PREFIX_LEN]
        cands, best_r, best_t = [], 0.0, None
        for i in range(len(S) - PREFIX_LEN):
            t = stream_times[i]
            if abs(t - est) > WINDOW or t <= prev_b + 1.0:
                continue
            r = difflib.SequenceMatcher(None, S[i:i + PREFIX_LEN], prefix).ratio()
            if r >= 0.75:
                cands.append((t, r))
            if r > best_r:
                best_r, best_t = r, t
        if cands:
            best_t, best_r = min(cands, key=lambda c: abs(c[0] - est))
        if best_t is None or best_r < 0.55:
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)
            print(f"{sid}: prefix match weak (best={best_r:.2f}) — proportional fallback @ {b:.2f}")
        else:
            b = max(prev_b + 1.0, best_t - BOUNDARY_MARGIN)
        boundaries[sid] = b
        prev_b = b
    for i, sid in enumerate(sids):
        start = boundaries[sid]
        end = boundaries[sids[i + 1]] if i + 1 < len(sids) else total_dur
        b0 = int(start * bps) // 2 * 2
        b1 = int(end * bps) // 2 * 2
        write_wav(pcm[b0:b1], OUT / f"{sid}.wav")
        print(f"{sid}: {start:.2f}s ~ {end:.2f}s ({end-start:.1f}s)")


if __name__ == "__main__":
    generate_full()
    need = [s for s in SCENES if not (OUT / f"{s}.wav").exists()]
    if need:
        split_scenes()
    else:
        print("scene wavs: cached")
    print("TTS DONE")
