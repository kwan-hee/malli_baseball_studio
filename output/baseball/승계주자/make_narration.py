# 승계주자 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "자, 보십시오. 구원투수가 마운드에 올라왔는데, 베이스에는 주자가 가득 차 있습니다. 그리고 이 투수가 그 주자들을 몽땅 홈으로 불러들였어요. 그런데 다음 날 기록을 보니, 이 투수 방어율이 0.00입니다. 점수를 내줬는데 방어율은 그대로다? 오늘의 주인공은, 바로 승계주자입니다.",
    "s02": "승계주자, 말 그대로 물려받은 주자예요. 앞선 투수가 주자를 베이스에 남겨 둔 채 마운드를 내려가면, 뒤이어 올라온 구원투수는 그 주자들을 그대로 이어받게 됩니다. 이렇게 넘겨받은 주자를, 승계주자 또는 책임주자라고 불러요. 영어로는 물려받은 주자, 인헤리티드 러너라고 하죠.",
    "s03": "자, 여기서 오늘의 핵심입니다. 이 승계주자가 홈을 밟아서 점수가 나도, 그 실점은 지금 던지는 구원투수가 아니라, 앞서 그 주자를 내보낸 투수의 책임이 됩니다. 앞 투수의 자책점으로 올라가는 거예요. 그러니까 구원투수 방어율에는, 한 점도 잡히지 않습니다.",
    "s04": "이 규칙, 생각보다 오래됐어요. 메이저리그가 1940년에 규칙집에 딱 못 박았거든요. 구원투수가 올라왔을 때 이미 나가 있던 주자가 득점하면, 그건 구원투수가 아니라 앞선 투수에게 기록한다. 이 문장이 처음 들어간 게 1940년, 다시 정리된 게 1950년입니다.",
    "s05": "그 전에는 어땠을까요? 놀랍게도, 딱 정해진 규칙이 없었어요. 그래서 이 점수를 누구 책임으로 할지, 공식 기록원이 상황을 봐 가며 그때그때 정했습니다. 사람마다 판단이 다르니 들쭉날쭉했죠. 그래서 주자를 남긴 사람이 끝까지 책임진다, 이렇게 깔끔하게 정리한 겁니다.",
    "s06": "그럼 우리 KBO는 어떨까요. 2016년 기록을 보면 재밌어요. 그 해에 물려받은 주자를 가장 많이 실점시킨 투수가, 한화 박정진과 삼성 박근홍이었는데요. 두 선수가 각각 스물한 점씩, 승계주자를 홈으로 들여보냈습니다. 그런데 이 스물한 점, 두 선수 자책점에는 단 한 점도 잡히지 않았어요.",
    "s07": "자, 여기서 은근 헷갈리는 겁니다. 많은 분들이, 구원투수가 주자를 불러들이면 그 투수 방어율이 나빠진다고 생각하세요. 아니에요. 승계주자 실점은 방어율에 잡히지 않습니다. 그래서 야구팬들은 이걸, 분식한다고 불러요. 기업들 장부 예쁘게 꾸미는 분식회계, 거기서 따온 말이죠.",
    "s08": "실제로는 불을 못 껐는데, 자기 방어율은 깨끗하게 유지되니까, 성적을 좋아 보이게 분식한다는 겁니다. 이게 바로 방어율의 함정이에요. 방어율이 0점대인 구원투수가, 알고 보면 물려받은 주자를 펑펑 불러들이고 있었을 수도 있는 거죠. 숫자 하나만 믿으면 안 되는 이유입니다.",
    "s09": "그래서 고인물들은 방어율만 보지 않습니다. 구원율이라는 지표를 같이 봐요. 물려받은 주자 중에 몇 명이나 홈을 밟았는지, 그 비율을 따지는 거죠. 승계주자를 꾸역꾸역 잘 틀어막는 투수, 그게 감독이 정말 믿고 내보내는 진짜 불펜입니다.",
    "s10": "방어율 0.00 뒤에 숨은 진짜 실력, 이제 좀 보이시나요? 승계주자는, 야구 기록을 한 겹 더 깊이 보게 해 주는 열쇠예요. 다음에 구원투수가 위기에 올라오거든, 물려받은 주자를 몇 명이나 지켜 내는지 함께 지켜봐 주세요. 다음 편은, 이 승계주자와 딱 붙어 다니는 기록, 홀드 이야기로 올게요. 오늘 도움이 됐다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 또 만나요!",
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
