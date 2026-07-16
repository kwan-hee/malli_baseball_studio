# 말리와 방귀쟁이 며느리 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어(뿌웅 등)는 씬 시작에 금지·중간에만 (2026-07-16 까치편 whisper 환각 교훈)
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
    "말리(강아지)의 대사는 신나고 귀엽게, 착하고 부지런한 며느리의 대사는 수줍고 정답게, "
    "인자한 시아버지의 대사는 너그럽고 따뜻하게, "
    "어마어마한 방귀로 온 집안이 들썩이는 장면은 아주 익살스럽고 왁자지껄하게, "
    "며느리가 재주로 배를 따 주어 마을 사람들이 환호하는 장면은 신나고 통쾌하게, "
    "마지막 교훈 장면은 다정하고 따뜻하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 웃기고 재미있는 이야기를 가져왔어요. 세상에서 제일 힘이 센 방귀를 뀌는 며느리 이야기랍니다. 방귀가 얼마나 셌길래 그러냐고요? 후후, 정말 깜짝 놀랄 거예요! 자, 옛날 어느 시골집으로 함께 가 볼까요?",
    "s02": "옛날 어느 집에, 참하고 부지런한 새 며느리가 시집을 왔어요. 일도 잘하고 마음씨도 고와서 온 식구가 다 좋아했지요. 그런데 이상하게도, 날이 갈수록 며느리의 얼굴이 노랗게 뜨고 시름시름 시들어 가는 거예요. 토실토실하던 볼도 쏙 들어가고, 기운도 하나 없어 보였답니다.",
    "s03": "하루는 걱정이 된 시아버지가 며느리에게 다정하게 물었어요. 아가야, 어디 아픈 게냐? 왜 이리 기운이 없누? 며느리는 얼굴이 새빨개져서 조그맣게 대답했지요. 실은요, 아버님. 시집온 뒤로 방귀를 꾹 참았더니, 자꾸만 몸이 아파요. 그 말에 온 식구가 눈이 휘둥그레졌어요.",
    "s04": "시아버지는 껄껄 웃으며 시원하게 말했어요. 저런, 그동안 얼마나 힘들었누! 어서 맘껏 뀌어라, 아가야! 며느리는 그럼 조심하시라며, 식구들에게 단단히 일렀어요. 아버님은 기둥을, 어머님은 문고리를, 서방님은 솥단지를 꼭 붙잡으세요! 식구들은 영문도 모른 채 하나씩 꽉 붙잡았답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 며느리는 왜 몸이 아팠을까요? 맞아요, 뀌고 싶은 방귀를 억지로 꾹 참았기 때문이에요! 참고 싶지 않은 걸 억지로 참으면, 이렇게 몸이 아플 수도 있대요. 자, 이제 며느리가 방귀를 뀌면 과연 어떤 일이 벌어질까요?",
    "s06": "드디어 며느리가 숨을 크게 들이마시고, 참았던 방귀를 뀌었어요. 뿌우웅! 그 순간, 세상에! 온 집이 부르르 흔들리고, 문짝이 벌컥 열렸다 닫히고, 솥뚜껑이 팽그르르 날아올랐지 뭐예요. 붙잡고 있던 식구들은 깃발처럼 펄럭펄럭 나부꼈답니다. 정말 어마어마한 방귀였어요!",
    "s07": "한바탕 방귀 바람이 지나가고 나자, 며느리의 얼굴은 다시 발그레 화사해졌어요. 참았던 걸 시원하게 내보내니 몸이 아주 개운했거든요. 어리둥절하던 식구들도 그만 배꼽을 잡고 깔깔 웃음을 터뜨렸어요. 아이고, 우리 며느리 방귀가 이렇게 셌구나! 온 집안이 웃음바다가 되었답니다.",
    "s08": "그러던 어느 날, 마을에 큰 걱정거리가 생겼어요. 마을 한가운데 아주 높다란 배나무에, 탐스러운 배가 주렁주렁 열렸는데, 나무가 너무 높아서 아무도 딸 수가 없었거든요. 사다리를 놓아도, 장대를 휘둘러도 소용이 없었지요. 그때 며느리가 방긋 웃으며 앞으로 나섰어요.",
    "s09": "커다란 배나무 앞에 선 며느리는, 나무를 향해 엉덩이를 대고 다시 한번 힘껏 방귀를 뀌었어요. 뿌우웅! 그러자 세찬 바람에 잘 익은 배가 우수수, 비처럼 쏟아져 내렸답니다! 마을 사람들은 손뼉을 치며 환호했어요. 며느리의 방귀가 이렇게 대단한 재주였다니! 모두가 며느리를 칭찬했지요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 남과 조금 다른 점도, 알고 보면 아주 멋진 개성이고 재주가 될 수 있대요. 그러니 나만의 특별한 점을 부끄러워하지 말아요! 말리도 나만의 멋진 점을 아끼는 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
