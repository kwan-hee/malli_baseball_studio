# 스트라이크 존 — 썸네일 텍스트 합성: thumb_bg.png 위에 메인/서브 문구 drawtext → thumbnail.png
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
FFMPEG = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.EXE"
)

# 콜론 이스케이프 회피 위해 폰트를 로컬로 복사해 상대경로 참조
FONT = BASE / "malgunbd.ttf"
if not FONT.exists():
    shutil.copy(r"C:\Windows\Fonts\malgunbd.ttf", FONT)

MAIN = "보이지 않는 상자"
SUB = "존은 타자마다 다르다"

vf = (
    f"drawtext=fontfile=malgunbd.ttf:text='{MAIN}':fontsize=80:fontcolor=yellow:"
    f"borderw=7:bordercolor=black:x=w-tw-50:y=h*0.24,"
    f"drawtext=fontfile=malgunbd.ttf:text='{SUB}':fontsize=44:fontcolor=white:"
    f"borderw=5:bordercolor=black:x=w-tw-50:y=h*0.24+120"
)

r = subprocess.run(
    [FFMPEG, "-y", "-i", "thumb_bg.png", "-vf", vf, "-frames:v", "1", "thumbnail.png"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(BASE),
)
if r.returncode != 0:
    raise SystemExit(f"drawtext failed:\n{r.stderr[-1200:]}")
print("thumbnail.png written")
