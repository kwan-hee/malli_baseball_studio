# 말리와 소가 된 게으름뱅이 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
BASE_STYLE = "어린이 동화 구연 성우, 5~7세 아이에게 들려주듯 또박또박, 밝고 사랑스럽게, 자연스럽고 경쾌한 속도, 문장 사이 쉼은 짧게"
SCENE_STYLES = {
    "s01": "말리가 반갑고 신나게 인사, 소가 되어 버린다는 대목은 깜짝 놀란 듯 귀엽게",
    "s02": "옛날이야기를 시작하듯 다정하게, 어머니 대사는 다정하게 부르듯, 돌쇠 대사는 늘어지게 하품하며 게으르게",
    "s03": "살금살금 빠져나가듯 장난스럽게, 돌쇠 혼잣말은 부러운 듯 나른하게",
    "s04": "신비롭게 시작해서, 할아버지 대사는 느긋하고 수상쩍게(무섭지 않게), 소로 변하는 대목은 깜짝 놀라고 신기하게",
    "s05": "아이들에게 다급하게 알려 주듯, 할아버지 말을 전하는 대목은 수수께끼처럼 궁금하게",
    "s06": "돌쇠 외침은 억울하고 다급하게, 음매 소리는 풀 죽어 처량하게(우습고 귀엽게), 힘든 대목은 안쓰럽게",
    "s07": "조금씩 밝아지듯 따뜻하게, 농부 대사는 투박하지만 다정하게, 새싹 대목은 뿌듯하고 흐뭇하게",
    "s08": "차분하고 뭉클하게, 어머니를 그리는 대목은 그립고 애틋하게, 무를 발견하는 대목은 반짝 기대되게",
    "s09": "신기하고 기쁘게 터지듯, 돌쇠 대사는 감격스럽고 씩씩하게, 마지막 문장은 흐뭇하게",
    "s10": "교훈은 차분하고 따뜻하게, 구독 부탁과 마지막 인사는 말리처럼 귀엽고 신나게",
}

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 일하기 싫어서 누워만 있던 게으름뱅이 총각 이야기를 가져왔어요. 그런데 이 총각이 글쎄, 진짜 소가 되어 버린대요! 땀 흘려 일하는 게 왜 즐거운지, 함께 알아볼까요?",
    "s02": "옛날 옛날, 어느 산골 마을에 돌쇠라는 총각이 살았어요. 돌쇠는 해가 중천에 떠도, 이불 밖으로 나올 생각을 안 했지요. 돌쇠야, 밭에 좀 나가 보렴! 어머니가 불러도 돌쇠는 하품만 했어요. 아함, 귀찮아. 나 일하기 싫은데~",
    "s03": "하루는 어머니 잔소리를 피해서, 돌쇠가 슬그머니 집을 빠져나왔어요. 고갯마루 나무 그늘에 누운 돌쇠는, 풀을 뜯는 소를 보며 중얼거렸지요. 소는 좋겠다. 풀만 먹고 누워 있으면 되잖아. 나도 소가 되면 좋겠다!",
    "s04": "바로 그때, 하얀 수염이 긴 할아버지 한 분이 나타났어요. 할아버지 손에는, 소머리 모양의 탈이 들려 있었지요. 젊은이, 이걸 한번 써 보겠나? 일 안 하고 편하게 지낼 수 있다네. 돌쇠는 좋아라 하며 탈을 덥석 써 보았어요. 그런데 이게 웬일이에요? 돌쇠가 정말로, 커다란 누렁소가 되어 버린 거예요!",
    "s05": "친구들, 큰일 났어요! 돌쇠가 진짜 소가 되어 버렸어요! 할아버지는 소가 된 돌쇠에게 이렇게 말했대요. 일하는 기쁨을 알게 되는 날, 무 한 입이 너를 돌려보내 줄 거란다. 무 한 입이라니, 무슨 뜻일까요? 우리 끝까지 지켜봐요!",
    "s06": "소가 된 돌쇠는, 할아버지를 따라 어느 농부 아저씨네 집에 가게 되었어요. 저는 소가 아니에요! 사람이라고요! 하지만 입에서 나오는 소리는, 음매~ 뿐이었지요. 다음 날부터 돌쇠는 밭을 갈고, 무거운 짐을 날라야 했어요. 음매~ 나 일하기 싫은데~ 돌쇠는 힘들어서 눈물이 찔끔 났답니다.",
    "s07": "그렇게 며칠이 지나자, 돌쇠의 마음이 조금씩 달라지기 시작했어요. 농부 아저씨는 일이 끝나면, 돌쇠의 등을 쓰다듬어 주었지요. 오늘도 수고 많았다, 고맙구나. 땀 흘린 뒤에 먹는 밥은, 누워서 먹던 밥보다 훨씬 꿀맛이었어요. 내가 간 밭에서 파란 새싹이 쏙쏙 올라오니, 마음이 참 뿌듯했답니다.",
    "s08": "어느 날 저녁, 노을을 보던 돌쇠는 생각했어요. 일하는 게, 이렇게 기분 좋은 거였구나. 우리 어머니도 매일 이렇게 힘드셨겠지? 집에 계신 어머니가, 너무너무 보고 싶었어요. 그때 밭 한쪽에서, 하얗고 통통한 무 하나가 눈에 쏙 들어왔어요. 돌쇠는 그 무를, 한 입 아삭 베어 물었지요.",
    "s09": "그러자 신기한 일이 일어났어요! 소의 탈이 스르르 벗겨지더니, 돌쇠가 다시 사람으로 돌아온 거예요. 와, 내 손이다! 내 발이다! 돌쇠는 집으로 돌아가, 어머니를 꼭 안았어요. 어머니, 이제부터는 제가 열심히 일할게요! 그날부터 돌쇠는 해가 뜨면 제일 먼저 일어나는, 마을에서 소문난 부지런한 총각이 되었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 게으름뱅이 돌쇠는, 소가 되어 일해 보고 나서야 땀 흘리는 기쁨을 알게 되었지요? 내가 할 일을 스스로 해내면요, 마음이 이렇게 뿌듯하고 행복해진답니다. 우리도 오늘 할 일을 하나씩, 씩씩하게 해 보기로 해요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
