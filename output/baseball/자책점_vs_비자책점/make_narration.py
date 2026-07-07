# 자책점 vs 비자책점 — 나레이션 생성: Gemini TTS Puck + 해설자 연기 지시
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
    "s01": "투수가 홈런을 맞았습니다. 점수판엔 3점이 올라갔어요. 그런데 이 투수 방어율은 그대로입니다. 점수는 났는데, 투수 기록에는 없는 점수. 오늘은 자책점과 비자책점 이야기입니다.",
    "s02": "자책점, 말 그대로 스스로 책임지는 점수예요. 안타, 볼넷, 폭투처럼 투수 자신의 공 때문에 난 점수죠. 반대로 야수가 공을 빠뜨려서 난 점수는요? 그건 투수 잘못이 아니잖아요. 그래서 비자책점입니다.",
    "s03": "자, 여기서 재밌는 게 뭐냐면요. 이걸 정하는 사람이 심판이 아니라는 겁니다. 기록원이 정해요. 기록원은 실책이 없었다면 이 이닝이 어떻게 흘러갔을까, 머릿속으로 경기를 통째로 다시 돌립니다. 이걸 이닝의 재구성이라고 부릅니다.",
    "s04": "이 규칙, 왜 생겼을까요? 옛날 야구는 선발투수가 처음부터 끝까지 던졌습니다. 그러니 승패 기록만 봐도 충분했죠.",
    "s05": "그런데 1900년대, 구원투수라는 게 등장합니다. 한 경기 실점을 여러 투수가 나눠 책임져야 하는 시대가 온 거죠. 그래서 1912년, 메이저리그가 자책점을 공식 기록으로 채택합니다.",
    "s06": "2019년 류현진 선수 기억나시죠? 7월 15일 경기에서 안타로 기록됐던 타구 하나가, 보름이 지나서 실책으로 정정됩니다. 그 순간 자책점 2점이 사라졌어요. 방어율이 1.66에서 1.53으로. 경기장이 아니라 책상 위에서 바뀐 겁니다.",
    "s07": "이거 은근 헷갈리시죠? 예를 하나 볼게요. 2아웃에서 야수가 평범한 뜬공을 떨어뜨립니다. 원래라면 이닝이 끝났어야 했죠. 그런데 다음 타자가 홈런을 칩니다. 이 홈런, 몇 점이 자책일까요? 정답은 0점. 실책만 없었으면 아예 없었을 이닝이니까요.",
    "s08": "하나 더. 폭투와 포일, 비슷해 보이죠? 운명은 정반대입니다. 투수가 잘못 던진 폭투는 자책. 포수가 잘못 받은 포일은 비자책. 던진 사람 잘못이냐, 받는 사람 잘못이냐의 차이예요.",
    "s09": "마지막으로, 이건 몰랐죠? 투수한테는 자책인데 팀에는 비자책인 점수도 있습니다. 반자책이라고 하는데요. 구원투수는 자기가 올라오기 전에 나온 실책의 혜택을 못 받거든요. 참고로 KBO는 1987년부터 지금의 메이저리그식 계산법을 씁니다.",
    "s10": "정리하면, 자책점은 투수가 온전히 자기 공으로 내준 점수만 셉니다. 그리고 그 판단은 기록원의 몫이죠. 다음 편에서는 그 기록원이 정하는 실책 판정 기준을 다뤄볼게요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 만나요!",
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
