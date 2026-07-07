# 말리와 커다란 순무 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 할아버지·할머니는 다정하게, "
    "'영차, 영차! 쑤욱, 쑤욱!' 후렴은 힘차고 리듬감 있게, "
    "순무가 뽑히는 순간은 신나게 외치듯. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 시골 할아버지 밭에 놀러 가는 날이에요. 할아버지 밭에는 맛있는 게 아주 많거든요. 밭에서 무슨 일이 기다리고 있을까요? 우와, 궁금하다!",
    "s02": "할아버지는 봄에 순무 씨앗을 심었어요. 순무야, 순무야, 크게 크게 자라라! 달콤하고 튼튼하게 자라라! 여름 내내 물도 주고, 노래도 불러 주었지요.",
    "s03": "우와! 저것 좀 봐요! 순무가 산처럼 커졌어요! 할아버지도 깜짝 놀랐어요. 세상에, 이렇게 큰 순무는 처음인걸! 말리도 눈이 동그래졌어요. 정말정말 크다!",
    "s04": "할아버지가 순무를 잡았어요. 영차, 영차! 쑤욱, 쑤욱! 그런데 순무는 꿈쩍도 안 했어요. 한 번 더! 영차, 영차! 쑤욱, 쑤욱! 아이고, 순무가 힘이 세도 너무 세구나!",
    "s05": "제가 도울게요, 멍멍! 할머니도 달려오셨어요. 나도 도우마! 다 같이, 영차, 영차! 쑤욱, 쑤욱! 그래도 순무는 꿈쩍도 안 했어요.",
    "s06": "지나가던 토끼가 말했어요. 나도 같이 할래! 야옹 고양이도 왔어요. 나도 나도! 영차, 영차! 쑤욱, 쑤욱! 영차, 영차! 쑤욱, 쑤욱! 아직도 순무는 꿈쩍도 안 해요. 아이고, 어떡하지?",
    "s07": "그때, 아주 쪼끄만 생쥐가 왔어요. 나도 도와줄래! 에이, 넌 너무 작잖아. 고양이가 웃었어요. 그러자 말리가 말했어요. 아니야! 작은 힘도 소중한걸! 우리 같이 하자! 생쥐가 방긋 웃었어요. 고마워, 말리야!",
    "s08": "모두 함께 소리쳤어요. 영차, 영차! 쑤욱, 쑤욱! 바로 그 순간! 펑! 순무가 쑥 뽑혔어요! 우와, 해냈다! 만세! 만세! 모두 함께 해냈어요!",
    "s09": "그날 저녁, 모두 모여 달콤한 순무 수프를 나눠 먹었어요. 생쥐도 어깨가 으쓱했어요. 히히, 내 힘도 보탬이 됐어! 말리는 이제 알아요. 아무리 작은 힘도, 모이고 모이면 아주아주 커진다는 걸요.",
    "s10": "오늘 이야기 어땠어요? 우리 같이 외쳐 볼까요? 영차, 영차! 쑤욱, 쑤욱! 참 잘했어요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 그럼 다음에 또 만나요. 안녕!",
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
