# 희생플레이 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "타자가 아웃을 당했는데요, 덕아웃에서는 박수가 터집니다. 기록지를 보면 타율도 안 깎였어요. 아웃인데 손해가 없다? 야구에서 제일 이상한 아웃, 오늘은 희생플레이 이야기입니다.",
    "s02": "희생플레이는 한마디로, 내 타석을 팀에 기부하는 겁니다. 첫 번째가 희생번트예요. 주자를 한 베이스 보내려고 살짝 공을 굴리고, 나는 1루에서 아웃되는 거죠. 아웃 하나를 내주고 주자를 안전하게 보내는 작전입니다.",
    "s03": "두 번째는 희생플라이. 노아웃이나 원아웃에서 외야로 뜬공을 날리면, 수비가 잡아도 3루 주자가 태그업해서 홈을 밟을 수 있어요. 아웃 하나랑 1점을 바꾸는 거죠. 그리고 여기가 포인트인데요, 둘 다 타수에서 빠집니다. 아웃을 당해도 타율이 안 깎여요. 팀을 위해 희생했으니 기록도 봐주는 겁니다.",
    "s04": "자, 여기서 재밌는 게 뭐냐면요. 이 봐주기, 1889년에 처음 생겼습니다. 기록지에 희생타 항목이 처음 등장했는데요, 처음엔 번트든 땅볼이든 뜬공이든 주자만 보내면 다 희생타로 쳐줬어요. 그런데 정작 타수는 그대로 깎았습니다. 이름만 희생이었던 거죠. 1894년에 번트로 한정하면서, 타수 제외까지 확정됩니다.",
    "s05": "그런데 희생플라이는 팔자가 사나웠어요. 1908년에 생겼다가, 1930년에 리그 전체 타율이 2할 9푼을 넘자 타자들 너무 봐준다며 폐지됩니다. 1939년에 부활했다가 이듬해 또 폐지. 결국 1954년에야 지금 모습으로 정착했죠. 생겼다 없어졌다를 이렇게 반복한 기록은 희생플라이가 거의 유일합니다.",
    "s06": "KBO에서 희생번트 하면 이 이름을 기억하시면 됩니다. 김민재. 통산 희생번트 이백스물아홉 개, 역대 1위예요. 화려한 홈런 대신 아웃 이백스물아홉 개를 팀에 바친, 작전 수행의 장인이죠.",
    "s07": "희생플라이의 명장면도 있습니다. 2026년 6월 17일 창원. 9회말, NC 오태양 선수가 깊은 중견수 뜬공을 날립니다. 공은 잡혔지만 3루 주자가 유유히 홈인. 아웃 하나로 경기가 끝나는 끝내기 희생플라이였어요. 5대 4, NC의 역전승이었습니다.",
    "s08": "여기서 고인물 상식 하나. 희생플라이도 희생번트처럼 기록에 아무 영향이 없을까요? 아닙니다. 타율은 안 깎이는데, 출루율은 깎여요. 번트는 처음부터 아웃될 작정이지만, 플라이는 사실 안타를 치려다 실패한 타구잖아요. 그래서 절반만 봐주는 겁니다. 이거 알면 고인물이에요.",
    "s09": "오해 하나 바로잡죠. 깊은 뜬공에 태그업만 하면 희생플라이다? 아니요. 주자가 득점해야만 인정됩니다. 2루 주자가 3루로 태그업하면 그냥 평범한 아웃이고, 타율도 깎여요. 그리고 아주 드물지만 타점 두 개짜리 희생플라이도 있습니다. 2007년 잠실에서 최희섭 선수가 기록했죠.",
    "s10": "오늘 한 줄 요약. 희생플레이는 아웃 하나로 팀의 점수를 벌어주는 플레이, 그래서 이름이 희생이다. 다음 편은 몸에 맞는 공입니다. 맞으면 아픈데 왜 웃으면서 1루로 나갈까요? 오늘 내용이 쓸 만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
