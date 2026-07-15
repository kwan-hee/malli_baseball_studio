# 말리와 토끼와 자라 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
VOICE = "Kore"
SR, BITS, CH = 24000, 16, 1
BOUNDARY_MARGIN = 0.15  # 씬 경계 컷 여유 (초)

# 성우 연기 지시 (TTS에만 전달, 자막에는 미포함)
STYLE = (
    "당신은 어린이 동화 구연 전문 성우입니다. 5~7세 아이에게 들려주듯 "
    "천천히, 또박또박, 밝고 사랑스럽게, 감정을 풍부하게 연기하며 읽으세요. "
    "서두르지 말고 문장 사이에 여유를 두세요. "
    "말리(강아지)의 대사는 신나고 귀엽게, 병드신 용왕님의 대사는 근엄하지만 힘없고 약하게, "
    "충직한 자라의 대사는 정중하고 씩씩하게, 꾀 많은 토끼의 대사는 재치있고 능청스럽게, "
    "깊은 바닷속 용궁 장면은 웅장하고 신비롭게, 토끼가 위기에서 꾀를 내는 장면은 "
    "조마조마하다가 통쾌하게, 마지막 훈훈한 장면은 다정하고 따뜻하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 깊고 푸른 바닷속 용궁으로 떠나는 신나는 이야기를 가져왔어요. 병드신 용왕님과, 꾀 많은 토끼, 그리고 충직한 자라가 나온답니다. 토끼는 과연 무사히 집으로 돌아올 수 있을까요? 자, 바닷속으로 함께 풍덩 들어가 볼까요?",
    "s02": "깊고 깊은 바닷속에는 산호와 진주로 지은, 눈부시게 아름다운 용궁이 있었어요. 그곳을 다스리는 용왕님이 그만 큰 병이 들고 말았지요. 좋다는 약을 다 써 봐도 도무지 낫질 않으니, 용왕님은 나날이 기운을 잃었고 신하들의 걱정은 이만저만이 아니었어요. 그때 나이 많은 의원이 조심스레 말했답니다. 저 멀리 육지에 사는 토끼가 있어야만 용왕님이 나으실 수 있다고요.",
    "s03": "충직한 신하 자라가 용왕님 앞으로 썩 나섰어요. 용왕님, 제가 육지로 올라가 토끼를 꼭 데려오겠나이다. 자라는 등껍질에 봇짐을 지고, 먼 길을 헤엄쳐 육지로 향했지요. 파도를 넘고 또 넘어, 드디어 푸른 산기슭에 도착했답니다. 자, 이제 꾀 많은 토끼를 어떻게 찾을까요?",
    "s04": "산속에서 자라는 드디어 토끼를 만났어요. 토끼님, 바닷속 용궁은 정말이지 멋진 곳이랍니다. 맛있는 것도 가득하고, 높은 벼슬까지 준다지요! 토끼는 그 말에 그만 마음이 솔깃해졌어요. 벼슬이라니, 정말 근사한걸! 토끼는 자라 등에 냉큼 올라타, 넘실넘실 바닷속으로 함께 떠났답니다.",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 토끼는 왜 낯선 바다까지 자라를 따라갔을까요? 맞아요, 높은 벼슬과 좋은 것에 그만 마음이 혹했기 때문이에요. 하지만 너무 달콤한 이야기에는 늘 조심해야 한답니다. 자, 용궁에서는 어떤 일이 토끼를 기다리고 있을까요?",
    "s06": "화려한 용궁에 도착하고 나서야, 토끼는 그제야 깜짝 놀랄 이야기를 들었어요. 글쎄, 토끼가 있어야만 용왕님 병이 낫는다는 거예요! 토끼는 가슴이 철렁 내려앉았지만, 여기서 겁을 먹으면 큰일이었지요. 토끼는 두 눈을 반짝이며 아주 침착하게 꾀를 냈답니다. 아이고 용왕님, 저는요, 그 소중한 것을 볕에 잘 말리려고 산속 바위에 걸어 두고 그냥 왔지 뭐예요.",
    "s07": "용왕님은 토끼의 말을 그만 곧이곧대로 믿고 말았어요. 저런, 그렇게 중한 것을 두고 왔다니 큰일이로구나. 어서 육지로 돌아가 가져오도록 하여라. 그리하여 토끼는 다시 자라 등에 올라, 무사히 육지로 돌아가게 되었답니다. 토끼는 속으로 살금살금 웃었지요.",
    "s08": "육지에 발이 닿자, 토끼는 그제야 활짝 웃으며 큰 소리로 외쳤어요. 자라야, 정말 미안하지만, 세상에 소중한 것을 몸에서 넣었다 뺐다 하는 동물이 어디 있겠니? 나는 무서운 위기에서 재빨리 꾀를 내어 살아난 거란다. 자라는 그만 멍하니 토끼를 바라보았지요.",
    "s09": "빈손이 된 자라는 그만 풀이 죽어 긴 한숨을 쉬었어요. 그 모습을 본 토끼는 마음이 짠해져서, 이번에는 아주 다정하게 말했답니다. 자라야, 그래도 용왕님을 그토록 아끼는 네 정성만큼은 참으로 갸륵하구나. 자, 그 마음이 고마우니 이 좋은 약초를 대신 가져다드리렴. 토끼가 알려 준 신기한 약초 덕분에, 용왕님도 얼마 지나지 않아 툭툭 자리를 털고 일어났답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 아무리 무섭고 급한 순간에도, 침착하게 지혜를 내면 위기를 훌쩍 벗어날 수 있대요. 그리고 지나친 욕심은 조심, 또 조심! 말리도 슬기롭고 착한 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
