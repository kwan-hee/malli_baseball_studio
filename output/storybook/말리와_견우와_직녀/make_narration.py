# 말리와 견우와 직녀 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 견우와 직녀의 대사는 맑고 다정하게, "
    "하늘나라 임금님의 대사는 낮고 부드럽고 위엄 있지만 따뜻하게, "
    "일을 잊는 장면은 장난스럽게, 이별 장면은 잔잔하고 그립게, "
    "오작교 장면은 신비롭고 웅장하게, 재회 장면은 벅차고 기쁘게, "
    "칠석 비 장면은 뭉클하게 연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 밤하늘 은하수에 사는 두 사람, 견우와 직녀 이야기를 가져왔어요. 일 년에 딱 하루만 만날 수 있는 애틋한 약속이 있대요. 왜 그렇게 됐을까요? 자, 반짝반짝 하늘나라로 떠나 볼까요?",
    "s02": "옛날 옛적 하늘나라에, 소를 돌보는 견우와 베를 짜는 직녀가 살았어요. 견우는 새벽부터 소들을 보살피는 부지런한 목동이었고, 직녀는 구름처럼 고운 옷감을 짜는 솜씨꾼이었지요. 견우가 돌보는 소들은 언제나 반질반질 윤이 났고, 직녀가 짠 옷감은 별빛보다 곱게 반짝였답니다. 하늘나라 사람들은 두 사람을 무척 아꼈어요.",
    "s03": "어느 날, 견우와 직녀가 은하수 냇가에서 만났어요. 둘은 보자마자 사이좋은 짝꿍이 되었지요. 함께 있으면 하루가 어떻게 가는지도 몰랐대요. 웃고 이야기하다 보면 어느새 해가 저물었지요. 그런데 문제가 생겼어요. 둘이 노는 게 너무 재미있어서, 그만 일을 몽땅 잊어버린 거예요. 소들은 여기저기 구름 밭을 망치고, 베틀에는 먼지가 뽀얗게 쌓였답니다.",
    "s04": "하늘나라가 발칵 뒤집혔어요. 새 옷감이 없어서 별들이 반짝일 수 없고, 소들은 구름 밭을 엉망으로 만들었지요. 하늘나라 임금님이 두 사람을 불렀어요. 견우야, 직녀야. 맡은 일을 잊으면 모두가 힘들어진단다. 두 사람은 고개를 푹 숙였답니다.",
    "s05": "친구들, 잠깐만요! 말리가 물어볼게요. 좋아하는 놀이만 하고 해야 할 일을 잊으면 어떻게 될까요? 맞아요. 모두가 곤란해져요. 말리도 신나게 논 다음에는 꼭 집을 지킨답니다, 멍멍! 그럼 견우와 직녀는 어떻게 됐을까요?",
    "s06": "임금님은 두 사람을 은하수 양쪽으로 보냈어요. 그리고 약속했지요. 맡은 일을 다시 열심히 하면, 일 년에 한 번 만나게 해 주마. 견우는 다시 소를 돌보고, 직녀는 다시 베틀 앞에 앉았어요. 은하수 이편에서 저편이 얼마나 멀던지요. 밤마다 두 사람은 강 건너를 바라보며 그날을 손꼽아 기다렸어요. 서로가 그리울 때마다, 더 열심히, 더 정성껏 일했답니다.",
    "s07": "드디어 칠월 칠석날이 되었어요. 그런데 은하수가 너무 넓어서 건널 수가 없지 뭐예요. 그때! 까치와 까마귀들이 포르르 날아와 소리쳤어요. 우리가 도와줄게요! 새들은 날개를 맞대고 은하수 위에 길고 긴 다리를 놓았답니다. 바로 오작교예요!",
    "s08": "견우와 직녀는 오작교 위를 달려가 꼭 만났어요. 일 년 동안 열심히 일한 이야기가 밤새 끝나지 않았지요. 하늘나라 임금님도 빙그레 웃으며 말했어요. 참으로 성실하구나. 이제 해마다 칠석날에 만나거라!",
    "s09": "그래서 지금도 칠월 칠석이 되면 견우와 직녀가 오작교에서 만난대요. 칠석날 내리는 보슬비는 두 사람이 다시 만나 흘리는 기쁨의 눈물이라고 하지요. 그리고 칠석이 지나고 다시 굵은 비가 내리면, 그건 헤어짐을 아쉬워하는 눈물이래요. 나머지 날들은 각자 자리에서 부지런히 일한답니다. 다음 만남을 손꼽아 기다리면서요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 맡은 일을 열심히 하면, 기다리던 소중한 날이 꼭 온대요. 오늘 밤 은하수를 보면 견우와 직녀에게 손 흔들어 줘요. 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 멍멍! 다음에 또 만나요. 안녕!",
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
