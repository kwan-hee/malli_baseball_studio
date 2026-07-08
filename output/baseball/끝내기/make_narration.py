# 끝내기 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

ENV = Path(r"C:\youtube_longform_agent\.env")
API_KEY = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith(("GEMINI_API_KEY=", "gemini=")):
        API_KEY = line.split("=", 1)[1].strip()
        break
if not API_KEY:
    sys.exit("GEMINI_API_KEY not found")

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Puck"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 야구를 20년 본 동네 형 같은 유튜브 해설자입니다. "
    "친근한 존댓말로 리듬감 있게, 궁금증 유발 구간은 톤을 올리고, "
    "명장면 소개 구간은 살짝 극적으로, 자연스럽게 연기하며 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "9회 말 투아웃. 타자가 공을 딱 때리자, 공이 담장을 훌쩍 넘어갑니다. 경기 끝. 끝내기 홈런이에요. 야구에서 이보다 짜릿한 장면은 없죠. 그런데 이걸 영어로 워크오프라고 부르는데, 이 단어, 원래는 좋은 뜻이 아니었습니다.",
    "s02": "끝내기가 뭐냐. 쉽게 말하면, 홈 팀이 마지막 이닝에 앞서 나가는 순간 경기가 딱 끝나는 겁니다. 후공 팀이 이기고 있으면 상대는 더 공격할 기회가 없잖아요. 그러니 이닝을 다 채울 이유가 없는 거죠.",
    "s03": "이거 은근 헷갈리시죠? 9회 초가 끝났는데 이미 홈 팀이 이기고 있으면요? 9회 말은 아예 하지도 않고 경기가 끝납니다. 동점이거나 지고 있을 때만 마지막 공격을 하는 거예요.",
    "s04": "자, 여기서 재밌는 게 뭐냐면요. 워크오프라는 말, 이걸 처음 만든 사람이 타자가 아니라 투수예요. 1988년, 오클랜드의 전설적인 마무리 투수 데니스 에커슬리가 한 말이거든요.",
    "s05": "끝내기 홈런을 맞으면, 진 팀 투수는 고개를 푹 숙이고 마운드에서 터벅터벅 걸어 내려가야 하잖아요. 그 쓸쓸하게 걸어 나가는 모습을 두고 워크오프라고 부른 겁니다. 원래는 얻어맞은 투수의 비참함을 담은 말이었는데, 지금은 정반대로 가장 짜릿한 단어가 됐죠.",
    "s06": "우리 KBO에도 전설로 남은 끝내기가 있죠. 2002년 한국시리즈 6차전. 지고 있던 9회 말, 이승엽 선수가 동점 쓰리런을 때립니다. 관중석이 뒤집어졌는데, 바로 다음 타자가 곧바로 역전 끝내기 홈런을 이어서 쳐버려요. 백투백으로요.",
    "s07": "2009년 한국시리즈 7차전에서도, 마지막 승부를 가른 역전 끝내기 홈런 한 방으로 우승이 확정됐습니다. 그런데 말이죠, 한국시리즈 마지막 경기가 끝내기로 끝난 건 지금까지 딱 두 번밖에 없어요. 그만큼 귀한 장면입니다.",
    "s08": "자, 여기서 고인물도 헷갈리는 디테일 하나. 9회 말 만루에서 끝내기 안타를 쳤어요. 주자 셋이 다 뛰어들어오면 한 번에 3점일까요? 아니에요. 끝내기 안타는 승리에 딱 필요한 결승 점수만 인정됩니다. 결승점 하나 들어오는 순간 경기가 끝나니까, 타자 기록도 단타 처리가 되는 거죠.",
    "s09": "그런데 딱 하나 예외가 있어요. 끝내기 홈런은 다릅니다. 홈런은 주자가 몇 명이든 전부 다 홈인이 인정되고, 타자도 당당하게 홈런으로 기록돼요. 그래서 선수들이 이왕이면 담장을 넘기고 싶어 하는 겁니다.",
    "s10": "정리하면, 끝내기는 마지막 이닝에 홈 팀이 앞서는 순간 끝나는 경기고, 워크오프라는 이름은 원래 진 투수가 걸어 나가던 데서 온 말이었습니다. 다음 편에서는 다 잡은 경기를 놓치는 아픈 순간, 블론세이브를 다뤄볼게요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 만나요!",
}

FULL_WAV = OUT / "narration_full.wav"


def write_wav(pcm, path):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm)


def norm(text):
    # 발음 문자만 남김 (공백·문장부호 제거) — Whisper 전사와 대본의 문자 위치 정렬용
    return "".join(ch for ch in text if ch.isalnum())


def generate_full():
    if FULL_WAV.exists() and FULL_WAV.stat().st_size > 100000:
        print("full narration: cached")
        return
    client = genai.Client(api_key=API_KEY, http_options={"timeout": 300000})
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
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                sys.exit("quota exceeded - stop, report to user")
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

    # 씬 시작의 정규화 문자 오프셋
    offsets, pos = {}, 0
    for sid, text in SCENES.items():
        offsets[sid] = pos
        pos += len(norm(text))
    total_norm = pos

    # 전사 단어를 순서대로 걸으며 씬 경계 시각 결정 (전사 오차에 관대한 문자 누적 방식)
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
    bps = SR * BITS // 8  # bytes per second

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
