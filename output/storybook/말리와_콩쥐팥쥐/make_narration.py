# 말리와 콩쥐팥쥐 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 콩쥐의 대사는 맑고 씩씩하게, "
    "새엄마와 팥쥐가 일을 시키는 장면은 얄밉고 우스꽝스럽게, "
    "두꺼비와 참새들이 도와주는 장면은 신나고 사랑스럽게, "
    "꽃신이 개울에 빠지는 장면은 깜짝 놀라게, "
    "원님의 대사는 점잖고 따뜻하게, 사과와 화해 장면은 잔잔하고 뭉클하게, "
    "잔치 장면은 흥겹고 따뜻하게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 예쁜 꽃신 한 짝이 퐁당 빠지는 이야기, 콩쥐팥쥐를 가져왔어요. 착하고 부지런한 콩쥐에게 어떤 신기한 일이 생길까요? 자, 우리 같이 옛날 옛적 마을로 떠나 볼까요?",
    "s02": "옛날 옛적, 어느 마을에 콩쥐라는 착한 아이가 살았어요. 그런데 새엄마와 동생 팥쥐는 놀기만 하면서, 힘든 일은 몽땅 콩쥐에게 시켰지요. 콩쥐야, 물 길어 와라! 콩쥐야, 빨래도 해라! 그래도 콩쥐는 씩씩하게 웃었어요. 괜찮아. 열심히 하다 보면 좋은 일이 생길 거야.",
    "s03": "어느 날, 콩쥐는 커다란 항아리에 물을 가득 채워야 했어요. 그런데 아무리 부어도 물이 줄줄 새는 거예요. 항아리 바닥에 구멍이 뻥 뚫려 있었거든요. 그때, 엉금엉금 두꺼비가 나타났어요. 콩쥐야, 콩쥐야, 우리가 도와줄게! 두꺼비가 구멍을 꼭 막아 주자, 물이 찰랑찰랑 가득 찼답니다.",
    "s04": "이번에는 산더미처럼 쌓인 벼를 다 까야 했어요. 그러자 하늘에서 참새 떼가 포르르 날아왔어요. 콩쥐야, 콩쥐야, 우리가 도와줄게! 짹짹짹! 참새들이 부리로 벼 껍질을 톡톡 까 주었지요. 커다란 검은 소도 어슬렁어슬렁 와서 넓은 밭을 쓱쓱 갈아 주었어요. 고마워, 얘들아! 정말 고마워!",
    "s05": "친구들, 잠깐만요! 말리가 물어볼게요. 동물 친구들은 왜 콩쥐만 도와줬을까요? 맞아요. 콩쥐가 언제나 착한 마음으로 열심히 지냈으니까요. 착한 마음은 숨겨도 반짝반짝 보이나 봐요. 그런데 이제 더 신나는 일이 기다린대요. 쉿, 잘 들어봐요.",
    "s06": "마을에 커다란 잔치가 열리는 날이었어요. 새엄마와 팥쥐는 고운 옷을 입고 쌩 가 버렸지요. 콩쥐가 시무룩해 있는데, 동물 친구들이 다시 모여들었어요. 콩쥐야, 콩쥐야, 우리가 도와줄게! 그러자 눈앞에 고운 치마저고리와 반짝이는 꽃신이 짠 하고 나타났답니다. 와, 정말 예쁘다!",
    "s07": "콩쥐는 신이 나서 잔치에 가고 있었어요. 그런데 개울 징검다리를 건너다가, 아이쿠! 꽃신 한 짝이 개울에 퐁당 빠져 버렸어요. 어떡해, 내 꽃신! 꽃신은 데굴데굴 물길을 따라 흘러갔지요. 하지만 잔치에 늦을까 봐, 콩쥐는 한 짝만 신은 채 서둘러 가야 했어요.",
    "s08": "그때, 마을 원님이 개울가에서 반짝이는 꽃신 한 짝을 주웠어요. 이렇게 고운 꽃신이라니! 주인을 꼭 찾아 주어야겠구나. 원님은 잔치에 온 사람들에게 꽃신을 신겨 보았어요. 팥쥐도 얼른 발을 쑥 내밀었지만, 맞지 않았지요. 그런데 콩쥐가 신어 보자, 어머나! 발에 쏙 맞았답니다.",
    "s09": "원님은 콩쥐를 잔치의 주인공으로 모셨어요. 그 모습을 본 팥쥐와 새엄마는 얼굴이 빨개졌지요. 콩쥐야, 미안해. 우리가 너무 심했어. 콩쥐는 방긋 웃으며 두 사람의 손을 꼭 잡았어요. 괜찮아요. 우리 이제 같이 웃어요! 그날 밤, 모두 함께 덩실덩실 춤을 추었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 착한 마음은 꽃신보다 더 반짝반짝 빛난대요. 콩쥐처럼 착한 마음으로 지내면, 도와주는 친구들이 꼭 나타날 거예요. 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
