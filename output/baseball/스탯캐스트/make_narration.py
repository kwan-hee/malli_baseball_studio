# 스탯캐스트 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
VOICE = "Puck"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 야구를 20년 본 동네 형 같은 유튜브 해설자입니다. "
    "친근한 존댓말로 리듬감 있게, 궁금증 유발 구간은 톤을 올리고, "
    "설명 구간은 차분하게, 자연스럽게 연기하며 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "홈런이 터지면 중계 화면에 이런 숫자가 뜨죠. 타구 속도 172킬로, 발사각 28도, 비거리 135미터. 그런데 이 숫자, 대체 누가 어떻게 재는 걸까요? 스톱워치 든 사람이 뛰어다니는 것도 아닌데 말이죠. 오늘은 이 마법의 정체, 스탯캐스트 이야기입니다.",
    "s02": "쉽게 말하면요, 스탯캐스트는 경기장에 설치된 초고속 눈이에요. 카메라랑 레이더가 공하고 선수들 움직임을 초당 수만 장씩 찍어서, 속도며 각도며 거리를 자동으로 계산해 줍니다. 사람 눈으로는 그냥 빠르다 정도지만, 이 장비는 정확히 시속 158킬로, 회전수 2400 이렇게 딱 떨어지게 알려줘요.",
    "s03": "여기서 중요한 거 하나. 스탯캐스트는 야구 규칙이 아니에요. 심판이 쓰는 것도 아니고요. 그냥 야구를 숫자로 바꿔주는 측정 장비입니다. 예전엔 감으로 보던 걸, 이제는 데이터로 딱 보여주는 거죠.",
    "s04": "이게 언제 생겼냐면요, 2015년입니다. 그전까지 야구는 감의 스포츠였어요. 저 타구가 얼마나 세게 맞았는지, 저 외야수가 얼마나 빨리 뛰었는지, 다 눈대중이었죠. 그런데 레이더 장비값이 싸지면서, 메이저리그가 전 구장에 이걸 쫙 깔아버립니다.",
    "s05": "처음엔 트랙맨이라는 레이더를 썼는데요, 2020년부터는 호크아이라는 걸로 갈아탑니다. 이 호크아이, 어디서 많이 들어보셨죠? 네, 테니스에서 공이 라인 안이냐 밖이냐 딱 잡아주는 그 기술이에요. 그걸 야구장에 그대로 가져온 겁니다.",
    "s06": "그럼 우리 KBO는요? 여기서 재밌는 게 뭐냐면, KBO가 이 트래킹 기술로 세계 최초 사고를 하나 칩니다. 바로 2024년, 자동 볼 판정 시스템, ABS예요. 기계가 공 궤적을 추적해서 스트라이크냐 볼이냐를 판별하고, 구심은 이어폰으로 그 결과를 받아 외치는 거죠. 세계 어느 프로리그도 정규시즌에 이걸 먼저 한 데가 없었어요.",
    "s07": "그리고 2025년부터는 중계 화면에도 트래킹 데이터가 뜨기 시작했어요. 잠실이랑 광주 챔피언스필드부터 말이죠. 홈런이나 삼진 리플레이 때, 구속이랑 회전수, 발사각이 화면에 쫙 그려지는 겁니다. 메이저리그에서만 보던 걸 이제 KBO 중계에서도 보게 된 거죠.",
    "s08": "자, 여기서 많이들 헷갈리시는 거 하나. 스탯캐스트가 세이버메트릭스 아니냐? 이거 다른 겁니다. 세이버메트릭스는 기록을 가지고 분석하는 생각이고요, 스탯캐스트는 그 기록을 만들어내는 장비예요. 요리로 치면 세이버는 레시피, 스탯캐스트는 신선한 재료 공급처인 셈이죠.",
    "s09": "그리고 고인물도 헷갈리는 디테일 하나. 우리 KBO가 쓰는 건 엄밀히 스탯캐스트라는 메이저리그 상표가 아니라, 트랙맨이나 피티에스라는 비슷한 트래킹 장비예요. 참고로 스탯캐스트는 공을 초당 이만 프레임으로 쫓습니다. 눈 깜짝할 사이에 이만 장을 찍는 거예요. 이거 알면 여러분도 이제 고인물입니다.",
    "s10": "정리하면, 스탯캐스트는 야구를 감에서 숫자로 바꿔놓은 장비다, 이겁니다. 다음에 중계 보다가 타구 속도 뜨면, 아 저게 트래킹이구나 하고 아는 척 한번 해보세요. 다음 편에서는 이 스탯캐스트가 만든 대표 스타, 발사각 이야기를 들고 올게요. 오늘 내용 쓸만했다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 만나요!",
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

    offsets, pos = {}, 0
    for sid, text in SCENES.items():
        offsets[sid] = pos
        pos += len(norm(text))
    total_norm = pos

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
    bps = SR * BITS // 8

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
