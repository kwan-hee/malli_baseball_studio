# 말리와 도깨비 방망이 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 씬 시작 금지 (2026-07-16 까치편 whisper 환각 교훈)
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
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 가난하지만 착하고 효심 깊은 나무꾼의 대사는 순하고 다정하게, "
    "도깨비들의 대사는 짓궂지만 귀엽고 신나게, 욕심쟁이 영감의 대사는 우스꽝스럽게, "
    "도깨비들이 방망이로 잔치를 벌이는 장면은 흥겹고 왁자지껄하게, "
    "개암을 깨물어 도깨비가 놀라 도망치는 장면은 통쾌하고 익살스럽게, "
    "마지막 효도하고 나누는 장면은 따뜻하고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 신기하고 통쾌한 이야기를 가져왔어요. 두드리기만 하면 뭐든지 나오는 요술 도깨비 방망이 이야기랍니다. 금 나와라 뚝딱, 은 나와라 뚝딱! 정말 신기하죠? 자, 옛날 옛적 깊은 산골 마을로 함께 떠나 볼까요?",
    "s02": "옛날 어느 산골에, 가난하지만 마음씨 착하고 효심이 깊은 나무꾼이 살았어요. 하루는 산에서 나무를 하다가, 땅에 떨어진 도토리처럼 생긴 개암 몇 알을 주웠지요. 나무꾼은 이 맛있는 걸 부모님께 갖다 드려야지, 하고는 배가 고파도 꾹 참고 품속에 소중히 넣어 두었답니다.",
    "s03": "날이 저물어 산속이 캄캄해지자, 나무꾼은 오래된 빈집에 들어가 하룻밤 묵기로 했어요. 그런데 한밤중이 되자, 뿔 달린 도깨비들이 우르르 몰려와 흥겨운 잔치를 벌이는 거예요! 도깨비들은 하나도 무섭지 않고, 알록달록 귀여운 모습으로 신나게 춤을 추었지요. 나무꾼은 얼른 다락에 숨어 숨을 죽였어요.",
    "s04": "도깨비 대장이 요술 방망이를 번쩍 들고 외쳤어요. 금 나와라, 뚝딱! 그러자 방망이를 두드릴 때마다 반짝이는 금덩이가 우르르 쏟아졌어요. 은 나와라, 뚝딱! 이번엔 은덩이가 와르르 쏟아졌지요. 쌀 나와라 뚝딱, 떡 나와라 뚝딱! 온갖 보물과 먹을 것이 산더미처럼 쌓여 갔답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 다락에 숨은 나무꾼은 이제 어떻게 될까요? 배는 고픈데 도깨비들은 갈 생각을 안 하니, 나무꾼은 참 난처했어요. 그때 문득 품속에 넣어 둔 개암이 떠올랐지요. 자, 나무꾼이 개암을 어떻게 했을까요?",
    "s06": "배가 고파진 나무꾼은, 품속의 개암을 하나 꺼내 입에 넣고 힘껏 깨물었어요. 그러자 딱! 하고 온 집 안이 쩌렁쩌렁 울릴 만큼 큰 소리가 났지 뭐예요. 깜짝 놀란 도깨비들은 집이 무너지는 줄로만 알고, 걸음아 날 살려라 도망쳐 버렸어요. 요술 방망이도 그대로 두고 말이에요!",
    "s07": "다음 날 아침, 나무꾼은 도깨비들이 두고 간 요술 방망이를 가지고 집으로 돌아왔어요. 그러고는 방망이를 두드려 부모님께 따뜻한 집과 쌀을 지어 드리며 정성껏 효도했지요. 착한 나무꾼은 혼자만 잘 살지 않고, 어려운 이웃들에게도 아낌없이 나누어 주었답니다. 온 마을이 넉넉하고 행복해졌어요.",
    "s08": "그런데 옆 마을에, 욕심이 아주 많은 영감이 한 사람 살았어요. 나무꾼이 부자가 된 이야기를 듣고는, 눈이 번쩍 뜨였지요. 옳지, 나도 방망이를 얻어 부자가 되어야겠다! 욕심쟁이 영감은 일부러 개암을 잔뜩 챙겨서, 도깨비들이 나온다는 그 빈집으로 부랴부랴 달려갔답니다.",
    "s09": "밤이 되어 도깨비들이 다시 나타나 잔치를 벌이자, 욕심쟁이 영감은 얼른 개암을 딱 깨물었어요. 하지만 이번엔 도깨비들이 속지 않았지요. 옳거니, 지난번에 우리를 골탕 먹인 게 바로 너로구나! 도깨비들이 방망이를 흔들며 와르르 다가오자, 욕심쟁이 영감은 혼비백산 도망치며 크게 뉘우쳤답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 착하고 정직하게 살면 뜻밖의 복이 찾아오고, 욕심을 부리면 오히려 혼이 난대요. 그리고 부모님께 효도하고 이웃과 나누는 마음은 참 아름답지요. 말리도 정직하고 나눌 줄 아는 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
    print("TTS DONE")
