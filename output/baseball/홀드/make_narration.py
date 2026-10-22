# 홀드 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "세이브는 다 아시죠? 마무리 투수가 마지막에 나와서 리드를 지키면 세이브. 근데요, 7회에 나와서 불을 끄고, 8회에 또 다른 투수가 나와서 불을 끈다면? 이 투수들한테는 세이브가 안 붙어요. 오늘의 야구사전, 홀드입니다.",
    "s02": "홀드는요, 쉽게 말해서 중간에 나와서 리드를 지킨 구원투수에게 주는 기록이에요. 세이브는 경기를 마무리해야 받을 수 있잖아요. 그러면 6회든 7회든 나와서 화재를 진압한 투수는요? 아무 기록도 없었어요. 그래서 만든 게 홀드입니다.",
    "s03": "홀드를 받으려면 조건이 있어요. 첫째, 세이브 상황에 들어와야 해요. 3점 이내 리드, 동점 가능 주자 상황, 이런 조건이죠. 둘째, 최소 1아웃 이상을 잡아야 해요. 등판만 하고 아무도 못 잡으면 안 돼요. 셋째, 리드를 지킨 채 마운드를 내려와야 합니다. 넷째, 경기를 마무리하면 안 돼요. 마무리하면 세이브니까요.",
    "s04": "정리하면 이래요. 같은 세이브 상황에서 등판해서, 리드를 지키고 끝까지 던지면? 세이브. 리드를 지키고 도중에 다음 투수에게 넘기면? 홀드. 리드를 못 지키고 동점이나 역전을 허용하면? 블론세이브. 딱 이 세 갈래예요.",
    "s05": "홀드가 처음 나온 건 1986년이에요. 미국의 야구 데이터 회사 스탯스에서 존 듀완과 마이크 오도넬이라는 통계 전문가 두 명이 만들었어요. 마무리 투수만 세이브로 인정받고, 중간에 불 끄는 투수들은 아무 기록이 없으니까, 이 사람들의 공헌을 숫자로 남기자는 취지였어요.",
    "s06": "재밌는 게 뭐냐면요, 이 기록을 만든 미국, 그러니까 메이저리그에서는 아직까지 홀드를 공식 기록으로 인정하지 않아요. 비공식이에요. 반면에 우리 KBO는 2000년부터 정식 기록으로 채택했어요. 일본 프로야구도 2005년에 공인했고요. 만든 나라에서 안 알아주는데 우리가 먼저 인정해 준 거예요.",
    "s07": "자, KBO 역사에서 홀드의 전설을 한 분 소개할게요. LG 트윈스의 김진성. 2026년 8월 11일, 키움전에서 7회에 등판해 1이닝을 틀어막고 통산 178번째 홀드를 기록했습니다. 안지만이 2016년에 세운 177홀드를 무려 10년 만에 갈아치운 거예요. 역대 통산 홀드 1위.",
    "s08": "이 기록이 더 대단한 이유가 있어요. 김진성, 프로 생활 동안 세 번이나 방출을 당했습니다. 팀에서 잘렸다가 다시 붙고, 또 잘리고, 또 붙은 거예요. 마흔한 살에도 불펜에서 묵묵히 던지면서 역대 1위에 오른 겁니다. 팬들이 헌신좌라고 부르는 이유가 있어요.",
    "s09": "단일 시즌 최다 홀드도 있어요. 2019년 키움 히어로즈의 김상수, 67경기에 등판해서 한 시즌에만 40홀드를 기록했어요. 67경기 중 40번이나 세이브 상황에서 불을 껐다는 뜻이에요. 거의 두 경기에 한 번꼴이죠. 세이브 편에서 말씀드린 승계주자 기억나시죠? 홀드 투수가 물려받은 주자를 잘 막으면 그 점수는 앞 투수 자책점이 돼요. 홀드와 승계주자, 이 둘을 같이 보면 중간계투 실력이 딱 보입니다.",
    "s10": "자, 정리하면요. 홀드는 마무리가 아닌 중간계투, 불 끄는 소방관한테 주는 기록이에요. 세이브 상황에서 리드를 지키고 다음 투수에게 넘기면 홀드. 끝까지 던지면 세이브. 못 지키면 블론세이브. 이 세 가지만 기억하면 돼요. 다음 편은 방어율입니다. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
