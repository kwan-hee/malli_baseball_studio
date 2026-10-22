# 말리와 청개구리 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 씬 시작 금지 (2026-07-16 까치편 whisper 환각 교훈)
import base64
import os
import sys
import time
import wave
from pathlib import Path

# Whisper가 subprocess로 ffmpeg를 호출 — WinGet 설치 경로를 PATH에 추가
FFMPEG_DIR = (
    "/opt/homebrew/bin:/usr/local/bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 청개구리가 엄마 말을 반대로만 하는 장면은 익살스럽고 장난스럽게, "
    "엄마 개구리가 속상해하는 장면은 애틋하게, "
    "엄마가 먼 여행을 떠나 청개구리가 뉘우치는 장면은 뭉클하고 슬프게(단 무섭지 않게), "
    "청개구리가 이번만은 엄마 말대로 하는 장면은 정성스럽게, "
    "비가 오면 슬피 우는 마지막은 애틋하고 여운 있게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 비가 오는 날이면요, 개구리들이 개굴개굴 슬프게 우는 소리가 들려요. 왜 하필 비가 오면 그렇게 울까요? 오늘은요, 엄마 말을 늘 반대로만 하던, 말썽꾸러기 청개구리 이야기를 가져왔어요. 자, 옛날 어느 연못가로 함께 가 볼까요?",
    "s02": "옛날 어느 연못가에, 엄마 개구리와 아들 청개구리가 살았어요. 그런데 이 청개구리는요, 엄마가 하는 말이면 무엇이든 꼭 반대로만 했답니다. 엄마가 산으로 가라고 하면 물가로 폴짝, 일찍 자라고 하면 밤새도록 놀고, 목욕하라고 하면 흙탕물에서 뒹굴었지요.",
    "s03": "엄마가 이리 오라고 하면 저리로 폴짝, 조용히 하라고 하면 더 크게 개굴개굴. 청개구리는 하루도 빠짐없이 엄마 속을 태웠어요. 엄마 개구리는 그런 아들을 보며 한숨을 푹 쉬면서도, 그래도 하나뿐인 아들을 무척이나 사랑했답니다. 아이고, 저 말썽꾸러기를 어쩌면 좋을까.",
    "s04": "그러던 어느 날, 엄마 개구리가 그만 자리에 눕고 말았어요. 오래오래 마음고생을 한 탓에, 기운이 점점 없어진 거예요. 엄마는 아무래도 자기가 곧 먼 여행을 떠나게 될 것 같다고 생각했지요. 그래서 마지막으로 아들에게 한 가지 부탁을 남기기로 했답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 엄마 개구리는 아들에게 어떤 부탁을 했을까요? 늘 반대로만 하는 아들이니까, 엄마는 아주 특별한 방법으로 소원을 전했대요. 과연 어떤 지혜를 냈을까요? 자, 함께 들어 봐요!",
    "s06": "엄마 개구리는 가만히 아들을 불러 말했어요. 얘야, 내가 먼 여행을 떠나거든, 나를 산이 아니라 꼭 개울가에 묻어 다오. 사실 엄마는 양지바른 산에 묻히고 싶었지만, 아들이 늘 반대로 하니까, 일부러 반대로 말한 거였지요. 그래야 아들이 산에 묻어 줄 테니까요.",
    "s07": "얼마 뒤, 엄마 개구리는 조용히 눈을 감고 먼 여행을 떠났어요. 그제야 청개구리는 엉엉 울며 후회했답니다. 엄마가 살아 계실 때, 왜 한 번도 말을 잘 듣지 못했을까. 이제라도 엄마의 마지막 부탁만큼은, 꼭 그대로 들어 드려야겠다고 다짐했지요.",
    "s08": "청개구리는 눈물을 뚝뚝 흘리며, 엄마 말씀 그대로 개울가에 정성껏 무덤을 만들었어요. 난생처음으로 엄마 말을 반대로 하지 않고, 그대로 따른 거예요. 하지만 개울가에 무덤을 쓰고 나니, 이번엔 새로운 걱정이 생겨나고 말았답니다.",
    "s09": "비가 내리기 시작하면, 개울물이 불어나 엄마의 무덤이 떠내려갈까 봐 겁이 났던 거예요. 그래서 청개구리는 비만 오면 개울가에 앉아, 개굴개굴 목 놓아 슬프게 울었답니다. 비 오는 날 개구리가 우는 건, 바로 이때부터 생긴 일이래요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 청개구리는 엄마가 먼 여행을 떠난 뒤에야, 말을 잘 듣지 못한 걸 후회했지요? 우리는 엄마 아빠가 곁에 계실 때, 말씀도 잘 듣고 사랑한다고 많이 표현해요. 그래야 나중에 후회하지 않는답니다. 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
                model=MODEL,
                contents=STYLE + full_text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
                        )
                    ),
                ),
            )
            data = resp.candidates[0].content.parts[0].inline_data.data
            pcm = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
            # 최소 길이 가드: 잘린 take(Kore가 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10  # 정규화 글자수 × 0.10초
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
                    client = pool.rotate()  # 키 소진 → 다음 계정으로
                    continue
                except RuntimeError:
                    sys.exit("all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    sys.exit("full TTS: all retries failed")


def split_scenes():
    import json

    import whisper

    print("loading whisper large-v3 ...")
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(FULL_WAV), language="ko", word_timestamps=True)
    words = [w for seg in result["segments"] for w in seg["words"]]
    if not words:
        sys.exit("whisper returned no words")

    # 자막 실측 생성용(A안) — compose.py 가 글자수 비례 대신 이 실측으로 SRT 생성
    (OUT / "word_timestamps.json").write_text(
        json.dumps([{"word": w["word"], "start": w["start"], "end": w["end"]} for w in words],
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"word_timestamps.json: {len(words)} words")

    with wave.open(str(FULL_WAV), "rb") as wf:
        pcm = wf.readframes(wf.getnframes())
    total_dur = len(pcm) / (SR * BITS // 8)
    bps = SR * BITS // 8

    # 씬 경계 = 각 씬 첫 구절(정규화 14자)을 whisper 단어 스트림에서 접두어 퍼지 매칭 (2026-07-16 상시화).
    # 기존 누적 글자 방식은 whisper 오전사/환각으로 뒤 씬 경계가 통째로 밀려 붕괴 → 접두어 매칭으로 교체.
    # 매칭 실패(환각 구간)면 글자수 비례 추정으로 graceful fallback (붕괴 대신 근사치). 필요시 fix_boundaries 로 보정.
    import difflib

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
            if r >= 0.75:  # 후렴 반복 함정 방지: 0.75+ 후보 중 추정치 근접 우선
                cands.append((t, r))
            if r > best_r:
                best_r, best_t = r, t
        if cands:
            best_t, best_r = min(cands, key=lambda c: abs(c[0] - est))
        if best_t is None or best_r < 0.55:
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)  # 환각 구간 — 비례 폴백
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
