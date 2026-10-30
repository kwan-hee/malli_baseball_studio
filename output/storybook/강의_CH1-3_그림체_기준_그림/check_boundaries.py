# 장면 경계 검증 — 장면 wav 마다 whisper small 재전사 후 대본 머리·꼬리 6자와 대조 (1-1 교훈: 2화자 강의 필수 단계)
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["PATH"] = ("C:/Users/user/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
                      "ffmpeg-8.1.1-full_build/bin" + os.pathsep + os.environ["PATH"])
from pathlib import Path

import whisper

from make_narration import SCENES, norm

BASE = Path(__file__).parent
model = whisper.load_model("small")
bad = []
for sid, line in SCENES.items():
    r = model.transcribe(str(BASE / "audio" / f"{sid}.wav"), language="ko", fp16=False)
    got, want = norm(r["text"]), norm(line)
    head_ok = got[:3] == want[:3] or want[:3] in got[:8]
    tail_ok = got[-3:] == want[-3:] or want[-3:] in got[-8:]
    flag = "" if head_ok and tail_ok else "  <-- 확인"
    if flag:
        bad.append(sid)
    print(f"{sid}: [{got[:8]} … {got[-8:]}] / 대본 [{want[:8]} … {want[-8:]}]{flag}")
print("의심:", bad or "없음")
