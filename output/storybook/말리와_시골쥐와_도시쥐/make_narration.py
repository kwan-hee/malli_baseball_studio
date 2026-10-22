# 말리와 시골쥐와 도시쥐 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 소박하게 대접하는 시골쥐는 순박하고 다정하게, "
    "도시 자랑을 하는 도시쥐는 우쭐하고 들뜨게, "
    "화려한 저택을 보고 감탄하는 장면은 눈이 휘둥그레 놀라며, "
    "고양이가 나타나 숨는 장면은 다급하고 조마조마하게, "
    "시골쥐가 돌아가기로 마음먹는 장면은 차분하고 진솔하게, "
    "시골집에 돌아와 편안해하는 마지막은 포근하고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은 사이좋은 두 친구, 시골쥐와 도시쥐 이야기를 가지고 왔어요. 진짜 행복이란 무엇일까요? 화려한 것과 마음 편한 것 중에 무엇이 더 소중한지, 함께 알아볼까요?",
    "s02": "옛날 옛날, 조용한 시골 마을에 마음씨 착한 시골쥐가 살았어요. 어느 날, 도시에 사는 친구 도시쥐가 놀러 왔지요. 시골쥐는 반가운 마음에, 정성껏 모아 둔 보리와 콩, 잘 익은 이삭을 잔뜩 내왔답니다. 어서 와, 친구야! 많이 먹어.",
    "s03": "그런데 도시쥐는 소박한 음식을 보고 고개를 갸웃했어요. 얘, 넌 매일 이런 것만 먹니? 도시에 가면 말이야, 달콤한 케이크랑 고소한 치즈가 산더미처럼 쌓여 있어! 나랑 같이 도시로 가자. 시골쥐는 조금 망설이다가, 그럼 한번 가 볼까, 하고 따라나섰답니다.",
    "s04": "두 쥐는 넓은 들판을 지나고 강을 건너, 마침내 커다란 도시에 도착했어요. 도시쥐가 안내한 곳은 으리으리하게 큰 저택이었지요. 넓은 식탁 위에는 먹음직스러운 케이크와 치즈, 탐스러운 과일이 가득했어요. 우와아! 시골쥐는 눈이 휘둥그레졌답니다.",
    "s05": "우와, 정말 근사한 곳이죠? 시골쥐는 이렇게 멋진 음식은 태어나서 처음 봤대요. 그런데 친구들, 과연 시골쥐는 이 맛있는 걸 마음 편히 먹을 수 있을까요? 우리 함께 지켜봐요!",
    "s06": "두 쥐가 막 케이크를 한 입 베어 물려는 순간이었어요. 그때, 갑자기 문이 벌컥 열리더니, 커다란 고양이가 쓱 들어왔지 뭐예요! 두 쥐는 깜짝 놀라 부리나케 벽 틈으로 쏙 숨었어요. 시골쥐는 심장이 콩닥콩닥, 온몸이 다 떨렸답니다.",
    "s07": "고양이가 지나가고 나서야 두 쥐는 겨우 다시 나왔어요. 하지만 이번에는 저벅저벅 사람들 발소리에, 멍멍 강아지 짖는 소리까지 들려왔지요. 도시쥐는 익숙한 듯 요리조리 잘 피했지만, 시골쥐는 밥이 입으로 들어가는지 코로 들어가는지 도무지 알 수가 없었답니다.",
    "s08": "결국 시골쥐가 조용히 말했어요. 도시쥐야, 이 진수성찬도 참 좋지만, 나는 이렇게 조마조마해서는 도저히 못 먹겠어. 아무리 맛있어도, 마음이 편하지 않으면 소용이 없는걸. 나는 다시 시골로 돌아갈래. 도시쥐는 그 마음을 이해하고 고개를 끄덕였지요.",
    "s09": "시골쥐는 도시쥐와 정답게 작별 인사를 하고, 그리운 시골집으로 돌아왔어요. 소박한 이삭 한 알을 물고, 아무 걱정 없이 냠냠 맛있게 먹었지요. 아, 역시 우리 집이 최고야! 그 뒤로 도시쥐도 가끔 시골로 놀러 와, 둘은 조용하고 평화로운 시골에서 함께 즐거운 시간을 보냈답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 시골쥐는 화려한 도시보다, 마음 편한 자기 집이 훨씬 소중하다는 걸 알게 되었죠? 남의 것이 아무리 좋아 보여도, 내 자리에서 느끼는 편안함이 진짜 행복이랍니다. 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
