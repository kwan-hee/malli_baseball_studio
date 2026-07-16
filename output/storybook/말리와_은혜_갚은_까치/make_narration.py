# 말리와 은혜 갚은 까치 — 나레이션: Gemini TTS(Kore) 전체 대본 단일 호출 + Whisper large-v3 씬 분할
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
    "말리(강아지)의 대사는 신나고 귀엽게, 착한 나그네의 대사는 다정하고 용감하게, "
    "아기 까치들은 짹짹 귀엽게, 엄마 까치는 고맙고 정답게, "
    "심술꾸러기 큰 뱀의 대사는 짓궂지만 하나도 무섭지 않게 우스꽝스럽게, "
    "밤에 길이 막히는 장면은 조마조마하게, 까치들이 종을 울리는 장면은 웅장하고 통쾌하게, "
    "마지막 서로 고마워하는 장면은 따뜻하고 뭉클하게 "
    "연기하세요. 다음을 읽으세요:\n\n"
)

# 대본 단일 출처 — compose.py 가 import 해서 자막도 여기서 생성
SCENES = {
    "s01": "안녕, 친구들! 나는 말리예요, 멍멍! 오늘은요, 받은 은혜를 잊지 않고 꼭 갚은, 착하고 고마운 까치 이야기를 가져왔어요. 위험에 빠진 아기 까치들과, 그들을 도와준 마음씨 착한 나그네가 나온답니다. 과연 어떤 일이 벌어질까요? 자, 푸른 산속으로 함께 떠나 볼까요?",
    "s02": "옛날 어느 산골에, 마음씨 착한 젊은 나그네가 먼 길을 걷고 있었어요. 봇짐을 메고 지팡이를 짚으며, 굽이굽이 산길을 넘어갔지요. 새들이 지저귀고 바람이 솔솔 부는 평화로운 날이었어요. 그런데 그때, 어디선가 다급하게 우는 소리가 들려왔답니다. 짹짹, 짹짹, 도와주세요!",
    "s03": "나무 위에서 아기 까치들이 새파랗게 겁에 질려 떨고 있었어요. 커다란 심술꾸러기 뱀이 둥지로 스멀스멀 다가가고 있었거든요. 나그네는 깜짝 놀라 얼른 지팡이를 높이 치켜들고 큰 소리로 외쳤어요. 이놈, 저리 썩 물러가지 못할까! 그러자 뱀은 움찔 놀라, 슬금슬금 숲속으로 도망쳐 버렸답니다.",
    "s04": "엄마 까치가 한달음에 날아와, 나그네에게 몇 번이고 고개를 숙이며 고마워했어요. 둥지 속 아기 까치들도 반가워 짹짹 노래했지요. 정말 고맙습니다, 이 은혜는 절대로 잊지 않을게요. 나그네는 빙그레 웃으며 대답했답니다. 아기 까치들이 무사하니 나도 참 기쁘구나. 부디 몸 건강히 잘 지내렴, 얘들아!",
    "s05": "친구들, 잠깐만요! 말리가 궁금한 게 있어요. 나그네는 왜 위험을 무릅쓰고 아기 까치들을 도와주었을까요? 맞아요, 어려움에 처한 친구를 그냥 지나칠 수 없었기 때문이에요! 그런데 이 착한 나그네에게, 조금 뒤에 뜻밖의 위기가 찾아온답니다. 어떤 일일까요?",
    "s06": "해가 저물어 산속이 캄캄해지자, 나그네는 낡은 종이 걸린 오래된 종각에서 하룻밤 쉬어 가기로 했어요. 그런데 이게 웬일이에요? 낮에 도망쳤던 심술꾸러기 뱀이 스르르 나타나 길을 턱 가로막은 거예요! 뱀은 심통이 잔뜩 나서 말했어요. 저 종이 저절로 세 번 울리기 전엔, 절대로 못 지나간다!",
    "s07": "바로 그때, 놀라운 일이 벌어졌어요. 어디선가 까치들이 떼를 지어 포드득 날아온 거예요! 낮에 도움을 받은 그 까치 가족이었지요. 까치들은 온 힘을 모아 날개로, 부리로, 커다란 종을 힘껏 밀고 두드렸어요. 그러자 마침내, 뎅! 뎅! 뎅! 종이 우렁차게 세 번 울려 퍼졌답니다.",
    "s08": "뎅, 뎅, 뎅! 우렁찬 종소리가 온 산에 쩌렁쩌렁 울리자, 심술꾸러기 뱀은 그만 깜짝 놀라고 말았어요. 아이고, 이게 무슨 소리야! 뱀은 눈이 휘둥그레져서, 부랴부랴 저 멀리 숲속으로 스르르 물러가 버렸지요. 나그네는 그제야 휴, 하고 안도의 한숨을 내쉬었답니다.",
    "s09": "아침 해가 밝자, 나그네는 종각을 빙 둘러싼 까치들을 보고 모든 것을 알아차렸어요. 너희가 밤새 나를 지켜 준 거로구나. 정말 고맙다! 까치들은 짹짹 즐겁게 노래하며 대답하는 것 같았지요. 은혜를 갚은 것뿐인걸요! 나그네와 까치들은 서로를 바라보며 환하게 웃었답니다.",
    "s10": "친구들, 오늘 이야기 어땠어요? 내가 베푼 작은 친절은 언젠가 반드시 고마움으로 되돌아온대요. 그리고 받은 은혜는 잊지 않고 꼭 갚는 마음이 참 아름답지요. 말리도 고마움을 아는 착한 강아지가 될래요, 멍멍! 재미있었다면 구독이랑 좋아요, 꾹 눌러 주세요! 다음에 또 만나요. 안녕!",
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
