# 강의 소개 영상 — 타임라인: 장면 순서는 콘티 그대로, 길이는 실제 녹음에 맞춤 (2026-10-22 결정)
# 대사 장면 = 장면 wav 길이 + PAD / 대사 없는 장면(무대사·화자 전환·쉼·클립) = 콘티 원문 길이
import wave
from pathlib import Path

from storyboard import SCENES

BASE = Path(__file__).parent
PAD = 0.15


def wav_dur(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def build():
    out, t = [], 0.0
    for s in SCENES:
        wav = BASE / "audio" / f"{s['id']}.wav"
        if s["speaker"] and wav.exists():
            d = wav_dur(wav) + PAD
        else:
            d = float(s["dur"])  # 녹음 전(렌더 미리보기) 또는 대사 없는 장면
        out.append({**s, "start": t, "length": d, "wav": wav if s["speaker"] else None})
        t += d
    return out


TIMELINE = build()
TOTAL = sum(s["length"] for s in TIMELINE)

if __name__ == "__main__":
    for s in TIMELINE:
        print(f"{s['id']} {s['start']:7.2f} +{s['length']:5.2f} (콘티 {s['dur']}s) {s['speaker'] or '-'}")
    print(f"TOTAL {TOTAL:.1f}s ({int(TOTAL // 60)}:{TOTAL % 60:04.1f})")
