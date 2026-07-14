# 볼넷 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "투수가 공을 한 개도 던지지 않았는데, 타자가 1루로 걸어 나갑니다. 반칙 아니냐고요? 정식 규칙입니다. 야구에는 공짜로 1루를 얻는 방법이 있거든요. 그런데 왜 하필 볼 네 개일까요? 삼진은 세 개인데 말이죠. 오늘은 걸어서 나가는 안타, 볼넷 이야기입니다.",
    "s02": "볼넷은 말 그대로 볼 네 개예요. 투수가 스트라이크 존을 벗어난 공을 네 번 던지면, 타자는 방망이 한 번 안 휘두르고 1루에 나갑니다. 영어로는 베이스 온 볼스, 걸어 나간다고 해서 워크라고도 불러요. 투수의 실수가 쌓이면 타자에게 상이 되는 거죠.",
    "s03": "볼넷이 무서워지는 순간이 있어요. 바로 만루. 베이스가 꽉 찬 상태에서 볼넷이 나오면, 주자들이 한 칸씩 밀려서 3루 주자가 그냥 홈을 밟습니다. 이게 밀어내기예요. 투수가 공 네 개로 점수를 헌납하는, 야구에서 제일 허무한 실점이죠.",
    "s04": "자, 여기서 재밌는 게 뭐냐면요. 처음부터 네 개가 아니었습니다. 1879년, 볼넷이 처음 생겼을 때는 볼 아홉 개였어요. 아홉 개! 타자가 걸어 나가려면 한나절이 걸렸죠. 구경하던 관중이 졸 만도 합니다.",
    "s05": "그런데 1884년에 어깨 위로 던지는 오버핸드 투구가 허용되면서 투수들이 너무 강해졌어요. 그래서 리그는 볼 개수를 깎기 시작합니다. 여덟 개, 일곱 개, 여섯 개, 다섯 개. 그리고 1889년, 드디어 네 개에 정착했죠. 그 뒤로 백삼십 년 넘게 한 번도 안 바뀐 숫자입니다.",
    "s06": "볼넷을 일부러 주는 경우도 있습니다. 상대 타자가 너무 무서우면, 차라리 1루를 내주고 다음 타자랑 승부하는 거죠. 이게 고의사구입니다. 옛날엔 포수가 일어서서 일부러 빠지는 공 네 개를 실제로 받아야 했어요. 다들 결과를 아는데도 말이죠.",
    "s07": "그래서 KBO는 2018년부터 자동 고의4구를 도입했습니다. 감독이 심판에게 사인만 보내면, 투수는 공 하나 안 던지고 타자를 1루로 보내요. 야구 역사상 가장 이상한 장면이죠. 아무 일도 안 일어났는데 타자가 걸어 나갑니다. 경기 시간을 아끼려는 변화였어요.",
    "s08": "여기서 고인물 상식 하나. 볼넷은 타율에 아무 영향이 없습니다. 타수 자체에 안 잡히거든요. 그래서 볼넷을 아무리 골라도 타율은 그대로예요. 대신 출루율이 올라갑니다. 타율은 낮은데 출루율이 높은 선수, 그 비밀이 바로 볼넷인 거죠. 흔히 눈야구라고 부르는 능력입니다.",
    "s09": "오해 하나 바로잡죠. 볼넷이랑 몸에 맞는 공은 달라요. 몸에 맞으면 볼 개수랑 상관없이 바로 1루입니다. 그리고 볼넷으로 나간 주자도 도루하고 득점하는 건 똑같아요. 공짜로 나갔다고 값어치가 떨어지는 게 아닙니다. 기록지에서는 볼넷과 몸에 맞는 공을 묶어서 사사구라고 부르기도 하고요.",
    "s10": "오늘 한 줄 요약. 볼넷은 투수의 실투 네 개가 만든 공짜 1루, 그리고 아홉 개에서 시작해 백삼십 년을 살아남은 숫자다. 다음 편은 몸에 맞는 공입니다. 맞으면 아픈데 왜 웃으면서 나갈까요? 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
