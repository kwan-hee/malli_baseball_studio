# 말리와 팥죽 할머니와 호랑이 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 마음씨 착한 팥죽 할머니의 대사는 정답고 인자하게, "
    "심술궂은 호랑이의 대사는 짓궂지만 하나도 무섭지 않게 우스꽝스럽게, "
    "알밤·자라·개똥·송곳·멍석·지게 작은 친구들의 대사는 씩씩하고 귀엽게, "
    "작은 친구들이 힘을 모아 호랑이를 골탕 먹이는 장면은 통쾌하고 왁자지껄하게, "
    "마지막에 다 함께 팥죽을 나눠 먹는 장면은 따뜻하고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 통쾌하고 재미있는 이야기를 가져왔어요. 작디작은 친구들이 힘을 모아 커다란 호랑이를 물리친 이야기랍니다. 알밤이랑 자라, 송곳, 멍석, 지게까지 다 함께 나온대요! 자, 팥죽 냄새 솔솔 나는 산골 마을로 함께 가 볼까요?",
    "s02": "옛날 어느 산골에, 마음씨 착한 할머니가 혼자 살았어요. 할머니는 밭에서 붉은 팥을 정성껏 길렀지요. 팥이 잘 익으면 보글보글 맛있는 팥죽을 쑤어, 이웃과 나눠 먹을 생각에 늘 흐뭇했답니다. 올해도 팥이 탐스럽게 익어서, 할머니는 콧노래를 부르며 팥을 거두었어요.",
    "s03": "그러던 어느 날, 심술궂은 호랑이 한 마리가 어슬렁어슬렁 나타났어요. 호랑이는 할머니의 팥죽이 어찌나 탐이 나던지, 눈을 부라리며 으름장을 놓았지요. 할멈, 그 팥죽이랑 집을 몽땅 나한테 내놓지 못할까! 할머니는 그만 겁이 나서, 앞치마에 얼굴을 묻고 엉엉 울고 말았답니다.",
    "s04": "할머니가 엉엉 우는 소리에, 부엌 여기저기서 작은 친구들이 하나둘 모여들었어요. 아궁이 속 알밤이 톡, 물독 옆 자라가 쓱, 마당의 개똥과 뾰족한 송곳, 둘둘 멍석과 튼튼한 지게까지! 친구들은 입을 모아 씩씩하게 말했어요. 할머니, 걱정 마세요. 저희가 힘을 모아 도와드릴게요!",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 이렇게 작은 친구들이, 과연 커다란 호랑이를 어떻게 물리칠 수 있을까요? 맞아요, 혼자서는 힘들어도 여럿이 힘을 모으면 못 할 일이 없답니다! 자, 저녁이 되어 호랑이가 다시 오면 어떤 일이 벌어질까요?",
    "s06": "드디어 해가 지고, 심술궂은 호랑이가 어슬렁어슬렁 할머니 집으로 들어왔어요. 그런데 호랑이가 몸을 녹이려 아궁이 앞에 앉는 순간, 뜨겁게 달궈진 알밤이 탁 튀어 올라 호랑이 눈을 콩 때렸지 뭐예요! 호랑이가 아이고, 하고 물독으로 달려가자, 이번엔 자라가 코를 꽉 깨물었답니다.",
    "s07": "부엌 바닥에서는 또 다른 소동이 기다리고 있었어요. 깜짝 놀란 호랑이가 도망치려는데, 마당의 개똥을 밟고 그만 발라당 미끄러졌지요! 겨우 일어서려는 순간, 이번엔 뾰족한 송곳이 콕 하고 호랑이를 찔렀어요. 호랑이는 정신을 못 차리고 이리 쿵 저리 쿵, 우당탕탕 나뒹굴었답니다.",
    "s08": "그때 마당에서는 멍석과 지게가 기다리고 있었어요. 넓은 멍석이 데굴데굴 굴러와 호랑이를 둘둘 말아 버리자, 힘센 지게가 번쩍 짊어지고는 냇가로 성큼성큼 걸어갔지요. 그러고는 호랑이를 풍덩! 냇물에 던져 버렸답니다. 호랑이는 걸음아 날 살려라, 물살을 헤치며 멀리멀리 달아나 버렸어요.",
    "s09": "호랑이가 도망친 뒤, 할머니는 작은 친구들을 꼭 끌어안으며 고마워했어요. 얘들아, 너희 덕분에 살았단다. 정말 고맙구나! 할머니는 가마솥 가득 따끈한 팥죽을 보글보글 쑤어, 알밤이랑 자라, 송곳, 멍석, 지게 모두에게 한 그릇씩 나눠 주었어요. 온 집안이 웃음소리로 가득했답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 아무리 작고 힘이 약해도, 여럿이 마음을 모으면 아주 큰 일도 거뜬히 해낼 수 있대요. 서로 돕는 마음이 세상에서 제일 힘이 세답니다! 말리도 친구들과 힘을 모을 줄 아는 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
