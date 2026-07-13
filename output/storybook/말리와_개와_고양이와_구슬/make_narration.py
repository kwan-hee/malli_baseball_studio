# 말리와 개와 고양이와 구슬 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 여우가 구슬을 훔치는 장면은 장난스럽고 아슬아슬하게, "
    "강을 건너는 장면은 씩씩하고 신나게, "
    "구슬이 강물에 퐁당 빠지는 장면은 깜짝 놀라게, "
    "서로 탓하지 않고 다시 찾는 장면은 따뜻하고 뭉클하게, "
    "구슬을 되찾는 장면은 기쁨이 터지듯 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 씩씩한 개 누렁이랑 새침한 고양이 나비가 나오는 신나는 보물찾기 이야기를 가져왔어요. 반짝반짝 빛나는 요술 구슬이 사라졌거든요! 구슬아, 구슬아, 어디 있니? 자, 우리 같이 찾으러 가볼까요?",
    "s02": "옛날 옛적, 강가 마을에 마음씨 좋은 할아버지와 할머니가 살았어요. 집에는 씩씩한 개 누렁이와 새침한 고양이 나비도 함께 살았지요. 이 집에는 아주 특별한 보물이 하나 있었어요. 바로 반짝반짝 요술 구슬! 구슬을 살살 쓰다듬으면, 쌀독에는 쌀이 가득가득, 마당에는 감이 주렁주렁 열렸답니다. 모두모두 사이좋게, 행복하게 살았어요.",
    "s03": "그런데 어느 날 밤, 심술쟁이 여우가 살금살금 담을 넘어왔어요. 어머나, 저를 어째! 여우는 요술 구슬을 몰래 안고, 강 건너 자기 굴로 쌩 하고 달아나 버렸어요. 다음 날 아침, 할아버지와 할머니는 그만 풀이 푹 죽었지요. 그때 누렁이와 나비가 서로 마주 봤어요. 걱정 마세요! 우리가 구슬을 찾아올게요! 멍멍! 야옹!",
    "s04": "누렁이와 나비는 강가로 달려갔어요. 앗, 그런데 어쩌죠? 고양이 나비는 헤엄을 못 치는걸요. 그러자 누렁이가 씩 웃으며 말했어요. 걱정 마, 나비야. 내 등에 타! 나비는 누렁이 등에 폴짝 올라탔지요. 첨벙첨벙, 첨벙첨벙! 누렁이는 힘차게 강을 건넜답니다. 구슬아, 구슬아, 어디 있니? 조금만 기다려!",
    "s05": "친구들, 잠깐만요! 말리가 한 가지 알려줄게요. 누렁이는 헤엄을 잘 치고요, 나비는 살금살금 걷기랑 쥐 친구들이랑 이야기하는 걸 잘해요. 서로 잘하는 게 다르죠? 그래서 둘이 함께라면 못 할 게 없는 거예요! 어라, 벌써 여우네 굴 앞에 도착했나 봐요. 쉿, 조용조용!",
    "s06": "여우네 굴 앞에서, 나비가 쥐 친구들을 살짝 불렀어요. 쥐 친구들아, 부탁이 있어. 우리 요술 구슬 좀 찾아 줄래? 착한 쥐 친구들은 고개를 끄덕끄덕, 찍찍! 좁은 문틈으로 쏙쏙 들어가서는, 데굴데굴 구슬을 굴려서 가지고 나왔어요. 와, 찾았다, 찾았다! 구슬아, 구슬아, 거기 있었구나! 쥐 친구들아, 정말 정말 고마워!",
    "s07": "이제 신나게 집으로 갈 시간! 나비가 구슬을 입에 꼭 물고, 누렁이 등에 올라탔어요. 첨벙첨벙, 강을 건너는데, 누렁이가 자꾸자꾸 물어봤어요. 나비야, 구슬 잘 있니? 나비야, 구슬 잘 있어? 나비는 참다참다 그만, 응, 잘 있어! 하고 대답해 버렸지 뭐예요. 그 순간, 퐁당! 아이쿠, 구슬이 강물 속으로 빠지고 말았어요!",
    "s08": "어떡해, 어떡해! 나비 눈에 눈물이 그렁그렁 맺혔어요. 미안해, 누렁아. 나 때문에 구슬이 빠졌어. 그런데 누렁이는 화내지 않았어요. 아니야, 내가 자꾸 물어봐서 그런걸. 괜찮아, 우리 같이 다시 찾자! 둘은 강가에서 첨벙첨벙 물고기를 잡았어요. 그런데 어라? 통통한 물고기 배가 반짝반짝 빛나는 거예요. 세상에! 물고기가 구슬을 꿀꺽 삼켰던 거죠. 찾았다, 찾았다! 구슬아, 구슬아, 거기 있었구나!",
    "s09": "누렁이와 나비는 신이 나서 집으로 달려갔어요. 할아버지, 할머니! 저희가 구슬을 찾아왔어요! 멍멍! 야옹! 할아버지와 할머니는 둘을 꼭 안아 주었지요. 아이고, 우리 누렁이, 우리 나비, 정말 정말 장하다! 그날 밤, 집은 다시 반짝반짝 빛났고요. 누렁이와 나비는 나란히 앉아, 반짝이는 밤하늘 별을 오래오래 바라봤답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 나비가 실수로 구슬을 퐁당 빠뜨렸지만, 누렁이는 탓하지 않았어요. 괜찮아, 우리 같이 다시 하자! 말리는 이 말이 요술 구슬보다 더 반짝이는 보물 같아요. 여러분도 친구가 실수하면, 괜찮아, 하고 꼭 말해 주세요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
