# 말리와 미운 오리 새끼 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 아기 오리가 슬픈 장면은 잔잔하고 애틋하게, "
    "백조를 동경하는 장면은 꿈꾸듯 설레게, "
    "물에 비친 백조를 발견하는 장면은 벅차고 놀랍게, "
    "백조들과 날아오르는 장면은 희망차고 눈부시게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 조금 특별한 아기 새 이야기를 가져왔어요. 형제들이랑 다르게 생겨서 미운 오리 새끼라고 불린 아기예요. 흑흑, 이름부터 너무 슬프죠? 그런데 있잖아요, 이 아기한테는 아주아주 놀라운 비밀이 숨어 있대요. 무슨 비밀이냐고요? 그건 끝까지 봐야 알 수 있어요! 자, 우리 같이 만나러 가볼까요?",
    "s02": "옛날 옛적, 햇살 좋은 농장 연못가에서 엄마 오리가 알을 폭 품고 있었어요. 톡, 토톡! 알에서 노란 아기 오리들이 차례차례 나왔지요. 삐약삐약, 엄마 안녕하세요! 아유, 예쁘기도 하지. 그런데 제일 크고 이상한 알 하나만 조용했어요. 엄마 오리는 고개를 갸웃갸웃했지요. 한참을 더 기다리자, 톡! 드디어 마지막 알도 깨졌답니다.",
    "s03": "어라? 마지막에 나온 아기는 정말 달랐어요. 몸집은 형제들보다 훨씬 크고, 깃털은 잿빛이었죠. 보들보들 노란 형제들 사이에서 혼자만 회색이었어요. 그래도 아기는 씩씩했어요. 뒤뚱뒤뚱, 첨벙첨벙! 엄마를 따라 헤엄도 아주 잘 쳤답니다. 엄마 오리는 말했어요. 괜찮아, 너도 내 소중한 아기란다.",
    "s04": "그런데 연못 친구들이 수군수군 거렸어요. 쟤는 왜 저렇게 생겼지? 회색이잖아, 정말 밉게 생겼다! 형제들도 같이 놀아 주지 않았어요. 저리 가, 너랑 안 놀아! 아기 오리는 너무너무 슬펐어요. 눈물이 뚝뚝 떨어졌지요. 그래서 어느 날 저녁, 아무도 모르게 조용히 연못을 떠났답니다. 훌쩍훌쩍.",
    "s05": "친구들, 잠깐만요. 말리가 물어볼게요. 다르게 생긴 게 정말 미운 걸까요? 음, 말리는 아닌 것 같은데요. 말리도 곱슬곱슬 털이 다른 강아지들이랑 다르지만, 이게 바로 말리인걸요! 저 아기한테도 분명 멋진 모습이 숨어 있을 거예요. 우리 조금만 더 지켜봐요.",
    "s06": "혼자가 된 아기 오리는 이곳저곳을 떠돌았어요. 어느새 가을이 되었지요. 그때, 하늘에서 눈부시게 하얀 새들이 훨훨 날아가는 걸 봤어요. 기다랗고 우아한 목, 커다란 하얀 날개. 세상에, 백조였어요! 우와, 나도 저렇게 아름다워지고 싶다. 아기는 목을 쭉 빼고, 한참 동안 한참 동안 하늘만 바라봤답니다.",
    "s07": "곧 추운 겨울이 왔어요. 쌩쌩, 찬바람이 불고 눈이 펑펑 내렸지요. 아기 오리는 갈대숲에 몸을 웅크리고 꾹 참았어요. 춥고 외로웠지만, 포기하지 않았어요. 하늘을 날던 하얀 새들을 떠올리면 마음이 사르르 따뜻해졌거든요. 그리고 마침내! 살랑살랑, 따뜻한 봄바람이 불어왔답니다.",
    "s08": "봄이 온 연못은 반짝반짝 빛났어요. 그때, 하얀 백조들이 아기에게 스르르 다가왔어요. 어떡해, 나같이 미운 애는 싫어할 텐데. 아기는 부끄러워서 고개를 푹 숙였죠. 그런데, 세상에! 물에 비친 자기 모습을 본 아기는 깜짝 놀랐어요. 물속에는 잿빛 아기 오리가 아니라, 눈처럼 하얗고 아름다운 백조가 있었으니까요!",
    "s09": "나, 나도 백조였구나! 백조들이 반갑게 맞아 주었어요. 어서 와, 우리랑 같이 가자. 넌 정말 아름다워! 아기 백조는 커다란 하얀 날개를 활짝 펴고, 친구들과 함께 파란 하늘로 힘차게 날아올랐어요. 연못가에 놀러 온 아이들이 소리쳤죠. 우와, 저 백조 좀 봐! 저 백조가 제일 예쁘다! 훨훨, 훨훨!",
    "s10": "미운 오리 새끼는 사실, 처음부터 아름다운 백조였던 거예요. 미운 게 아니라, 그냥 달랐던 것뿐이죠. 말리는 오늘 알았어요. 남들과 다르게 생겼다고 이상한 게 절대 아니라는 걸요. 여러분도 여러분 그대로, 아주아주 특별하고 소중하답니다! 오늘 이야기 재미있었죠? 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
