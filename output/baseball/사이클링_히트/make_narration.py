# 사이클링 히트 — 나레이션 생성: Gemini TTS Puck + 해설자 연기 지시 (2026-07-07 보이스 확정)
import base64
import sys
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
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
VOICE = "Puck"
SR, BITS, CH = 24000, 16, 1

STYLE = (
    "당신은 야구를 20년 본 동네 형 같은 유튜브 해설자입니다. "
    "친근한 존댓말로 리듬감 있게, 궁금증 유발 구간은 톤을 올리고, "
    "기록 소개 구간은 살짝 극적으로, 자연스럽게 연기하며 읽으세요:\n\n"
)

SCENES = {
    "s01": "타자가 한 경기에서 단타, 2루타, 3루타, 홈런을 전부 다 칩니다. 이게 가능할까요? 노히터만큼 보기 힘들다는 기록. 오늘은 사이클링 히트 이야기입니다.",
    "s02": "사이클링 히트, 말 그대로예요. 한 경기에서 네 종류 안타를 하나씩 다 치면 됩니다. 순서요? 상관없습니다. 자, 여기서 재밌는 게 뭐냐면요. 순서대로 치면 이름이 따로 있어요. 내추럴 사이클링 히트.",
    "s03": "그런데 이거 은근 헷갈리시죠? 사이클링 히트는 사실 정식 영어가 아닙니다. 미국에서는 히트 포 더 사이클, 그러니까 사이클을 완성한다고 말해요.",
    "s04": "이 말이 처음 활자로 등장한 건 1933년, 워싱턴포스트였습니다. 지미 폭스의 대기록을 소개하면서였죠. 기록 자체는 훨씬 전인 1882년, 커리 폴리가 최초였습니다.",
    "s05": "얼마나 귀하냐면요. 140년 넘는 메이저리그 역사에서 400번이 채 안 나왔습니다. 노히터급 희귀 기록이라는 말, 과장이 아니에요.",
    "s06": "그럼 우리 KBO에선 어땠을까요? 놀랍게도 원년, 1982년 6월 12일에 바로 나왔습니다. 삼성 오대석 선수가 부산 구덕구장에서 삼미를 상대로 해냈죠.",
    "s07": "그리고 2024년 7월 23일, 광주. KIA 김도영 선수가 역사를 새로 씁니다. 1회 단타, 3회 2루타, 5회 3루타. 그리고 6회, 타구가 담장을 넘어갑니다.",
    "s08": "단타부터 홈런까지 순서대로, 그것도 단 네 타석 만에. KBO 42년 역사상 처음 나온 기록이었습니다. 이때 김도영 선수 나이, 겨우 스무 살이었어요.",
    "s09": "마지막으로, 이건 몰랐죠? 사이클링 히트의 최대 관문은 홈런이 아니라 3루타입니다. 발이 느리면 절대 못 만드는 안타거든요. 그래서 힘 좋은 거포보다, 발 빠른 교타자에게 더 자주 나옵니다.",
    "s10": "정리하면 사이클링 히트는 네 종류 안타를 한 경기에 모두 담는, 야구에서 가장 귀한 기록 중 하나입니다. 다음 편에서는 이것보다 더 귀하다는 노히터를 다뤄볼게요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
                    sys.exit(f"{sid}: quota exceeded - stop")
                time.sleep(5 * (attempt + 1))
        else:
            sys.exit(f"{sid}: all retries failed")

    print("TTS DONE")
