# 하린이와 초코의 이상한 나라 (강의 샘플) — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)
SNAP_WINDOW = 1.5  # whisper 경계를 실측 무음으로 옮길 탐색 반경 (초)

# 성우 연기 지시 (TTS에만 전달, 자막·낭독에는 미포함) — 공통 톤 + 씬별 감정
# 속도: '천천히·문장 사이 여유'를 넣으면 2.5 대비 30% 느려짐(41편 테스트 194s→253s) → 자연스러운 속도로 지시
BASE_STYLE = "잠자리 그림책을 읽어 주는 다정한 동화 구연 성우, 5~7세 아이에게 들려주듯 또박또박, 포근하고 사랑스럽게, 자연스러운 속도, 문장 사이 쉼은 짧게"
SCENE_STYLES = {
    "s01": "고요한 밤 분위기로 소곤소곤 시작해서, 그림책이 반짝이는 대목은 신비롭게, 초코가 뛰어드는 대목은 깜짝 놀라게",
    "s02": "초코를 부르는 대사는 다급하지만 귀엽게, 떠내려가는 대목은 꿈꾸듯 둥실둥실 부드럽게",
    "s03": "호기심 가득하게, 앨리스 대사는 상냥하고 반갑게",
    "s04": "신비롭게, 체셔 고양이 대사는 장난스럽고 능청스럽게",
    "s05": "즐겁고 들뜨게, 모자 장수 대사는 유쾌하게, 마지막 후렴은 씩씩하게",
    "s06": "두근두근 조심스럽게 시작해서, 물감을 엎는 대목은 아이고 하듯, 여왕 대사는 투덜투덜 우습게(무섭지 않게)",
    "s07": "신나고 빠르게, 바람이 부는 대목부터는 시원하고 통쾌하게, 웃음은 밝게",
    "s08": "따뜻하고 살짝 아쉽게, 앨리스 작별 대사는 다정하고 애틋하게",
    "s09": "잠에서 깨듯 나른하고 부드럽게, 하트 카드를 발견하는 대목은 설레게",
    "s10": "아주 포근하고 졸리게, 교훈은 차분하고 따뜻하게, 마지막 인사는 속삭이듯",
}

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "까만 밤, 하린이는 초코와 함께 침대에 누웠어요. 오늘 밤 그림책은 이상한 나라의 앨리스예요. 하린이가 하아암, 하품을 하는 순간이었어요. 그림책 속 토끼 굴이 반짝반짝 빛나기 시작했어요. 초코가 꼬리를 살랑 흔들더니, 굴 속으로 쏙 들어가 버렸어요!",
    "s02": "초코야, 기다려! 같이 가자! 하린이도 초코를 따라 굴 속으로 들어갔어요. 둥실, 둥실. 하린이와 초코는 깃털처럼 천천히 내려갔어요. 찻잔도, 시계도, 그림책도 함께 둥둥 떠다녔어요. 하나도 무섭지 않았어요. 초코가 옆에 있었으니까요.",
    "s03": "도착한 곳은 아주 작은 문이 있는 방이었어요. 탁자 위에는 나를 마셔요, 라고 적힌 병이 있었어요. 하린이와 초코가 한 모금씩 마시자, 둘 다 쏙 작아졌어요. 그때 금빛 머리의 여자아이가 다가왔어요. 안녕, 나는 앨리스야. 너희도 길을 잃었구나?",
    "s04": "셋은 나란히 숲길을 걸었어요. 나뭇가지 위에 커다란 웃음 하나가 둥실 떠올랐어요. 히히, 집에 가고 싶니? 줄무늬 체셔 고양이였어요. 집으로 가는 문은 여왕님 정원 너머에 있지. 고양이는 웃음만 남기고 스르르 사라졌어요.",
    "s05": "숲 속 빈터에서는 신나는 차 모임이 열리고 있었어요. 커다란 모자를 쓴 모자 장수가 외쳤어요. 생일 아닌 날, 축하해! 하린이도 초코도 함께 노래를 불렀어요. 모자 장수는 시계 모양 열쇠를 건네주었어요. 이 열쇠가 집으로 가는 문을 열어 줄 거야. 초코야, 같이 가자!",
    "s06": "드디어 하트 여왕님의 정원에 왔어요. 카드 병정들이 하얀 장미를 빨갛게 칠하고 있었어요. 그런데 초코가 꼬리를 흔들다가, 물감 통을 엎어 버렸어요. 하얀 길이 온통 빨갛게 물들었어요. 여왕님이 발을 동동 구르며 소리쳤어요. 누가 내 정원을 이렇게 만들었느냐!",
    "s07": "카드 병정들이 허둥지둥 쫓아오기 시작했어요. 얘들아, 달려! 앨리스가 외쳤어요. 초코야, 같이 가자! 셋은 장미 덤불 사이로 힘껏 달렸어요. 그때 시원한 바람이 휘이잉 불어왔어요. 카드 병정들이 와르르 흩어져 하늘로 날아갔어요. 하린이와 앨리스는 깔깔 웃었어요.",
    "s08": "정원 끝에 작고 둥근 문이 있었어요. 하린이가 시계 열쇠를 넣고 돌리자, 철컥 문이 열렸어요. 문 너머로 따뜻한 빛이 쏟아졌어요. 앨리스, 같이 가지 않을래? 나는 내 집으로 가야 해. 하지만 또 놀러 와. 꿈에서 기다릴게. 하린이와 앨리스는 서로를 꼭 안아 주었어요.",
    "s09": "눈을 떠 보니, 하린이는 자기 침대에 누워 있었어요. 초코도 옆에서 새근새근 자고 있었어요. 모두 꿈이었을까요? 그런데 베개 옆에 작은 하트 카드 한 장이 놓여 있었어요. 하린이는 카드를 꼭 쥐고 살며시 웃었어요.",
    "s10": "엄마가 들어와 이불을 포근히 덮어 주었어요. 엄마, 나 내일 밤에도 앨리스 만나는 꿈 꿀래. 그래, 초코랑 같이 다녀오렴. 낯선 곳에서도 함께라면, 언제나 길을 찾을 수 있어요. 하린이는 초코를 꼭 안고 스르르 잠이 들었어요. 잘 자요, 우리 친구들.",
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
    # 씬마다 text 1개 + 그 씬의 style — 한 요청(user_input 1개) 안에 전부 담아 단일 호출 유지
    content = [
        {
            "type": "text",
            "text": text,
            "annotations": [{"type": "speech_metadata", "style": f"{BASE_STYLE}, {SCENE_STYLES[sid]}"}],
        }
        for sid, text in SCENES.items()
    ]
    body = json.dumps({
        "model": MODEL,
        "input": [{"type": "user_input", "content": content}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": VOICE}]},
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
                    pool.rotate()  # 키 소진 → 다음 계정으로 (pool.idx 갱신)
                    continue
                except RuntimeError:
                    sys.exit("all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    sys.exit("full TTS: all retries failed")


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
    silences = find_silences(pcm)

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
    generate_full()
    need = [s for s in SCENES if not (OUT / f"{s}.wav").exists()]
    if need:
        split_scenes()
    else:
        print("scene wavs: cached")
