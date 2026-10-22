# 누의 공과 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "/opt/homebrew/bin:/usr/local/bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
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
    "s01": "주자가 2루를 안 밟고 3루까지 그냥 뛰어갑니다. 심판도 두 눈으로 똑똑히 봤어요. 그런데 아웃을 안 줍니다. 세이프예요. 명백한 규칙 위반인데 왜 안 잡을까요? 오늘의 야구사전, 누의 공과입니다.",
    "s02": "누의 공과, 한자를 풀면 이래요. 누는 베이스, 공과는 비우고 지나쳤다는 뜻입니다. 그러니까 밟아야 할 베이스를 안 밟고 지나친 거예요. 주자는 1루, 2루, 3루, 홈을 순서대로 밟아야 하는데, 그중 하나를 건너뛴 거죠.",
    "s03": "여기서 진짜 핵심이 나옵니다. 이건 어필 플레이예요. 심판이 그 장면을 두 눈으로 봤어도, 수비가 직접 지적하지 않으면 아무 일도 안 일어납니다. 그냥 경기가 그대로 흘러가요.",
    "s04": "수비가 어필하는 방법은 두 가지입니다. 공을 들고 주자가 건너뛴 그 베이스를 밟거나, 아니면 주자 몸을 직접 태그하는 거예요. 그렇게 심판에게 알려야 비로소 아웃이 선언됩니다.",
    "s05": "좀 이상하죠? 심판이 봤는데 왜 가만히 있나. 여기에 야구만의 독특한 철학이 있어요. 어떤 상황은 일부러 수비한테 맡겨둔 겁니다. 너희가 직접 지적해라. 이걸 어필 플레이라고 불러요.",
    "s06": "대신 조건이 하나 있습니다. 시효예요. 언제까지고 어필할 수 있는 게 아니라, 다음 투구나 다음 플레이가 시작되면 그 기회가 사라집니다. 그러니까 수비는 알아챈 그 순간 바로 움직여야 해요.",
    "s07": "자, KBO 역사에 길이 남은 장면을 하나 볼까요. 2011년 5월 3일 사직구장, 삼성과 롯데 경기입니다. 1루에 삼성 채태인 선수가 있었어요. 타자가 우중간으로 깊은 타구를 날립니다.",
    "s08": "채태인, 2루를 돌아 3루로 가려는데 외야수가 공을 잡을 것 같아요. 급히 되돌아 2루를 밟고 1루 쪽으로 향합니다. 그런데 이 공이 안타로 툭 떨어져요. 마음이 급해진 채태인, 여기서 그만 사고를 칩니다.",
    "s09": "2루로 정상적으로 가는 대신, 마운드 옆 잔디를 가로질러 곧장 3루로 직행해 버려요. 2루를 안 밟은 겁니다. 롯데 조성환 선수가 공을 잡아 2루를 밟고 어필. 아웃. 새 항로를 개척했다고, 채럼버스라는 별명까지 붙은 전설의 장면입니다.",
    "s10": "오해 하나만 짚고 갈게요. 심판이 봤으면 알아서 아웃 주겠지? 아닙니다. 수비가 어필 안 하면 세이프예요. 게다가 홈을 밟아 득점한 뒤에도, 그 주자가 루를 하나 빠뜨렸다면 어필로 점수를 취소시킬 수 있습니다. 다음 편은 리터치입니다. 오늘 내용이 쓸 만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
            # 최소 길이 가드: 잘린 take(Kore/Puck이 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10  # 정규화 글자수 × 0.10초
            if dur < min_dur:
                raise RuntimeError(f"truncated take: {dur:.1f}s < {min_dur:.1f}s expected — retry")
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
    # 기존 누적 글자 방식은 whisper 오전사/환각으로 뒤 씬 경계가 통째로 밀려 붕괴 → 접두어 매칭으로 교체.
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
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)  # 환각 구간 — 비례 폴백
            print(f"{sid}: prefix match weak (best={best_r:.2f}) — proportional fallback @ {b:.2f}")
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
