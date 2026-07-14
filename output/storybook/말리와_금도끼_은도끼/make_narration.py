# 말리와 금도끼 은도끼 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 도끼가 연못에 빠지는 장면은 깜짝 놀라게, "
    "연못 할아버지의 대사는 낮고 부드럽고 신비롭게, "
    "나무꾼이 정직하게 대답하는 장면은 맑고 당당하게, "
    "욕심쟁이 장면은 우스꽝스럽고 얄밉게, 반성 장면은 잔잔하고 뭉클하게, "
    "화해 장면은 따뜻하게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 반짝반짝 금도끼가 나오는 이야기를 가져왔어요. 깊은 산속 연못에서 신비한 할아버지가 이렇게 묻는대요. 이 도끼가 네 도끼냐? 여러분이라면 뭐라고 대답할 거예요? 자, 우리 같이 산속으로 가볼까요?",
    "s02": "옛날 옛적, 산골 마을에 마음씨 착한 나무꾼이 살았어요. 나무꾼의 보물은 딱 하나, 반질반질 길이 든 낡은 쇠도끼였지요. 나무꾼은 날마다 산에 올라 쓱싹쓱싹 나무를 했어요. 힘들어도 콧노래를 부르면서요. 오늘도 연못가 큰 나무 앞에서 신나게 도끼질을 시작했답니다.",
    "s03": "그런데 그때! 손이 쭉 미끄러지면서, 도끼가 하늘로 붕 날아올랐어요. 퐁당! 아이고, 도끼가 그만 깊은 연못에 빠져 버렸지 뭐예요. 나무꾼은 연못가에 주저앉아 눈물을 뚝뚝 흘렸어요. 하나뿐인 내 도끼. 이제 나무를 못 하면 어떡하지?",
    "s04": "그때였어요. 연못 물이 부글부글 갈라지더니, 하얀 수염이 기다란 연못 할아버지가 스르르 나타났어요! 할아버지 손에는 눈부신 금도끼가 들려 있었지요. 나무꾼아, 이 금도끼가 네 도끼냐? 나무꾼은 눈이 휘둥그레졌어요. 세상에, 번쩍번쩍 금도끼라니!",
    "s05": "친구들, 잠깐만요! 말리가 물어볼게요. 여러분이라면 뭐라고 했을 거예요? 금도끼, 갖고 싶죠? 사실 말리도 조금 갖고 싶어요, 멍멍. 그런데 저건 나무꾼의 도끼가 아니잖아요. 우리 나무꾼은 과연 뭐라고 할까요? 쉿, 잘 들어봐요.",
    "s06": "나무꾼은 고개를 저었어요. 아니요, 할아버지. 제 도끼는 낡은 쇠도끼인걸요. 할아버지는 은도끼도 들어 보였지만, 나무꾼은 또 고개를 저었지요. 그러자 할아버지가 껄껄 웃었어요. 참으로 정직하구나! 그리고 금도끼, 은도끼, 쇠도끼까지 세 자루를 모두 선물해 주셨답니다. 와, 신난다!",
    "s07": "이 소문을 들은 옆집 욕심쟁이 나무꾼이 코웃음을 쳤어요. 흥, 그거야 쉽지! 욕심쟁이는 연못으로 달려가서, 멀쩡한 도끼를 일부러 퐁당 던져 넣었어요. 그리고 할아버지가 금도끼를 들고 나타나자마자 냉큼 소리쳤죠. 맞아요, 맞아요! 그 금도끼가 제 도끼예요!",
    "s08": "연못 할아버지는 조용히 고개를 저었어요. 거짓말은 금방 티가 난단다. 그리고 스르르 물속으로 사라져 버렸지요. 금도끼도, 던져 넣은 쇠도끼도 없이 빈손이 된 욕심쟁이는 그제야 고개를 푹 숙였어요. 욕심을 부리다가 거짓말까지 했구나. 할아버지, 죄송해요. 흑흑.",
    "s09": "그 모습을 본 착한 나무꾼이 다가와 어깨를 토닥토닥해 주었어요. 괜찮아요. 제 쇠도끼를 빌려드릴게요. 우리 같이 나무해요! 그날부터 두 나무꾼은 나란히 산에 올라 쓱싹쓱싹 나무를 했답니다. 정직한 마음도, 용서하는 마음도 반짝반짝 빛나는 마을이 되었지요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 금도끼보다 더 반짝이는 건 바로 정직한 마음이었어요. 이 도끼가 네 도끼냐? 이제 우리 모두 씩씩하게 대답할 수 있겠죠? 아니요, 제 것이 아니에요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
