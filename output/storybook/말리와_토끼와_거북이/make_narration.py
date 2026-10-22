# 말리와 토끼와 거북이 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
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

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

ENV = Path(next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()) + "/.env")
API_KEY = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith(("GEMINI_API_KEY=", "gemini=")):
        API_KEY = line.split("=", 1)[1].strip()
        break
if not API_KEY:
    sys.exit("GEMINI_API_KEY not found")

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 토끼는 까불거리고 잘난 척하게, "
    "거북이는 느긋하고 다정하게, '한 걸음, 또 한 걸음!'은 씩씩하고 리듬감 있게, "
    "거북이가 먼저 결승선에 도착하는 순간은 신나게 외치듯. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 초록초록 예쁜 숲으로 놀러 왔어요. 이 숲에는요, 아주아주 빠른 친구랑, 아주아주 느린 친구가 살고 있대요. 둘이서 재미있는 시합을 한다는데... 우와, 과연 누가 이길까요? 나도 너무너무 궁금해요! 우리 같이 지켜봐요!",
    "s02": "숲 속에는 깡충깡충 토끼가 살았어요. 토끼는 정말정말 빨랐어요. 바람처럼 쌩! 하고 달렸지요. 그리고 저기, 느릿느릿 거북이도 살았어요. 거북이는 아주 천천히, 아주 조심조심 걸었어요. 한 걸음, 또 한 걸음. 느려도 언제나 씩씩했답니다.",
    "s03": "어느 날, 토끼가 거북이를 보고 깔깔 웃었어요. 야, 거북아! 너는 어쩜 그렇게 느리니? 하하! 거북이는 빙그레 웃으며 말했어요. 토끼야, 그럼 우리 달리기 시합할까? 저 언덕 위 큰 나무까지, 누가 먼저 가나 볼까? 토끼는 배꼽을 잡고 웃었어요. 너랑 나랑? 좋아, 해 보자!",
    "s04": "자, 이제 시합이 시작됐어요! 준비, 땅! 토끼는 바람처럼 쌩 하고 달려 나갔어요. 순식간에 저 멀리, 점점 작아졌지요. 거북이는요? 여전히 느릿느릿, 한 걸음, 또 한 걸음. 그래도 거북이는 멈추지 않았어요. 쉬지 않고 계속, 앞으로 걸어갔답니다.",
    "s05": "우와, 토끼가 너무너무 빨라요! 거북이는 아직도 저 뒤에 있는걸요? 이러다 거북이가 지는 거 아닐까요? 흐음... 그래도 거북이는 포기하지 않아요. 한 걸음, 또 한 걸음. 우리, 끝까지 지켜봐요!",
    "s06": "저 앞까지 온 토끼가 뒤를 돌아봤어요. 거북이는 코딱지만큼 작게 보였어요. 히히, 거북이는 아직 멀었네! 나는 잠깐 쉬어도 되겠다. 토끼는 시원한 나무 그늘에 벌러덩 누웠어요. 그러고는 스르르, 새근새근 그만 잠이 들고 말았어요.",
    "s07": "그동안 거북이는요? 쉬지 않았어요. 한 걸음, 또 한 걸음. 한 걸음, 또 한 걸음. 힘들어도 멈추지 않았어요. 땀이 나도 씩씩하게, 천천히 언덕을 올랐어요. 느려도 괜찮아. 계속 가면 되니까! 거북이는 그렇게 생각했답니다.",
    "s08": "드디어 거북이가 잠든 토끼 옆을 지나갔어요. 쿨쿨 자는 토끼는 아무것도 몰랐지요. 거북이는 살금살금, 그리고 씩씩하게 계속 걸었어요. 이제 큰 나무가 저기 코앞이에요! 조금만 더, 조금만 더! 거북이는 힘을 냈어요.",
    "s09": "바로 그때, 토끼가 눈을 번쩍 떴어요. 어? 거북이가 어디 갔지? 토끼는 깜짝 놀라 쌩 하고 달렸어요. 하지만 이미 늦었어요! 거북이가 큰 나무에 콩! 하고 먼저 도착했거든요. 우와, 거북이가 이겼다! 거북이가 시합에서 이겼어요! 느림보 거북이가, 정말 해냈어요!",
    "s10": "토끼는 부끄러워 얼굴이 빨개졌어요. 거북이야, 미안해. 내가 너무 잘난 척했어. 둘은 사이좋게 손을 잡았어요. 말리는 이제 알아요. 빠른 것보다, 쉬지 않고 꾸준히 하는 게 더 멋지다는 걸요! 오늘 이야기 어땠어요? 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 그럼 다음에 또 만나요. 안녕!",
}

FULL_WAV = OUT / "narration_full.wav"


def write_wav(pcm, path):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm)


def norm(text):
    # 발음 문자만 남김 (공백·문장부호 제거) — Whisper 전사와 대본의 문자 위치 정렬용
    return "".join(ch for ch in text if ch.isalnum())


def generate_full():
    if FULL_WAV.exists() and FULL_WAV.stat().st_size > 100000:
        print("full narration: cached")
        return
    client = genai.Client(api_key=API_KEY, http_options={"timeout": 300000})
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
            write_wav(pcm, FULL_WAV)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            print(f"full narration: {len(pcm):,} PCM bytes ({dur:.1f}s)")
            return
        except Exception as e:
            err = str(e)
            print(f"full TTS attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                sys.exit("quota exceeded - stop, report to user")
            time.sleep(10 * (attempt + 1))
    sys.exit("full TTS: all retries failed")


def split_scenes():
    import whisper

    print("loading whisper large-v3 ...")
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(FULL_WAV), language="ko", word_timestamps=True)
    words = [w for seg in result["segments"] for w in seg["words"]]
    if not words:
        sys.exit("whisper returned no words")

    # 씬 시작의 정규화 문자 오프셋
    offsets, pos = {}, 0
    for sid, text in SCENES.items():
        offsets[sid] = pos
        pos += len(norm(text))
    total_norm = pos

    # 전사 단어를 순서대로 걸으며 씬 경계 시각 결정 (전사 오차에 관대한 문자 누적 방식)
    sids = list(SCENES.keys())
    boundaries = {sids[0]: 0.0}
    next_i, acc = 1, 0
    for w in words:
        if next_i >= len(sids):
            break
        acc += len(norm(w["word"]))
        if acc >= offsets[sids[next_i]]:
            boundaries[sids[next_i]] = max(0.0, w["end"] - BOUNDARY_MARGIN)
            next_i += 1
    if next_i < len(sids):
        sys.exit(f"boundary not found for {sids[next_i]} (transcribed {acc}/{total_norm} chars)")

    with wave.open(str(FULL_WAV), "rb") as wf:
        pcm = wf.readframes(wf.getnframes())
    total_dur = len(pcm) / (SR * BITS // 8)
    bps = SR * BITS // 8  # bytes per second

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
