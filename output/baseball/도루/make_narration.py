# 도루 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "자, 투수가 공을 던지려는 그 찰나! 1루에 있던 주자가 번개처럼 튀어 나갑니다. 2루로, 헤드퍼스트 슬라이딩! 세이프! 안타 하나 없이, 순전히 두 다리만으로 베이스를 하나 훔쳐 냈어요. 바로 오늘의 주인공, 발야구의 꽃, 도루입니다.",
    "s02": "도루가 뭐냐면요. 말 그대로 베이스를 훔치는 겁니다. 타자가 안타를 쳐 주지 않아도, 주자가 스스로 투수의 빈틈을 노려, 순수하게 자기 주력으로 다음 베이스까지 달려가 세이프되면, 그게 바로 도루예요. 팀 입장에선 공짜로 한 베이스를 버는 셈이죠.",
    "s03": "자, 여기서 헷갈리는 거. 주자가 다음 베이스로 갔다고 다 도루는 아니에요. 예를 들어 투수가 공을 빠뜨리는 폭투나, 포수가 뒤로 빠뜨리는 포일, 또 견제 악송구로 주자가 진루하면, 그건 도루가 아니라 투수나 수비의 실수로 기록됩니다. 오직 주자가 자기 힘으로 스타트를 끊어 성공해야, 진짜 도루로 인정받아요.",
    "s04": "그럼 도루는 어떻게 성공할까요? 핵심은 스타트입니다. 주자는 베이스에서 살짝 떨어져 리드를 잡고, 투수가 홈으로 던지는 그 순간을 노려 총알처럼 튀어 나가요. 그리고 포수의 송구보다 먼저, 발이나 손을 베이스에 슉, 대는 겁니다. 눈 깜짝할 사이에 승부가 갈리죠.",
    "s05": "그런데 도루는 무작정 뛰면 안 돼요. 만약 아웃되면, 애써 나간 주자를 그냥 잃어버리는 거잖아요. 그래서 성공률이 정말 중요합니다. 보통 열 번 시도해서 여덟 번, 그러니까 8할 이상은 성공해야, 팀에 이득이라고 봐요. 그래서 감독님들도 도루 사인을 신중하게 낸답니다.",
    "s06": "물론 늘 성공하는 건 아니에요. 주자가 뛰는 걸 본 포수가, 총알 같은 송구로 2루수에게 공을 뿌립니다. 그리고 태그! 아웃! 이렇게 도루하려다 잡히는 걸, 도루 실패, 또는 도루자라고 불러요. 그래서 강한 어깨를 가진 포수는, 주자들에게 아주 무서운 존재랍니다.",
    "s07": "이 도루는, 힘으로 하는 야구가 아니라 발로 하는 야구, 이른바 스몰볼의 꽃입니다. 홈런 한 방이 없어도, 도루로 한 베이스씩 야금야금 훔쳐서 점수를 만들어 내는 거죠. 빠른 발 하나로 상대 배터리를 뒤흔드는, 아주 짜릿한 플레이예요.",
    "s08": "재밌는 건, 최근 도루가 확 늘었다는 거예요. 메이저리그가 2023년에 규칙을 바꿨거든요. 베이스 크기를 키우고, 투수의 견제를 두 번으로 제한했더니, 리그 전체 도루가 한 해 만에 무려 4할이나 늘었습니다. 그래서 2023년은 도루의 해라고까지 불렸죠.",
    "s09": "그럼 전설들을 볼까요? 우리 KBO 단일 시즌 최다 도루는, 1994년 이종범 선수의 84개입니다. 통산 기록은 전준호 선수가 549개로 1위죠. 하지만 메이저리그로 가면, 넘사벽이 있어요. 바로 리키 헨더슨. 통산 무려 1,406개! 2위보다 450개나 많은, 아마 영원히 깨지지 않을 기록이랍니다.",
    "s10": "자, 정리하면요. 도루는 안타 없이 순수한 발로 베이스를 훔쳐 내는, 야구에서 가장 스릴 넘치는 플레이예요. 다음에 중계 보실 때, 발 빠른 주자가 리드를 크게 잡으면, 아, 뛰겠구나! 하고 두근두근 지켜보세요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 또 만나요!",
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
