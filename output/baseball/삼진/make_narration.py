# 삼진 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "자, 투수가 던진 공에 타자가 헛스윙! 하나, 둘, 그리고 세 번째 스윙까지 헛돌면, 타자는 방망이 한 번 맞히지 못하고 고개를 숙인 채 돌아섭니다. 투수에겐 이보다 통쾌한 게 없고, 타자에겐 이보다 굴욕적인 게 없죠. 바로 오늘의 주인공, 삼진입니다.",
    "s02": "삼진이 뭐냐면요. 아주 간단해요. 타자가 스트라이크 세 개를 먹으면, 그냥 아웃되는 겁니다. 타자 입장에선 삼진을 당한 거고, 반대로 이걸 잡아낸 투수 입장에선 탈삼진, 삼진을 빼앗았다고 표현하죠. 같은 장면인데, 부르는 이름이 다른 거예요.",
    "s03": "삼진에도 종류가 있어요. 첫째, 헛스윙 삼진. 방망이를 힘껏 휘둘렀는데 공을 못 맞히고 헛친 거죠. 둘째, 루킹 삼진. 방망이도 안 내밀고 가만히 서 있었는데, 심판이 스트라이크를 선언한 겁니다. 흔히 서서 삼진, 또는 루킹 삼진이라고 하는데, 타자 입장에선 이게 더 부끄럽답니다.",
    "s04": "자, 여기서 헷갈리는 거. 투 스트라이크에서 파울을 치면 어떻게 될까요? 삼진일까요? 아니에요. 파울은 아무리 많이 쳐도 삼진이 되지 않고, 스트라이크 상태가 계속 유지됩니다. 단, 딱 하나 예외! 투 스트라이크에서 번트를 대다 파울이 나면, 그건 그냥 삼진 아웃이에요. 이거 알면 고인물입니다.",
    "s05": "그리고 재밌는 게, 세 번째 스트라이크를 포수가 깔끔하게 잡지 못하고 놓치면요? 타자가 아웃이 아니라, 1루로 냅다 뛸 수 있어요. 이걸 낫아웃이라고 하죠. 삼진을 잡고도 주자를 살려 보내는, 포수에겐 아찔한 순간이랍니다. 이건 지난 낫아웃 편에서 자세히 다뤘어요.",
    "s06": "삼진은 기록지에 알파벳 케이로 적어요. 그래서 야구장에 가면, 투수가 삼진을 잡을 때마다 관중석에 케이 카드가 하나씩 늘어나는 걸 볼 수 있죠. 참고로 한 경기에서 타자가 네 번이나 삼진을 당하면, 골든 솜브레로라는 좀 불명예스러운 별명이 붙는답니다.",
    "s07": "투수에게 탈삼진은 최고의 무기예요. 주자가 있어도 삼진만 잡으면 안타나 진루를 원천 봉쇄할 수 있으니까요. 그래서 아홉 이닝당 삼진을 몇 개나 잡는지 보는 케이나인이라는 지표도 있고, 한 시즌 삼진을 가장 많이 잡은 투수에게는 탈삼진왕이라는 타이틀을 줍니다.",
    "s08": "재밌는 건, 요즘 야구에서 삼진이 점점 늘고 있다는 거예요. 투수들의 공은 더 빨라지고, 타자들은 홈런을 노려 크게 휘두르다 보니 삼진도 많아진 거죠. 물론 삼진은 주자를 진루시키지 못하는 최악의 아웃이기도 하지만, 병살처럼 아웃 두 개를 당할 위험은 없다는 양면성도 있답니다.",
    "s09": "그럼 기록을 볼까요? 우리 KBO 단일 시즌 최다 탈삼진은, 2021년 두산의 미란다가 세운 225개입니다. 통산 기록은 오랫동안 송진우 선수가 2,048개로 1위였는데, 2024년 KIA 양현종 선수가 이 기록을 넘어 새로운 역사를 썼죠. 그리고 메이저리그로 가면, 놀런 라이언. 통산 무려 5,714개! 이건 정말 영원히 깨지지 않을 기록이랍니다.",
    "s10": "자, 정리하면요. 삼진은 스트라이크 세 개로 타자를 돌려세우는, 투수의 가장 확실한 아웃이에요. 다음에 중계 보실 때, 투수가 투 스트라이크를 잡으면, 아, 삼진 나오나? 하고 숨죽여 지켜보세요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 또 만나요!",
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
