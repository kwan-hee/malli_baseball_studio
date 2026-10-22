# 타율 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "자, 야구에는 참 신기한 게 하나 있어요. 열 번 타석에 나와서, 딱 세 번만 안타를 쳐도 최고의 타자라고 불립니다. 나머지 일곱 번은 실패했는데도 말이죠. 세상에 이렇게 후한 종목이 또 있을까요? 바로 이 3할의 비밀, 오늘의 주인공 타율입니다.",
    "s02": "타율이 뭐냐면요. 아주 간단해요. 타자가 친 안타 수를, 타수로 나눈 값입니다. 쉽게 말해, 이 타자가 타석에 섰을 때 안타를 칠 확률이죠. 열 번 쳐서 세 번 안타면 3할, 열 번 쳐서 네 번이면 4할. 야구에서 가장 오래되고, 가장 기본이 되는 지표예요.",
    "s03": "자, 여기서 은근히 헷갈리는 거. 분모가 타석이 아니라 타수예요. 이게 왜 중요하냐면요. 볼넷으로 걸어 나가거나, 몸에 맞는 공, 또 희생번트나 희생플라이는 타수에서 쏙 빠집니다. 그러니까 볼넷을 아무리 많이 골라도, 타율은 1도 안 떨어져요. 손해도 이득도 없는 거죠.",
    "s04": "그리고 타율은 소수점 셋째 자리까지 읽는데요. 우리말로 할, 푼, 리라고 합니다. 0.333이면 3할 3푼 3리, 이렇게요. 중계에서 3할 2푼 5리 하면, 아, 0.325구나 하고 알아들으시면, 이제 여러분도 야구 좀 보는 겁니다.",
    "s05": "그럼 어느 정도면 잘하는 걸까요? 2할 5푼, 0.250 정도면 평범한 타자고요. 3할, 0.3을 넘으면 잘 친다, 우수하다는 소리를 듣습니다. 3할 3푼을 넘으면 그 해 타격왕을 다투는 최상급이고요. 그리고 4할, 0.4는요? 그건 전설의 영역입니다.",
    "s06": "이 4할이 얼마나 어렵냐면요. 메이저리그에서 마지막으로 4할을 친 선수가, 무려 1941년 테드 윌리엄스입니다. 그 해 마지막 경기 전에 타율이 3할 9푼 9리, 반올림하면 4할이었어요. 감독이 안 나가도 된다고 했지만, 그는 당당하게 더블헤더 두 경기를 다 뛰어서 기어이 4할 6리를 완성했죠. 그 뒤로 80년이 넘도록, 아무도 못 했습니다.",
    "s07": "그럼 우리 KBO는요? 놀랍게도 딱 한 명 있습니다. 1982년, 프로야구 원년에 백인천 선수가 무려 4할 1푼 2리를 쳤어요. 이게 지금까지도 KBO 유일한 4할이자, 역대 단일 시즌 최고 타율입니다. 아쉽게 놓친 선수도 있어요. 1994년 이종범 선수가 3할 9푼 3리까지 갔지만, 딱 거기까지였죠.",
    "s08": "그럼 꾸준함의 상징, 통산 타율은 누가 1위일까요? 오랫동안 장효조 선수가 3할 3푼으로 1위를 지켰는데요. 최근엔 이정후 선수가 통산 3할 4푼으로 새 역사를 썼습니다. 참고로 메이저리그 통산 1위는, 그 유명한 타이 콥의 3할 6푼 6리랍니다. 통산 3할이 얼마나 대단한 건지 아시겠죠?",
    "s09": "그런데 이 타율, 완벽하진 않아요. 생각해 보면, 단타를 치든 홈런을 치든 똑같이 안타 한 개로만 셉니다. 볼넷으로 나가는 건 아예 반영도 안 되고요. 그래서 타율이 놓치는 걸 잡으려고, 우리가 앞에서 배운 출루율, 장타율, 그리고 그 둘을 합친 오피에스가 나온 겁니다. 타율은 기본이지만, 전부는 아니라는 거죠.",
    "s10": "자, 정리하면요. 타율은 타자가 안타를 칠 확률을 보여 주는, 야구에서 가장 기본이 되는 지표예요. 3할이면 최고의 타자, 4할이면 전설. 다음에 중계 보실 때, 좋아하는 타자의 타율이 3할을 넘는지 응원하며 지켜보세요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편은 발야구의 꽃, 도루 이야기로 찾아올게요. 다음 편에서 만나요!",
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
