# 말리와 바보온달 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 울보 공주 장면은 익살스럽게, "
    "공주가 온달에게 시집가겠다고 고집하는 장면은 야무지고 당차게, "
    "공주가 온달을 가르치고 온달이 열심히 배우는 장면은 따뜻하고 씩씩하게, "
    "온달이 사냥대회에서 늠름하게 활약하는 장면은 웅장하고 통쾌하게, "
    "온달이 훌륭한 장군이 되는 마지막은 벅차고 뿌듯하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 바보라고 놀림받던 한 청년이, 훌륭한 장군으로 멋지게 다시 태어난 이야기를 가져왔어요. 사람은 노력하면 누구나 달라질 수 있다는 걸 알려 주는, 바보 온달과 평강 공주 이야기랍니다. 자, 아주 먼 옛날 고구려로 함께 가 볼까요?",
    "s02": "옛날 고구려에, 걸핏하면 눈물을 뚝뚝 흘리는 울보 공주가 있었어요. 바로 평강 공주였지요. 공주가 하도 울어 대니, 임금님은 웃으며 이렇게 놀리곤 했답니다. 자꾸 그렇게 울면, 이 다음에 바보 온달에게 시집을 보내 버릴 테다! 온달은 마을에서 소문난, 마음씨만은 착한 바보였어요.",
    "s03": "세월이 흘러 공주가 시집갈 나이가 되자, 임금님은 이름난 귀족 집안에 공주를 보내려 했어요. 그런데 공주가 딱 잘라 말했지요. 아바마마께서는 늘 저를 온달에게 시집보낸다 하셨잖아요. 임금님의 말씀은 천금같이 무거운 법, 저는 온달에게 가겠어요! 공주는 그 길로 궁궐을 나섰답니다.",
    "s04": "공주가 찾아간 온달의 집은, 다 쓰러져 가는 아주 가난한 오두막이었어요. 온달은 눈이 잘 보이지 않는 늙은 어머니를 모시고, 끼니도 겨우겨우 잇고 있었지요. 공주는 조금도 실망하지 않았어요. 오히려 온달의 착한 마음씨를 알아보고, 이 사람을 훌륭하게 키워 봐야겠다고 마음먹었답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 사람들이 다 바보라고 하는 온달이, 정말로 훌륭한 사람이 될 수 있을까요? 하지만요, 공주에게는 아주 특별한 힘이 있었어요. 바로, 온달을 진심으로 믿어 주는 마음이었지요. 자, 온달이 어떻게 달라지는지 함께 지켜봐요!",
    "s06": "공주는 그날부터 온달에게 하나하나 가르치기 시작했어요. 글 읽는 법, 예의범절, 그리고 말 타고 활 쏘는 무예까지요. 온달은 처음엔 서툴렀지만, 자기를 믿어 주는 공주를 위해 이를 악물고 배웠어요. 넘어지고 또 넘어져도, 온달은 결코 포기하지 않았답니다.",
    "s07": "날마다 온달은 새벽부터 밤까지 말타기와 활쏘기를 갈고닦았어요. 처음엔 활시위 하나 제대로 당기지 못하던 온달이, 이제는 달리는 말 위에서도 과녁을 척척 맞히게 되었지요. 바보라고 놀림받던 온달은 온데간데없고, 늠름한 장수의 모습이 조금씩 갖추어져 갔답니다.",
    "s08": "드디어 나라에서 큰 사냥 대회가 열리는 날이 왔어요. 온달은 힘차게 말을 몰며, 누구보다 많은 짐승을 잡아 당당히 일 등을 차지했지요. 저 늠름한 젊은이가 대체 누구냐? 임금님이 깜짝 놀라 물었어요. 온달이라는 대답에, 온 나라 사람들이 눈이 휘둥그레지고 말았답니다.",
    "s09": "얼마 뒤 이웃 나라가 쳐들어오자, 온달은 앞장서서 용감하게 싸워 나라를 지켜 냈어요. 마침내 임금님은 온달을 자랑스러운 사위이자 훌륭한 장군으로 맞이했지요. 바보라고 놀림받던 온달이, 온 나라가 우러러보는 영웅이 된 거예요. 온달과 공주는 오래오래 행복하게 살았답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 바보라고 불리던 온달도, 자기를 믿어 주는 사람과 끊임없는 노력으로 훌륭한 장군이 되었지요? 그러니 지금 조금 서툴러도 괜찮아요. 포기하지 않고 노력하면, 누구나 멋진 사람이 될 수 있답니다! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
