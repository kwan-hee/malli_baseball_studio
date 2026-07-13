# 아웃의 종류 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "투수의 글러브가 홈으로 파고드는 주자를 태그합니다. 심판은 아웃. 그런데 잠깐, 글러브 안에 공이 없었습니다. 2015년 7월 9일 대구에서 실제로 벌어진 장면인데요. 공도 없이 어떻게 아웃이 됐을까요? 오늘은 야구의 심장, 아웃 이야기입니다.",
    "s02": "야구는 아웃 세 개가 모이면 공격이 끝나는 게임이에요. 그래서 아웃을 어떻게 만드는지 알면 야구 절반은 아는 겁니다. 방법은 크게 네 가지. 삼진, 플라이아웃, 포스아웃, 태그아웃. 삼진은 다들 아시죠? 스트라이크 세 개. 오늘은 나머지 셋을 확실하게 잡아보죠.",
    "s03": "먼저 플라이아웃. 타자가 친 공이 땅에 닿기 전에 수비수가 잡으면 타자는 그 자리에서 아웃입니다. 담장 앞이든 파울 지역이든 상관없어요. 노바운드로 잡히면 끝. 단, 주자는 얘기가 다릅니다. 공이 잡힌 뒤에 베이스를 다시 밟고 출발하면 다음 베이스로 뛸 수 있어요. 이게 바로 태그업입니다.",
    "s04": "다음, 포스아웃. 타자가 공을 치고 1루로 뛰는 순간, 1루에 있던 주자는 2루로 밀려날 수밖에 없죠. 이렇게 갈 곳이 정해진 주자는 터치할 필요도 없습니다. 공을 잡고 베이스만 먼저 밟으면 아웃이에요. 병살, 그러니까 더블플레이가 순식간에 되는 이유가 이겁니다. 밟고, 던지고, 밟고. 끝.",
    "s05": "그런데 주자가 갈 곳이 정해져 있지 않다면? 이제 태그아웃의 영역입니다. 도루하는 주자, 홈으로 파고드는 주자는 베이스를 밟는 걸로는 못 잡아요. 공을 잡은 글러브나 손으로 주자의 몸을 직접 터치해야 합니다. 핵심은 이겁니다. 공을 가진 채로 터치할 것. 빈 글러브 태그는 아웃이 아니에요.",
    "s06": "자, 여기서 재밌는 게 뭐냐면요. 3아웃이라는 규칙, 1845년 뉴욕의 니커보커 클럽이 만든 규칙집에서 나왔습니다. 그전에는 한 명만 아웃돼도 공수교대거나, 크리켓처럼 전원이 아웃될 때까지 치는 방식이었죠. 니커보커 규칙 20개 중에 진짜 새 발명품은 3아웃 하나뿐이었다는 연구도 있어요. 그만큼 야구를 야구로 만든 규칙인 겁니다.",
    "s07": "다시 2015년 7월 9일 대구. SK와 삼성의 경기, 삼성 최형우 선수가 홈으로 쇄도합니다. 투수 김광현 선수가 글러브를 갖다 댔고, 심판은 아웃을 선언했어요. 그런데 느린 화면을 보니 공은 글러브가 아니라 다른 곳에 있었습니다. 공 없는 글러브, 이른바 유령 태그였던 거죠.",
    "s08": "규칙대로라면 공 없는 태그는 태그가 아니니까 아웃이 될 수 없습니다. 문제는 당시 홈 태그 플레이가 비디오 판독 대상이 아니었다는 거예요. 심판 눈에는 완벽한 태그로 보였고, 판정은 그대로 굳었습니다. 이런 장면들이 쌓이면서 KBO는 판독 대상을 계속 넓혀 왔고요. 규칙과 제도는 이렇게 사건을 먹고 자랍니다.",
    "s09": "마지막으로 이건 몰랐죠. 뜬공이 잡히면 주자는 무조건 죽는다? 아닙니다. 태그업만 하면 얼마든지 진루할 수 있고, 희생플라이 득점이 그렇게 나옵니다. 하나 더, 고인물용. 포스아웃은 상황이 풀리기도 해요. 뒤따라오던 주자가 먼저 아웃되면 앞 주자는 더 이상 밀려나는 신세가 아니라서, 그때부턴 태그를 해야 잡을 수 있습니다.",
    "s10": "오늘 한 줄 요약. 갈 곳이 정해진 주자는 베이스를 밟아서, 자유로운 주자는 몸을 터치해서, 뜬공은 잡는 순간 타자 아웃. 이 세 개면 중계가 훨씬 잘 보입니다. 다음 편은 투수와 타자의 전쟁터, 스트라이크 존입니다. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
