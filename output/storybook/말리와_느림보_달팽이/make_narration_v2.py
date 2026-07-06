# 말리와 느림보 달팽이 — v2 나레이션: Gemini TTS(Kore) + 성우 감정 연기, 행동 지문 제거 대본
import base64
import sys
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio_v2"
OUT.mkdir(exist_ok=True)

ENV = Path(r"C:\youtube_longform_agent\.env")
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

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "밝고 사랑스럽게, 감정을 풍부하게 연기하며 자연스럽게 읽으세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 토토(달팽이)의 대사는 느긋하고 다정하게, "
    "슬픈 장면은 조금 촉촉하게. 다음을 읽으세요:\n\n"
)

# v2 대본 — 행동 지문은 화면이 보여줌. 나레이션은 대사 + 감정 + 이야기 흐름만.
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 꽃밭으로 소풍 가는 날이에요. 우와, 신난다!",
    "s02": "꽃밭아, 기다려! 내가 제일 먼저 갈 거야! 말리는 한껏 신이 났어요.",
    "s03": "어? 안녕? 나는 토토야. 만나서 반가워. 토토는 아주아주 느린 달팽이 친구였어요.",
    "s04": "토토야, 너는 너무 느려! 나 먼저 갈게! 말리는 토토를 두고 먼저 가 버렸어요.",
    "s05": "어라? 어느 쪽이지? 여기가 어디지? 말리는 그만 길을 잃고 말았어요. 무서워. 눈물이 핑 돌았어요.",
    "s06": "울지 마, 말리야. 나는 길을 다 기억하는걸. 빨간 꽃 옆을 지나서, 둥근 돌 옆으로! 토토는 천천히 왔기 때문에, 길을 다 보아 두었던 거예요.",
    "s07": "천천히, 천천히, 하나씩 보면서! 우와, 반짝반짝 이슬이다! 저기 노란 나비도 있어!",
    "s08": "우와, 도착했다! 꽃이 이렇게 많다니! 말리와 토토는 함께 활짝 웃었어요.",
    "s09": "말리는 이제 알아요. 빠른 것만 좋은 게 아니라는 걸. 천천히 가면, 예쁜 것들이 더 많이 보인다는 걸요.",
    "s10": "오늘 이야기 어땠어요? 우리 같이 외쳐 볼까요? 천천히, 천천히, 하나씩 보면서! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 그럼 다음에 또 만나요. 안녕!",
}


def write_wav(pcm, path):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm)


if __name__ == "__main__":
    client = genai.Client(api_key=API_KEY, http_options={"timeout": 120000})

    for sid, text in SCENES.items():
        out = OUT / f"{sid}.wav"
        if out.exists() and out.stat().st_size > 10000:
            print(f"{sid}: cached")
            continue
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=MODEL,
                    contents=STYLE + text,
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
                write_wav(pcm, out)
                print(f"{sid}: {len(pcm):,} PCM bytes")
                break
            except Exception as e:
                err = str(e)
                print(f"{sid}: attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    sys.exit(f"{sid}: quota exceeded - stop, report to user")
                time.sleep(5 * (attempt + 1))
        else:
            sys.exit(f"{sid}: all retries failed")

    print("TTS V2 DONE")
