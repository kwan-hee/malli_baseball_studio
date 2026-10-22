# 장타율 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
import base64
import os
import sys
import time
import wave
from pathlib import Path

FFMPEG_DIR = (
    "/opt/homebrew/bin:/usr/local/bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Puck"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15

STYLE = (
    "당신은 야구를 20년 본 동네 형 같은 유튜브 해설자입니다. "
    "친근한 존댓말로 리듬감 있게, 궁금증 유발 구간은 톤을 올리고, "
    "설명 구간은 차분하게, 야구를 처음 보는 사람도 이해하게 쉽게 연기하며 읽으세요:\n\n"
)

SCENES = {
    "s01": "자, 같은 타율 3할인 타자가 두 명 있습니다. 한 명은 단타만 열 개, 다른 한 명은 홈런 두 개에 2루타 세 개. 둘 다 타율은 3할인데, 과연 팀에 같은 기여를 한 걸까요? 오늘의 주제는 타율이 놓치는 타격의 질, 장타율입니다.",
    "s02": "장타율, 영어로 슬러깅 퍼센티지. 한 타수에 평균 몇 루타를 치느냐를 나타내는 숫자예요. 이름에 율이 붙어 있지만 실은 확률이 아니라 평균이에요. 그래서 값이 1을 넘을 수 있고, 이론상 최대는 4점, 매 타석 홈런만 치면 그렇게 됩니다.",
    "s03": "계산은 간단합니다. 단타는 1, 2루타는 2, 3루타는 3, 홈런은 4, 이렇게 루타수를 전부 더한 다음 타수로 나누면 돼요. 볼넷이나 몸에 맞는 공은 빠집니다. 그러니까 순수하게 방망이로 때려서 얼마나 멀리 보내느냐, 그게 장타율이에요.",
    "s04": "그럼 타율이랑 뭐가 다를까요? 타율은 안타면 다 똑같이 한 개로 칩니다. 단타든 홈런이든 타율에는 똑같은 1안타예요. 장타율은 다릅니다. 홈런은 단타의 네 배 가치를 인정해요. 그래서 같은 3할이라도 장타율은 완전히 다를 수 있습니다.",
    "s05": "이 지표의 역사가 생각보다 오래됐어요. 1867년, 야구 기록의 아버지라 불리는 헨리 채드윅이 경기당 총 루타수라는 개념을 처음 만들었습니다. 여기서 분모를 경기 수 대신 타수로 바꾸면 지금의 장타율이 돼요. 공식 기록으로 채택된 건 내셔널리그가 1923년, 아메리칸리그는 1946년이에요.",
    "s06": "그럼 어느 정도면 잘하는 걸까요? 리그 평균이 보통 4할 초반이에요. 5할을 넘으면 중심타선급, 6할 이상이면 리그 최정상 슬러거입니다. 참고로 KBO에서는 1984년부터 장타율왕 타이틀을 수여하기 시작했어요.",
    "s07": "KBO 역대 기록을 보면요. 단일 시즌 1위는 2015년 에릭 테임즈의 7할 9푼, 0.790입니다. 한 시즌 동안 한 타수에 거의 0.8루타를 만들어냈다는 뜻이에요. 한국인 최고 기록은 이승엽이 1999년과 2003년에 세운 7할 3푼 3리. 이승엽은 6년 연속 6할 이상을 기록한 유일한 타자예요.",
    "s08": "메이저리그에서는요. 80년 동안 베이브 루스의 8할 4푼 7리가 깨지지 않는 벽이었습니다. 그런데 2001년 배리 본즈가 8할 6푼 3리로 갱신했어요. 한 타수에 거의 1루타 가까이 만들어냈다는 뜻이니까, 정말 상상을 초월하는 기록이죠.",
    "s09": "장타율도 완벽하진 않아요. 볼넷을 아무리 잘 골라도 장타율에는 한 푼도 안 잡힙니다. 그래서 순수한 장타력만 보고 싶으면 장타율에서 타율을 빼요. 이걸 아이에스오 파워, 순수 장타력이라고 하는데, 이 값이 2할을 넘으면 진짜 슬러거로 분류됩니다.",
    "s10": "지난 편에서 출루율을 배웠죠? 출루율은 얼마나 자주 나가느냐, 장타율은 얼마나 멀리 보내느냐. 이 둘을 더한 게 바로 오피에스입니다. 오피에스의 두 축을 이제 다 아시게 된 거예요. 다음 편에서는 도루 이야기로 찾아올게요. 오늘 도움이 됐다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 또 만나요!",
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
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10
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
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit("all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    sys.exit("full TTS: all retries failed")


def split_scenes():
    import json
    import difflib
    import whisper

    print("loading whisper large-v3 ...")
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(FULL_WAV), language="ko", word_timestamps=True)
    words = [w for seg in result["segments"] for w in seg["words"]]
    if not words:
        sys.exit("whisper returned no words")

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
            if r >= 0.75:
                cands.append((t, r))
            if r > best_r:
                best_r, best_t = r, t
        if cands:
            best_t, best_r = min(cands, key=lambda c: abs(c[0] - est))
        if best_t is None or best_r < 0.55:
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)
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
