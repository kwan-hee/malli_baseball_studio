# 말리와 벌거벗은 임금님 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 옷만 좋아하는 임금님은 우쭐하고 뽐내듯, "
    "꾀 많은 재봉사는 능청스럽고 천연덕스럽게, "
    "다들 눈치 보며 안 보이는 옷을 거짓 칭찬하는 장면은 어색하고 조마조마하게, "
    "아이가 진실을 큰 소리로 외치는 장면은 맑고 씩씩하게, "
    "마지막 교훈을 전하는 부분은 따뜻하고 밝게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은 아주 재미있는 이야기를 가지고 왔어요. 새 옷을 너무너무 좋아하는 임금님 이야기랍니다. 솔직하게 말하는 게 왜 중요한지, 함께 알아볼까요?",
    "s02": "옛날 옛날, 어느 나라에 옷을 세상에서 제일 좋아하는 임금님이 살았어요. 이 임금님은 하루에도 몇 번씩 새 옷으로 갈아입고, 거울 앞에서 뽐내는 걸 가장 좋아했지요. 나라를 다스리는 일보다, 멋진 옷 입는 일에 더 관심이 많았답니다.",
    "s03": "그러던 어느 날, 꾀 많은 재봉사 두 명이 임금님을 찾아왔어요. 임금님, 저희가 세상에서 가장 신기한 옷을 지어 드리겠습니다. 이 옷은요, 어리석은 사람의 눈에는 절대 보이지 않는 마법의 옷이랍니다! 임금님은 귀가 솔깃했어요. 오, 그것 참 신기하구나. 당장 지어 보아라!",
    "s04": "재봉사들은 텅 빈 베틀 앞에 앉아, 옷을 짜는 시늉만 했어요. 손은 부지런히 움직였지만, 사실 아무것도 없었죠. 임금님이 신하를 보내 살펴보게 했어요. 그런데 신하의 눈에도 아무것도 보이지 않는 거예요! 하지만 신하는 바보로 보일까 봐, 오, 정말 아름다운 옷이군요! 하고 거짓말을 했답니다.",
    "s05": "친구들, 어때요? 정말 이상하죠? 베틀에는 아무것도 없는데, 다들 옷이 보인다고 말하네요. 바보로 보이는 게 그렇게 무서웠던 걸까요? 우리 함께 계속 지켜봐요!",
    "s06": "드디어 임금님이 직접 옷을 보러 왔어요. 그런데, 이를 어째요? 임금님 눈에도 아무것도 보이지 않는 거예요! 임금님은 속으로 깜짝 놀랐지만, 내가 어리석다는 걸 들킬 순 없지! 하고는, 오, 정말 훌륭한 옷이로구나! 하고 크게 칭찬했어요. 그리고 재봉사들에게 상까지 듬뿍 내렸답니다.",
    "s07": "며칠 뒤, 재봉사들은 임금님에게 다 지어진 옷을 입혀 주는 시늉을 했어요. 여기 소매를 넣으시고, 이렇게 입으시면 됩니다! 임금님은 속옷 차림으로 거울 앞에 섰지만, 마치 세상에서 가장 멋진 옷을 입은 것처럼 우쭐거렸지요. 신하들도 모두 입을 모아, 정말 잘 어울리십니다! 하고 칭찬했어요.",
    "s08": "임금님은 그 멋진 새 옷을 온 백성에게 자랑하고 싶었어요. 그래서 거리로 행진을 나섰지요. 길에 모인 백성들은 임금님을 보고 다들 깜짝 놀랐어요. 하지만 아무도 사실대로 말하지 못했어요. 나만 옷이 안 보이면 바보인 거잖아? 그래서 모두 우와, 임금님 옷이 정말 멋져요! 하고 박수를 쳤답니다.",
    "s09": "바로 그때였어요. 사람들 틈에 있던 한 어린아이가, 손가락으로 임금님을 가리키며 큰 소리로 외쳤어요. 어? 임금님이 아무것도 안 입었어요! 벌거숭이예요! 순간 거리가 조용해지더니, 사람들이 하나둘 웃음을 터뜨렸어요. 그제야 다들 솔직하게 말하기 시작했죠. 정말이네, 임금님이 속으셨구나! 임금님은 얼굴이 새빨개졌답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 어른들도, 신하들도 못 한 말을, 솔직한 아이 한 명이 용감하게 해냈죠? 남들이 다 그렇다고 해도, 아닌 건 아니라고 솔직하게 말하는 용기. 그게 정말 멋진 거예요. 오늘 이야기가 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕, 멍멍!",
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
