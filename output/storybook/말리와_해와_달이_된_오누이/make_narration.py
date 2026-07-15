# 말리와 해와 달이 된 오누이 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
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
    "말리(강아지)의 대사는 신나고 귀엽게, 엄마의 대사는 다정하게, "
    "호랑이의 대사는 우스꽝스럽고 능청스럽게 (무섭지 않게), "
    "오누이의 대사는 맑고 씩씩하게, 문틈 손 장면은 두근두근 긴장되지만 가볍게, "
    "하늘에 비는 장면은 간절하게, 동아줄 승천 장면은 신비롭고 웅장하게, "
    "호랑이 반성 장면은 우습고 뭉클하게, 해와 달 장면은 따뜻하게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 하늘의 해님과 달님이 어떻게 생겨났는지 알려주는 이야기, 해와 달이 된 오누이를 가져왔어요. 무서운 호랑이가 나와도 걱정 마세요. 우리 오누이는 아주 침착하거든요! 자, 깊은 산속으로 떠나 볼까요?",
    "s02": "옛날 옛적 깊은 산골에, 엄마와 오빠와 여동생이 살았어요. 어느 날 엄마가 떡을 팔러 장에 갔지요. 얘들아, 문 꼭 잠그고 있어. 금방 올게! 남매는 씩씩하게 대답했어요. 네, 엄마! 그런데 해가 뉘엿뉘엿 지는 고갯길에, 커다란 호랑이 한 마리가 떡하니 나타났지 뭐예요.",
    "s03": "어흥! 떡 하나 주면 그냥 보내주지! 엄마는 얼른 떡 하나를 던져 주었어요. 그런데 고개를 넘을 때마다 호랑이가 또 나타났어요. 어흥! 떡 하나 주면 그냥 보내주지! 떡은 금세 다 떨어졌고, 엄마는 빈 광주리만 안고 종종걸음을 쳤답니다. 욕심쟁이 호랑이는 그래도 배가 안 찼나 봐요.",
    "s04": "호랑이는 남매네 집까지 쫓아와 엄마 목소리를 흉내 냈어요. 얘들아, 엄마 왔다. 문 열어 주렴. 그런데 목소리가 이상했어요. 오빠가 말했죠. 그럼 손을 보여 주세요! 문틈으로 쑥 들어온 손은, 세상에, 털이 북슬북슬! 남매는 깜짝 놀라 뒷문으로 살금살금 빠져나갔어요.",
    "s05": "친구들, 잠깐만요! 말리가 물어볼게요. 무서운 호랑이가 문 앞에 있어요. 엉엉 울어야 할까요? 아니죠! 우리 남매처럼 침착하게 생각해야 해요. 손을 보여 달라고 한 것 보세요. 정말 똑똑하죠? 자, 남매는 이제 어디로 갔을까요?",
    "s06": "남매는 마당의 큰 나무 위로 올라갔어요. 호랑이가 나무 밑에서 어슬렁거렸지만, 남매는 울지 않고 꼭 붙어 있었지요. 그리고 하늘을 향해 두 손을 모아 빌었어요. 하늘님, 하늘님, 저희를 도와주세요! 튼튼한 동아줄을 내려 주세요!",
    "s07": "그러자 하늘에서 반짝반짝 금빛 동아줄이 스르르 내려왔어요! 남매는 동아줄을 꼭 잡았지요. 동아줄은 남매를 태우고 두둥실 하늘 높이 올라갔답니다. 구름을 지나, 별을 지나, 자꾸자꾸 위로요. 호랑이는 나무 밑에서 눈만 끔뻑끔뻑했어요.",
    "s08": "호랑이도 소리쳤어요. 나도 동아줄 줘! 하늘은 호랑이에게도 동아줄을 내려 주었지만, 어이쿠, 호랑이가 너무 무거웠나요? 줄이 뚝 끊어져서 호랑이는 폭신한 짚더미에 풍덩 빠졌답니다. 엉덩방아를 찧은 호랑이는 그제야 고개를 푹 숙였어요. 욕심부리고 겁만 줬구나. 미안해. 그리고 산속으로 슬금슬금 돌아갔지요.",
    "s09": "하늘로 올라간 남매는 어떻게 됐을까요? 여동생은 반짝반짝 해님이 되고, 오빠는 은은한 달님이 되었답니다. 낮에는 해님이, 밤에는 달님이 산골 집을 환하게 비춰 주었어요. 엄마는 하늘을 올려다보며 방긋 웃었지요. 우리 아가들, 잘 있구나!",
    "s10": "친구들, 오늘 이야기 어땠어요? 무서울수록 울지 말고, 침착하게 생각하기! 그러면 꼭 좋은 길이 열린대요. 오늘 밤 달님을 보면 오빠한테 인사해 줘요. 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
    import json

    import whisper

    print("loading whisper large-v3 ...")
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(FULL_WAV), language="ko", word_timestamps=True)
    words = [w for seg in result["segments"] for w in seg["words"]]
    if not words:
        sys.exit("whisper returned no words")

    # 자막 실측 생성용(A안) — compose.py 가 글자수 비례 대신 이 실측으로 SRT 생성
    (OUT / "word_timestamps.json").write_text(
        json.dumps([{"word": w["word"], "start": w["start"], "end": w["end"]} for w in words],
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"word_timestamps.json: {len(words)} words")

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
