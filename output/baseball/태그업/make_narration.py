# 태그업 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
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

# cp949 콘솔에서 비-cp949 문자(em-dash 등) print 크래시 방지 (2026-07-18 유료루프 교훈)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Puck"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 야구를 20년 본 동네 형 같은 유튜브 해설자입니다. "
    "친근한 존댓말로 리듬감 있게, 궁금증 유발 구간은 톤을 올리고, "
    "설명 구간은 차분하게, 야구를 처음 보는 사람도 이해하게 쉽게 연기하며 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "자, 보십시오. 외야 깊숙한 곳으로 뻗은 큰 플라이, 수비수가 잡았습니다. 그런데 3루에 있던 주자가 홈으로 내달립니다. 세이프! 아니, 분명히 공을 잡았는데 왜 아웃이 아닐까요? 오늘의 주인공은 바로, 잡힌 공을 기회로 바꾸는 플레이, 태그업입니다.",
    "s02": "뜬공이 높이 떴을 때, 베이스에 있던 주자는 함부로 뛰쳐나갈 수가 없어요. 만약 그 공이 잡히면, 원래 있던 베이스로 되돌아가야 하니까요. 그래서 주자는 베이스에 발을 딱 붙인 채, 공이 잡히기를 기다립니다. 이렇게 밟고 있다가 출발하는 것을, 태그업 또는 리터치라고 부릅니다.",
    "s03": "그럼 언제부터 출발할 수 있을까요? 규칙은 이렇습니다. 야수가 그 공을 잡는 순간, 주자는 베이스를 박차고 다음 루로 달릴 수 있습니다. 수비수가 공을 잡자마자, 주자의 발과 수비수의 어깨가 맞붙는 숨 막히는 승부가 시작되는 거죠.",
    "s04": "그런데 여기, 많은 분들이 모르는 사실이 하나 있어요. 주자는 야수가 공을 완전히 움켜쥘 때까지 기다릴 필요가 없습니다. 공이 글러브에 처음 닿는 바로 그 순간부터 출발이 가능하거든요. 그래서 발 빠른 주자는 이 찰나를 노려서, 한 발이라도 먼저 튀어 나갑니다.",
    "s05": "만약 주자가 공이 잡히기도 전에 먼저 출발해 버리면 어떻게 될까요? 이때 수비는, 공을 잡은 다음 그 주자의 원래 베이스를 밟으면서 심판에게 어필합니다. 심판이 인정하면 그 주자는 아웃이죠. 재밌는 건, 심판이 먼저 나서서 잡아 주지 않는다는 점입니다. 반드시 수비가 어필해야만 인정되는, 어필 플레이예요.",
    "s06": "그런데 이 아웃은 포스아웃이 아닙니다. 뜬공으로 잡힌 상황이라, 주자가 꼭 진루해야 하는 의무, 그러니까 포스 상태가 아니기 때문이죠. 그래서 아주 중요한 차이가 생겨요. 설령 이 어필이 그 이닝의 세 번째 아웃이라고 해도, 그 전에 홈을 밟은 득점은 그대로 인정됩니다. 포스아웃이었다면 무효가 됐을 점수죠.",
    "s07": "바로 이 태그업이, 우리가 잘 아는 희생플라이를 만들어 냅니다. 무사나 1사에 3루 주자가 있을 때, 타자가 깊은 플라이를 치고 주자가 태그업으로 홈을 밟으면, 타자는 아웃이 되지만 소중한 1점을 만들어 내죠. 이때 타자에게는 타점이 기록되고, 타수에서는 빠집니다. 그래서 몸을 던진 희생, 희생플라이라고 부르는 거예요.",
    "s08": "실제 경기에서는 짜릿한 장면도 나옵니다. 2022년, 롯데의 한 주자가 태그업으로 진루하자 상대 팀은 출발이 너무 빨랐다며 어필에 나섰어요. 그런데 그 어필에 정신이 팔린 사이, 이 주자는 오히려 홈까지 내달려서 득점에 성공했습니다. 태그업과 어필은, 이렇게 한순간에 승부를 뒤집는 양날의 검인 거죠.",
    "s09": "자, 그림을 한번 그려 볼까요. 1사에 주자는 3루, 타자가 외야 깊숙이 공을 높이 띄웁니다. 외야수가 그 공을 잡는 순간, 3루 주자가 홈을 향해 폭발적으로 튀어 나갑니다. 날아오는 송구와 달려드는 주자가 홈 플레이트에서 맞부딪히는 짜릿한 승부! 잡힌 공 하나가 이렇게 소중한 1점으로 바뀌는 순간입니다.",
    "s10": "잡혔다고 끝이 아닙니다. 태그업은, 실패처럼 보이는 뜬공을 기회로 바꾸는 야구의 지혜예요. 다음에 깊은 플라이가 뜨거든, 공만 보지 마시고 베이스에 딱 붙어 있는 주자의 발끝을 함께 지켜보세요. 훨씬 더 짜릿할 겁니다. 오늘 내용이 쓸 만했다면 구독이랑 좋아요 부탁드리고요. 다음 편에서 또 만나요!",
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
            # 최소 길이 가드: 잘린 take(Puck이 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10  # 정규화 글자수 × 0.10초
            if dur < min_dur:
                raise RuntimeError(f"truncated take: {dur:.1f}s < {min_dur:.1f}s expected - retry")
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
    # 매칭 실패(환각 구간)면 글자수 비례 추정으로 graceful fallback. 필요시 fix_boundaries 로 보정.
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
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)  # 환각 구간 - 비례 폴백
            print(f"{sid}: prefix match weak (best={best_r:.2f}) - proportional fallback @ {b:.2f}")
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
