# 인필드플라이 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "야구를 보다 보면 정말 황당한 장면이 있어요. 타자가 친 공이 내야에 높이 붕 떴는데, 수비수가 그 공을 잡지도 않았어요. 그런데 심판이 대뜸 타자 아웃을 외칩니다. 잡지도 않았는데 아웃이라니? 이게 대체 무슨 규칙일까요? 오늘은 초보자를 가장 헷갈리게 하는 규칙, 인필드 플라이 이야기입니다.",
    "s02": "인필드 플라이는 한마디로, 내야에 뜬 공을 잡든 안 잡든 타자를 아웃시키는 규칙입니다. 조건이 딱 정해져 있어요. 첫째, 아웃 카운트가 무사거나 1사일 때. 둘째, 주자가 1루와 2루에 있거나 만루일 때. 셋째, 내야수가 평범하게 잡을 수 있는 높이 뜬 공일 때. 이 세 가지가 맞으면 심판이 선언하고, 타자는 바로 아웃입니다.",
    "s03": "그런데 왜 이런 이상한 규칙을 만들었을까요? 바로 지난 편에서 배운 포스아웃, 그 병살 때문입니다. 이 규칙이 없으면요, 수비수가 뜬 공을 일부러 툭 떨어뜨릴 수 있어요. 그러고는 냉큼 주워서 베이스를 밟아, 주자 둘을 한꺼번에 포스아웃시키는 병살을 노리는 거죠. 그 얄미운 꼼수를 막으려고 만든 규칙이랍니다.",
    "s04": "자, 상황을 그려 볼게요. 무사에 주자가 1루와 2루에 있어요. 타자가 내야에 공을 높이 띄웠어요. 주자들은 공이 잡힐까 봐 베이스를 함부로 못 떠나고 엉거주춤 서 있죠. 이때 수비수가 공을 일부러 떨어뜨려 주워 던지면, 밀려날 수밖에 없는 주자들이 그대로 포스아웃, 순식간에 두 명이 죽습니다. 너무 억울하잖아요?",
    "s05": "그래서 심판은 아예 이렇게 정리해 버려요. 잡을 수 있는 뜬 공이면, 잡든 안 잡든 타자는 그냥 아웃! 타자가 미리 아웃되면 포스 상황이 사라지니까, 주자들은 밀려날 걱정 없이 안전해지죠. 그런데 여기서 궁금한 게 하나 생겨요. 왜 하필 1루에 주자가 꼭 있어야 할까요? 그 답은 잠시 뒤에 풀어 드릴게요.",
    "s06": "인필드 플라이는 심판이 선언을 해야만 효력이 생깁니다. 심판은 공이 뜨는 순간, 한 팔을 번쩍 하늘로 들어 올리며 인필드 플라이, 배터 아웃을 외치죠. 만약 공이 파울 선 근처라 애매하면, 페어가 되면 아웃이라는 뜻으로 인필드 플라이 이프 페어라고 외칩니다. 그러다 진짜 파울이 되면, 인필드 플라이는 취소되고 그냥 평범한 파울이 되는 거예요.",
    "s07": "여기서 아주 중요한 포인트. 인필드 플라이가 선언돼도, 경기가 멈추는 게 아닙니다. 공은 여전히 살아 있어요. 타자만 아웃됐을 뿐, 주자들은 위험을 무릅쓰고 다음 베이스로 뛸 수 있습니다. 공이 잡히면 원래 베이스로 돌아와 태그업을 해야 하고, 공이 땅에 떨어지면 눈치껏 진루를 노려도 돼요. 단, 이때는 포스가 아니라서 억지로 뛸 의무는 없답니다.",
    "s08": "여기서 고인물 상식 하나. 모든 뜬 공이 인필드 플라이가 되는 건 아니에요. 쭉 뻗는 직선타구, 라인드라이브는 해당되지 않습니다. 번트를 대다가 살짝 뜬 공도 제외예요. 오로지 내야수가 평범하게 잡을 수 있는, 딱 봐도 잡히겠다 싶은 뜬 공만 인필드 플라이가 됩니다. 판단은 순전히 심판의 몫이고요.",
    "s09": "이제 아까 그 궁금증. 왜 1루에 주자가 꼭 있어야 할까요? 답은 간단해요. 병살을 노리려면, 주자들이 밀려나는 포스 상황이 만들어져야 하거든요. 그러려면 1루가 채워져 뒤 주자를 밀어 줘야 하죠. 만약 2루나 3루에만 주자가 있다면, 밀릴 일이 없으니 꼼수를 부릴 수도 없어요. 그래서 인필드 플라이는 1루가 포함된 1·2루나 만루에서만 적용되는 겁니다.",
    "s10": "오늘 한 줄 요약. 인필드 플라이는, 수비가 일부러 공을 떨어뜨려 병살을 노리는 꼼수로부터 주자를 지켜 주는 규칙이다. 그래서 잡든 안 잡든 타자를 아웃시키는 거죠. 다음 편은 낫아웃입니다. 삼진을 당했는데 어떻게 1루로 살아 나갈까요? 오늘 내용이 쓸 만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
