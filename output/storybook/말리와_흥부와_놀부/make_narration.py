# 말리와 흥부와 놀부 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 흥부의 대사는 맑고 따뜻하게, "
    "놀부의 대사는 얄밉고 우스꽝스럽게, 제비의 대사는 작고 귀엽게, "
    "아기 제비를 치료하는 장면은 다정하게, "
    "박에서 보물이 쏟아지는 장면은 깜짝 놀라며 신나게, "
    "빈 박과 반성 장면은 잔잔하고 뭉클하게, "
    "형제가 화해하는 장면은 따뜻하게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 제비가 물어다 준 신기한 박씨 이야기, 흥부와 놀부를 가져왔어요. 조그만 박씨 하나에서 무엇이 나올까요? 자, 우리 같이 옛날 옛적 마을로 떠나 볼까요?",
    "s02": "옛날 옛적, 어느 마을에 흥부와 놀부 형제가 살았어요. 동생 흥부는 가난했지만 마음씨가 참 착했지요. 형 놀부는 부자였지만 심술쟁이였어요. 흥, 내 것은 하나도 못 줘! 놀부네 곳간에는 쌀이 가득했지만, 흥부네 집은 늘 배가 고팠지요. 그래도 흥부는 웃으며 말했답니다. 괜찮아요, 형님. 우리는 서로 도우며 살아요.",
    "s03": "어느 봄날, 흥부네 처마 밑 둥지에서 아기 제비가 툭 떨어졌어요. 짹짹, 짹짹! 다리를 다친 아기 제비가 울고 있었지요. 아이고, 아프겠다! 흥부는 아기 제비 다리를 헝겊으로 살살 감아 주었어요. 제비야, 제비야, 어서 나아라! 며칠 뒤, 다 나은 아기 제비는 하늘로 포르르 날아올라, 고맙다고 지붕 위를 빙글빙글 돌았답니다.",
    "s04": "다음 해 봄이 되었어요. 그 제비가 흥부네 집으로 다시 날아왔지 뭐예요! 입에는 조그만 박씨 하나를 물고서요. 고마워요, 흥부 아저씨! 흥부네 가족은 박씨를 마당에 심었어요. 여름 내내 박 넝쿨은 무럭무럭, 쑥쑥 자랐지요. 가을이 되자, 지붕 위에 집채만 한 박이 주렁주렁 열렸답니다.",
    "s05": "친구들, 잠깐만요! 말리가 물어볼게요. 제비는 왜 흥부에게 박씨를 줬을까요? 맞아요. 흥부가 아무 대가 없이 아기 제비를 도와줬으니까요. 착한 일은 꼭 돌아오나 봐요. 그럼 저 커다란 박 속에는 뭐가 들었을까요? 쉿, 같이 열어 봐요!",
    "s06": "흥부네 가족이 톱을 들고 박을 탔어요. 쓱싹쓱싹, 어기여차! 펑! 박이 쩍 갈라지자, 세상에! 반짝반짝 금은보화가 와르르 쏟아져 나왔어요. 쌀도, 비단도, 고운 옷도 가득가득! 와, 이게 다 뭐야! 흥부네 가족은 얼싸안고 덩실덩실 춤을 추었답니다. 흥부는 보물을 보고도 형님 생각을 먼저 했어요. 우리 형님네도 갖다 드리자!",
    "s07": "이 소문을 들은 놀부가 배가 아팠어요. 흥, 나도 제비를 도와주면 되지! 놀부는 멀쩡한 제비를 붙잡아 억지로 붕대를 칭칭 감았어요. 자, 이제 박씨를 물고 와라! 제비는 고개를 갸우뚱갸우뚱. 아저씨, 저는 다치지도 않았는걸요?",
    "s08": "놀부네 지붕에도 박이 열리긴 했어요. 놀부는 신이 나서 박을 탔지요. 쓱싹쓱싹, 어기여차! 펑! 그런데 박 속은 텅텅 비어 있었어요. 먼지만 풀풀 날렸지요. 두 번째 박도, 세 번째 박도 텅텅! 놀부는 그제야 고개를 푹 숙였어요. 욕심만 부리고 거짓으로 흉내만 냈구나. 미안해, 제비야.",
    "s09": "그 모습을 본 흥부가 달려와 놀부 손을 꼭 잡았어요. 형님, 괜찮아요. 우리 보물을 나눠요! 흥부는 쌀도 비단도 형과 사이좋게 나누었지요. 고맙다, 흥부야. 이제 형도 착하게 살게! 그날 밤, 두 형제는 함께 잔치를 열고 덩실덩실 춤을 추었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 착한 일은 박씨처럼 자라서 커다란 복이 된대요. 우리도 흥부처럼 작은 친구들을 살살 도와줘요. 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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

    # 자막 실측 생성용(A안, 2026-07-15) — compose.py 가 글자수 비례 대신 이 실측으로 SRT 생성
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
