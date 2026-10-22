# 말리와 아기 돼지 삼형제 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
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
    "말리(강아지)의 대사는 신나고 귀엽게, 아기 돼지들은 명랑하고 귀엽게, "
    "'안 돼요, 안 돼요, 절대 안 돼요!' 후렴은 씩씩하고 당차게, "
    "늑대의 '아기 돼지야, 문 열어라!'는 굵고 우스꽝스럽게, "
    "늑대가 후우~ 하고 부는 장면은 과장되고 익살스럽게, "
    "늑대가 지쳐 도망치는 장면은 다급하고 우스꽝스럽게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 귀여운 아기 돼지 삼형제 이야기를 가져왔어요. 삼형제가 집을 지을 건데요, 과연 누구 집이 제일 튼튼할까요? 후후~ 하고 바람을 부는 커다란 늑대도 나온대요. 자, 우리 같이 가볼까요?",
    "s02": "옛날 옛적, 아기 돼지 삼형제가 엄마 돼지랑 살았어요. 어느 날, 엄마가 말했어요. 얘들아, 이제 다 컸으니 각자 집을 지어 보렴. 튼튼하게 지어야 한다! 네! 삼형제는 씩씩하게 대답하고, 신나게 길을 떠났어요. 뒤뚱뒤뚱, 뒤뚱뒤뚱.",
    "s03": "첫째 돼지는 빨리 놀고 싶어서 마음이 급했어요. 옳지! 가볍고 빠른 지푸라기로 짓자! 슥삭슥삭, 뚝딱! 반나절 만에 노란 지푸라기 집이 완성됐어요. 야호, 이제 실컷 놀아야지! 첫째는 데굴데굴 구르며 신나게 놀았답니다.",
    "s04": "둘째 돼지도 노는 게 좋았어요. 나무로 지으면 금방이겠지? 뚝딱뚝딱, 쾅쾅! 하루 만에 나무 집이 완성됐어요. 히히, 지푸라기보다는 튼튼하겠지? 둘째도 첫째랑 같이 폴짝폴짝 뛰어놀았어요.",
    "s05": "그런데 막내 돼지는요? 어라, 무거운 벽돌을 낑낑 나르고 있네요. 형들이 놀렸어요. 야, 그렇게 느려서 언제 다 짓니? 하지만 막내는 씩 웃기만 했어요. 친구들, 막내는 왜 힘들고 무거운 벽돌을 골랐을까요?",
    "s06": "막내 돼지는 며칠 밤낮을 열심히 일했어요. 벽돌을 차곡차곡, 차곡차곡. 땀이 뻘뻘 났지만 멈추지 않았죠. 그리고 마침내! 빨간 벽돌집이 완성됐어요. 아무리 센 바람이 불어도 끄떡없는, 아주아주 튼튼한 집이었답니다.",
    "s07": "그때, 커다란 늑대가 나타났어요! 늑대는 첫째네 지푸라기 집 앞에서 소리쳤어요. 아기 돼지야, 문 열어라! 안 돼요, 안 돼요, 절대 안 돼요! 그러자 늑대가 숨을 크게 들이쉬고, 후우~! 세상에, 지푸라기 집이 훨훨 날아가 버렸어요! 첫째는 걸음아 날 살려라, 둘째네 집으로 뛰었어요.",
    "s08": "늑대는 나무 집으로 쫓아왔어요. 아기 돼지야, 문 열어라! 안 돼요, 안 돼요, 절대 안 돼요! 후우~! 후우~! 늑대가 두 번 불자, 나무 집이 삐거덕삐거덕 흔들리더니 와르르 무너졌어요! 첫째와 둘째는 눈이 동그래져서, 막내네 벽돌집으로 후다닥 달려갔답니다.",
    "s09": "늑대가 벽돌집 앞에 떡 버티고 섰어요. 후우! 후우! 후우~! 있는 힘껏 불고 또 불었지만, 벽돌집은 꿈쩍도 하지 않았어요. 늑대는 볼이 빵빵해지도록 불다가, 그만 어지러워서 데굴데굴 굴렀지 뭐예요. 에구구, 못 당하겠다! 늑대는 꼬리를 내리고 걸음아 날 살려라 도망쳐 버렸어요! 삼형제는 얼싸안고 폴짝폴짝 뛰었답니다.",
    "s10": "첫째와 둘째가 막내에게 말했어요. 막내야, 고마워. 우리도 이제 벽돌로 튼튼하게 지을게! 셋은 벽돌집에서 오래오래 사이좋게 살았어요. 말리는 오늘 알았어요. 조금 힘들어도 차근차근 튼튼하게 준비하면, 무서운 일이 와도 끄떡없다는 걸요! 오늘 이야기 재미있었죠? 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
