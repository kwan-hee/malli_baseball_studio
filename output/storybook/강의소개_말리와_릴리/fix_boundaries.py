# 릴리 트랙 장면 경계 수동 보정 (2026-10-22)
# whisper large-v3 가 178~199s 를 환각(외국어 잡음 단어)으로 채워 S04-18~S05-02 가 비례 폴백됨.
# 원본 음성은 정상(whisper medium 재전사로 확인) → 실측 무음 위치로 경계 지정 후 해당 장면만 다시 자른다.
# 경계 = 장면 시작 시각(초, narration_lily.wav 기준). 나머지 장면은 make_narration 결과 그대로.
import wave
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE / "audio" / "narration_lily.wav"

# 장면: (시작, 끝)
CUTS = {
    # "여섯째,"가 S04-14 끝에 붙어 있었음 (whisper small 재전사로 발견) → 앞 무음 165.60~166.05 가운데로
    "S04-14": (157.83, 165.83),
    "S04-15": (165.83, 171.73),
    "S04-19": (185.27, 193.59),  # 끝: "범위 밖이에요." 뒤 무음 193.48~193.70 가운데
    "S04-20": (193.59, 199.47),  # 시작: "이 강의의 목표는" (medium 재전사로 확인)
}

with wave.open(str(SRC), "rb") as w:
    sr, sw, ch = w.getframerate(), w.getsampwidth(), w.getnchannels()
    pcm = w.readframes(w.getnframes())
bps = sr * sw * ch
for sid, (a, b) in CUTS.items():
    seg = pcm[int(a * bps) // 2 * 2: int(b * bps) // 2 * 2]
    with wave.open(str(BASE / "audio" / f"{sid}.wav"), "wb") as o:
        o.setnchannels(ch)
        o.setsampwidth(sw)
        o.setframerate(sr)
        o.writeframes(seg)
    print(f"{sid}: {a:.2f}s ~ {b:.2f}s ({b - a:.1f}s)")
