# 구종 완전 정복 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
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
    "s01": "투수가 방금 던진 공, 그냥 빠른 공 아니었습니다. 옆으로 미끄러졌거든요. 이게 보이기 시작하면 야구가 두 배로 재밌어지는데요. 오늘은 구종 딱 다섯 개, 포심, 투심, 슬라이더, 커브, 체인지업만 기억하시면 됩니다.",
    "s02": "자, 구종이 뭐냐. 투수가 공 잡는 법이랑 회전을 바꿔서 만드는 공의 종류예요. 야구공에는 빨간 실밥이 108개 있는데, 이 실밥이 공기랑 부딪히면서 궤적이 달라집니다. 말하자면 구종은 투수의 메뉴판이에요. 뭘 주문하느냐에 따라 공이 다르게 날아갑니다.",
    "s03": "첫 번째, 포심 패스트볼. 실밥 네 줄을 가로질러 잡고 던지는, 투수가 낼 수 있는 가장 빠른 공이에요. 흔히 직구라고 부르죠. 강한 백스핀 때문에 덜 가라앉아서, 타자 눈에는 공이 떠오르는 것처럼 보입니다.",
    "s04": "두 번째, 투심 패스트볼. 이번엔 실밥 두 줄에 손가락을 나란히 올려요. 포심보다 살짝 느린 대신, 던지는 팔 쪽으로 휘면서 가라앉습니다. 타자가 정타를 못 만들고 땅볼을 치게 만드는 공이죠.",
    "s05": "세 번째랑 네 번째는 방향이 다른 형제예요. 슬라이더는 이름 그대로 옆으로 미끄러지는 공인데, 변화구인데도 빨라서 KBO 투수들이 주무기로 제일 많이 씁니다. 커브는 반대로 살짝 위로 솟는 듯하다가 아래로 뚝 떨어져요. 제일 느리지만 낙차는 제일 크죠.",
    "s06": "그리고 다섯 번째, 체인지업. 이게 진짜 재밌는 구종인데요. 던지는 폼은 패스트볼이랑 똑같은데 공만 시속 12에서 20킬로 느리게 갑니다. 타자는 빠른 공인 줄 알고 방망이가 먼저 나가버리죠. 타이밍을 통째로 훔쳐가는 공이에요.",
    "s07": "그럼 이 공들, 누가 만들었을까요? 커브는 1860년대 캔디 커밍스라는 선수가 처음 던졌다고 알려져 있어요. 1863년 여름에 바닷가에서 조개껍데기를 던지고 놀다가, 껍데기가 휘어 날아가는 걸 보고 야구공도 휘겠다 싶었다는 거죠. 슬라이더는 훨씬 나중인 1920년대에 나왔는데, 처음엔 다들 이걸 미끄러지는 패스트볼이라고 불렀답니다.",
    "s08": "우리 리그에도 구종 장인들이 있죠. 체인지업 하면 류현진. 원래 팜볼을 던지던 선수라 2006년에 체인지업을 금방 배웠고, 메이저리그에서도 포심 다음으로 많이 던지는 주무기가 됐습니다. 슬라이더 하면 김광현이죠. 시속 140 후반의 고속 슬라이더, 패스트볼이랑 딱 두 가지만 갖고 리그를 평정했으니까요. 커브의 윤성환, 포크볼의 조정훈까지, 자기 이름 옆에 구종 하나가 따라붙는 선수들입니다.",
    "s09": "여기서 많이들 하시는 오해 하나. 직구는 안 휘는 공이다? 아닙니다. 포심도 백스핀이 잔뜩 걸린 회전구예요. 덜 떨어질 뿐이지, 회전 없는 공이 아니에요. 하나 더. 슬라이더랑 커브를 둘 다 잘 던지는 투수는 의외로 드뭅니다. 손목을 쓰는 방향이 반대라, 쓰는 근육이 달라서 그래요. 그리고 이건 아는 분만 아는 얘긴데, 박명환의 그 유명한 슬라이더는 커브 그립을 잡고 속구처럼 세게 던지는 실험에서 나온 공이었습니다.",
    "s10": "오늘 한 줄 요약. 포심은 곧고, 투심은 휘며 가라앉고, 슬라이더는 옆으로, 커브는 아래로, 체인지업은 느리게. 이 다섯 개만 기억하시면 중계 해설이 들리기 시작합니다. 다음 편에서는 뚝 떨어지는 마구, 포크볼과 스플리터 얘기를 해볼까 하는데요. 오늘 내용이 쓸만했다면 구독이랑 좋아요 부탁드려요. 다음 편에서 만나요!",
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
    import whisper

    print("loading whisper large-v3 ...")
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(FULL_WAV), language="ko", word_timestamps=True)
    words = [w for seg in result["segments"] for w in seg["words"]]
    if not words:
        sys.exit("whisper returned no words")

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
