# 말리와 소가 된 게으름뱅이 — 동화 전용 BGM(b1→b2 순서) 으로 bgm.mp3 생성
# 2026-10-15 규칙: assets/bgm/storybook 의 b1,b2 를 순서대로. 합본(234.6s)은 본편(270.6s)보다 짧아
# stream_loop 되감기 지점에서 b2 끝→b1 처음이 뚝 끊김 → b1→b2→b1 을 전부 acrossfade 로 이어 영상 길이 이상 확보.
# 두 곡 음량 차이(b1 -16.8 / b2 -15.4 LUFS)로 전환이 티 나지 않도록 각 곡을 -16 LUFS 로 맞춘 뒤 연결.
# (기존 템플릿 곡은 -12.2 LUFS — 약 4dB 낮아져 나레이션 아래 더 은은하게 깔림, compose 볼륨 0.15 그대로)
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
FFMPEG = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.EXE"
)
SRC = Path(r"C:\PROJECT\assets\bgm\storybook")
ORDER = ["b1", "b2", "b1"]  # 순서대로, 본편 길이 이상이 되도록 b1 한 번 더
XFADE = 3.0
LUFS = -16
MEASURED = {"b1": -16.8, "b2": -15.4}  # ebur128 integrated loudness (2026-10-15 측정)
# loudnorm 1-pass 는 동적 보정이라 곡 강약이 출렁임 → 측정값 기준 고정 게인만 적용

inputs, chains = [], []
for i, name in enumerate(ORDER):
    inputs += ["-i", str(SRC / f"{name}.mp3")]
    gain = LUFS - MEASURED[name]
    chains.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,volume={gain:+.1f}dB[n{i}]")
prev = "n0"
for i in range(1, len(ORDER)):
    out = f"x{i}"
    chains.append(f"[{prev}][n{i}]acrossfade=d={XFADE}:c1=tri:c2=tri[{out}]")
    prev = out

subprocess.run(
    [FFMPEG, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chains),
     "-map", f"[{prev}]", "-ar", "44100", "-b:a", "192k", str(BASE / "bgm.mp3")],
    check=True,
)
print("bgm.mp3 done")
