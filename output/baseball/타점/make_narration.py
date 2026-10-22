# 타점 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "자, 만루입니다. 위기이자 기회죠. 타자가 딱 안타 하나를 쳤어요. 그랬더니 주자 셋이 우르르 홈으로 쏟아져 들어옵니다. 순식간에 3점! 그런데 이 세 점이, 전부 이 타자 한 명의 공로로 기록됩니다. 바로 오늘의 주인공, 타점이에요.",
    "s02": "타점이 뭐냐면요. 말 그대로, 타자가 타격을 해서 주자를 홈으로 불러들여 만들어 낸 점수를 말합니다. 영어로는 알비아이, 런 배티드 인이라고 하죠. 재밌는 건, 홈런을 치면요? 자기 자신이 홈에 들어온 것도 타점으로 쳐줍니다. 그래서 만루 홈런은 한 방에 4타점이 되는 거예요.",
    "s03": "그럼 어떤 경우에 타점이 될까요? 안타로 불러들이면 당연히 타점이고요. 심지어 내가 아웃당하면서 점수를 내도 타점이 됩니다. 외야로 깊게 친 희생플라이, 번트로 주자를 밀어주는 희생번트, 그리고 만루에서 볼넷이나 몸에 맞는 공으로 밀어내기 득점을 해도, 전부 타점으로 인정해 줘요.",
    "s04": "그런데 점수가 나도 타점이 안 되는 경우가 있어요. 대표적인 게 실책입니다. 상대 수비 실수로 주자가 홈에 들어오면, 그건 타자의 공이 아니니까 타점을 안 줍니다. 마찬가지로 폭투나 포수 뒤로 빠지는 공, 또 도루로 홈을 훔쳐도 타점은 없어요.",
    "s05": "여기 고인물 디테일 하나. 병살타를 쳤을 때는요, 그 사이에 3루 주자가 홈에 들어와도 타점을 안 줍니다. 아웃을 두 개나 헌납하면서 낸 점수라, 규칙상 타자의 공으로는 쳐주지 않는 거예요. 이거 은근히 헷갈리시죠?",
    "s06": "그런데 예외도 있어요. 무사나 1사에서, 3루 주자가 어차피 여유 있게 홈에 들어올 상황이었다면, 그 과정에 수비 실책이 살짝 끼어도 타점을 인정해 줍니다. 실책이 아니었어도 어차피 점수가 났을 거라고 보는 거죠.",
    "s07": "그럼 타점이 왜 중요할까요? 흔히 해결사, 클러치 능력의 상징이잖아요. 위기에 한 방 쳐 주는 타자, 정말 멋지죠. 그런데 여기엔 함정도 있어요. 타점은 내 앞 타자들이 나가 있어야만 올릴 수 있습니다. 아무리 잘 쳐도 앞에 주자가 없으면 타점이 안 나요. 그래서 순수한 개인 실력만 보긴 어려운, 팀과 타순의 영향을 받는 기록이랍니다.",
    "s08": "이 타점, 역사도 깊어요. 메이저리그에서는 1920년부터 공식 기록으로 삼기 시작했습니다. 100년이 넘도록, 타자의 생산력을 보여 주는 대표적인 지표로 사랑받고 있죠.",
    "s09": "그럼 기록을 볼까요? 놀랍게도 우리 KBO 단일 시즌 최다 타점은, 바로 2025년에 새로 쓰였어요. 삼성의 디아즈가 무려 147타점을 올리며, 2015년 박병호의 146타점을 딱 1점 차로 넘어섰습니다. 통산 기록은 최형우 선수가 1,733타점으로 역대 1위. 메이저리그 통산 1위는 그 위대한 행크 애런의 2,297타점이랍니다.",
    "s10": "자, 정리하면요. 타점은 타자가 주자를 홈으로 불러들여 만든 점수예요. 해결사의 상징이지만, 앞 타자들의 도움도 필요한 기록이죠. 다음에 중계 보실 때, 만루에서 타석에 선 타자를 응원하며 타점을 기대해 보세요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편은 야구의 가장 기본, 타율 이야기로 찾아올게요. 다음 편에서 만나요!",
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
