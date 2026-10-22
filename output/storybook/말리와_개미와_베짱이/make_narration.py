# 말리와 개미와 베짱이 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 씬 시작 금지 (2026-07-16 까치편 whisper 환각 교훈)
import base64
import os
import sys
import time
import wave
from pathlib import Path

# cp949 콘솔에서 em-dash 등 비-cp949 문자 print 시 UnicodeEncodeError 로 죽는 것 방지
# (2026-07-19 도깨비감투 편: 폴백 경고 print의 em-dash가 whisper 씬분할 후 크래시 유발)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 여름에 노래하는 베짱이는 밝고 흥겹게, "
    "부지런히 일하는 개미는 씩씩하고 다부지게, "
    "겨울에 춥고 배고픈 베짱이는 가엾고 떨리는 목소리로, "
    "개미가 따뜻하게 맞아 주는 장면은 다정하고 포근하게, "
    "베짱이가 뉘우치며 고마워하는 장면은 뭉클하고 진심 어리게, "
    "봄에 다 함께 어울려 노래하는 마지막은 즐겁고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은 아주 유명한 이야기를 가지고 왔어요. 부지런한 개미와, 노래를 좋아하는 베짱이 이야기랍니다. 미리 준비하는 마음, 그리고 따뜻하게 나누는 마음에 대한 이야기예요. 자, 우리 함께 떠나 볼까요?",
    "s02": "햇살이 쨍쨍한 여름날이었어요. 개미들은 아침부터 저녁까지 땀을 뻘뻘 흘리며 먹이를 나르고 있었지요. 무거운 밀알을 지고 줄지어 걸어가는 개미들. 모두 추운 겨울을 준비하느라 아주 바빴답니다. 그런데 저기, 시원한 나무 그늘 아래에서는 베짱이가 즐겁게 노래를 부르고 있었어요.",
    "s03": "베짱이가 개미에게 말을 걸었어요. 개미야, 이렇게 좋은 날에 왜 일만 하니? 나처럼 노래도 부르고 신나게 놀자! 그러자 개미가 씩씩하게 대답했지요. 지금 부지런히 모아 두어야, 추운 겨울에 굶지 않는단다. 하지만 베짱이는 고개를 절레절레 흔들었어요. 겨울은 아직 멀었는걸, 뭘!",
    "s04": "여름 내내 베짱이는 바이올린을 켜며 노래했어요. 랄랄라, 여름은 정말 즐거워! 나비와 함께 빙글빙글 춤을 추고, 시원한 냇가에서 물장구도 쳤지요. 베짱이에게는 매일매일이 신나는 소풍 같았답니다. 개미들이 구슬땀을 흘리며 일하는 동안에도, 베짱이는 그저 놀기만 했어요.",
    "s05": "친구들, 베짱이는 정말 즐거워 보이죠? 그런데 말이에요, 이렇게 놀기만 하다가 추운 겨울이 오면 과연 어떻게 될까요? 음, 어쩐지 조금 걱정이 되네요. 우리 함께 계속 지켜볼까요?",
    "s06": "즐겁던 여름이 지나고, 어느새 하얀 눈이 펑펑 내리는 겨울이 찾아왔어요. 온 세상이 꽁꽁 얼어붙었지요. 베짱이는 그제서야 덜덜 떨기 시작했어요. 먹을 것도 하나 없고, 몸을 녹일 따뜻한 집도 없었거든요. 배에서는 자꾸만 꼬르륵 소리가 났답니다.",
    "s07": "배고프고 추운 베짱이는 눈밭을 힘없이 걷다가, 저 멀리 따뜻한 불빛이 새어 나오는 개미네 집을 발견했어요. 베짱이는 조심스럽게 문을 똑똑 두드렸지요. 개미야, 나… 너무 춥고 배가 고파. 베짱이의 목소리가 파르르 떨렸답니다.",
    "s08": "그러자 개미가 문을 활짝 열어 주었어요. 그런데 개미는 베짱이를 나무라지 않았지요. 오히려 따뜻하게 웃으며 말했어요. 어서 들어와, 베짱이야! 여기 따뜻한 수프랑 빵이 있단다. 개미는 여름내 정성껏 모은 먹이를, 베짱이와 기꺼이 나누어 주었답니다.",
    "s09": "따뜻한 수프를 먹으며 베짱이는 눈물이 핑 돌았어요. 개미야, 정말 고마워. 그리고 미안해. 나도 이제부터 열심히 준비할게. 이듬해 봄, 베짱이는 개미와 나란히 부지런하게 일했어요. 그리고 일이 끝나면, 베짱이의 즐거운 노래에 맞춰 다 함께 어깨동무하고 춤을 추었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 개미처럼 미리미리 준비하는 마음도, 따뜻하게 나누는 마음도 정말 멋지죠? 여러분도 오늘 해야 할 일을 미루지 않고 해 보는 건 어떨까요? 오늘 이야기가 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 더 재미있는 이야기로 만나요. 안녕, 멍멍!",
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
            # 최소 길이 가드: 잘린 take(Kore가 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
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
    # 매칭 실패(환각 구간)면 글자수 비례 추정으로 graceful fallback (붕괴 대신 근사치). 필요시 fix_boundaries 로 보정.
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
