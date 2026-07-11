# 말리와 브레멘 음악대 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, r"C:\youtube_longform_agent")
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
    "말리(강아지)의 대사는 신나고 귀엽게, 당나귀는 든든하게, 동물들이 힘을 합치는 장면은 씩씩하고 신나게, "
    "'히힝 멍멍 야옹 꼬끼오' 합창 부분은 우렁차고 재미있게, "
    "심술쟁이들이 놀라 도망치는 장면은 다급하고 익살스럽게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 신나는 이야기를 가져왔어요. 나이가 많다고 쫓겨날 뻔한 동물 친구 넷이, 힘을 합쳐서 멋진 일을 해낸대요. 브레멘이라는 곳으로 음악을 하러 떠나는 친구들이죠. 자, 우리 같이 따라가 볼까요?",
    "s02": "옛날 옛적에, 늙은 당나귀 한 마리가 살았어요. 이제 힘이 없어서 일을 못 하게 되자, 주인이 당나귀를 쫓아내려고 했지 뭐예요. 당나귀는 슬펐지만, 이렇게 생각했어요. 그래, 나는 목소리가 크니까, 브레멘에 가서 멋진 음악가가 되는 거야! 당나귀는 씩씩하게 길을 떠났어요.",
    "s03": "터덜터덜 길을 걷는데, 저기 지친 개 한 마리가 앉아 있었어요. 개도 나이가 많다고 쫓겨난 참이었죠. 당나귀가 다정하게 말했어요. 친구야, 우리 같이 브레멘 가서 음악하자! 개는 반가워서 멍멍 짖었어요. 그렇게 둘이 나란히 걸어갔답니다.",
    "s04": "조금 더 가니까, 이번엔 시무룩한 고양이가 있었어요. 고양이도 이가 빠져서 쥐를 못 잡는다고 구박받던 참이었죠. 당나귀랑 개가 말했어요. 고양이야, 너도 우리랑 같이 가자! 야옹, 고양이도 반가워서 폴짝 따라나섰어요. 이제 셋이 되었네요.",
    "s05": "그런데 어디선가, 꼬끼오! 하는 소리가 들렸어요. 담장 위에서 수탉이 목청껏 울고 있었죠. 수탉도 곧 쫓겨날 신세였어요. 친구들이 외쳤어요. 수탉아, 넷이 모이면 더 멋진 음악대가 될 거야! 우와, 이제 당나귀, 개, 고양이, 수탉. 넷이 다 모였어요! 말리도 너무너무 신나요!",
    "s06": "넷이 걷다 보니, 어느새 해가 뉘엿뉘엿 저물었어요. 깊고 깜깜한 숲이었죠. 배도 고프고 다리도 아팠어요. 그때, 저 멀리 반짝! 하고 작은 불빛 하나가 보였어요. 작은 오두막이었어요. 친구들은 살금살금 그 집으로 다가갔답니다.",
    "s07": "키가 제일 큰 당나귀가 창문 너머를 살짝 들여다봤어요. 그랬더니, 세상에! 맛있는 음식이 상다리가 부러지게 잔뜩 차려져 있었어요. 그런데 그 앞엔, 심술궂은 아저씨들이 왁자지껄 앉아 있지 뭐예요. 배고픈 친구들은 머리를 맞대고 꾀를 하나 냈어요.",
    "s08": "친구들은 살금살금 창문 앞에 섰어요. 당나귀 등에 개가 올라타고, 개 등에는 고양이가, 고양이 등에는 수탉이 폴짝! 높다랗게 탑을 쌓았죠. 그러고는 다 같이, 하나, 둘, 셋! 히힝! 멍멍! 야옹! 꼬끼오! 세상에서 제일 크고 우렁찬 노래를 불렀어요!",
    "s09": "그 소리가 어찌나 크고 이상하던지! 심술궂은 아저씨들은 소스라치게 놀랐어요. 으악, 괴물이다! 아저씨들은 걸음아 날 살려라 하고 숲속으로 후다닥 도망쳐 버렸어요. 친구들은 서로를 보며 깔깔 웃었어요. 그리고 따뜻한 오두막과 맛있는 음식이, 전부 친구들 차지가 되었답니다!",
    "s10": "당나귀도, 개도, 고양이도, 수탉도, 이제 아무도 외롭지 않았어요. 넷이 함께라면 무엇이든 할 수 있었으니까요. 말리는 오늘 알았어요. 혼자서는 어려운 일도, 친구들과 힘을 합치면 거뜬히 해낼 수 있다는 걸요! 여러분도 친구랑 손을 잡으면 못 할 게 없어요. 오늘 이야기 재미있었죠? 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
            write_wav(pcm, FULL_WAV)
            dur = len(pcm) / (SR * BITS // 8 * CH)
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
