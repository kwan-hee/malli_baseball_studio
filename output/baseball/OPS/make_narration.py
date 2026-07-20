# OPS — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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

# cp949 콘솔에서 비-cp949 문자(em-dash 등) print 크래시 방지 (2026-07-18 유료루프 교훈)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    "s01": "자, 여기 두 타자가 있습니다. 둘 다 타율이 똑같이 3할이에요. 그럼 둘은 똑같은 타자일까요? 천만에요. 한 명은 볼넷도 잘 골라 나가고 홈런도 뻥뻥 치는데, 다른 한 명은 딱 안타만 칩니다. 타율은 이 차이를 못 잡아내요. 그래서 나온 게 바로 오늘의 주인공, 오피에스입니다.",
    "s02": "오피에스, 영어로 온 베이스 플러스 슬러깅. 우리말로 풀면, 출루율 더하기 장타율이에요. 이름 그대로, 두 지표를 툭 더한 값입니다. 타자가 얼마나 자주 루에 나가고, 또 얼마나 멀리 치는지. 이 두 가지를 한 숫자로 합쳐서, 타자의 진짜 생산력을 보여 주는 거죠.",
    "s03": "먼저 출루율. 이건 타자가 어떻게든 루를 밟는 능력이에요. 안타를 치든, 볼넷을 골라 걸어 나가든, 아웃 안 되고 루에 나가면 다 쳐줍니다. 타율은 안타만 따지지만, 출루율은 볼넷까지 인정해 줘요. 그래서 눈야구 잘하는 타자가 여기서 빛을 봅니다.",
    "s04": "다음은 장타율. 이건 한 방의 힘을 재는 지표예요. 똑같은 안타라도, 단타보다 2루타가, 2루타보다 홈런이 훨씬 값지잖아요? 단타는 한 점, 2루타는 두 점, 3루타는 세 점, 홈런은 무려 네 점. 이렇게 루타로 계산하니까, 뻥뻥 치는 거포일수록 장타율이 쭉쭉 올라가죠.",
    "s05": "자, 이 둘을 더한 게 오피에스인데요. 그럼 어느 정도면 잘하는 걸까요? 대략 8할, 그러니까 0.8을 넘으면 아주 좋은 타자예요. 0.9를 넘으면 리그를 대표하는 특급 타자, 그리고 딱 1.0을 넘으면요? 그건 그 시즌을 씹어먹는 괴물이라고 보시면 됩니다.",
    "s06": "이 지표, 생각보다 역사가 있어요. 1978년에 피트 파머라는 분이 처음 고안했고요. 1984년, 히든 게임 오브 베이스볼이라는 책으로 세상에 널리 알려졌습니다. 원래는 더 복잡한 계산식이었는데, 그냥 출루율 더하기 장타율, 이 단순한 형태가 계산도 쉽고 설명도 쉬워서 대박이 난 거예요.",
    "s07": "그럼 우리 KBO 최고 기록은 누구일까요? 바로 2015년, NC 다이노스의 에릭 테임즈입니다. 이 선수, 그 해 오피에스를 무려 1.287까지 찍었어요. 그 전까지 1위는 1982년 원년, 백인천 선수의 1.237이었는데, 무려 33년 만에 이 기록이 깨진 거죠. 정말 만화 같은 숫자입니다.",
    "s08": "자, 여기서 은근히 헷갈리는 거. 오피에스는 출루율 곱하기가 아니에요. 곱하기가 아니라, 더하기입니다. 출루율 0.4에 장타율 0.6, 이렇게 더해서 딱 1.0이 되는 거예요. 이름에 플러스, 그러니까 더하기가 괜히 들어간 게 아니랍니다.",
    "s09": "물론 오피에스도 완벽하진 않아요. 사실 야구에서는, 출루율이 장타율보다 득점에 더 중요하다고 하거든요. 그런데 오피에스는 둘을 그냥 1대 1로 더해 버리죠. 그래서 시대와 구장까지 보정한 오피에스 플러스, 또는 더 정교한 더블유오비에이 같은 지표가 나왔어요. 하지만 계산이 쉽고 직관적이라, 오피에스는 여전히 최고의 입문 지표입니다.",
    "s10": "정리하면요. 오피에스는 출루율과 장타율을 더해서, 타율이 놓치는 타자의 진짜 힘을 한 숫자로 보여 주는 지표예요. 다음에 중계 볼 때, 타자 오피에스가 8할을 넘는지 한번 확인해 보세요. 그 선수가 진짜 잘하는지 딱 보일 겁니다. 다음 편은, 이 오피에스의 절반인 출루율 이야기로 올게요. 오늘 도움이 됐다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 또 만나요!",
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
            # 최소 길이 가드: 잘린 take(Puck이 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10  # 정규화 글자수 × 0.10초
            if dur < min_dur:
                raise RuntimeError(f"truncated take: {dur:.1f}s < {min_dur:.1f}s expected - retry")
            write_wav(pcm, FULL_WAV)
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

    with wave.open(str(FULL_WAV), "rb") as wf:
        pcm = wf.readframes(wf.getnframes())
    total_dur = len(pcm) / (SR * BITS // 8)
    bps = SR * BITS // 8

    # 씬 경계 = 각 씬 첫 구절(정규화 14자)을 whisper 단어 스트림에서 접두어 퍼지 매칭 (2026-07-16 상시화).
    # 매칭 실패(환각 구간)면 글자수 비례 추정으로 graceful fallback. 필요시 fix_boundaries 로 보정.
    import difflib

    stream_times, stream_chars = [], []
    for w in words:
        for ch in norm(w["word"]):
            stream_chars.append(ch)
            stream_times.append(w["start"])
    S = "".join(stream_chars)

    sids = list(SCENES.keys())
    chars = {sid: len(norm(SCENES[sid])) for sid in sids}
    total_c = sum(chars.values())
    PREFIX_LEN, WINDOW = 14, 20.0

    boundaries = {sids[0]: 0.0}
    acc, prev_b = 0, 0.0
    for k, sid in enumerate(sids[1:], start=1):
        acc += chars[sids[k - 1]]
        est = total_dur * acc / total_c
        prefix = norm(SCENES[sid])[:PREFIX_LEN]
        cands, best_r, best_t = [], 0.0, None
        for i in range(len(S) - PREFIX_LEN):
            t = stream_times[i]
            if abs(t - est) > WINDOW or t <= prev_b + 1.0:
                continue
            r = difflib.SequenceMatcher(None, S[i:i + PREFIX_LEN], prefix).ratio()
            if r >= 0.75:  # 후렴 반복 함정 방지: 0.75+ 후보 중 추정치 근접 우선
                cands.append((t, r))
            if r > best_r:
                best_r, best_t = r, t
        if cands:
            best_t, best_r = min(cands, key=lambda c: abs(c[0] - est))
        if best_t is None or best_r < 0.55:
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)  # 환각 구간 - 비례 폴백
            print(f"{sid}: prefix match weak (best={best_r:.2f}) - proportional fallback @ {b:.2f}")
        else:
            b = max(prev_b + 1.0, best_t - BOUNDARY_MARGIN)
        boundaries[sid] = b
        prev_b = b

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
