# 강의 소개 영상 — 완성작 미리보기 클립 (S03-08 한국어 / S03-10 영어, 각 20초)
# 원본: 하린이와_초코의_이상한_나라 완성본. 구간 = 2장면(굴 속으로 떨어짐, Veo 클립) 시작부터 20초 (2026-10-22)
# 산출: clips/harin_ko.mp4·harin_en.mp4 (1280x720, 25fps, 소리 포함 — 콘티: 🎵 꺼짐 / 클립 소리만)
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE.parent / "하린이와_초코의_이상한_나라"
CUTS = {
    "harin_ko": (SRC / "✅하린이와_초코의_이상한_나라_final.mp4", 28.4),     # s02 시작 (audio/ 씬 길이 합)
    "harin_en": (SRC / "✅하린이와_초코의_이상한_나라_EN_final.mp4", 29.0),  # s02 시작 (audio_en/)
}
DUR = 20.0
FADE = 0.4  # 잘린 끝 대사가 뚝 끊기지 않게

for name, (src, start) in CUTS.items():
    out = BASE / "clips" / f"{name}.mp4"
    if out.exists() and out.stat().st_size > 100000:
        print(f"{name}: cached")
        continue
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start}", "-t", f"{DUR}", "-i", str(src),
                    "-vf", "scale=1280:720,fps=25",
                    "-af", f"afade=t=in:d={FADE},afade=t=out:st={DUR - FADE}:d={FADE}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    print(f"{name}: {start}s +{DUR}s")
