# 강의 챕터1 「시작하기 전에」 말리 프레젠테이션 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
BASE_STYLE = "강아지 캐릭터 말리가 강의 오리엔테이션을 진행하는 목소리, 밝고 맑고 귀여운 여자아이 같은 말투, 처음 배우는 어른 수강생에게 친절하고 또박또박 설명하듯, 자연스러운 속도, 문장 사이 쉼은 짧게"
SCENE_STYLES = {
    "s01": "반갑고 신나게 인사하며 시작해서, 강의 소개는 설레는 목소리로, 마지막 질문은 다정하게",
    "s02": "기대감을 담아 또렷하게, 만드는 순서를 말하는 대목은 하나씩 짚어 주듯 리듬감 있게",
    "s03": "걱정하는 수강생을 다독이듯 따뜻하게, 코딩 몰라도 된다는 대목은 자신 있게, 마지막은 경쾌하게",
    "s04": "도구를 하나씩 소개하듯 또박또박, 각 도구 설명은 친근한 비유처럼 즐겁게",
    "s05": "처음엔 공감하듯 살짝 걱정스럽게, 방법을 알려 주는 대목부터는 안심시키듯 차분하고 든든하게",
    "s06": "편안하고 친절하게, 막혔을 때 묻는 법은 쉽고 다정하게 알려 주듯",
    "s07": "조금 진지하고 또렷하게, 다섯 가지 약속을 하나, 둘 세며 힘주어 차근차근",
    "s08": "뿌듯하고 힘차게 응원하듯, 마지막 인사는 밝고 사랑스럽게",
}

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
# 씬 시작 문장은 전부 고유 + 의성어 씬 시작 금지 (까치편 whisper 환각 교훈)
SCENES = {
    "s01": "안녕하세요, 여러분! 저는 말리예요. 오늘부터 여러분과 함께 AI로 우리 아이 동화를 만들어 볼 거예요. 본격적으로 시작하기 전에, 꼭 알아 두면 좋은 것들을 먼저 알려 드릴게요. 챕터 1, 시작하기 전에! 지금부터 하나씩 같이 볼까요?",
    "s02": "첫 번째, 이 강의에서 무엇을 만드는지부터 소개할게요. 강의를 마치면, 우리 아이와 반려동물이 주인공인 동화 영상이 여러분 손에 남아요. 한국어 영상도, 영어 영상도 함께요. 순서는 아주 간단해요. 캐릭터를 만들고, 이야기를 쓰고, 목소리를 입히고, 영상으로 완성해요. 누가, 무엇을, 어떤 순서로 만드는지, 이제 감이 오시죠?",
    "s03": "두 번째는 준비물 확인이에요. 나도 할 수 있을까, 걱정되시죠? 컴퓨터 한 대와 인터넷만 있으면 충분해요. 운영체제와 메모리가 괜찮은지는 강의에서 같이 확인해 드릴게요. 그리고 코딩은 몰라도 괜찮아요. 어려운 부분은 AI가 대신 해 주거든요. 파일을 저장하고, 폴더를 만들 줄 알면 준비 끝이에요!",
    "s04": "세 번째는 우리가 함께 쓸 AI 도구들이에요. 클로드는 이야기를 같이 쓰고, 작업을 도와주는 똑똑한 친구예요. VS Code는 우리가 작업하는 책상이에요. 제미나이는 그림과 목소리를 만들어 주고요. 힉스필드는 그림을 움직이는 영상으로 바꿔 줘요. 처음에는 무료로 시작하고, 꼭 필요할 때 유료로 바꾸면 돼요. 언제 가입하면 되는지, 한 편에 비용이 얼마쯤 드는지도 강의에서 알려 드릴게요.",
    "s05": "네 번째, 요금 폭탄이 걱정되시나요? 걱정 마세요, 방법이 있어요. 먼저, 내가 얼마나 썼는지 사용량을 자주 확인해요. 그리고 결제 한도를 미리 정해 두면, 생각보다 많이 쓰는 일을 막을 수 있어요. 구독은 언제든 해지할 수 있어요. 영상을 여러 번 다시 만들면 비용이 빨리 늘어나니까, 그것만 조심하면 돼요.",
    "s06": "다섯 번째는 이 강의를 잘 듣는 방법이에요. 추천 수강 일정대로 천천히 따라오시면 충분해요. 워크북과 예시 파일, 용어집도 꼭 함께 펼쳐 두세요. 그러다 막히면, 클로드에게 물어보세요. 지금 화면을 캡처해서 보여 주고, 무엇이 안 되는지 그대로 말하면 돼요. 그래도 어렵다면, 코칭권으로 선생님께 직접 도움을 받을 수 있어요.",
    "s07": "마지막 여섯 번째, 시작 전에 꼭 지킬 약속 다섯 가지예요. 하나, 우리 아이의 실제 사진은 AI에 올리지 않아요. 연습할 때는 예시 사진을 써요. 둘, 저 말리는 연습용 캐릭터예요. 공개할 작품에는 여러분만의 캐릭터를 써 주세요. 셋, 저작권 걱정 없는 옛이야기로만 동화를 만들어요. 넷, API 키는 비밀번호처럼 나만 봐요. 다섯, 영상을 공개할 때는 AI로 만들었다고 꼭 표시해요.",
    "s08": "자, 이제 준비가 모두 끝났어요! 무엇을 만들고, 무엇이 필요하고, 무엇을 조심해야 하는지 다 알았죠? 여러분도 충분히 할 수 있어요. 제가 처음부터 끝까지 옆에서 함께할게요. 그럼 다음 챕터에서 만나요. 안녕!",
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
