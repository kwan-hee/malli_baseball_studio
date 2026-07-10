# 수비번호 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "야구 중계 보다 보면 화면에 이런 자막 뜨죠. 6-4-3 병살. 5-4-3 삼중살. 이 숫자들, 그냥 아무렇게나 붙인 거 아닙니다. 그리고 여기 진짜 이상한 게 하나 있어요. 3루수는 5번인데, 바로 옆 유격수는 6번. 위치는 붙어 있는데 번호는 왜 뒤로 밀렸을까요? 여기엔 백 년도 더 된 사연이 있습니다.",
    "s02": "수비번호는 쉽게 말하면 아홉 개 수비 자리에 붙인 이름표예요. 기록지에 타구가 어디로 갔는지 빨리 적으려고 숫자로 약속을 정한 겁니다. 투수가 1번, 포수가 2번. 그다음 1루수 3번, 2루수 4번, 3루수 5번, 유격수 6번. 외야로 넘어가서 좌익수 7번, 중견수 8번, 우익수 9번이에요.",
    "s03": "그러니까 유격수가 공을 잡아서 1루로 던져 아웃시키면, 기록지엔 딱 6-3 이렇게 적습니다. 그 유명한 6-4-3 병살은요, 유격수 6번이 잡아서 2루수 4번한테, 다시 1루수 3번한테 넘긴 거예요. 숫자만 봐도 공이 어떻게 돌았는지 그림이 그려지죠.",
    "s04": "자, 여기서 중요한 거 하나. 이 수비번호는 등번호랑 완전히 다른 겁니다. 6번 유니폼 입었다고 그 선수가 유격수인 거 아니에요. 수비번호는 사람이 아니라 위치에 딱 붙어 있는 번호거든요.",
    "s05": "이 번호를 처음 만든 사람이 헨리 채드윅이라는 19세기 미국 기자예요. 야구 기록법의 아버지 같은 분인데, 재밌는 게 뭐냐면요, 크리켓 기록지를 보고 야구에 맞게 뜯어고친 겁니다. 근데 이 분이 처음 밀었던 방식은 지금이랑 달랐어요. 타순대로 번호를 매기자 했는데, 이게 안 먹혔죠.",
    "s06": "지금 우리가 쓰는 3루수 5번, 유격수 6번. 이걸 실제로 정리한 사람은 해리 라이트라는 감독이에요. 이 분이 남긴 기록장에 조그맣게 5, 6 이렇게 또박또박 적혀 있었고, 1909년쯤 되면 이 번호가 완전히 표준으로 굳어집니다.",
    "s07": "그럼 이 번호가 실제 경기에선 어떻게 쓰이냐. 2016년 6월, 잠실이었어요. 무사 1, 2루 위기 상황. 타자가 친 공이 3루수 글러브로 쏙 들어갑니다. 3루 밟고, 2루로, 다시 1루로. 순식간에 세 명이 아웃. 이게 기록지엔 5-4-3 삼중살로 남아요. KBO에선 손에 꼽게 드문 장면이죠.",
    "s08": "자, 많이들 헷갈리시는 거. 번호가 위치 순서대로 아니냐? 아니에요. 1루수 3번, 2루수 4번, 3루수 5번까지는 순서가 맞아요. 근데 유격수는 위치상 3루 바로 옆인데 번호는 6번으로 뒤에 있죠. 여기가 함정입니다.",
    "s09": "그 이유는 야구 초창기 유격수의 정체에 있어요. 유격수는 아홉 포지션 중에 가장 늦게, 1849년쯤 생긴 자리예요. 근데 처음엔 내야수가 아니었어요. 2루하고 중견수 사이에 서서 외야 송구를 중계하던, 말하자면 얕은 외야수였거든요. 그 시절 공이 크고 가벼워서 외야에서 베이스로 바로 못 던졌어요. 그래서 번호를 매길 때 내야 3루수까지 3, 4, 5를 다 붙이고, 반쯤 외야였던 유격수를 그다음 6번으로 넣은 겁니다. 위치가 아니라 역사가 만든 번호인 거죠. 이거 알면 여러분도 이제 고인물입니다.",
    "s10": "정리하면, 수비번호는 백 년 전 기록법에서 시작된 약속이고, 유격수가 6번인 건 옛날엔 걔가 외야수였기 때문이다, 이겁니다. 다음에 중계 보다가 6-4-3 자막 뜨면, 아 유격수 2루수 1루수구나 하고 바로 읽으실 거예요. 다음 편에서는 이 번호들이 제일 화려하게 터지는 순간, 삼중살을 제대로 파볼게요. 오늘 내용 쓸만했다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 만나요!",
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
