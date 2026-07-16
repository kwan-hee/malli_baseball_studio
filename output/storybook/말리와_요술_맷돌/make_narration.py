# 말리와 요술 맷돌 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 금지 (2026-07-16 까치편 whisper 환각 교훈)
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
    "말리(강아지)의 대사는 신나고 귀엽게, 마음씨 착한 아우의 대사는 따뜻하고 정답게, "
    "신비한 노인의 대사는 인자하고 나지막하게, 욕심 많은 도둑의 대사는 능글맞고 우스꽝스럽게, "
    "맷돌에서 온갖 것이 쏟아지는 장면은 놀랍고 신나게, 바다에서 소금이 멈추지 않는 장면은 "
    "허둥지둥 다급하게, 마지막 유래를 알려 주는 장면은 다정하고 신비롭게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 신기한 수수께끼로 시작할게요. 우리가 헤엄치는 넓고 푸른 바닷물은 왜 이렇게 짤까요? 사실은요, 바닷속에 아주 신비한 요술 맷돌이 숨어 있기 때문이래요! 대체 무슨 일이 있었는지, 옛날 옛적으로 함께 떠나 볼까요?",
    "s02": "옛날 어느 마을에, 가난하지만 마음씨 착한 아우가 살았어요. 어느 날 아우는 길에서 만난 신비한 노인에게 작은 맷돌 하나를 선물로 받았지요. 노인이 나지막이 일러 주었어요. 나오너라, 하고 돌리면 원하는 것이 나오고, 멈춰라, 하면 딱 그친단다. 부디 착한 일에만 쓰거라.",
    "s03": "착한 아우가 맷돌에게 쌀이 나오너라, 하고 돌리자, 하얀 쌀이 소복소복 쏟아졌어요. 따뜻한 옷이 나오너라, 하면 폭신한 옷이 나왔지요. 아우는 혼자만 잘 살지 않았어요. 배고픈 이웃에게는 쌀을, 추운 이웃에게는 옷을 나눠 주었답니다. 온 마을이 다 함께 넉넉하고 행복해졌어요.",
    "s04": "신기한 맷돌은 돌리기만 하면 무엇이든 척척 만들어 냈어요. 먹음직스러운 떡도, 알록달록한 과일도, 반짝이는 그릇도 끝없이 쏟아져 나왔지요. 그럴 때마다 아우는 꼭 잊지 않고 말했어요. 이제 그만 멈춰라! 그러면 맷돌은 얌전히 돌기를 멈췄답니다. 참 신통방통한 맷돌이었지요.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 이렇게 신기한 맷돌이 있다는 소문은, 과연 착한 사람에게만 들렸을까요? 아니에요. 이 소문은 그만 욕심 많은 도둑의 귀에까지 들어가고 말았답니다. 도둑은 눈이 번쩍 뜨였어요. 자, 이제 어떤 일이 벌어질까요?",
    "s06": "그런데 이 소문을 들은 욕심쟁이 도둑이, 그만 나쁜 마음을 먹고 말았어요. 도둑은 깜깜한 밤을 틈타 아우의 집에 몰래 숨어들어, 요술 맷돌을 슬쩍 훔쳐 달아났지요. 그러고는 작은 배 한 척에 올라타, 아무도 쫓아오지 못하게 넓은 바다로 노를 저어 도망쳤답니다.",
    "s07": "넓은 바다 한가운데에 다다르자, 도둑은 욕심스레 생각했어요. 옳지, 옛날에는 소금이 아주 귀하고 값진 보물이었지! 이 맷돌로 소금을 잔뜩 만들어 큰 부자가 되어야겠다. 도둑은 신이 나서 크게 외쳤어요. 소금아, 어서어서 나오너라! 그러자 새하얀 소금이 콸콸 쏟아지기 시작했지요.",
    "s08": "하얀 소금은 배 위로 산더미처럼 자꾸자꾸 쌓여 갔어요. 그런데 큰일이 났어요! 욕심에 눈이 먼 도둑은, 맷돌을 멈추는 주문을 그만 까맣게 잊어버린 거예요. 멈춰라! 그쳐라! 아무리 소리쳐도 소용이 없었어요. 소금은 계속 쏟아졌고, 배는 그만 한쪽으로 기우뚱 기울고 말았답니다.",
    "s09": "물에 빠진 도둑은 허우적허우적, 겨우 헤엄을 쳐서 뭍으로 올라왔어요. 그러고는 자기 욕심을 크게 뉘우쳤지요. 하지만 요술 맷돌은 소금을 만들며 바닷속 깊이 가라앉고 말았답니다. 그리고 지금도 저 바다 밑에서 쉬지 않고 소금을 갈고 있대요. 바닷물이 짠 게 바로 그 때문이래요!",
    "s10": "친구들, 오늘 이야기 어땠어요? 지나친 욕심을 부리면, 가진 것마저 모두 잃게 된대요. 그리고 넓은 바다가 짜디짠 건, 바로 이 요술 맷돌 때문이라니, 정말 신기하죠? 말리는 욕심내지 않는 착한 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
