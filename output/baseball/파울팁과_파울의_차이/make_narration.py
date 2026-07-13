# 파울팁과 파울의 차이 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "따닥. 분명히 배트에 맞는 소리가 났습니다. 그런데 심판은 삼진 아웃을 외칩니다. 타자는 억울한 표정이죠. 2020년 5월, 프로야구에서 실제로 벌어진 일인데요. 이날 감독까지 퇴장당했습니다. 도대체 뭐가 문제였을까요? 오늘의 주인공, 파울팁입니다.",
    "s02": "자, 쉽게 말하면 이렇습니다. 파울은 다시 기회를 주는 공, 파울팁은 헛스윙 취급받는 공이에요. 타자가 친 공이 배트를 살짝 스쳐서 날카롭게 곧장 포수한테 날아가고, 포수가 이걸 노바운드로 잡으면, 그게 바로 파울팁입니다.",
    "s03": "핵심은 딱 두 가지예요. 곧장, 그리고 포구. 공이 포수 미트에 닿기 전에 다른 데를 거치면 안 되고, 포수가 놓치면 그냥 파울이 됩니다. 이거 은근 헷갈리시죠? 기준은 소리가 나느냐가 아니라, 포수가 잡느냐입니다.",
    "s04": "그럼 뭐가 달라지느냐. 파울은 투 스트라이크까지만 스트라이크로 쌓이고, 그 뒤로는 아무리 쳐도 노카운트예요. 그래서 파울로 버티는 커트 신공이 가능하죠. 그런데 파울팁은 헛스윙이랑 똑같이 취급합니다. 투 스트라이크에서 파울팁이 나오면 그대로 삼진 아웃이에요.",
    "s05": "자, 여기서 재밌는 게 뭐냐면요. 원래 야구에서 파울은 스트라이크도 볼도 아니었습니다. 그냥 없던 일이었어요. 그래서 어떤 일이 벌어졌냐. 백 년도 더 전에 로이 토마스라는 선수는 마음에 안 드는 공을 계속 파울로 걷어내면서 볼넷을 얻어냈습니다. 투수 입장에선 답이 없죠.",
    "s06": "결국 내셔널리그가 1901년에 파울도 스트라이크로 센다는 규칙을 만들었고, 아메리칸리그도 1903년에 따라갑니다. 파울팁이라는 말 자체는 그보다 앞선 1889년 규칙집에 처음 등장했고요. 팁은 영어로 끝을 살짝 건드린다는 뜻입니다. 말 그대로 배트 끝에 살짝 스친 공인 거죠.",
    "s07": "다시 2020년 5월로 가볼까요. 두산 최주환 선수, 볼카운트 원 볼 투 스트라이크에서 롯데 박세웅의 떨어지는 공에 방망이가 나갔습니다. 따닥, 소리가 났어요. 무관중 경기라 중계에 소리가 그대로 잡혔죠. 그런데 주심은 헛스윙 삼진을 선언했고, 두산은 곧바로 비디오 판독을 신청합니다.",
    "s08": "자, 여기서 경우의 수를 볼까요? 배트에 안 맞았으면 헛스윙 삼진. 배트에 맞고 포수가 노바운드로 잡았으면 파울팁, 역시 삼진. 맞았는데 바운드된 다음에 잡혔다면 파울이라서 타석이 이어집니다. 공 하나에 운명이 세 갈래로 갈리는 거예요. 판독 결과는 원심 유지, 삼진. 김태형 감독은 항의하다가 그 시즌 감독 1호 퇴장을 기록했습니다.",
    "s09": "마지막으로 이건 몰랐죠, 하나 갑니다. 파울은 볼 데드예요. 공이 죽어서 주자들은 원래 베이스로 돌아갑니다. 그런데 파울팁은 살아있는 공이에요. 그래서 파울팁 순간에 주자가 뛰었다면 도루가 그대로 인정됩니다. 이거 알면 고인물이에요. 아, 그리고 배트에 스치면 다 파울팁이다, 이것도 오해입니다. 포수가 떨어뜨리면 그냥 파울이에요.",
    "s10": "오늘 한 줄 요약. 포수가 노바운드로 잡으면 파울팁, 못 잡으면 파울. 포수 글러브가 타자의 운명을 정하는 셈이죠. 다음 편은 오늘 잠깐 스쳐 간 낫아웃입니다. 삼진인데 1루로 뛰는, 그 이상한 규칙이요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
