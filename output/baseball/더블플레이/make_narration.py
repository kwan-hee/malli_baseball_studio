# 더블플레이 — 나레이션: Gemini TTS(Puck) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
# (씬별 호출 금지 규칙 — 호출마다 톤이 달라지는 문제 방지, 07_AUDIO.md)
# 자막: whisper 단어 타임스탬프를 word_timestamps.json 으로 저장 — compose 가 실측 자막 생성
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

# cp949 콘솔에서 비-cp949 문자 print 크래시 방지
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
    "s01": "6-4-3! 야구 중계 보면 해설자가 갑자기 이런 암호 같은 숫자를 읊죠. 뭔 소린지 하나도 모르겠는 분들, 손 들어 보세요. 오늘 이거 한 번만 보면 다음부턴 '아 저거!' 하실 겁니다. 오늘의 주제, 더블플레이입니다.",
    "s02": "더블플레이. 우리말로 병살. 한 타석에서 수비가 연속 동작으로 아웃을 두 개 잡는 플레이예요. 공격팀 입장에선 찬스가 한 방에 날아가는, 정말 뼈아픈 순간이죠.",
    "s03": "자, 먼저 이걸 알아야 해요. 야구 수비에는 포지션마다 고유 번호가 있습니다. 투수가 1번, 포수 2번, 1루수 3번, 2루수 4번, 3루수 5번, 유격수 6번. 그리고 외야는 좌익수 7, 중견수 8, 우익수 9번이에요.",
    "s04": "이제 6-4-3 병살을 풀어 볼게요. 1루에 주자가 있는 상황. 타자가 땅볼을 쳤어요. 유격수, 6번이 잡았습니다. 바로 2루수, 4번에게 던져요. 2루 밟아서 선행주자 아웃! 그리고 다시 1루수, 3번한테 송구! 타자주자까지 아웃! 이게 6-4-3, 교과서적인 더블플레이입니다.",
    "s05": "타구 방향에 따라 조합이 바뀌어요. 2루수 쪽으로 가면 4-6-3. 3루수 쪽이면 5-4-3. 투수 앞 땅볼은 1-6-3이나 1-4-3. 이렇게 번호만 따라가면 공이 어떻게 움직였는지 바로 보이는 거예요.",
    "s06": "더블플레이에도 종류가 있어요. 가장 흔한 건 포스 더블플레이. 땅볼 때 선행주자를 먼저 포스아웃시키고 이어서 타자주자도 포스아웃. 반대로 리버스 포스 더블플레이는 타자주자를 먼저 1루에서 잡고, 포스가 풀린 선행주자를 태그로 잡는 거예요.",
    "s07": "라인드라이브 더블플레이도 있습니다. 타자가 직선타구를 쏘는데, 야수 정면으로 딱! 이미 스타트를 끊은 주자가 돌아오지 못하면 바로 병살. 어쩔 땐 이게 삼중살, 트리플 플레이로 연결되기도 해요. 2007년 KIA 손지환 선수가 혼자서 삼중살을 완성한 적도 있습니다.",
    "s08": "KBO 역사에서 가장 뼈아픈 병살이요? 2011년 플레이오프 1차전. 9회 말, 6대 6 동점, 1사 만루. 롯데 손아섭이 타석에 들어섰어요. 초구를 쳤는데, 4-6-3 병살. 끝내기 찬스가 한 순간에 증발해 버렸죠. 그날 이후 손아섭에겐 손페베네라는 별명이 붙었습니다.",
    "s09": "더블플레이가 무서운 이유, 정리하면 이겁니다. 아웃 카운트가 단번에 두 개 늘어요. 주자까지 사라져요. 찬스 자체가 소멸합니다. 투수한테는 이보다 좋은 선물이 없고, 타자한테는 이보다 뼈아픈 게 없죠.",
    "s10": "정리해 드릴게요. 더블플레이는 한 플레이에 아웃 둘. 숫자는 포지션 번호 순서. 6-4-3은 유격수에서 2루수, 1루수로 이어지는 가장 대표적인 병살입니다. 다음 중계 때 병살 나오면, 번호 따라가 보세요. 공의 여정이 보일 겁니다. 다음 편에선 병살과 찰떡인 포스아웃을 파헤쳐 볼게요. 도움 됐으면 구독이랑 좋아요 부탁드리고요, 다음 편에서 또 만납시다!",
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
            for part in (resp.candidates[0].content.parts if resp.candidates else []):
                if part.inline_data:
                    data = part.inline_data.data
                    pcm = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                    write_wav(pcm, FULL_WAV)
                    dur = len(pcm) / (SR * BITS // 8 * CH)
                    print(f"full narration saved: {FULL_WAV.stat().st_size:,} bytes ({dur:.1f}s)")
                    if dur < 60:
                        print(f"WARNING: narration too short ({dur:.1f}s), retrying...")
                        FULL_WAV.unlink()
                        break
                    return
            print(f"no audio in response (attempt {attempt+1})")
        except Exception as e:
            err = str(e)
            print(f"TTS attempt {attempt+1} failed - {type(e).__name__}: {err[:150]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit("all gemini keys exhausted")
        time.sleep(15 * (attempt + 1))
    raise RuntimeError("TTS failed after 3 attempts")


def split_by_whisper():
    import json
    import whisper

    ts_path = OUT / "word_timestamps.json"
    if ts_path.exists():
        print("whisper timestamps: cached")
        return

    print("Loading whisper large-v3...")
    model = whisper.load_model("large-v3")
    result = model.transcribe(
        str(FULL_WAV), language="ko", word_timestamps=True, condition_on_previous_text=True
    )

    words = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            words.append({"word": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3)})

    ts_path.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"word_timestamps.json saved ({len(words)} words)")

    # 씬별 오디오 분할
    full_text = "\n\n".join(SCENES.values())
    scene_boundaries = []
    pos = 0
    for sid, text in SCENES.items():
        start = pos
        end = pos + len(text)
        scene_boundaries.append((sid, start, end))
        pos = end + 2  # \n\n

    normed_full = norm(full_text)
    normed_words_cum = []
    cum = 0
    for w in words:
        normed_words_cum.append(cum)
        cum += len(norm(w["word"]))

    for sid, char_start, char_end in scene_boundaries:
        ns = len(norm(full_text[:char_start]))
        ne = len(norm(full_text[:char_end]))
        ws = next((i for i, c in enumerate(normed_words_cum) if c >= ns), 0)
        we = next((i for i, c in enumerate(normed_words_cum) if c >= ne), len(words)) - 1
        t_start = max(0, words[ws]["start"] - BOUNDARY_MARGIN)
        t_end = words[min(we, len(words)-1)]["end"] + BOUNDARY_MARGIN
        print(f"  {sid}: {t_start:.2f}s ~ {t_end:.2f}s")


if __name__ == "__main__":
    generate_full()
    split_by_whisper()
    print("\n=== Done ===")
