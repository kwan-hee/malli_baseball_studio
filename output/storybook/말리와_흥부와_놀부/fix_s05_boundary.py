# s05/s06 경계 붕괴 수동 복구 — 문자 비율 추정 + silencedetect 무음 스냅 (미운오리 편 대응법)
import re
import subprocess
import wave
from pathlib import Path

from make_narration import SCENES, norm

BASE = Path(__file__).parent
FULL = BASE / "audio" / "narration_full.wav"
FFMPEG = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.EXE"
)
SR, BITS = 24000, 16
S05_START = 108.85   # whisper 안정 경계 (s04→s05)
S06_END = 146.49     # whisper 안정 경계 (s06→s07)
MARGIN = 0.15

c5, c6 = len(norm(SCENES["s05"])), len(norm(SCENES["s06"]))
seg = S06_END - S05_START
est = S05_START + seg * c5 / (c5 + c6)
print(f"chars s05={c5} s06={c6}, estimated boundary={est:.2f}s")

r = subprocess.run(
    [FFMPEG, "-i", str(FULL), "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
sil = [(float(m.group(1))) for m in re.finditer(r"silence_start: ([\d.]+)", r.stderr)]
cand = [s for s in sil if abs(s - est) <= 4.0]
if not cand:
    raise SystemExit(f"no silence within +-4s of {est:.2f} (silences near: {[round(s,1) for s in sil if abs(s-est)<8]})")
boundary = min(cand, key=lambda s: abs(s - est)) + MARGIN
print(f"snapped boundary={boundary:.2f}s (candidates: {[round(c,2) for c in cand]})")

with wave.open(str(FULL), "rb") as wf:
    pcm = wf.readframes(wf.getnframes())
bps = SR * BITS // 8


def cut(start, end, path):
    b0 = int(start * bps) // 2 * 2
    b1 = int(end * bps) // 2 * 2
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(BITS // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm[b0:b1])
    print(f"{path.name}: {start:.2f}~{end:.2f} ({end-start:.1f}s)")


cut(S05_START, boundary, BASE / "audio" / "s05.wav")
cut(boundary, S06_END, BASE / "audio" / "s06.wav")
print("FIX DONE")
