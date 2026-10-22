# 말리와 재주많은 다섯 친구 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 씬 시작 금지 (2026-07-16 까치편 whisper 환각 교훈)
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
    "말리(강아지)의 대사는 신나고 귀엽게, 다섯 친구를 하나씩 소개하는 장면은 개성 있고 흥미진진하게, "
    "재주를 놀림받아 속상해하는 장면은 살짝 시무룩하게, "
    "산 너머 마을에 산불이 난 위기 장면은 긴장감 있게(단 무섭지 않게), "
    "다섯 친구가 힘을 합쳐 재주를 부리는 장면은 신나고 통쾌하게, "
    "마을을 구하고 다 함께 얼싸안는 마지막은 밝고 감동적으로 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 남들 눈엔 별것 아닌 재주를 가진 다섯 친구가, 힘을 모아 아주 큰일을 해내는 멋진 이야기를 가져왔어요. 세상에 쓸모없는 재주는 하나도 없대요. 자, 재주 많은 다섯 친구를 함께 만나러 가 볼까요?",
    "s02": "옛날 어느 마을에, 저마다 신기한 재주를 하나씩 가진 다섯 친구가 살았어요. 첫째는 커다란 바위도 번쩍 드는 힘센 친구, 둘째는 코로 세찬 바람을 일으키는 콧바람 친구, 셋째는 강물을 몽땅 들이켜는 물 친구, 넷째는 몸이 무쇠처럼 단단한 무쇠 친구, 그리고 다섯째는 아주 먼 곳의 소리도 듣는 귀 밝은 친구였답니다.",
    "s03": "그런데 마을 사람들은 다섯 친구의 재주를 보고 자꾸만 고개를 갸웃거렸어요. 저런 재주를 대체 어디다 쓴담? 힘이 세면 뭐 하고, 콧바람은 또 어디다 쓴다니. 다섯 친구는 조금 속이 상했지만, 서로를 바라보며 씩씩하게 웃었지요. 우리 재주도 언젠가 꼭 쓸모가 있을 거야!",
    "s04": "어느 날 저녁이었어요. 귀 밝은 친구가 두 귀를 쫑긋 세우더니 깜짝 놀랐어요. 얘들아, 산 너머 마을에서 불이야 하는 소리가 들려! 아주 큰 산불이 났나 봐! 다섯 친구는 서로를 마주 보았어요. 그리고 누가 먼저랄 것도 없이, 그 마을을 향해 있는 힘껏 달려가기 시작했답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 재주 하나하나는 작고 별것 아닌 것 같은데, 이 다섯이 힘을 합치면 과연 무슨 일이 벌어질까요? 저렇게 커다란 산불을, 정말 다섯 친구가 끌 수 있을까요? 자, 두근두근한 마음으로 함께 지켜봐요!",
    "s06": "마을에 도착해 보니, 시뻘건 불길이 집들을 향해 무섭게 번지고 있었어요. 그때 콧바람 친구가 성큼 앞으로 나섰지요. 코를 크게 벌름거리더니, 후우우! 세찬 바람을 내뿜어 타오르는 불길을 저 멀리 밀어냈어요. 하지만 불길이 너무 커서, 콧바람 하나만으로는 좀처럼 잡히지 않았답니다.",
    "s07": "이번엔 힘센 친구가 나설 차례였어요. 불에 타 쓰러진 커다란 나무와 바위를 번쩍번쩍 들어 치우며, 사람들이 빠져나갈 길을 활짝 만들었지요. 무쇠 친구는 겁도 없이 불 속으로 성큼성큼 걸어 들어가, 미처 빠져나오지 못한 사람들을 등에 업고 안전하게 데리고 나왔답니다.",
    "s08": "그래도 불길은 여전히 활활 타올랐어요. 마지막으로 물 친구가 앞으로 성큼 나섰지요. 물 친구는 커다란 강으로 달려가, 강물을 꿀꺽꿀꺽 배가 빵빵해지도록 들이켰어요. 그러고는 타오르는 불길을 향해, 촤아아! 그 많은 물을 시원하게 뿜어냈답니다. 무섭던 산불이 순식간에 스르르 꺼지고 말았어요.",
    "s09": "산불이 완전히 꺼지자, 마을은 다시 평화를 되찾았어요. 목숨을 구한 마을 사람들은 다섯 친구를 빙 둘러싸고 만세를 불렀지요. 쓸모없어 보이던 그 재주들이, 마을을 통째로 구해 낸 자랑스러운 영웅의 재주가 된 거예요. 다섯 친구는 서로 얼싸안고 활짝 웃었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 혼자서는 작아 보이던 재주도, 다 같이 힘을 합치니 이렇게 큰일을 해냈지요? 여러분이 가진 재주도, 세상에 하나뿐인 아주 소중한 보물이랍니다. 그러니 나의 재주를 부끄러워 말아요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
            # 최소 길이 가드: 잘린 take(Kore가 중간에 끊는 경우) 자동 폐기 후 재시도 (2026-07-16 방귀편 교훈)
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
    # 매칭 실패(환각 구간)면 글자수 비례 추정으로 graceful fallback (붕괴 대신 근사치). 필요시 fix_boundaries 로 보정.
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
