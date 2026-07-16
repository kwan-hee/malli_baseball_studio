# 포스아웃 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, r"C:\youtube_longform_agent")
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
    "s01": "야구를 보다 보면 참 이상한 장면이 있어요. 1루수가 공을 잡고 주자 몸엔 손도 안 댔는데, 베이스만 밟았을 뿐인데 아웃이 선언됩니다. 그런데 반대로 어떤 날은, 3루 주자가 홈을 먼저 밟았는데도 점수가 안 나요. 대체 무슨 일일까요? 오늘은 이 모든 비밀의 열쇠, 포스아웃 이야기입니다.",
    "s02": "포스아웃은 한마디로, 주자가 어쩔 수 없이 다음 베이스로 밀려나야 하는 상황에서 나오는 아웃입니다. 타자가 공을 치면, 타자도 1루로 달려가야 하죠? 그럼 원래 1루에 있던 주자는 자기 자리를 뺏겨서, 무조건 2루로 밀려나야 해요. 이렇게 갈 곳이 정해진 채로 밀려나는 주자를, 포스 상황의 주자라고 부릅니다.",
    "s03": "여기가 진짜 포인트인데요. 이렇게 밀려나는 주자는, 수비수가 몸에 태그를 안 해도 됩니다. 그냥 공을 들고 그 베이스를 먼저 밟기만 하면 아웃이에요. 타자를 1루에서 잡을 때, 1루수가 타자 몸을 건드리지 않고 베이스만 밟죠? 그게 바로 포스아웃입니다. 주자는 갈 곳이 딱 정해져 있으니, 그 베이스만 지켜도 되는 거죠.",
    "s04": "그럼 반대는 뭘까요? 밀려나지 않는 주자입니다. 예를 들어 2루에만 주자가 있고 1루는 비어 있으면, 이 2루 주자는 굳이 3루로 갈 의무가 없어요. 뒤에서 미는 사람이 없으니까요. 그래서 이런 주자는 반드시 몸에 태그를 해야 아웃입니다. 베이스만 밟아선 안 잡혀요. 밀리면 포스아웃, 안 밀리면 태그아웃. 이 차이가 야구 수비의 기본입니다.",
    "s05": "자, 그런데 아까 첫머리에서 말했죠. 3루 주자가 홈을 먼저 밟았는데도 점수가 안 나는 이상한 장면. 그 비밀은 잠시 뒤에 시원하게 풀어 드릴게요. 그 전에, 이 포스아웃이 만들어 내는, 야구에서 가장 짜릿한 장면부터 보고 가시죠.",
    "s06": "바로 병살, 더블플레이입니다. 무사에 1루 주자가 있을 때 타자가 땅볼을 치면요, 유격수나 2루수가 공을 잡아 2루를 먼저 밟아 1루 주자를 포스아웃시키고, 곧바로 1루로 던져 타자까지 아웃시킵니다. 공 하나로 아웃 두 개를 잡는 거죠. 이게 다, 태그 없이 베이스만 밟으면 되는 포스아웃이라서 가능한 겁니다. 투수한테 병살보다 반가운 선물은 없어요.",
    "s07": "포스아웃엔 함정도 있어요. 처음엔 포스 상황이었어도, 도중에 포스가 풀려 버리는 경우가 있거든요. 예를 들어 타자가 1루에서 먼저 아웃되면, 뒤에서 밀려오던 주자는 이제 밀릴 이유가 없어져요. 앞자리가 비었으니까요. 바로 그 순간 포스가 해제돼서, 그 주자는 이제 베이스만 밟아선 못 잡고, 반드시 몸에 태그를 해야 합니다. 이걸 모르면 다 잡은 주자를 놓쳐요.",
    "s08": "자, 이제 아까 그 미스터리. 3루 주자가 홈을 먼저 밟았는데 왜 점수가 안 났을까요? 규칙이 이렇습니다. 그 이닝의 세 번째 아웃이 포스아웃이면, 그 전에 홈을 밟은 주자의 득점은 인정되지 않아요. 만루에서 땅볼이 나왔다고 해 볼게요. 3루 주자가 홈을 밟는 그 순간, 2루에서 포스아웃으로 세 번째 아웃이 만들어지면? 홈을 먼저 밟았어도 그 점수는 없던 일이 됩니다. 이거 알면 진짜 고인물이에요.",
    "s09": "흔한 오해 하나 바로잡죠. 수비가 주자 몸을 안 건드렸으니 세이프다? 포스 상황이라면 아닙니다. 밀려나는 주자는 태그가 아예 필요 없으니까요. 반대로, 밀리지 않는 주자한테 베이스만 밟고 아웃을 외치면? 그건 세이프예요. 그래서 노련한 주자는 상황을 딱 보고, 포스가 풀렸다 싶으면 베이스에서 살짝 벗어나 태그를 피하기도 합니다.",
    "s10": "오늘 한 줄 요약. 밀려나는 주자는 태그 없이 베이스만 밟아도 아웃, 이게 바로 포스아웃이다. 그래서 주자 몸을 안 건드려도, 심지어 주자가 홈을 먼저 밟아도 점수가 안 될 수 있는 거죠. 다음 편은 인필드 플라이입니다. 잡기 쉬운 공을 일부러 안 잡으면 왜 아웃일까요? 오늘 내용이 쓸 만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
            # 최소 길이 가드: 잘린 take(Kore/Puck이 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10  # 정규화 글자수 × 0.10초
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
    # 기존 누적 글자 방식은 whisper 오전사/환각으로 뒤 씬 경계가 통째로 밀려 붕괴 → 접두어 매칭으로 교체.
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
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)  # 환각 구간 — 비례 폴백
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
