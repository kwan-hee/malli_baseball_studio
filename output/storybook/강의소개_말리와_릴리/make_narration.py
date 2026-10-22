# 강의 소개 영상 「말리의 동화나라」 — 나레이션: 화자별 Gemini TTS 단일 호출 2회(말리 Kore / 릴리 Leda) + Whisper large-v3 장면 분할
# 2026-10-22 결정: 화자가 둘이라 '전체 대본 단일 호출' 규칙을 화자별로 적용 (각 화자 톤 일정). 대사는 콘티 md 원문 그대로.
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 씬 시작 금지 (2026-07-16 까치편 whisper 환각 교훈)
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
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

# 2026-10-15: gemini-3.8-flash-tts 로 교체 (사용자 A/B 청취 후 승인).
# 3.8 은 text 를 전부 그대로 낭독함 — 연기 지시를 대본 앞에 붙이면 지시문까지 읽어 버린다.
# 지시는 Interactions API 의 speech_metadata.style 로 씬(문단)별 분리 전달, 호출은 여전히 1회.
# google-genai 2.9.0 SDK 는 2번째 이후 annotation 을 'UNKNOWN' 으로 직렬화해 400 → raw REST 로 호출.
MODEL = "gemini-3.8-flash-tts"
API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
VOICES = {"malli": "Kore", "lily": "Leda"}  # 혼용 금지 (07_AUDIO.md)
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)
SNAP_WINDOW = 1.5  # whisper 경계를 실측 무음으로 옮길 탐색 반경 (초)

# 성우 연기 지시 (TTS에만 전달, 자막·낭독에는 미포함) — 화자 공통 톤 + STAGE별 감정
BASE_STYLE = {
    "malli": "강아지 캐릭터 말리가 강의를 소개하는 목소리, 밝고 맑고 귀여운 여자아이 같은 말투, 신나고 사랑스럽게, 감정 풍부하게, 자연스러운 속도, 문장 사이 쉼은 짧게",
    # docs/07_AUDIO.md 릴리 선생 BASE_STYLE
    "lily": "20대 초반의 밝고 친근한 여자 강사, 학생들 앞에서 실제로 강의하듯 자연스럽게. 책 읽는 말투가 아니라 말하듯이, 감정 풍부하게, 웃음기와 호기심이 살아 있게, 자연스러운 속도",
}
STAGE_STYLES = {
    1: "처음 만나 반갑고 설레게",
    2: "사람을 소개하듯 다정하고 자랑스럽게, 자기소개는 진솔하고 든든하게",
    3: "기대감을 담아 신나게, 완성작을 보여 줄 때는 두근두근하게",
    4: "고마운 마음은 진심으로, 선물을 하나씩 열어 보이듯 또렷하고 즐겁게",
    5: "길을 차근차근 안내하듯 편안하고 또박또박",
    6: "다음 강의를 기대하게 만들며 따뜻하게, 마지막 인사는 밝고 힘차게",
}

from storyboard import SCENES as BOARD

# 대본 단일 출처 — 콘티 md 의 대사 칸 원문 (compose.py 가 import 해서 자막도 여기서 생성)
SCENES = {s["id"]: s["line"] for s in BOARD if s["speaker"]}
SPEAKER = {s["id"]: s["speaker"] for s in BOARD if s["speaker"]}
STAGE = {s["id"]: s["stage"] for s in BOARD}


def write_wav(pcm, path):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm)


def norm(text):
    return "".join(ch for ch in text if ch.isalnum())


