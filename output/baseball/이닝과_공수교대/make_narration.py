# 이닝과 공수교대 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "야구 중계 보면요, 1회초, 1회말, 이러다가 9회말에서 끝나죠. 근데 여기 궁금한 거 두 개. 야구는 왜 하필 딱 9회일까요? 그리고 가끔 9회말인데 경기를 아예 안 하고 끝나버릴 때, 보신 적 있죠? 오늘은 야구의 가장 기본, 이닝과 공수교대 이야기입니다.",
    "s02": "이닝을 쉽게 비유하면요, 두 팀이 번갈아 한 판씩 주고받는 한 회예요. 한 이닝은 초하고 말, 두 부분으로 나뉘어요. 초에는 원정팀이 공격하고, 말에는 홈팀이 공격하죠.",
    "s03": "그럼 공격이 언제 끝나느냐. 아웃 세 개예요. 공격팀이 아웃 세 번을 당하면, 공격이랑 수비가 딱 자리를 바꿔요. 선수들이 우르르 그라운드를 뛰어 들어가고 나오죠. 이게 바로 공수교대예요.",
    "s04": "초에 한 번, 말에 한 번, 이렇게 두 번 자리를 바꾸면 1이닝이 끝나요. 그리고 이걸 아홉 번 반복하는 게 바로 야구 한 경기입니다. 생각보다 단순하죠?",
    "s05": "그럼 왜 하필 9회일까요? 1857년, 뉴욕 구단들이 모여서 야구 규칙을 통일해요. 그때, 경기는 9이닝으로 한다, 하고 딱 정해버린 거죠. 마침 그 무렵 야수도 9명으로 굳어져서, 9명이 9이닝, 이 구조가 같이 자리 잡았어요.",
    "s06": "재밌는 게 뭐냐면요, 그 전엔 회 수가 정해져 있지도 않았어요. 그냥 21점 먼저 내는 팀이 이기는 방식이었거든요. 근데 이러니까 경기가 어떤 날은 금방 끝나고, 어떤 날은 한없이 길어졌어요. 그래서 9회로 딱 못을 박은 거죠.",
    "s07": "그럼 우리 KBO는요? 9회까지 하다가 승부가 안 나면 연장에 들어가죠. 근데 2025시즌부터 바뀐 게 있어요. 정규시즌 연장이 12회에서 11회로 줄었습니다. 피치클락이 도입되면서 투수들 체력을 아껴주려고요. 그래서 11회까지 비기면, 그냥 무승부로 끝나요.",
    "s08": "자, 아까 훅에서 물어본 거. 9회말인데 왜 경기를 안 할 때가 있냐. 답은 간단해요. 9회초까지 끝났는데 홈팀이 이미 이기고 있으면, 굳이 9회말 공격을 할 필요가 없거든요. 이길 걸 또 공격할 이유가 없잖아요? 그래서 그냥 경기 끝이에요.",
    "s09": "그리고 이게 바로, 홈팀만 끝내기 승리를 할 수 있는 이유예요. 마지막 공격이 늘 홈팀 차지니까요. 9회말, 홈팀 타자가 담장을 훌쩍 넘기는 순간! 경기가 그대로 끝나버리는 그 짜릿한 장면, 이게 다 이 구조 덕분입니다.",
    "s10": "정리하면, 이닝은 두 팀이 아웃 세 개씩 주고받는 한 회고, 그걸 아홉 번 하는 게 야구다, 이겁니다. 이제 9회말에 경기가 일찍 끝나도 안 당황하시겠죠? 다음 편에서는 이 공수교대의 핵심, 아웃 세 개를 만드는 방법들을 들고 올게요. 오늘 내용 쓸만했다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 만나요!",
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
