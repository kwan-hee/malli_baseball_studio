# 배럴타구 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "설명 구간은 차분하게, 자연스럽게 연기하며 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "여러분, 중계 보다가 배럴타구! 이 말 들어보셨죠. 근데 이거 그냥 세게 친 공이 아니에요. 세기도 세기지만, 각도까지 딱 맞아떨어져야 인정되는 아주 까다로운 타구입니다. 그리고 이 배럴 하나만 보면, 그 타자가 리그 최고인지 아닌지가 보여요. 오늘은 이 배럴타구 이야기입니다.",
    "s02": "배럴을 쉽게 비유하면요, 안타 확정에 가장 가까운 타구예요. 스탯캐스트가 수만 개 타구를 다 뒤져봤더니, 어떤 속도랑 어떤 각도로 맞은 공들은 타율이 5할, 장타율이 무려 1.500을 넘더라는 거예요. 그 조건을 만족하는 타구, 이걸 배럴이라고 이름 붙인 겁니다.",
    "s03": "실제로 이 배럴 타구들 성적이 얼마였는지 아세요? 타율 8할 2푼이었어요. 열 번 치면 여덟 번 넘게 안타라는 거죠. 배럴만 만들어내면 거의 자동으로 안타, 아니 장타가 된다는 얘깁니다.",
    "s04": "이게 언제 나왔냐면, 2016년이에요. 스탯캐스트가 2015년에 전 구장에 깔리면서 타구 데이터가 산더미처럼 쌓였거든요. 그걸 톰 탱고라는 데이터 분석가가 파고들다가, 세게 친 것보다 세게 그리고 좋은 각도로 친 게 진짜 중요하구나, 하고 이 배럴 개념을 딱 정리해서 발표한 겁니다.",
    "s05": "자, 여기서 재밌는 게 뭐냐면요. 배럴의 출발선은 타구 속도 98마일, 우리 식으로 시속 158킬로예요. 딱 이 속도일 땐 발사각이 26도에서 30도, 이 좁은 구간에 들어와야 배럴로 인정됩니다.",
    "s06": "근데 공을 더 세게 치면요? 인정되는 각도 범위가 점점 넓어져요. 100마일로 치면 24도에서 33도까지 오케이. 진짜 괴물처럼 116마일로 후려치면, 낮은 라인드라이브부터 높은 뜬공까지 웬만하면 다 배럴이에요. 세게 칠수록 봐주는 각도가 넉넉해지는 거죠.",
    "s07": "많이들 배럴이랑 하드히트를 헷갈리세요. 이거 다른 겁니다. 하드히트는 그냥 세게 맞힌 공, 세기만 봐요. 근데 배럴은 세기에다가 장타 각도까지 갖춘 것만 골라냅니다. 하드히트가 힘이라면, 배럴은 힘 곱하기 정확도인 셈이죠.",
    "s08": "그래서 2024년 배럴 비율 1위가 누구였냐. 애런 저지, 무려 26퍼센트였어요. 친 공 네 개 중 하나가 배럴이라는 거예요. 그다음이 오타니 21퍼센트. 이런 배럴 비율 높은 선수가 곧 리그를 씹어먹는 최고 파워 히터인 겁니다.",
    "s09": "그럼 우리 KBO는요? 사실 여기 함정이 있어요. MLB 기준을 KBO에 그대로 대면 배럴이 1퍼센트도 안 나와요. 타구 속도 분포 자체가 다르거든요. 메이저리그는 타구 열 개 중 한 개 가까이가 배럴인데, KBO는 백 개 중 한 개도 안 되는 거죠. 그래서 국내에선 한국형 배럴 기준을 따로 만들자는 연구가 계속되고 있습니다. 이거 알면 여러분도 이제 고인물이에요.",
    "s10": "정리하면, 배럴타구는 세기와 각도를 둘 다 잡은, 안타에 가장 가까운 최고의 타구다, 이겁니다. 다음에 중계에서 배럴 뜨면, 아 저건 그냥 센 게 아니라 각도까지 완벽한 거구나 하고 봐주세요. 다음 편에서는 이 배럴의 절반을 책임지는 짝꿍, 발사각 이야기를 들고 올게요. 오늘 내용 쓸만했다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 만나요!",
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
