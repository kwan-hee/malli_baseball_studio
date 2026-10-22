# 말리와 양치기 소년 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "소년이 거짓말로 외치는 장면은 장난스럽고 신나게, "
    "마을 사람들이 달려오는 장면은 급하고 걱정스럽게, "
    "진짜 늑대가 나타나는 장면은 긴장감 있고 조마조마하게, "
    "소년이 울며 사과하는 장면은 안쓰럽고 진심 어리게, "
    "용서받는 마지막은 따뜻하고 훈훈하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은 양치기 소년 이야기를 해 줄 거예요. 거짓말을 하면 어떤 일이 벌어질까요? 같이 알아봐요!",
    "s02": "옛날 옛날, 작은 마을 근처 언덕에 양치기 소년이 살았어요. 소년은 매일매일 하얀 양 떼를 데리고 풀밭에 나가 돌봤지요. 그런데 혼자 있으니 너무너무 심심했어요. 재미있는 일이 없을까, 소년은 궁리를 시작했답니다.",
    "s03": "소년이 갑자기 큰 소리로 외쳤어요. 늑대다! 늑대가 나타났어요! 도와주세요! 마을 사람들이 깜짝 놀라 호미랑 갈퀴를 들고 후다닥 언덕으로 달려왔어요.",
    "s04": "그런데 어디에도 늑대는 없었어요. 소년은 배꼽을 잡고 깔깔 웃었지요. 히히, 다 속았다! 마을 사람들은 허탈한 얼굴로 고개를 저으며 돌아갔어요.",
    "s05": "며칠 뒤, 소년은 또 소리쳤어요. 늑대가 또 나타났어요! 빨리 와 주세요! 마을 사람들이 다시 헐레벌떡 달려왔지만, 이번에도 늑대는 없었어요. 사람들은 정말 화가 나서 말했지요. 다시는 안 속아!",
    "s06": "그런데 어느 날, 진짜로 늑대가 숲에서 슬금슬금 나타났어요. 커다란 눈에 날카로운 이빨! 소년은 심장이 쿵쾅쿵쾅 뛰었어요.",
    "s07": "소년이 목이 터져라 외쳤어요. 늑대다! 이번엔 진짜예요! 제발 와 주세요! 하지만 마을 사람들은 고개를 저었어요. 또 거짓말이겠지. 아무도 올라오지 않았어요.",
    "s08": "늑대가 양 떼를 향해 달려들었어요. 양들이 메에, 메에 울며 사방으로 흩어졌지요. 소년은 울면서 언덕 아래로 뛰어 내려갔어요. 살려 주세요, 이번엔 정말이에요!",
    "s09": "소년의 울음소리를 들은 마을 사람들이 그제야 달려왔어요. 다 함께 소리를 지르며 늑대를 쫓아냈지요. 다행히 양들도 모두 무사했어요. 소년은 눈물을 뚝뚝 흘리며 말했어요. 정말 죄송해요. 다시는 거짓말 안 할게요. 마을 사람들은 소년의 진심을 알고, 이번 한 번만 용서해 주었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 거짓말을 하면 진짜 도움이 필요할 때 아무도 믿어 주지 않아요. 믿음은 한번 잃으면 다시 얻기 정말 어렵답니다. 여러분은 늘 솔직하게 말하는 멋진 친구가 돼 주세요! 재미있었다면 구독이랑 좋아요 꾹 눌러 주세요. 다음에 또 만나요, 멍멍!",
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
