# 말리와 의좋은 형제 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 형과 아우가 서로를 걱정하는 장면은 다정하고 뭉클하게, "
    "밤에 몰래 볏단을 나르는 장면은 조심스럽고 따뜻하게, "
    "낟가리가 그대로여서 이상해하는 장면은 궁금하고 아리송하게, "
    "달밤에 두 형제가 딱 마주치는 장면은 뭉클하고 감동적으로, "
    "서로 얼싸안는 마지막은 벅차고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 서로를 아끼는 마음이 얼마나 따뜻한지 알려 주는, 아주 뭉클한 형제 이야기를 가져왔어요. 밤마다 볏단이 신기하게 줄지 않는, 의좋은 형제 이야기랍니다. 대체 무슨 일이 있었던 걸까요? 자, 옛날 어느 시골 마을로 함께 가 볼까요?",
    "s02": "옛날 어느 마을에, 우애가 아주 깊은 형과 아우가 나란히 이웃해 살았어요. 형은 식구가 많은 넉넉한 살림이었고, 아우는 얼마 전 혼인해 이제 막 살림을 꾸린 새신랑이었지요. 두 형제는 어릴 적부터 무엇이든 사이좋게 나누며, 서로를 몹시 아끼고 위했답니다.",
    "s03": "어느 가을, 두 형제는 나란히 있는 논에서 벼를 거두었어요. 노랗게 익은 벼를 베어, 각자의 논에 볏단을 차곡차곡 똑같이 쌓아 두었지요. 커다란 낟가리 두 개가 나란히 서자, 형제는 서로를 바라보며 흐뭇하게 웃었답니다. 올해도 참 풍년이구나!",
    "s04": "그날 밤, 형은 잠자리에 누웠다가 문득 아우 생각이 났어요. 아우는 이제 막 살림을 시작했으니, 쓸 데가 얼마나 많을까. 내 볏단을 몰래 좀 나눠 주어야겠구나. 형은 살금살금 일어나, 자기 볏단을 한 아름 안고 아우의 낟가리로 가만가만 옮겨 놓았답니다.",
    "s05": "친구들, 잠깐만요! 말리가 살짝 귀띔해 줄게요. 사실은요, 바로 그 시각에 아우도 똑같은 생각을 하고 있었대요. 형님은 식구가 많으니 얼마나 힘드실까. 그럼 이 다정한 형제에게, 다음 날 아침 과연 무슨 신기한 일이 벌어졌을까요? 함께 지켜봐요!",
    "s06": "아우도 가만히 잠자리에서 일어났어요. 형님은 거두어 먹일 식구가 많으니, 내 볏단을 조금 보태 드려야지. 아우는 자기 볏단을 한 아름 안고, 형님의 낟가리로 조심조심 옮겨 놓았지요. 그렇게 두 형제는 캄캄한 밤길에서 서로 엇갈리며, 밤새 볏단을 옮기고 또 옮겼답니다.",
    "s07": "다음 날 아침, 형은 자기 낟가리를 보고 두 눈이 휘둥그레졌어요. 어라? 어젯밤에 그렇게나 옮겼는데, 내 볏단이 왜 하나도 줄지 않았지? 아우도 자기 낟가리를 보고 고개를 갸웃거렸어요. 이상하다, 분명 형님께 한 아름 가져다 드렸는데! 두 형제는 도무지 영문을 알 수가 없었답니다.",
    "s08": "그날 밤도, 두 형제는 또 볏단을 안고 몰래 길을 나섰어요. 휘영청 밝은 달빛 아래, 볏단을 잔뜩 진 두 사람이 좁은 논둑길 한가운데서 그만 딱 마주치고 말았지요. 형님! 아우야! 두 형제는 그제야 모든 걸 깨닫고, 볏단을 내려놓은 채 서로를 뭉클하게 바라보았답니다.",
    "s09": "형과 아우는 달빛 아래에서 두 손을 마주 잡고, 그대로 와락 얼싸안았어요. 서로를 위하는 그 따뜻한 마음이, 두 사람의 가슴을 가득 채웠지요. 그 뒤로도 두 형제는 서로 아끼고 나누며, 온 마을이 부러워하는 의좋은 형제로 오래오래 정답게 살았답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 형과 아우는 서로를 아끼는 마음에, 자기 것을 조금이라도 더 나눠 주고 싶어 했지요? 이렇게 아끼고 나누는 마음이 바로, 세상에서 가장 따뜻한 보물이랍니다. 그러니 우리도 가족과 친구를 많이많이 아껴 줘요! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
