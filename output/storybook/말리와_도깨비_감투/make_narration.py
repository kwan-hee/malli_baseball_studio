# 말리와 도깨비 감투 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
# (2026-07-19 도깨비감투 편: 폴백 경고 print의 em-dash가 whisper 씬분할 후 크래시 유발)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 넘어져 우는 아기 도깨비는 가엾고 앙증맞게, "
    "감투를 선물하는 도깨비는 고맙고 장난스럽게, "
    "몸이 사라져 신기해하는 총각은 놀랍고 들뜨게, "
    "빨간 헝겊이 둥둥 떠서 마을이 놀라는 장면은 익살스럽고 소란스럽게, "
    "정체가 드러나 고마워하는 마을 사람들은 따뜻하고 뭉클하게, "
    "잔치를 여는 마지막은 흥겹고 행복하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 쓰면 몸이 감쪽같이 사라지는 신기한 도깨비감투 이야기를 가져왔어요. 착한 마음은 아무도 보지 않을 때 더욱 반짝인대요. 남몰래 착한 일을 한 마음씨 고운 총각과, 귀여운 도깨비 이야기랍니다. 자, 깊은 산속 마을로 함께 떠나 볼까요?",
    "s02": "옛날 옛날, 마음씨 착한 총각이 깊은 산으로 나무를 하러 갔어요. 그런데 바위 틈에서 조그만 아기 도깨비가 폭 넘어져 훌쩍훌쩍 울고 있지 뭐예요. 총각은 얼른 도깨비를 일으켜 세워 주고, 다친 무릎을 살살 닦아 주었지요. 고마워요, 총각님! 답례로 이 도깨비감투를 드릴게요. 머리에 쓰면 아무에게도 보이지 않는답니다!",
    "s03": "총각은 반신반의하며 조심조심 감투를 머리에 써 보았어요. 그러자 이게 웬일일까요? 총각의 몸이 스르르 옅어지더니, 감쪽같이 보이지 않았어요! 맑은 개울물에 비춰 보아도 그림자조차 없었지요. 우아, 정말 신기하다! 총각의 두 눈이 휘둥그레졌답니다.",
    "s04": "처음엔 그저 신기해서 이리저리 장난을 쳤어요. 하지만 착한 총각은 곧 아주 좋은 생각이 떠올랐지요. 그래, 아무도 모르게 마을 사람들을 도와주자! 총각은 감투를 쓰고, 무거운 짐을 진 할머니의 지게를 살며시 받쳐 주고, 부서진 울타리도 뚝딱뚝딱 고쳐 놓았답니다.",
    "s05": "친구들, 몸이 안 보이는 감투가 있으면 짓궂은 장난도 칠 수 있었을 텐데, 착한 총각은 오직 남을 돕는 데에만 썼어요. 정말 멋지죠? 그런데 마을 사람들은 누가 도와주는지 도무지 알 수가 없었어요. 아니, 대체 누가 이렇게 고마운 일을 해 주는 걸까? 다들 고개를 갸웃갸웃했답니다.",
    "s06": "그러던 어느 추운 겨울날이었어요. 총각이 따뜻한 화롯가에서 깜빡 졸고 있는데, 불똥이 톡 튀어 그만 감투에 조그만 구멍이 뽕 뚫리고 말았지 뭐예요. 아이고, 아까워라. 총각은 곱게 접어 둔 빨간 헝겊을 구멍 위에 대고, 한 땀 한 땀 정성껏 기워 붙였답니다.",
    "s07": "다음 날, 총각은 감투를 쓰고 또 마을을 도우러 나갔어요. 그런데 이를 어째요? 빨간 헝겊 조각만 허공에 둥둥 떠서 요리조리 움직이는 게 아니겠어요! 어머, 저기 좀 봐요, 빨간 게 저절로 날아다녀요! 마을 사람들이 눈을 동그랗게 뜨고 우르르 몰려들었답니다.",
    "s08": "사람들이 살금살금 다가가 빨간 조각을 살짝 잡아당기자, 스르륵 감투가 벗겨졌어요. 그러자 그 안에서 마음씨 착한 총각이 쑥스러운 얼굴로 쏙 나타났지 뭐예요. 아니, 그동안 우리를 몰래 도와준 고마운 사람이 바로 자네였구먼! 총각의 두 볼이 발그레 붉어졌답니다.",
    "s09": "마을 사람들은 착한 총각의 두 손을 꼭 잡고 진심으로 고마워했어요. 그리고 커다란 잔치를 열어, 다 함께 웃고 노래하며 덩실덩실 춤을 추었지요. 총각은 이제 감투가 없어도, 활짝 웃으며 언제나 이웃을 도왔답니다. 저 멀리 나무 뒤에서, 아기 도깨비도 흐뭇하게 방긋 웃고 있었어요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 착한 총각은 아무도 보지 않을 때에도 남을 도왔더니, 온 마을의 사랑을 듬뿍 받게 되었지요? 남몰래 하는 착한 일은요, 언젠가 꼭 예쁜 마음이 되어 우리에게 돌아온답니다. 우리도 오늘 하나씩, 작고 따뜻한 착한 일을 해 볼까요? 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
