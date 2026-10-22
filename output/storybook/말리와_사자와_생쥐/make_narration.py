# 말리와 사자와 생쥐 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 사자는 크고 우렁차지만 다정하게, "
    "생쥐는 작고 여리게, '쓱싹, 쓱싹!' 소리는 부지런하고 리듬감 있게, "
    "그물이 끊어지고 사자가 풀려나는 순간은 신나게 외치듯. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 깊고 푸른 숲으로 놀러 가는 날이에요. 이 숲에는요, 아주아주 큰 친구랑, 아주아주 작은 친구가 살고 있대요. 둘이 무슨 일을 겪게 될까요? 우와, 나도 너무너무 궁금하다!",
    "s02": "숲 속에는 커다란 사자가 살았어요. 갈기가 멋지고, 목소리는 우렁찼지요. 어흥! 오늘도 사자는 따뜻한 햇살 아래에서 쿨쿨, 낮잠을 자고 있었어요. 새근새근, 아주 기분이 좋았답니다.",
    "s03": "그때, 쪼끄만 생쥐가 그만, 잠든 사자 코 위를 지나가고 말았어요. 사자가 눈을 번쩍 떴어요. 누구야? 내 낮잠을 깨운 게 누구야? 어이쿠, 큰일 났다! 생쥐는 그만 사자의 커다란 앞발에 붙잡히고 말았어요.",
    "s04": "생쥐는 오들오들 떨면서 빌었어요. 사자님, 사자님, 한 번만 살려 주세요! 제가 언젠가 꼭, 은혜를 갚을게요! 사자는 껄껄 웃었어요. 너처럼 조그만 생쥐가? 하하, 귀여운걸. 좋아, 오늘은 특별히 봐주마! 그러고는 살며시 앞발을 열어 주었어요.",
    "s05": "생쥐는 꾸벅 인사하고 쪼르르 달아났어요. 말리는 곰곰이 생각했어요. 저렇게 작은 생쥐가, 정말 크고 힘센 사자를 도울 수 있을까? 흐음... 우리, 끝까지 지켜봐요!",
    "s06": "며칠이 지났어요. 사자가 숲을 거닐다가, 그만! 장난꾸러기들이 몰래 쳐 놓은 튼튼한 그물에 걸리고 말았어요. 아무리 힘을 써도 그물은 풀리지 않았어요. 어흥! 어흥! 사자는 그물 속에서 이리저리 버둥거렸어요.",
    "s07": "사자는 큰 소리로 외쳤어요. 누구 없어요? 나 좀 도와주세요! 하지만 숲은 조용하기만 했어요. 아무도, 아무도 오지 않았어요. 힘이 센 사자도 이번엔 눈물이 핑 돌았답니다.",
    "s08": "바로 그때! 어디선가 쪼르르, 생쥐가 달려왔어요. 사자님! 제가 왔어요! 생쥐는 작고 뾰족한 이빨로 그물을 갉기 시작했어요. 쓱싹, 쓱싹! 쓱싹, 쓱싹! 조그만 이빨로 쉬지 않고, 갉고 또 갉았어요.",
    "s09": "그러자, 뚝! 뚜두둑! 드디어 그물이 툭 끊어졌어요! 사자가 그물에서 쑥 빠져나왔어요. 우와, 해냈다! 사자는 생쥐를 살포시 안아 주었어요. 고마워, 작은 친구야! 네가 나를 구해 줬구나! 정말정말 고마워!",
    "s10": "사자와 생쥐는 그날부터 둘도 없는 친구가 되었어요. 말리는 이제 알아요. 아무리 작은 친구라도, 아주 큰 도움이 될 수 있다는 걸요. 오늘 이야기 어땠어요? 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 그럼 다음에 또 만나요. 안녕!",
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
