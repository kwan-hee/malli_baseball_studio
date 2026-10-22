# 말리와 신데렐라 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 구박받는 신데렐라 부분은 안쓰럽지만 씩씩하게, "
    "요정 할머니가 마법을 부리는 장면은 신비롭고 다정하게, "
    "무도회에서 왕자와 춤추는 장면은 설레고 꿈결처럼, "
    "자정 종에 급히 도망치는 장면은 다급하고 조마조마하게, "
    "유리구두가 딱 맞고 화해하는 마지막은 벅차고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은 아주 유명한 이야기, 신데렐라를 가지고 왔어요. 힘든 순간에도 상냥한 마음을 잃지 않으면 어떤 일이 생길까요? 함께 알아볼까요?",
    "s02": "옛날 옛날, 마음씨 착하고 부지런한 소녀 신데렐라가 살았어요. 그런데 새엄마와 두 언니는 신데렐라를 몹시 구박했지요. 신데렐라는 아침부터 밤까지 청소에 빨래에, 온갖 집안일을 도맡아 했어요. 그래도 신데렐라는 늘 웃음을 잃지 않았답니다.",
    "s03": "그러던 어느 날, 궁전에서 무도회 초대장이 왔어요. 왕자님이 신붓감을 찾는 성대한 무도회였지요. 두 언니는 예쁜 드레스를 입고 신이 나서 궁전으로 떠났어요. 하지만 신데렐라는 입을 옷도 없어서, 혼자 남아 눈물을 글썽였답니다.",
    "s04": "바로 그때, 반짝반짝 빛과 함께 요정 할머니가 나타났어요. 얘야, 울지 말렴. 요정 할머니가 지팡이를 휘두르자, 커다란 호박은 멋진 마차로, 생쥐들은 늠름한 말로 변했어요. 그리고 신데렐라의 누더기 옷은, 세상에서 가장 아름다운 드레스와 반짝이는 유리 구두로 변했지요! 단, 자정 종이 울리면 마법이 풀린다는 걸 잊지 말아라!",
    "s05": "우와, 신데렐라가 정말 눈부시게 예쁘죠? 그런데 친구들, 꼭 기억해야 해요. 밤 열두 시, 자정 종이 울리기 전에는 돌아와야 한다는 거! 과연 신데렐라는 무사히 돌아올 수 있을까요?",
    "s06": "무도회장에 신데렐라가 들어서자, 모두가 그 아름다움에 감탄했어요. 왕자님은 신데렐라에게 한눈에 반해, 손을 내밀며 말했지요. 저와 함께 춤을 추시겠어요? 둘은 시간 가는 줄도 모르고, 꿈처럼 즐겁게 춤을 추었답니다.",
    "s07": "그런데 그때, 뎅, 뎅! 자정을 알리는 종소리가 울리기 시작했어요. 아, 이런! 신데렐라는 깜짝 놀라 인사도 제대로 못 한 채, 계단을 급히 뛰어 내려갔어요. 그러다 그만, 유리 구두 한 짝이 계단에 툭 벗겨지고 말았지요. 하지만 멈출 수 없었던 신데렐라는, 한쪽 구두만 신은 채 어둠 속으로 사라졌답니다.",
    "s08": "홀로 남은 왕자님은, 신데렐라가 떨어뜨린 유리 구두 한 짝을 소중히 들고 결심했어요. 이 구두가 꼭 맞는 아가씨를 찾아, 반드시 다시 만나겠어! 왕자님은 신하들과 함께 온 나라 집집마다 돌아다니며, 처녀들에게 유리 구두를 신겨 보았어요. 하지만 그 누구의 발에도 맞지 않았지요.",
    "s09": "드디어 신데렐라의 집에도 왕자님이 찾아왔어요. 두 언니가 서로 신어 보려 했지만, 구두는 도무지 맞지 않았어요. 마지막으로 신데렐라가 조심스레 발을 넣자, 어머! 유리 구두가 발에 꼭 맞는 거예요! 왕자님은 뛸 듯이 기뻐했어요. 새엄마와 언니들도 그제야 자신들의 심술을 부끄러워하며, 진심으로 축하해 주었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 신데렐라는 아무리 힘들어도 상냥한 마음을 잃지 않았고, 결국 그 착한 마음이 큰 행복으로 돌아왔지요? 여러분도 신데렐라처럼, 마음속 상냥함과 희망을 잃지 마세요. 오늘 이야기가 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
