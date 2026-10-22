# 말리와 호랑이와 나그네 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 함정에 빠진 호랑이가 애원하는 장면은 가엾고 절박하게, "
    "호랑이가 돌변해 나그네를 잡아먹으려는 장면은 무섭고 능청스럽게, "
    "나그네가 억울해하는 장면은 다급하고 안타깝게, "
    "소나무와 소가 판결하는 장면은 무뚝뚝하고 진중하게, "
    "토끼가 꾀를 내는 장면은 천연덕스럽고 영리하게, "
    "호랑이가 도로 함정에 갇히는 마지막은 통쾌하고 후련하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 은혜를 베풀었다가 큰일 날 뻔한 어느 착한 나그네 이야기를 가져왔어요. 고마움을 아는 마음이 왜 소중한지, 또 지혜가 우리를 어떻게 구해 주는지 알려 주는, 호랑이와 나그네 이야기랍니다. 자, 깊은 산속으로 함께 떠나 볼까요?",
    "s02": "옛날 옛날, 한 나그네가 깊은 산길을 넘어가고 있었어요. 그런데 어디선가 애처로운 울음소리가 들려왔지요. 소리를 따라가 보니, 커다란 호랑이 한 마리가 깊은 함정에 빠져 벌벌 떨고 있었어요. 나그네님, 제발 저 좀 꺼내 주세요. 이 은혜는 절대로 잊지 않겠습니다!",
    "s03": "마음 착한 나그네는 한참을 망설였어요. 호랑이가 무섭기도 했지만, 애원하는 모습이 너무나 딱했지요. 결국 나그네는 길고 튼튼한 나무를 함정 속에 넣어 주었답니다. 호랑이는 그 나무를 밟고 무사히 밖으로 올라올 수 있었어요.",
    "s04": "그런데 이게 웬일일까요? 밖으로 나온 호랑이가 갑자기 눈빛을 싹 바꾸었어요. 어흥! 나는 며칠을 굶어서 너무너무 배가 고프구나. 미안하지만, 너를 잡아먹어야겠다! 나그네는 너무 놀라 그 자리에 얼어붙고 말았답니다.",
    "s05": "친구들, 이럴 수가 있나요? 은혜를 베푼 사람을 잡아먹겠다니, 말리는 너무 화가 나요! 그래도 나그네는 정신을 바짝 차렸어요. 호랑이님, 이건 너무 억울해요. 그럼 지나가는 이들에게 물어봐서, 제가 정말 잡아먹혀야 하는지 판결을 받아 봐요. 과연 누가 나그네의 편을 들어줄까요?",
    "s06": "맨 먼저 길가에 서 있는 늙은 소나무에게 물었어요. 소나무는 잎을 스르르 흔들며 이렇게 말했지요. 사람들은 우리가 시원한 그늘을 주어도 고마운 줄 모르고, 도끼로 마구 베어 가기만 한단다. 그러니 사람은 잡아먹혀도 싸다! 호랑이는 신이 나서 껄껄 웃었어요.",
    "s07": "이번에는 밭을 갈고 있던 누렁소에게 물었어요. 누렁소도 천천히 고개를 저으며 말했지요. 사람들은 평생 나를 부려 먹고는, 내가 늙고 힘없어지면 내다 팔아 버린단다. 그러니 나그네가 잡아먹혀도 할 말이 없지! 나그네의 얼굴은 그만 새하얗게 질리고 말았어요.",
    "s08": "마지막으로 저만치서 다가오던 토끼에게 물었어요. 그런데 영리한 토끼는 짐짓 모르는 척 고개를 갸웃했지요. 아이참, 무슨 말인지 도무지 모르겠어요. 대체 처음에 어떻게 된 일인지, 저에게 그대로 한번 보여 주시겠어요?",
    "s09": "답답해진 호랑이는 스스로 다시 함정 속으로 뛰어들었어요. 자, 내가 원래 이렇게 갇혀 있었단 말이다! 바로 그때, 토끼가 나그네에게 눈을 찡긋했지요. 호랑이님은 거기 그대로 계세요! 나그네님, 어서 갈 길을 가세요! 어리석은 호랑이는 다시 함정에 갇히고 말았답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 은혜를 원수로 갚으려던 호랑이는, 결국 제 꾀에 넘어가 벌을 받았지요? 우리는 누군가에게 도움을 받으면 꼭 고마워할 줄 알아야 해요. 또 아무리 무서운 일이 닥쳐도, 토끼처럼 지혜를 내면 슬기롭게 헤쳐 나갈 수 있답니다! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
