# 말리와 여우와 학 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 여우가 학을 초대하는 장면은 능청스럽고 천연덕스럽게, "
    "학이 납작한 접시 앞에서 먹지 못해 속상한 장면은 시무룩하고 안쓰럽게, "
    "학이 여우를 되받아 초대하는 장면은 우아하고 점잖게, "
    "여우가 호리병 앞에서 낑낑대는 장면은 다급하고 우스꽝스럽게, "
    "여우가 미안해하며 뉘우치는 장면은 뭉클하고 진심 어리게, "
    "둘이 화해하고 정답게 나눠 먹는 마지막은 따뜻하고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 서로 다른 두 친구가 사이좋게 지내려면 무엇이 필요한지 알려 주는 이야기를 가져왔어요. 꾀 많은 여우와, 목이 길고 우아한 학이 주인공이랍니다. 상대방의 마음을 헤아리는 게 왜 소중한지, 함께 알아볼까요?",
    "s02": "옛날 옛날, 숲속에 여우와 학이 살았어요. 어느 날 여우가 학을 저녁 식사에 초대했지요. 학아, 우리 집에 와서 맛있는 거 같이 먹자! 학은 신이 나서 여우네 집으로 한걸음에 찾아갔답니다. 대체 여우가 무슨 맛있는 걸 준비했을까요?",
    "s03": "그런데 여우가 내온 건, 납작하고 넓적한 접시에 담긴 따끈한 수프였어요. 자, 어서 먹으렴! 여우는 긴 혀로 접시를 할짝할짝, 아주 맛있게 먹었지요. 하지만 학은 부리가 뾰족하고 길어서, 넓적한 접시를 톡톡 두드리기만 할 뿐 한 입도 먹을 수가 없었답니다.",
    "s04": "학은 배가 몹시 고팠지만, 꾹 참고 아무 말도 하지 않았어요. 여우는 학의 몫까지 싹싹 다 먹어 치우고는, 시치미를 뚝 떼며 말했지요. 어라, 학아, 입맛에 안 맞았니? 학은 그저 속상한 마음을 꾹 누른 채, 조용히 집으로 돌아갔답니다.",
    "s05": "친구들, 여우가 참 얄궂죠? 학은 얼마나 서운하고 배가 고팠을까요. 그런데 며칠 뒤, 이번에는 학이 여우를 자기 집으로 초대했어요. 여우야, 지난번에 잘 먹었으니, 오늘은 내가 대접할게! 여우는 콧노래를 부르며 신나게 학의 집으로 달려갔답니다.",
    "s06": "학은 맛있는 음식을 정성껏 준비했어요. 고소한 냄새가 솔솔 풍겨서 여우는 벌써부터 군침이 돌았지요. 그런데 학이 내온 그릇을 보니, 목이 길고 주둥이가 좁다란 호리병이었어요. 학은 긴 부리를 호리병 속에 쏙 넣어, 아주 우아하게 음식을 콕콕 집어 먹었답니다.",
    "s07": "여우도 얼른 먹으려고 했지만, 이를 어째요? 주둥이가 좁아서 여우의 뭉툭한 코로는 도무지 음식이 닿지를 않았어요. 여우는 호리병 둘레를 빙빙 돌며 낑낑댔지만, 냄새만 맡을 뿐 한 입도 먹지 못했지요. 그제야 여우는 지난번 학의 마음이 어땠을지 알 것 같았답니다.",
    "s08": "학은 빙그레 웃으며 말했어요. 여우야, 어떠니? 상대방을 생각하지 않으면, 아무리 좋은 것도 나눌 수가 없단다. 여우는 얼굴이 발갛게 달아올랐어요. 학아, 정말 미안해. 지난번에 내가 너무 심했지? 여우는 진심으로 고개를 숙여 사과했답니다.",
    "s09": "학은 여우의 사과를 기쁘게 받아 주었어요. 그리고 이번에는 여우도 먹을 수 있도록, 널찍한 접시에 음식을 다시 나누어 주었지요. 둘은 마주 앉아 도란도란 이야기하며 맛있게 나눠 먹었답니다. 서로의 그릇을 이해하고 나니, 음식은 훨씬 더 맛있고 마음은 따뜻해졌어요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 여우와 학은, 상대방의 입장을 헤아리고 나서야 진짜 친구가 되었지요? 나와 다른 친구를 만나면요, 그 친구에게는 무엇이 필요할지 한 번 더 생각해 보는 거예요. 그게 바로 배려랍니다! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