def generate_full(spk):
    FULL_WAV = OUT / f"narration_{spk}.wav"
    scenes = {k: v for k, v in SCENES.items() if SPEAKER[k] == spk}
    if FULL_WAV.exists() and FULL_WAV.stat().st_size > 100000:
        print(f"{spk} narration: cached")
        return
    pool = GeminiPool()
    # 씬마다 text 1개 + 그 씬의 style — 한 요청(user_input 1개) 안에 전부 담아 단일 호출 유지
    content = [
        {
            "type": "text",
            "text": text,
            "annotations": [{"type": "speech_metadata", "style": f"{BASE_STYLE[spk]}, {STAGE_STYLES[STAGE[sid]]}"}],
        }
        for sid, text in scenes.items()
    ]
    body = json.dumps({
        "model": MODEL,
        "input": [{"type": "user_input", "content": content}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": VOICES[spk]}]},
    }).encode("utf-8")
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                API_URL, data=body, method="POST",
                headers={"Content-Type": "application/json", "x-goog-api-key": pool.keys[pool.idx]},
            )
            try:
                resp = json.loads(urllib.request.urlopen(req, timeout=600).read())
            except urllib.error.HTTPError as he:
                raise RuntimeError(f"HTTP {he.code}: {he.read().decode('utf-8', 'replace')[:300]}") from he
            audio = next(c for st in resp["steps"] for c in st.get("content", []) if c.get("type") == "audio")
            # 3.8 은 RIFF 헤더 포함 wav 를 돌려줌 — PCM 만 꺼내서 기존 write_wav/분할 로직 그대로 사용
            with wave.open(io.BytesIO(base64.b64decode(audio["data"])), "rb") as wf:
                if (wf.getframerate(), wf.getsampwidth() * 8, wf.getnchannels()) != (SR, BITS, CH):
                    raise RuntimeError(f"unexpected wav format {wf.getframerate()}Hz/{wf.getsampwidth()*8}bit/{wf.getnchannels()}ch")
                pcm = wf.readframes(wf.getnframes())
            # 최소 길이 가드: 잘린 take(Kore가 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(scenes.values()))) * 0.10  # 정규화 글자수 × 0.10초
            if dur < min_dur:
                raise RuntimeError(f"truncated take: {dur:.1f}s < {min_dur:.1f}s expected — retry")
            write_wav(pcm, FULL_WAV)
            print(f"{spk} narration: {len(pcm):,} PCM bytes ({dur:.1f}s)")
            return
        except Exception as e:
            err = str(e)
            print(f"full TTS attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
            if is_quota_error(err):
                try:
                    pool.rotate()  # 키 소진 → 다음 계정으로 (pool.idx 갱신)
                    continue
                except RuntimeError:
                    sys.exit("all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    sys.exit(f"{spk} TTS: all retries failed")


def find_silences(pcm, frame_s=0.02, thresh_db=-40.0, min_len=0.2):
    """16bit mono PCM 에서 RMS < thresh_db(dBFS) 가 min_len 초 이상 이어지는 구간 [(start, end), ...]."""
    import array
    import math

    samples = array.array("h", pcm)
    n = int(SR * frame_s)
    out, run_start = [], None
    for f in range(len(samples) // n):
        chunk = samples[f * n:(f + 1) * n]
        rms = math.sqrt(sum(x * x for x in chunk) / n) or 1e-9
        quiet = 20 * math.log10(rms / 32768) < thresh_db
        t = f * frame_s
        if quiet and run_start is None:
            run_start = t
        elif not quiet and run_start is not None:
            if t - run_start >= min_len:
                out.append((run_start, t))
            run_start = None
    return out


def split_scenes(spk, model):
    import json

    FULL_WAV = OUT / f"narration_{spk}.wav"
    scenes = {k: v for k, v in SCENES.items() if SPEAKER[k] == spk}
    result = model.transcribe(str(FULL_WAV), language="ko", word_timestamps=True)
    words = [w for seg in result["segments"] for w in seg["words"]]
    if not words:
        sys.exit("whisper returned no words")

    # 자막 실측 생성용(A안) — compose.py 가 글자수 비례 대신 이 실측으로 SRT 생성
    (OUT / f"words_{spk}.json").write_text(
        json.dumps([{"word": w["word"], "start": w["start"], "end": w["end"]} for w in words],
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"words_{spk}.json: {len(words)} words")

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

    sids = list(scenes.keys())
    chars = {sid: len(norm(scenes[sid])) for sid in sids}
    total_c = sum(chars.values())
    PREFIX_LEN, WINDOW = 14, 20.0
    silences = find_silences(pcm)

    boundaries = {sids[0]: 0.0}
    acc, prev_b = 0, 0.0
    for k, sid in enumerate(sids[1:], start=1):
        acc += chars[sids[k - 1]]
        est = total_dur * acc / total_c
        prefix = norm(scenes[sid])[:PREFIX_LEN]
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
        # 무음 스냅 (2026-10-15, 3.8 TTS 도입 시 사용자 승인): whisper 단어 시작이 쉼 근처에서 ~1초 어긋남
        # → 경계 ±SNAP_WINDOW 안의 실측 무음 구간 중 가장 긴 것의 가운데로 이동 (32편 수동 보정의 자동화)
        # '가장 가까운' 무음은 문장 중간 숨 고르기를 잡음 — 씬 경계 = 문단 끝이라 쉼이 가장 김
        near = [(s1 - s0, (s0 + s1) / 2) for s0, s1 in silences
                if s1 > b - SNAP_WINDOW and s0 < b + SNAP_WINDOW and (s0 + s1) / 2 > prev_b + 1.0]
        if near:
            snapped = max(near)[1]
            print(f"{sid}: snap {b:.2f} -> {snapped:.2f} (silence)")
            b = snapped
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
    for spk in VOICES:
        generate_full(spk)
    model = None
    for spk in VOICES:
        need = [s for s in SCENES if SPEAKER[s] == spk and not (OUT / f"{s}.wav").exists()]
        if need:
            if model is None:
                import whisper

                print("loading whisper large-v3 ...")
                model = whisper.load_model("large-v3")
            split_scenes(spk, model)
        else:
            print(f"{spk} scene wavs: cached")
