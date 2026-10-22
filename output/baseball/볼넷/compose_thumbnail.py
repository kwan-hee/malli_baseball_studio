# 볼넷 — 썸네일 텍스트 합성: thumb_bg.png 위에 메인/서브 문구 drawtext → thumbnail.png
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
FFMPEG = (
    "ffmpeg"
)

# 콜론 이스케이프 회피 위해 폰트를 로컬로 복사해 상대경로 참조
FONT = BASE / "malgunbd.ttf"
if not FONT.exists():
    shutil.copy(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "fonts/malgunbd.ttf"), FONT)

MAIN = "왜 4개일까?"
SUB = "처음엔 9개였다"

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
