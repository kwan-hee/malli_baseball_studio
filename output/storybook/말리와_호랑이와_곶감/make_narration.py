# 말리와 호랑이와 곶감 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
import base64
import os
import sys
import time
import wave
from pathlib import Path

# Whisper가 subprocess로 ffmpeg를 호출 — WinGet 설치 경로를 PATH에 추가
FFMPEG_DIR = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

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
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 호랑이는 처음엔 웅장하지만 겁먹은 뒤로는 벌벌 떨며 우스꽝스럽게, "
    "엄마는 다정하게, 아기 울음 '으앙'은 실감나게, "
    "호랑이가 놀라 도망치는 장면은 다급하고 익살스럽게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 깊고 깊은 산속 마을로 왔어요. 옛날 옛적에, 이 마을에 아주 커다란 호랑이가 살았대요. 어흥! 그런데요, 이 무서운 호랑이가 그만, 곶감이라는 걸 세상에서 제일 무서워하게 됐다지 뭐예요? 대체 무슨 일이 있었을까요? 우리 같이 들어봐요!",
    "s02": "깊은 산속에, 커다란 호랑이 한 마리가 살았어요. 어느 추운 겨울밤이었어요. 호랑이는 배가 너무너무 고팠어요. 꼬르륵! 먹을 걸 찾아서, 살금살금 마을로 내려왔지요. 커다란 발로 살금, 살금. 호랑이는 불이 켜진 작은 집으로 다가갔어요.",
    "s03": "그 집에서는요, 아기가 앙앙 울고 있었어요. 으앙! 으앙! 아기는 좀처럼 울음을 그치지 않았어요. 호랑이는 창문 밖에서 가만히 귀를 기울였어요. 안에서 다정한 엄마 목소리가 들렸거든요.",
    "s04": "아가야, 울지 마렴. 저기 밖에 무서운 호랑이가 왔단다! 엄마가 그렇게 말했어요. 호랑이는 깜짝 놀랐어요. 어? 저거 내 이야기잖아? 이제 아기가 뚝 그치겠지! 그런데 이게 웬일이에요? 아기는 더 크게 울었어요. 으아앙!",
    "s05": "어라? 무서운 호랑이가 왔다는데 아기가 왜 안 그칠까요? 호랑이도 고개를 갸웃, 나 말리도 고개를 갸웃! 흐음... 그런데 바로 그때, 엄마가 아주 신기한 말을 했어요. 우리 같이 들어봐요!",
    "s06": "아가야, 여기 곶감! 달콤한 곶감이 있네! 엄마가 그러자, 세상에! 아기가 울음을 뚝 그쳤어요. 방금까지 앙앙 울던 아기가, 순식간에 조용해졌지 뭐예요. 창밖의 호랑이는 그 소리를 다 듣고 있었어요.",
    "s07": "호랑이는 눈이 휘둥그레졌어요. 뭐, 뭐라고? 내가 왔다고 해도 안 그치던 아기가, 곶감이라니까 뚝 그쳤어? 그럼 곶감은... 나보다 훨씬훨씬 무서운 놈인가 봐! 호랑이는 오들오들 떨기 시작했어요. 그 무서운 곶감이 근처에 있을까 봐서요.",
    "s08": "바로 그때였어요. 길을 잃은 나그네 한 사람이, 어두워서 앞이 잘 보이지 않았어요. 나그네는 커다란 호랑이를 소인 줄 알고, 슬그머니 그 등에 올라탔지 뭐예요! 호랑이는 소스라치게 놀랐어요. 으악! 드디어 그 무서운 곶감이 내 등에 올라탔구나!",
    "s09": "호랑이는 곶감이 자기를 잡으러 온 줄 알고, 걸음아 날 살려라 하고 냅다 내달렸어요! 다다다다! 어찌나 빨리 뛰었는지, 등에 탔던 나그네는 데굴데굴 굴러떨어졌어요. 다행히 폭신한 풀밭이라 하나도 안 다쳤지요. 호랑이는 뒤도 안 돌아보고, 산 넘고 물 건너 멀리멀리 도망쳤답니다.",
    "s10": "그 뒤로 호랑이는 무서워서, 다시는 마을에 내려오지 않았대요. 곶감이 뭔지도 모르면서 말이에요! 말리는 이제 알아요. 잘 알아보지도 않고 지레 겁부터 먹으면, 이렇게 우스운 일이 생긴다는 걸요. 무서울 땐, 그게 정말 무서운 건지 먼저 살펴봐요! 오늘 이야기 재미있었죠? 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
