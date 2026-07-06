# 사이클링 히트 — 해설자 남성 보이스 3종 샘플 생성 (Charon/Puck/Fenrir, 사용자 선택용)
import base64
import sys
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "voice_samples"
OUT.mkdir(exist_ok=True)

ENV = Path(r"C:\youtube_longform_agent\.env")
API_KEY = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith(("GEMINI_API_KEY=", "gemini=")):
        API_KEY = line.split("=", 1)[1].strip()
        break

MODEL = "gemini-2.5-flash-preview-tts"
VOICES = ["Charon", "Puck", "Fenrir"]
SR, BITS, CH = 24000, 16, 1

STYLE = (
    "당신은 야구를 20년 본 동네 형 같은 유튜브 해설자입니다. "
    "친근한 존댓말로 리듬감 있게, 궁금증 유발 구간은 톤을 올려서 자연스럽게 읽으세요:\n\n"
)
SAMPLE = (
    "타자가 한 경기에서 단타, 2루타, 3루타, 홈런을 전부 다 칩니다. 이게 가능할까요? "
    "노히터만큼 보기 힘들다는 기록. 오늘은 사이클링 히트 이야기입니다."
)


def write_wav(pcm, path):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm)


client = genai.Client(api_key=API_KEY, http_options={"timeout": 120000})

for voice in VOICES:
    out = OUT / f"sample_{voice}.wav"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{voice}: cached")
        continue
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=STYLE + SAMPLE,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                        )
                    ),
                ),
            )
            data = resp.candidates[0].content.parts[0].inline_data.data
            pcm = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
            write_wav(pcm, out)
            print(f"{voice}: {len(pcm):,} PCM bytes")
            break
        except Exception as e:
            print(f"{voice}: attempt {attempt+1} failed - {str(e)[:100]}")
            time.sleep(5 * (attempt + 1))
    else:
        sys.exit(f"{voice}: failed")

print("SAMPLES DONE")
