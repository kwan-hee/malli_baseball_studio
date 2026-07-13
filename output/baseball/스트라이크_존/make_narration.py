# 스트라이크 존 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
VOICE = "Puck"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 야구를 20년 본 동네 형 같은 유튜브 해설자입니다. "
    "친근한 존댓말로 리듬감 있게, 궁금증 유발 구간은 톤을 올리고, "
    "설명 구간은 차분하게, 야구를 처음 보는 사람도 이해하게 쉽게 연기하며 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "바깥쪽 꽉 찬 공, 스트라이크! 타자는 고개를 갸웃합니다. 방금 그게 들어왔다고? 야구에서 말다툼이 제일 많이 벌어지는 곳, 바로 스트라이크 존인데요. 그런데 이 존, 옛날에는 타자가 직접 주문했다는 거 아셨어요? 오늘은 보이지 않는 상자, 스트라이크 존 이야기입니다.",
    "s02": "자, 쉽게 말하면 스트라이크 존은 홈플레이트 위에 떠 있는 보이지 않는 유리 상자예요. 투수가 던진 공이 이 상자를 통과하면 스트라이크, 벗어나면 볼입니다. 문제는 이 상자가 눈에 안 보인다는 거죠. 그래서 심판이 대신 봐주는 겁니다.",
    "s03": "크기는 이렇게 정해져 있어요. 위는 타자 어깨와 바지 윗부분의 중간, 아래는 무릎 아래. 좌우는 홈플레이트 폭 그대로입니다. 여기서 중요한 거 하나. 타자마다 키도 다르고 타격 자세도 다르죠? 그래서 스트라이크 존은 타자마다 전부 다릅니다. 키가 작으면 존도 작아요.",
    "s04": "그리고 이건 몰랐죠. 스트라이크 존은 평면이 아니라 입체입니다. 홈플레이트가 오각형이니까, 그 위에 세워진 오각기둥인 셈이죠. 그래서 공이 존의 앞 모서리를 살짝 스치고 바깥으로 빠져도 스트라이크예요. 휘어져 들어오는 변화구가 앞에서 걸치기만 하면, 뒤에서 어디로 빠지든 상관없습니다.",
    "s05": "자, 여기서 재밌는 게 뭐냐면요. 1887년 전까지 타자는 투수에게 공을 주문할 수 있었습니다. 높은 공 주세요, 낮은 공 주세요. 진짜예요. 심판은 타자가 고른 높이에 맞춰서 스트라이크를 판정했죠. 투수는 주문받은 대로 던져야 하는, 말하자면 요리사였던 겁니다.",
    "s06": "그런데 심판 입장에선 존이 두 개라 너무 헷갈렸어요. 그래서 1887년, 주문 제도를 없애고 어깨부터 무릎까지 하나의 존으로 통일합니다. 존이 사실상 두 배로 커지면서 투수들이 날아다니기 시작했죠. 오늘날 스트라이크 존의 뼈대가 이때 만들어진 겁니다.",
    "s07": "그리고 2024년, KBO가 세계 최초로 큰일을 냅니다. 1군 리그에 로봇 심판, ABS를 도입한 거죠. 이제 존은 사람 눈이 아니라 기계가 봅니다. 기준도 숫자로 딱 정해졌어요. 위는 키의 56.35퍼센트, 아래는 27.64퍼센트. 키 180센티 타자라면 위가 약 101센티, 아래가 약 50센티인 셈이죠.",
    "s08": "그런데 존은 지금도 움직입니다. 첫 시즌이 끝나고 존이 너무 높다는 의견이 많았거든요. 그래서 KBO는 2025년부터 존 위아래를 조금씩 내렸습니다. 백사십 년 전에는 타자가 주문하던 존이, 이제는 데이터로 조정되는 시대인 거예요.",
    "s09": "마지막으로 오해 하나 바로잡죠. 포수가 공을 멋지게 잡으면 스트라이크가 된다? 아닙니다. 판정 기준은 존을 통과했느냐, 그거 하나예요. 포수 미트 위치는 규칙상 아무 상관 없습니다. 사람 심판 시절엔 프레이밍이라는 기술이 통하기도 했지만, 로봇 존 앞에서는 어림도 없죠.",
    "s10": "오늘 한 줄 요약. 스트라이크 존은 타자마다 다른, 홈플레이트 위의 보이지 않는 오각기둥이다. 이제 존 얘기가 나오면 아는 척 한번 해보세요. 다음 편은 볼넷입니다. 왜 하필 볼 네 개에 걸어 나갈까요? 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
