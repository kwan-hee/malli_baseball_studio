# 출루율 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "자, 2024년 LG 트윈스. 한 타자가 타율 3할 3푼, 홈런은 고작 다섯 개를 쳤습니다. 그런데 출루율은 4할 4푼 7리, 리그 1위예요. 2년 연속 출루왕. 홈런왕도 아닌데, 어떻게 1루에 가장 많이 서 있을까요? 오늘의 주인공은 바로 출루율입니다.",
    "s02": "출루율, 영어로 온 베이스 퍼센티지. 쉽게 말하면, 타석에 나왔을 때 아웃당하지 않고 베이스에 서는 확률이에요. 안타를 치든, 볼넷을 골라 나가든, 몸에 맞아 1루로 가든, 아웃만 안 되면 다 출루로 인정합니다. 타자가 얼마나 자주 살아남는지를 보여 주는 숫자죠.",
    "s03": "계산은 이렇습니다. 분자에 안타, 볼넷, 몸에 맞는 공을 더하고, 분모에는 타수, 볼넷, 몸에 맞는 공, 희생플라이를 더해서 나눕니다. 실책이나 야수 선택으로 나간 출루는 빠지고, 희생번트도 계산에서 제외돼요. 여기서 재밌는 게, 희생플라이는 분모에 들어간다는 점입니다.",
    "s04": "그럼 타율이랑 뭐가 다를까요? 타율은 안타만 세요. 볼넷을 아무리 잘 골라도 타율에는 한 푼도 안 잡힙니다. 출루율은 볼넷까지 인정하니까, 타율은 낮은데 출루율만 높은 타자가 생기죠. 흔히 눈야구라고 부르는 능력입니다. 여러분이 좋아하는 타자, 타율만 보고 있진 않으시죠?",
    "s05": "여기서 고인물 함정 하나. 희생플라이를 치면 타율은 안 깎이잖아요? 그런데 출루율은 깎입니다. 분모에 희생플라이가 들어가거든요. 아웃 하나로 점수를 벌어준 희생인데, 출루율 계산에서는 범타처럼 취급돼요. 그래서 희생플라이가 많은 타자는 타율보다 출루율이 더 낮아질 수 있습니다.",
    "s06": "이 지표, 생각보다 역사가 깁니다. 1954년, 브루클린 다저스의 브랜치 리키 단장과 통계 전문가 앨런 로스가 처음 발표했어요. 그런데 놀랍게도 KBO는 1982년 원년부터 출루율을 공식 기록으로 삼았습니다. 메이저리그보다 2년이나 빨랐죠. 1986년부터는 희생플라이도 분모에 넣는 지금 방식으로 바뀌었고요.",
    "s07": "그럼 어느 정도면 잘하는 걸까요? 대략 3할 4푼, 0.340을 넘으면 우수한 타자예요. 3할 8푼, 0.380을 넘으면 리그 최상급. KBO 단일 시즌 최고는 2001년 펠릭스 호세의 5할 3푼, 0.503입니다. 메이저리그 통산 1위는 테드 윌리엄스의 4할 8푼 2리. 정말 10번 중 거의 5번은 1루에 서 있었다는 뜻이에요.",
    "s08": "예전엔 구단들이 타율만 봤습니다. 그런데 영화 머니볼에 이런 대사가 나와요. 그 선수는 출루를 많이 한다. 안타든 볼넷이든, 그게 중요하냐? 맞습니다. 1루에 서는 건 1루타든 볼넷이든 똑같아요. 타율은 낮지만 출루율 높은 선수를 싸게 데려와 성공한 팀들이 있었고, 지금은 KBO도 출루율을 당연히 봅니다.",
    "s09": "우리 리그의 대표가 바로 홍창기예요. 96개의 볼넷, 12개의 몸에 맞는 공. 홈런은 5개뿐인데 출루율 1위. 지난 24편에서 다룬 오피에스의 절반이 바로 이 출루율입니다. 타율 3할 3푼에 출루율 4할 4푼, 이 차이가 바로 눈야구의 힘입니다.",
    "s10": "정리하면, 출루율은 타율이 놓치는 볼넷과 사구까지 잡아내는, 타자의 진짜 출루 능력입니다. 다음에 중계 볼 때 타자 출루율이 4할에 가까운지 한번 확인해 보세요. 다음 편은 오피에스의 다른 절반, 장타율 이야기로 올게요. 오늘 도움이 됐다면 구독이랑 좋아요 부탁드립니다. 다음 편에서 또 만나요!",
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
