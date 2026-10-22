# 퍼펙트게임 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "/opt/homebrew/bin:/usr/local/bin"
)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from google.genai import types

# cp949 콘솔에서 비-cp949 문자(em-dash 등) print 크래시 방지 (2026-07-18 유료루프 교훈)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
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
    "s01": "자, 2010년 6월 2일 미국 디트로이트. 한 투수가 스물여섯 명의 타자를 연달아 잡아냈습니다. 이제 딱 한 명, 마지막 한 명만 잡으면 완벽한 경기, 퍼펙트 게임이었죠. 그런데 1루심의 손이 올라간 순간, 그 완벽함이 와르르 무너졌습니다.",
    "s02": "퍼펙트 게임이 뭐냐면요. 한 경기에서 상대 타자 스물일곱 명을, 단 한 명도 1루를 밟게 하지 않고 전부 아웃시키는 겁니다. 안타도, 볼넷도, 몸에 맞는 공도, 실책도 없어야 해요. 그야말로 아무도 살아 나가지 못한 경기죠.",
    "s03": "이거 노히트노런이랑 헷갈리시죠? 노히트노런은 안타만 안 맞으면 됩니다. 볼넷을 내주거나 실책으로 주자가 나가도 상관없어요. 하지만 퍼펙트는 그 출루조차 하나도 허용하면 안 됩니다. 그러니까 모든 퍼펙트 게임은 노히트노런이지만, 노히트노런이라고 다 퍼펙트는 아닌 거예요.",
    "s04": "이 기록의 역사는 꽤 오래됐습니다. 1880년, 리 리치먼드와 존 워드라는 두 투수가 단 닷새 간격으로 퍼펙트를 해냈어요. 그런데 그때는 투수판이 지금보다 훨씬 가깝고, 볼넷도 여덟 개를 던져야 나가던 시절이라, 지금 규칙과는 많이 달랐죠.",
    "s05": "그래서 오늘날과 같은 규칙에서 나온 첫 퍼펙트 게임은 1904년, 그 유명한 사이 영의 경기로 봅니다. 재밌는 건, 퍼펙트 게임이라는 말 자체는 정작 1909년쯤에야 쓰이기 시작했다는 거예요. 기록이 먼저고, 이름이 나중이었던 셈이죠.",
    "s06": "그럼 그동안 몇 번이나 나왔을까요? 백오십 년 가까운 메이저리그 역사에서 딱 스물네 번뿐입니다. 가장 최근은 2023년 양키스의 도밍고 헤르만이었어요. 한 시즌에 수천 경기가 열리는 걸 생각하면, 정말 하늘이 허락해야 나오는 기록입니다.",
    "s07": "그중에서도 딱 하나, 전설로 남은 경기가 있습니다. 1956년 월드시리즈, 그 큰 무대에서 돈 라센이 퍼펙트 게임을 던졌어요. 지금까지도 가을 야구, 포스트시즌에서 나온 퍼펙트 게임은 이 경기, 단 하나뿐입니다.",
    "s08": "그리고 아까 그 2010년 이야기. 투수 갈라라가는 스물일곱 번째 아웃까지 다 잡았습니다. 그런데 1루심이 세이프를 선언해 버린 거예요. 느린 화면으로 다시 보니 명백한 아웃이었죠. 경기가 끝나고, 그 심판은 눈물을 흘리며 사과했습니다. 비록 기록으로 남지는 못했지만, 사람들은 이 경기를 아직도 가장 완벽했던 불완전한 경기로 기억합니다.",
    "s09": "자, 그럼 우리 KBO는요? 놀랍게도 마흔 해가 넘도록 퍼펙트 게임이 단 한 번도 없었습니다. 1997년 정민철은 8회까지 완벽하다 낫아웃 하나로, 2024년 LG 켈리는 8회까지 스물네 명을 완벽하게 잡고도 9회 첫 타자에게 안타를 맞았죠. 이 딱 한 걸음이, 이렇게나 어렵습니다.",
    "s10": "이렇게 퍼펙트 게임은, 투수의 실력에 운까지 완벽하게 겹쳐야만 나오는 야구 최고의 기록입니다. 언젠가 KBO에서도 이 장면이 나오면 정말 짜릿하겠죠? 오늘 내용이 재밌으셨다면 구독과 좋아요 부탁드려요. 다음 편에서는 출루율 이야기로 찾아뵙겠습니다!",
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
            # 최소 길이 가드: 잘린 take(Puck이 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
            dur = len(pcm) / (SR * BITS // 8 * CH)
            min_dur = len(norm("".join(SCENES.values()))) * 0.10  # 정규화 글자수 × 0.10초
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
            b = max(prev_b + 1.0, est - BOUNDARY_MARGIN)  # 환각 구간 - 비례 폴백
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
