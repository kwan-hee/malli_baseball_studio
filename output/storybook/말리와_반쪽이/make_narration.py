# 말리와 반쪽이 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, r"C:\youtube_longform_agent")
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
    "말리(강아지)의 대사는 신나고 귀엽게, 반쪽이가 놀림받아도 씩씩한 장면은 당당하고 밝게, "
    "호랑이가 나타나 마을이 겁먹는 장면은 조마조마하게(단 무섭지 않게), "
    "반쪽이가 꾀와 힘으로 호랑이를 골탕 먹이는 장면은 통쾌하고 신나게, "
    "부잣집 영감이 반쪽이를 인정하는 장면은 감격스럽게, "
    "모두가 반쪽이를 다시 보는 마지막은 밝고 뿌듯하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 몸은 반쪽이지만 누구보다 마음이 크고 당당한, 아주 용감한 친구 이야기를 가져왔어요. 겉모습만 보고 놀리면 안 된다는 걸 알려 주는, 반쪽이 이야기랍니다. 반쪽이가 어떤 멋진 일을 해낼까요? 자, 옛날 어느 마을로 함께 가 볼까요?",
    "s02": "옛날 어느 마을에, 오래도록 아기를 기다리던 부부가 있었어요. 어느 날 지나가던 스님이 잉어 세 마리를 주며, 꼭 세 마리를 다 잡숫고 소원을 비시라 했지요. 그런데 부인은 그만 두 마리 반만 먹고, 반 마리를 남기고 말았답니다. 딱 반 마리만큼이 모자랐던 거예요.",
    "s03": "얼마 뒤, 부부에게 아들 셋이 태어났어요. 위의 두 형은 몸이 온전했지만, 막내는 눈도 하나, 팔도 하나, 다리도 하나인 반쪽 몸이었지요. 사람들은 그 아이를 반쪽이라고 불렀어요. 하지만 부모님은 반쪽이를 세상 그 무엇보다 소중하게 아끼고 사랑했답니다.",
    "s04": "반쪽이는 몸은 반쪽이었지만, 힘은 온 마을에서 으뜸가는 천하장사였어요. 게다가 어찌나 꾀가 많고 영리한지, 못 푸는 문제가 없었지요. 짓궂은 아이들이 반쪽이라고 놀려도, 반쪽이는 조금도 주눅 들지 않고 씩씩하게 껄껄 웃어넘겼답니다. 나는 마음만은 누구보다 온전한걸!",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 몸이 반쪽이라고, 정말 할 수 있는 게 적을까요? 절대 아니에요! 반쪽이의 진짜 멋진 모습은 지금부터랍니다. 마침 그때, 마을에 아주 큰일이 벌어지고 있었거든요. 자, 무슨 일인지 함께 지켜봐요!",
    "s06": "그 무렵 마을에는, 사나운 호랑이 한 마리가 나타나 밤마다 사람들을 벌벌 떨게 했어요. 어흥 소리만 나면 온 마을이 문을 꽁꽁 걸어 잠갔지요. 힘세고 돈 많은 부잣집 영감도, 호랑이가 무서워 벌벌 떨기는 마찬가지였답니다. 아무도 감히 나서지를 못했어요.",
    "s07": "바로 그때, 반쪽이가 씩씩하게 나섰어요. 반쪽이는 꾀를 내어 튼튼한 밧줄로 올가미를 만들어 놓고, 호랑이를 슬슬 약 올렸지요. 성이 난 호랑이가 달려들자, 반쪽이는 폴짝 몸을 피하고 올가미를 확 잡아당겼어요. 호랑이는 밧줄에 대롱대롱 묶여, 걸음아 날 살려라 도망치고 말았답니다.",
    "s08": "마을 사람들은 반쪽이를 보고 입이 딱 벌어졌어요. 그렇게 무섭던 호랑이를, 반쪽이가 혼자서 물리치다니! 반쪽이를 늘 무시하던 부잣집 영감도 깜짝 놀랐지요. 영감은 반쪽이의 용기와 지혜에 감탄해, 그동안 겉모습만 보고 우습게 여긴 것을 진심으로 부끄러워했답니다.",
    "s09": "영감은 반쪽이의 손을 덥석 잡고 말했어요. 내가 그동안 자네를 잘못 보았네. 자네야말로 참으로 훌륭한 사람일세! 그 뒤로 반쪽이는 온 마을의 자랑이 되었어요. 반쪽이라고 놀리던 아이들도, 이제는 반쪽이를 가장 멋진 친구로 여기며 졸졸 따라다녔답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 반쪽이는 몸이 반쪽이었지만, 용기와 지혜, 그리고 따뜻한 마음은 누구보다 온전했지요? 그러니 겉모습만 보고 사람을 함부로 판단하면 안 된답니다. 여러분도 반쪽이처럼 언제나 당당하고 씩씩하기예요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
