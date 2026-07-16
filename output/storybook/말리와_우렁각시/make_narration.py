# 말리와 우렁각시 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 외롭지만 착한 총각의 대사는 순하고 다정하게, "
    "고운 우렁각시의 대사는 상냥하고 따뜻하게, "
    "누가 밥을 차렸는지 궁금해하는 장면은 신기하고 조마조마하게, "
    "우렁이에서 각시가 나오는 장면은 놀랍고 신비롭게, "
    "둘이 정답게 한 가족이 되는 마지막은 포근하고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 따뜻하고 신비로운 이야기를 가져왔어요. 어느 외로운 총각의 집에, 날마다 누군가 몰래 맛있는 밥상을 차려 놓았대요. 대체 누가 그랬을까요? 정말 궁금하죠? 자, 옛날 옛적 시골 마을로 함께 가 볼까요?",
    "s02": "옛날 어느 마을에, 마음씨 착하지만 혼자 사는 총각이 있었어요. 부지런히 농사를 지었지만, 함께 밥 먹을 식구가 없어 늘 쓸쓸했지요. 오늘도 총각은 넓은 논에서 땀 흘려 일하며 혼잣말을 했어요. 이 넓은 논에 농사를 지어도, 누구랑 나눠 먹고 산단 말인가. 참 외롭구나.",
    "s03": "하루는 논에서 일하던 총각이, 반짝반짝 예쁜 우렁이 한 마리를 발견했어요. 어쩜 이렇게 곱게 생겼을까! 총각은 우렁이를 소중히 두 손에 담아 집으로 가져왔어요. 그러고는 부엌 물독에 살며시 넣어 두고, 날마다 정성껏 돌보아 주었답니다. 이제 혼자가 아닌 것 같아 마음이 놓였어요.",
    "s04": "그런데 그날부터, 참으로 신기한 일이 벌어졌어요. 총각이 일을 마치고 집에 돌아오면, 따끈따끈한 밥과 국, 정갈한 반찬이 한 상 가득 차려져 있는 거예요! 하루도 아니고 날마다 말이에요. 총각은 어리둥절했어요. 대체 누가 이렇게 맛있는 밥상을 차려 놓는 걸까?",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 과연 누가 총각의 밥상을 몰래 차려 놓았을까요? 맞아요, 여러분이 생각하는 바로 그 친구일지도 몰라요! 총각도 너무너무 궁금해서, 그 비밀을 꼭 알아내기로 마음먹었답니다. 자, 총각은 어떻게 했을까요?",
    "s06": "궁금해진 총각은 다음 날, 일하러 가는 척하고는 문 뒤에 살그머니 숨어서 지켜보았어요. 그러자 세상에! 물독 속 우렁이에서 고운 각시가 스르르 나오더니, 소매를 걷고 정성껏 밥을 짓기 시작하는 거예요. 총각은 너무 놀라 하마터면 소리를 지를 뻔했답니다.",
    "s07": "총각은 반가운 마음에 얼른 뛰어나가 각시에게 인사했어요. 그동안 밥상을 차려 준 게 당신이었군요, 정말 고맙습니다! 각시는 방긋 웃으며 다정하게 대답했지요. 저를 소중히 거두어 주셔서, 그 고마움을 갚고 싶었어요. 총각의 따뜻한 마음이 저를 이곳으로 이끌었답니다.",
    "s08": "그날부터 둘은 서로를 아끼며 정답게 함께 살았어요. 총각은 부지런히 농사를 짓고, 각시는 솜씨 좋게 살림을 꾸렸지요. 둘이 도란도란 이야기를 나누니, 외롭던 집에 웃음소리가 끊이지 않았어요. 마을 사람들도 착한 두 사람을 참 좋아하고 아껴 주었답니다.",
    "s09": "어느 맑은 날, 총각과 각시는 마당에 상을 펴고 따뜻한 밥을 함께 나누어 먹었어요. 혼자 먹던 쓸쓸한 밥이 아니라, 웃음꽃이 활짝 핀 행복한 밥상이었지요. 이제 총각은 더 이상 외롭지 않았어요. 서로를 아끼는 마음이 있으니, 날마다가 잔칫날처럼 즐거웠답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 내가 베푼 작은 친절과 정성은, 언젠가 따뜻한 고마움이 되어 돌아온대요. 그리고 서로 아끼는 마음이 있으면, 평범한 하루도 참 행복해진답니다. 말리도 다정하고 고마움을 아는 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
