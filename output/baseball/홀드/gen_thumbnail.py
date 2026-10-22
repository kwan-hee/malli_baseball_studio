# 홀드 — 썸네일 배경 생성 (gemini-3-pro-image-preview)
# 텍스트 없는 배경 → compose_thumbnail.py drawtext 후합성
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "thumb_bg.png"

MODEL = "gemini-3-pro-image-preview"

PROMPT = (
    "YouTube thumbnail background, bright dramatic cartoon sports illustration, clean bold outlines, "
    "high click-through-rate composition: a heroic relief pitcher striding confidently out of the bullpen "
    "toward the mound under dramatic spotlights, fiery glowing aura around him suggesting he is the savior, "
    "behind him flames on the bases being extinguished, a baton handoff moment between two relievers, "
    "packed cheering stadium, strong warm golden glow and green field, "
    "composition leaves the RIGHT THIRD relatively empty for large Korean text overlay. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, "
    "NO English words, NO speech bubbles, NO captions, "
    "no real person likeness, generic cartoon face. "
    "WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall, "
    "aspect ratio 16:9, resolution 1280x720."
)

pool = GeminiPool()
client = pool.client()

for attempt in range(4):
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=PROMPT,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        done = False
        for part in resp.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                data = part.inline_data.data
                img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                OUT.write_bytes(img)
                print(f"thumb_bg: {len(img):,} bytes ({MODEL})")
                done = True
                break
        if done:
            break
        raise RuntimeError("no image part")
    except Exception as e:
        err = str(e)
        print(f"attempt {attempt+1} failed - {type(e).__name__}: {err[:120]}")
        if is_quota_error(err):
            try:
                client = pool.rotate()
                continue
            except RuntimeError:
                sys.exit("thumbnail: all gemini keys exhausted")
        time.sleep(10 * (attempt + 1))
else:
    sys.exit("thumbnail bg: all retries failed")
