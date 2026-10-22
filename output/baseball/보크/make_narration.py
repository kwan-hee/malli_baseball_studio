# 보크 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "한 공도 안 던지고 경기가 끝났다고요? 네, 진짜 있었습니다. 바로 보크 때문이에요. 자, 야구에서 가장 헷갈리는 규칙, 보크. 프로 선수들도 정확히 모르는 이 규칙, 오늘 깔끔하게 정리해 드릴게요.",
    "s02": "보크는요, 쉽게 말해서 투수가 주자를 속이는 부정 동작을 했을 때 선언되는 반칙이에요. 규칙의 핵심은 딱 하나. 투수가 주자를 고의로 속여서는 안 된다. 보크가 선언되면 어떻게 되냐면요, 주자 전원이 공짜로 한 베이스씩 진루해요. 3루에 주자가 있으면? 네, 그냥 1점 들어갑니다.",
    "s03": "이거 은근 헷갈리시죠? 보크 유형이 공식적으로 열세 가지나 되거든요. 근데 자주 나오는 건 세 가지예요. 첫째, 투구 동작을 시작했다가 멈추는 것. 던지려다 말면 보크. 둘째, 1루나 3루로 견제하는 척만 하고 안 던지는 것. 이걸 페이크 견제라고 하는데, 보크입니다. 셋째, 세트 포지션에서 완전히 정지하지 않고 투구하는 것. 이 세 가지만 알아도 중계 볼 때 아, 보크! 할 수 있어요.",
    "s04": "재밌는 게 뭐냐면요, 투수판을 밟고 있다가 공을 떨어뜨려도 보크예요. 손에서 미끄러져서 툭 떨어뜨리면? 보크. 주자가 없는 베이스에 견제구를 던져도 보크고요. 심지어 공을 안 갖고 투수판에 올라가도 보크입니다. 이래서 투수들이 긴장하는 거예요.",
    "s05": "자, 여기서 재밌는 역사가 하나 있어요. 1988년 메이저리그, 보크의 해라고 불립니다. 세트 포지션 정지 규칙을 아주 미세하게 바꿨는데, 이게 역대급 보크 폭발을 일으켰어요. 사십 이닝에 한 번꼴로 보크가 나왔고, 오클랜드의 데이브 스튜어트는 그 해에만 열여섯 개, 역대 최다 시즌 보크를 기록했습니다.",
    "s06": "근데 이건 더 대단해요. 1963년, 밀워키 브레이브스의 밥 쇼. 이 투수가 한 경기에서 보크를 다섯 개나 범했어요. 역대 최다. 심지어 3회에는 볼넷 하나 내보내놓고 보크 세 번 연속으로 주자를 2루, 3루, 홈까지 보냈습니다. 투구 한 개 안 하고 1점을 내줬어요. 이런 일이 실제로 일어납니다.",
    "s07": "우리 KBO에도 역대급 보크 사건이 있어요. 2006년 준플레이오프 1차전. 9회 말 2 대 2, 한 점도 안 지고 버텨야 하는 상황에서 한기주 투수가 보크를 범합니다. 3루 주자가 그냥 홈으로 들어와 결승점. 이게 패배로 이어지면서, 한기주에게는 계약금에 빗대 십억보크라는 별명이 붙었어요.",
    "s08": "2010년에는 권혁이 포스트시즌 9회 초 1점 차 상황에서 투수판을 밟은 채 공을 떨어뜨려 보크. 이후 포스트시즌 내내 심리적으로 위축됐다고 해요. 2013년에는 두산 유창준이 분노를 참지 못하고 공을 바닥에 패대기쳐서 보크 선언. 보크는 이렇게 순간의 실수나 감정이 경기를 뒤집어버리는, 무서운 규칙이에요.",
    "s09": "그런데 일부러 보크를 범하는 경우도 있어요. 2루 주자가 포수 사인을 훔쳐보는 걸 차단하려고, 일부러 보크를 줘서 3루로 보내버리는 거예요. 3루에서는 사인을 볼 수가 없거든요. 이걸 고의보크 전략이라고 해요. 2019년 다저스의 켄리 잰슨이 실제로 이 전략을 썼고, 2025년에는 오타니를 상대로도 했습니다. 이거 알면 고인물이에요.",
    "s10": "자, 정리하면요. 보크는 투수가 주자를 속이면 안 된다는 규칙이에요. 열세 가지나 되지만, 투구 중단, 페이크 견제, 세트 미정지, 이 세 가지만 기억하면 돼요. 다음에 중계 보실 때 투수 동작 잘 보세요. 아, 보크! 외치실 수 있을 겁니다. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 또 만나요!",
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
