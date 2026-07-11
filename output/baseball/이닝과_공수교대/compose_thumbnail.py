# 이닝과 공수교대 — 썸네일 텍스트 합성: thumb_bg.png 위에 메인/서브 문구 drawtext → thumbnail.png
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

MAIN = "왜 하필 9회?"
SUB = "야구 기초 완벽 정리"

vf = (
    f"drawtext=fontfile=malgunbd.ttf:text='{MAIN}':fontsize=88:fontcolor=yellow:"
    f"borderw=7:bordercolor=black:x=w-tw-50:y=h*0.24,"
    f"drawtext=fontfile=malgunbd.ttf:text='{SUB}':fontsize=46:fontcolor=white:"
    f"borderw=5:bordercolor=black:x=w-tw-50:y=h*0.24+130"
)

r = subprocess.run(
    [FFMPEG, "-y", "-i", "thumb_bg.png", "-vf", vf, "-frames:v", "1", "thumbnail.png"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(BASE),
)
if r.returncode != 0:
    raise SystemExit(f"drawtext failed:\n{r.stderr[-1200:]}")
print("thumbnail.png written")
