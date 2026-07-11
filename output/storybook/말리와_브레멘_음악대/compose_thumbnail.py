# 말리와 브레멘 음악대 — 썸네일 텍스트 합성: thumb_bg.png 위에 문구 drawtext → thumbnail.png
# 동화 채널이라 귀여운 폰트(font.ttf = MemomentKkukkukk) 사용, 좌측 1/3 영역에 배치
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
FFMPEG = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.EXE"
)

FONT = "font.ttf"  # MemomentKkukkukk (로컬 상대경로 — 콜론 이스케이프 회피)

MAIN = "넷이 힘을 합치면"
SUB = "브레멘 음악대"

vf = (
    f"drawtext=fontfile={FONT}:text='{MAIN}':fontsize=96:fontcolor=yellow:"
    f"borderw=8:bordercolor=black:x=60:y=h*0.30,"
    f"drawtext=fontfile={FONT}:text='{SUB}':fontsize=58:fontcolor=white:"
    f"borderw=6:bordercolor=black:x=60:y=h*0.30+150"
)

r = subprocess.run(
    [FFMPEG, "-y", "-i", "thumb_bg.png", "-vf", vf, "-frames:v", "1", "thumbnail.png"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(BASE),
)
if r.returncode != 0:
    raise SystemExit(f"drawtext failed:\n{r.stderr[-1200:]}")
print("thumbnail.png written")
