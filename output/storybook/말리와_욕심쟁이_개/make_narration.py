# 말리와 욕심쟁이 개 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "말리가 반갑고 신나게 인사, 귀엽게",
    "s02": "옛날이야기를 시작하듯 다정하게, 큰 고기를 얻은 대목은 들뜨고 신나게",
    "s03": "콧노래처럼 가볍게 시작해서, 물속 강아지를 발견하는 대목은 호기심 가득하고 놀랍게",
    "s04": "비밀을 알려 주듯 소곤소곤, 강아지 속마음 대사는 욕심내며 들뜨게",
    "s05": "아이들에게 다급하게 알려 주듯, 걱정스럽고 안타깝게",
    "s06": "탐욕스럽고 조급하게, 강아지 대사는 화나고 사납게(무섭지 않게)",
    "s07": "긴장감 있게 이어 가다가, 풍덩! 대목에서 아뿔싸 하며 당황스럽게",
    "s08": "멍하고 허탈하게, 천천히, 후회하는 대목은 시무룩하게",
    "s09": "뉘우치듯 차분하게, 다짐하는 대사는 진심을 담아",
    "s10": "교훈은 차분하고 따뜻하게, 구독 부탁과 마지막 인사는 말리처럼 귀엽고 신나게",
}

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 욕심을 부리면 어떻게 되는지 알려 주는 재미난 이야기를 가져왔어요. 맛있는 고기 한 덩이를 물고 가던, 욕심쟁이 강아지가 주인공이랍니다. 가진 것에 만족하는 게 왜 소중한지, 함께 알아볼까요?",
    "s02": "옛날 옛날, 어느 마을에 강아지 한 마리가 살았어요. 어느 날, 이 강아지는 커다랗고 먹음직스러운 고기 한 덩이를 얻었지 뭐예요. 우아, 이렇게 큰 고기라니! 강아지는 신이 나서, 아무도 없는 조용한 곳에서 혼자 먹으려고 고기를 입에 꼭 물고 길을 나섰답니다.",
    "s03": "강아지는 콧노래를 부르며, 맑은 개울 위에 놓인 작은 나무다리를 건너게 되었어요. 그런데 다리 한가운데에서 무심코 아래를 내려다본 순간, 강아지는 그만 걸음을 뚝 멈추고 말았지요. 잔잔한 물속에, 웬 강아지 한 마리가 자기를 똑같이 올려다보고 있는 게 아니겠어요?",
    "s04": "사실 그건 물에 비친 강아지 자기 모습, 바로 그림자였어요. 하지만 강아지는 그걸 알아차리지 못했지요. 어라? 저 녀석이 문 고기가, 내 것보다 훨씬 더 커 보이잖아! 강아지의 두 눈이 욕심으로 번들번들 빛나기 시작했답니다.",
    "s05": "친구들, 저건 그림자예요! 물에 비친 자기 모습이라고요! 그런데 욕심에 눈이 먼 강아지는, 그것도 모르고 저 큰 고기까지 빼앗아야겠다고 마음을 먹었어요. 아이고, 강아지야, 그러면 안 되는데. 과연 어떤 일이 벌어질까요?",
    "s06": "강아지는 물속의 강아지를 향해 으르렁, 사납게 이빨을 드러냈어요. 그 고기 내놔! 그건 내 거야! 물속의 강아지도 똑같이 이빨을 드러내며 지지 않을 것처럼 보였지요. 화가 잔뜩 난 강아지는, 그 고기를 뺏으려고 크게 짖어 대기로 했답니다.",
    "s07": "강아지가 물속을 향해 컹, 하고 크게 입을 벌리는 바로 그 순간이었어요. 입에 물고 있던 고기가 스르르 빠져나가더니, 풍덩! 그대로 개울물에 빠져 버리고 말았지 뭐예요. 게다가 물결이 크게 일렁이자, 물속의 강아지도, 그 큰 고기도 순식간에 사라져 버렸답니다.",
    "s08": "강아지는 텅 빈 입을 다신 채, 멍하니 개울물만 바라보았어요. 물속에 있던 큰 고기는 처음부터 없었고, 자기가 물고 있던 진짜 고기마저 이제는 온데간데없이 사라져 버린 거예요. 강아지는 그제야, 아뿔싸, 하고 크게 후회했답니다.",
    "s09": "괜한 욕심을 부리다가, 손에 쥐고 있던 소중한 것까지 몽땅 잃어버리고 만 거죠. 강아지는 축 처진 어깨로 터덜터덜 집으로 돌아가며 다짐했어요. 다음부터는 내가 가진 것에 만족하고, 절대로 헛된 욕심을 부리지 말아야지. 강아지는 소중한 교훈을 하나 얻었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 욕심쟁이 강아지는, 물에 비친 그림자를 탐내다가 가진 고기마저 잃어버렸지요? 지나친 욕심은요, 이렇게 우리가 이미 가진 소중한 것까지 잃게 만든답니다. 우리는 가진 것에 감사할 줄 아는, 지혜로운 친구가 되기로 해요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
