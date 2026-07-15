# 말리와 혹부리 영감 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 착한 혹부리 영감의 대사는 정답고 너그럽게, "
    "도깨비들의 대사는 짓궂지만 귀엽고 신나게, 욕심쟁이 영감의 대사는 우스꽝스럽게, "
    "산속 밤 장면은 조금 무서운 듯 조심스럽게, 도깨비가 몰려오는 장면은 신나고 왁자지껄하게, "
    "혹을 떼고 부자가 되는 장면은 놀랍고 기쁘게, 욕심쟁이가 혼나는 장면은 익살스럽게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 오래된 옛날이야기를 가져왔어요. 볼에 커다란 혹을 단 마음씨 착한 할아버지 이야기랍니다. 그 혹에서 아주 신기한 일이 벌어졌대요. 궁금하죠? 자, 달빛 환한 산골 마을로 함께 가 볼까요?",
    "s02": "옛날 옛적 어느 산골 마을에, 볼에 큰 혹이 달린 할아버지가 살았어요. 혹은 조금 불편했지만, 할아버지 마음씨는 온 마을에서 제일 고왔지요. 맛있는 게 생기면 이웃과 나눠 먹고, 힘든 일이 있으면 누구보다 먼저 나서서 도왔답니다. 그래서 마을 사람들은 혹부리 영감님을 참 좋아했어요.",
    "s03": "하루는 할아버지가 산에 나무를 하러 갔어요. 부지런히 일하다 보니 그만 해가 뉘엿뉘엿 저물었지 뭐예요. 집으로 돌아가기엔 너무 어두워졌어요. 그래서 할아버지는 산속에 있는 빈 오두막에 들어가 하룻밤 묵기로 했답니다. 혼자 있으니 조금 무섭기도 하고, 심심하기도 했지요.",
    "s04": "심심함을 달래려고 할아버지는 나지막이 노래를 불렀어요. 그런데 이게 웬일이에요? 노랫소리를 듣고 도깨비들이 우르르 몰려온 거예요! 뿔이 하나 달린 알록달록한 도깨비들은 하나도 무섭지 않았어요. 오히려 눈을 반짝이며 할아버지 노래에 폭 빠져서, 어깨를 들썩였답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 도깨비들은 왜 이렇게 할아버지 노래를 좋아했을까요? 맞아요, 할아버지가 즐겁고 정답게 불렀으니까요! 진심이 담긴 노래는 누구의 마음이든 활짝 열어 준답니다. 그럼 이제 어떤 일이 벌어졌을까요?",
    "s06": "도깨비 대장이 눈을 동그랗게 뜨고 물었어요. 영감님, 그 멋진 노래가 대체 어디서 나오는 거요? 할아버지는 장난스럽게 대답했지요. 허허, 바로 이 혹에서 나온다오! 그러자 도깨비들은 깜빡 속아 넘어가서, 반짝이는 보물을 잔뜩 안겨 주고는 할아버지 혹을 쏙 가져갔답니다.",
    "s07": "다음 날 아침, 할아버지가 마을로 돌아왔어요. 볼에 있던 커다란 혹이 감쪽같이 사라지고, 손에는 보물이 가득했지요. 마을 사람들은 깜짝 놀라 물었어요. 아니, 밤사이에 대체 무슨 일이 있었던 거예요? 할아버지는 지난밤 이야기를 웃으며 들려주었답니다.",
    "s08": "그런데 옆 마을에도 혹부리 영감이 한 분 살았어요. 이 할아버지는 욕심이 아주 많았지요. 소문을 듣고는 눈이 번쩍 뜨였어요. 옳지, 나도 혹을 떼고 부자가 되어야겠다! 할아버지는 그날 밤이 되기가 무섭게 산속 빈 오두막으로 달려갔답니다.",
    "s09": "욕심쟁이 할아버지도 노래를 부르자, 도깨비들이 다시 나타났어요. 할아버지는 얼른 소리쳤지요. 이 혹에서 노래가 나온다오! 하지만 도깨비들은 팔짱을 끼고 말했어요. 지난번에 우리가 감쪽같이 속았지! 이 혹은 도로 가져가시오! 그러고는 혹을 하나 더 척 붙여 주었답니다. 욕심쟁이 할아버지는 혹이 두 개가 되어서야 크게 뉘우쳤어요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 착하고 정직하게 살면 좋은 일이 찾아오고, 욕심을 부리면 오히려 손해를 본대요. 말리도 정직하고 착한 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
