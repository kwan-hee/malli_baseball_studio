# 말리와 북풍과 해님 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 씬 시작 금지 (2026-07-16 까치편 whisper 환각 교훈)
import base64
import os
import sys
import time
import wave
from pathlib import Path

# cp949 콘솔에서 em-dash 등 비-cp949 문자 print 시 UnicodeEncodeError 로 죽는 것 방지
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Whisper가 subprocess로 ffmpeg를 호출 — WinGet 설치 경로를 PATH에 추가
FFMPEG_DIR = (
    "/opt/homebrew/bin:/usr/local/bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, "
    "북풍이 쌩쌩 부는 장면은 힘차고 우렁차게, "
    "해님이 따뜻하게 비추는 장면은 포근하고 다정하게, "
    "나그네가 외투를 벗는 장면은 편안하고 기분 좋게, "
    "북풍과 해님이 화해하는 장면은 훈훈하고 따뜻하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은 북풍과 해님 이야기를 들려줄 거예요. 힘으로 억지로 하는 것과 따뜻하게 마음을 여는 것, 어떤 게 더 잘 통할까요? 같이 알아봐요!",
    "s02": "옛날 옛날, 하늘 위에서 북풍과 해님이 만났어요. 북풍이 큰 소리로 말했어요. 나는 세상에서 가장 힘이 센 바람이야! 그러자 해님이 빙그레 웃으며 대꾸했지요. 힘이 세다고 뭐든 할 수 있는 건 아니란다.",
    "s03": "마침 아래쪽 길에 나그네가 두꺼운 외투를 입고 걸어가고 있었어요. 북풍이 가리키며 말했어요. 좋아, 그럼 저 사람의 외투를 벗기는 쪽이 이기는 거다! 해님이 고개를 끄덕이며 대답했지요. 좋아, 네가 먼저 해 봐.",
    "s04": "북풍이 입을 크게 벌리고 쌩쌩 불기 시작했어요. 나뭇잎이 우수수 날리고, 나무가 흔들흔들, 바람이 온 들판을 휩쓸었지요. 하지만 나그네는 추워서 외투를 더 꽁꽁 여며 잡았어요.",
    "s05": "북풍은 더 세게, 더더 세게 불었어요. 모자가 날아갈 만큼 거센 바람이었지요. 그런데 나그네는 고개를 숙이고 외투 깃을 꽉 움켜쥔 채 꿈쩍도 하지 않았어요. 북풍은 결국 지쳐서 멈추고 말았답니다.",
    "s06": "이번엔 해님 차례예요. 해님이 구름 사이로 살며시 얼굴을 내밀고, 따스한 햇살을 비추기 시작했어요. 들판에 꽃이 활짝 피고, 나비가 팔랑팔랑, 온 세상이 환해졌어요.",
    "s07": "나그네가 걸음을 멈추고 하늘을 올려다봤어요. 아, 날씨가 이렇게 좋을 수가! 나그네는 활짝 웃으며, 스스로 외투 단추를 하나씩 풀더니, 외투를 벗어 팔에 걸었어요. 해님이 이겼답니다!",
    "s08": "북풍은 고개를 떨어뜨리고 작은 목소리로 말했어요. 세게 불면 벗을 줄 알았는데, 오히려 더 꽉 잡더라. 해님이 다정하게 대꾸했지요. 억지로 하면 마음이 닫히고, 따뜻하게 하면 마음이 열리는 거란다. 북풍도 고개를 끄덕이며 알겠다고 말했어요.",
    "s09": "그 뒤로 북풍은 사나운 바람 대신, 시원한 바람을 불어 주었어요. 해님과 함께 여름엔 시원하게, 겨울엔 따뜻하게, 세상을 사이좋게 돌보았답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 무섭게 화내고 억지로 하면 더 꽁꽁 숨지만, 따뜻하게 말하면 마음이 열린다는 거죠? 여러분도 친구한테 따뜻한 말 한마디 먼저 건네 보세요! 재미있었다면 구독이랑 좋아요 꾹 눌러 주세요. 다음에 또 만나요, 멍멍!",
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
                raise RuntimeError(f"truncated take: {dur:.1f}s < {min_dur:.1f}s expected — retry")
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
            print(f"{sid}: prefix match weak (best={best_r:.2f}) — proportional fallback @ {b:.2f}")
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
