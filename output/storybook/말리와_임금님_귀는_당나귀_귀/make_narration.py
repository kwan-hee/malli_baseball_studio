# 말리와 임금님 귀는 당나귀 귀 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막 A안 (2026-07-15): whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
# 씬 시작 문장은 전부 고유 + 의성어 금지 (2026-07-16 까치편 whisper 환각 교훈)
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
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 임금님의 대사는 근엄하지만 속으로 부끄러운 듯, "
    "마음씨 착한 두건 장인의 대사는 정답고 조심스럽게, "
    "비밀을 못 참아 답답해하는 장면은 안타깝고 간질간질하게, "
    "대나무숲이 비밀을 소리내는 장면은 신비롭고 놀랍게, "
    "임금님이 마음을 고쳐먹고 활짝 웃는 마지막은 따뜻하고 후련하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 아주 재미있는 비밀 이야기를 가져왔어요. 어느 나라 임금님에게는 남몰래 숨긴 깜짝 놀랄 비밀이 하나 있었대요. 그게 대체 무엇이었을까요? 그리고 그 비밀은 과연 어떻게 되었을까요? 자, 옛날 옛적 궁궐로 함께 떠나 볼까요?",
    "s02": "옛날 어느 나라에, 마음씨 착한 임금님이 살았어요. 그런데 이 임금님에게는 아무도 모르는 비밀이 하나 있었지요. 글쎄, 임금님의 두 귀가 당나귀 귀처럼 쫑긋하고 길쭉했던 거예요! 임금님은 그게 어찌나 부끄러운지, 늘 커다란 두건을 폭 눌러써서 귀를 꽁꽁 숨기고 다녔답니다.",
    "s03": "임금님의 비밀을 아는 사람은 딱 한 명, 두건을 만드는 착한 장인뿐이었어요. 임금님은 그에게 신신당부를 했지요. 이 비밀을 누구에게도 말해선 안 되네, 알겠는가? 장인은 고개를 끄덕이며 굳게 약속했어요. 여부가 있겠습니까, 임금님. 제 입은 자물쇠처럼 꼭 잠그겠습니다.",
    "s04": "하지만 장인은 나날이 괴로웠어요. 세상에서 가장 신기한 비밀을 알면서도, 아무에게도 말할 수가 없었으니까요. 말하고 싶은 마음을 꾹꾹 눌러 참다 보니, 그만 가슴이 답답해서 시름시름 앓아눕고 말았지 뭐예요. 아이고, 이 이야기를 딱 한 번만 시원하게 말할 수 있다면!",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 장인은 왜 이렇게 힘들어했을까요? 맞아요, 하고 싶은 말을 마음속에만 꾹 담아 두면 무척 답답하기 때문이에요. 그래서 장인은 아무도 없는 곳을 찾아가기로 했답니다. 과연 어디로 갔을까요?",
    "s06": "답답함을 견디다 못한 장인은, 사람이 아무도 없는 깊은 대나무숲으로 살금살금 들어갔어요. 그러고는 아무도 듣지 않는 걸 몇 번이나 확인한 뒤, 마침내 가슴속 이야기를 있는 힘껏 크게 외쳤답니다. 임금님 귀는 당나귀 귀! 임금님 귀는 당나귀 귀! 아, 이제야 좀 살 것 같았어요.",
    "s07": "그런데 참으로 신기한 일이 벌어졌어요. 그날부터 바람이 대나무숲을 스치고 지나갈 때마다, 이런 노랫소리가 들려오는 거예요. 임금님 귀는 당나귀 귀! 대나무들이 장인의 이야기를 고스란히 기억했다가, 온 세상에 노래하듯 들려주기 시작한 거랍니다.",
    "s08": "그 소리를 전해 들은 임금님은 처음엔 얼굴이 새빨개졌어요. 아니, 그토록 꽁꽁 숨겨 온 내 비밀이 온 나라에 다 퍼지다니! 임금님은 어찌나 속상하던지, 저 대나무숲을 몽땅 베어 버릴까 하고 생각하기까지 했지요. 하지만 대나무숲은 바람이 불 때마다 여전히 정답고 구성지게 노래했어요. 임금님 귀는 당나귀 귀!",
    "s09": "한참을 곰곰이 생각하던 임금님은, 문득 빙그레 웃음이 났어요. 그래, 당나귀 귀면 또 어떠냐. 남과 조금 다른 이 모습도 분명 나인걸! 임금님은 큰 용기를 내어 커다란 두건을 훌러덩 벗었답니다. 쫑긋한 귀가 드러나자, 백성들은 흉보기는커녕 오히려 정답고 다정하게 웃어 주었어요. 임금님도 그제야 마음이 날아갈 듯 참 후련해졌지요.",
    "s10": "친구들, 오늘 이야기 어땠어요? 숨기고 싶은 비밀도, 있는 그대로 받아들이면 조금도 부끄럽지 않대요. 나의 모습을 사랑하는 임금님이 참 멋지죠? 말리도 내 모습 그대로를 좋아하는 씩씩한 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
            write_wav(pcm, FULL_WAV)
            dur = len(pcm) / (SR * BITS // 8 * CH)
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

    offsets, pos = {}, 0
    for sid, text in SCENES.items():
        offsets[sid] = pos
        pos += len(norm(text))
    total_norm = pos

    sids = list(SCENES.keys())
    boundaries = {sids[0]: 0.0}
    next_i, acc = 1, 0
    for w in words:
        if next_i >= len(sids):
            break
        acc += len(norm(w["word"]))
        if acc >= offsets[sids[next_i]]:
            boundaries[sids[next_i]] = max(0.0, w["end"] - BOUNDARY_MARGIN)
            next_i += 1
    if next_i < len(sids):
        sys.exit(f"boundary not found for {sids[next_i]} (transcribed {acc}/{total_norm} chars)")

    with wave.open(str(FULL_WAV), "rb") as wf:
        pcm = wf.readframes(wf.getnframes())
    total_dur = len(pcm) / (SR * BITS // 8)
    bps = SR * BITS // 8

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
