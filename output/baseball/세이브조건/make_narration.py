# 세이브조건 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "s01": "야구 중계를 보면요, 팀이 이기고 있는데 9회에 새 투수가 뚜벅뚜벅 걸어 나옵니다. 그리고 경기가 끝나면 이 투수한테 세이브가 붙죠. 그런데 똑같이 9회를 깔끔하게 막았는데, 어떤 날은 세이브가 안 붙어요. 심지어 이겼는데도요. 대체 세이브는 언제 붙는 걸까요? 오늘은 세이브 조건 이야기입니다.",
    "s02": "세이브는 한마디로, 이기고 있는 경기를 끝까지 안전하게 지켜낸 마무리 투수에게 주는 상입니다. 조건은 세 가지 중에 하나만 만족하면 돼요. 첫째, 3점 이내로 앞선 상황에 나와서 최소 1이닝을 막고 경기를 끝낸다. 둘째, 점수 차가 크더라도 동점을 만들 주자가 타석이나 베이스, 심지어 대기 타석에만 있어도 나와서 막는다. 셋째, 점수 차와 상관없이 3이닝 이상을 던져서 끝낸다. 이 셋 중 하나죠.",
    "s03": "여기에 두 가지가 더 붙어요. 그 투수가 경기의 마지막 아웃을 잡아서 승리를 지켜야 하고, 또 그 투수 본인이 승리 투수가 아니어야 합니다. 그럼 왜 이렇게 조건을 깐깐하게 만들었을까요? 세이브는 아슬아슬한 리드를 지켜낸 공로에 주는 상이거든요. 그래서 열 점 차로 크게 이기는데 1이닝 막는 건 세이브를 안 줍니다. 너무 여유로우니까요. 반대로 점수 차가 커도 동점 주자가 나가 있으면, 그건 위기라서 세이브를 줍니다.",
    "s04": "세이브라는 기록, 은근히 사연이 있습니다. 1960년 무렵, 시카고의 야구 기자였던 제롬 홀츠먼이 처음 고안했어요. 홈런이나 승리만 주목받고, 뒤에서 묵묵히 경기를 지킨 구원 투수는 아무도 안 알아주는 게 안타까웠던 거죠. 이 아이디어를 야구 주간지가 표창하기 시작했고, 마침내 1969년, 메이저리그의 공식 기록으로 채택됩니다. 기자 한 명의 안타까움이 공식 기록이 된 셈이에요.",
    "s05": "자, 그럼 여기서 궁금해지죠. 아까 마무리 투수가 9회를 완벽하게 막았는데도 세이브가 안 붙는 날이 있다고 했잖아요. 대체 어떤 경우일까요? 잠시 뒤에 그 오해를 시원하게 풀어 드릴게요. 그 전에, 우리 KBO의 세이브 하면 절대 빼놓을 수 없는 전설을 먼저 만나 보시죠.",
    "s06": "KBO 세이브의 끝판왕, 바로 오승환 선수입니다. 오승환은 KBO 통산 사백스물일곱 세이브로, 역대 1위에 우뚝 서 있어요. 2위와는 비교하기 미안할 만큼 압도적인 기록이죠. 한국과 미국, 일본 무대를 모두 합치면 통산 세이브가 무려 오백사십구 개에 이릅니다. 이름 그대로 끝판왕이었던 그는 2025년 시즌을 끝으로 그라운드를 떠났습니다.",
    "s07": "세이브를 이야기할 때 짝꿍처럼 따라오는 기록이 둘 있어요. 하나는 블론세이브. 다 이긴 경기를 지키러 나왔다가, 동점이나 역전을 허용해서 세이브를 그만 날려 버리는 걸 말합니다. 마무리 투수한테는 악몽 같은 기록이죠. 다른 하나는 홀드예요. 마무리 앞에서 잠깐 나와 리드를 지키고 다음 투수한테 넘겨준 중간 계투에게 주는 상인데요, 1986년에 이런 숨은 공로자들을 인정해 주자며 만들어졌습니다.",
    "s08": "여기서 고인물 상식 하나. 한 경기에서 세이브는 딱 한 명만 받을 수 있습니다. 여러 투수가 나눠서 리드를 지켜도, 마지막에 경기를 끝낸 단 한 명한테만 세이브가 붙어요. 그럼 앞에서 위기를 막아 준 투수들은요? 방금 말한 홀드로 보상을 받습니다. 그래서 요즘 야구는 세이브 하나 뒤에 홀드 여러 개가 숨어 있는 거죠. 이거 알면 중계가 다르게 보입니다.",
    "s09": "이제 아까 그 궁금증, 풀어 드릴게요. 9회에 나와서 경기를 끝내기만 하면 무조건 세이브다? 아닙니다. 만약 4점 차 이상으로 여유롭게 앞선 상황에 나와서 딱 1이닝만 막았다면, 세이브가 안 붙어요. 위기가 아니었으니까요. 또 하나, 만약 그 투수가 그날의 승리 투수가 되면, 세이브 대신 승리가 기록됩니다. 세이브와 승리는 한 사람이 같이 가질 수 없거든요.",
    "s10": "오늘 한 줄 요약. 세이브는 이기고 있는 경기를, 아슬아슬한 순간에 끝까지 지켜낸 마무리 투수에게 주는 상이다. 그래서 여유로운 리드에는 안 붙는 거죠. 다음 편은 홀드입니다. 이기지도 않았는데 왜 상을 줄까요? 오늘 내용이 쓸 만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
