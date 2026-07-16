# 말리와 삼년고개 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 걱정 많은 할아버지의 대사는 처음엔 시무룩하고 근심스럽게, "
    "지혜로운 아이의 대사는 밝고 야무지게, "
    "할아버지가 좋은 방법을 깨닫는 장면은 통쾌하고 신나게, "
    "할아버지가 고개에서 데굴데굴 일부러 넘어지는 장면은 익살스럽고 흥겹게, "
    "병이 씻은 듯 나아 활짝 웃는 마지막은 밝고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 생각을 살짝 바꾸었더니 큰 걱정이 기쁨으로 변한, 아주 신기한 이야기를 가져왔어요. 한 번 넘어지면 삼 년밖에 못 산다는 이상한 고개 이야기랍니다. 정말 그럴까요? 자, 옛날 옛적 어느 산골 마을로 함께 가 볼까요?",
    "s02": "옛날 어느 마을에, 넘어지면 큰일 나는 신기한 고개가 하나 있었어요. 사람들은 그 고개를 삼년고개라고 불렀지요. 왜냐하면, 그 고개에서 한 번 넘어지면 딱 삼 년밖에 살지 못한다는 이야기가 전해 왔거든요. 그래서 마을 사람들은 그 고개를 넘을 때마다, 넘어질까 봐 조심조심 발걸음을 옮겼답니다.",
    "s03": "하루는 마음 여린 할아버지가 장에 다녀오다가, 그만 삼년고개에서 발을 헛디뎌 넘어지고 말았어요. 아이고, 이를 어째! 할아버지는 새파랗게 질려 버렸지요. 이제 나는 삼 년밖에 못 사는구나. 할아버지는 그 길로 집에 돌아와, 이불을 뒤집어쓰고 끙끙 앓아눕고 말았답니다.",
    "s04": "집에 돌아온 할아버지는 날마다 걱정에 잠겨, 밥도 제대로 넘기지 못했어요. 삼 년밖에 못 산다는 생각에 얼굴은 점점 핼쑥해지고, 기운도 하나 없이 시들시들해졌지요. 온 식구가 그런 할아버지를 보며 발을 동동 굴렀지만, 좀처럼 낫게 할 방법을 찾지 못해 애만 태웠답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 할아버지는 정말로 삼 년밖에 못 사는 걸까요? 사실은요, 넘어진 것보다 삼 년밖에 못 산다는 그 걱정이 할아버지를 더 아프게 한 거였어요. 그럼 이 걱정을 어떻게 하면 좋을까요? 자, 아주 지혜로운 친구가 나타난답니다!",
    "s06": "그때 마을에 사는 지혜로운 아이가 할아버지를 찾아왔어요. 할아버지, 너무 걱정 마세요. 아주 좋은 방법이 있답니다! 할아버지가 힘없이 물었지요. 그게 대체 무슨 방법이냐? 아이는 방긋 웃으며 말했어요. 삼년고개에서 한 번 넘어지면 삼 년을 사시죠? 그러면 여러 번 넘어지면 어떻게 될까요?",
    "s07": "할아버지는 무릎을 탁 치며 벌떡 일어났어요. 옳거니! 한 번 넘어져 삼 년, 두 번 넘어지면 육 년, 열 번 넘어지면 삼십 년을 더 살겠구나! 어쩜 이런 기막힌 생각을 다 했을꼬! 할아버지는 언제 아팠냐는 듯이 신이 나서, 곧장 삼년고개로 한달음에 달려갔답니다.",
    "s08": "할아버지는 다시 삼년고개에 오르자마자, 데굴데굴 신나게 구르며 일부러 넘어지기 시작했어요. 한 번 넘어지고 삼 년, 두 번 넘어지고 또 삼 년! 넘어질 때마다 오래오래 살 생각에, 할아버지는 껄껄 웃음이 터져 나왔지요. 지나가던 마을 사람들도 그 모습을 보고 함께 손뼉을 치며 웃었답니다.",
    "s09": "신기하게도, 할아버지의 병은 씻은 듯이 나아 버렸어요. 삼 년밖에 못 산다는 무거운 걱정이 싹 사라지고, 오히려 오래오래 살 거라는 기쁜 마음이 가득 찼으니까요. 그 뒤로 할아버지는 몸도 마음도 튼튼해져서, 아주 오래오래 건강하고 행복하게 잘 살았답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 똑같은 일도 생각을 살짝 바꾸어 보면, 무서운 걱정이 즐거운 기쁨으로 변할 수 있대요. 그러니 힘든 일이 있어도, 좋은 쪽으로 생각하는 지혜를 가져 봐요! 말리도 늘 밝게 생각하는 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
