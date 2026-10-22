# 화이트보드 오버레이 에셋 생성: 지우개 + 매직펜 든 손 (투명 배경 PNG)
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "overlays"
OUT.mkdir(exist_ok=True)

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

ASSETS = {
    "eraser": (
        "A whiteboard eraser held by a human right hand, viewed from the side, "
        "the hand is gripping a standard rectangular white/gray dry-erase board eraser, "
        "the hand and eraser are positioned as if wiping a whiteboard from left to right, "
        "clean simple illustration style, on a completely transparent background (PNG alpha), "
        "NO whiteboard surface, NO text, NO letters, just the hand holding the eraser. "
        "The eraser and hand should be about 200 pixels tall, oriented vertically. "
        "Square aspect ratio 512x512."
    ),
    "marker_hand": (
        "A human right hand holding a black whiteboard marker pen, viewed from above at an angle, "
        "the hand is positioned as if writing or drawing on a surface, pen tip pointing down-left, "
        "clean simple illustration style, on a completely transparent background (PNG alpha), "
        "NO whiteboard surface, NO text, NO letters, just the hand holding the marker. "
        "The hand and marker should be about 200 pixels tall. "
        "Square aspect ratio 512x512."
    ),
}

pool = GeminiPool()
client = pool.client()

for name, prompt in ASSETS.items():
    out = OUT / f"{name}.png"
    if out.exists() and out.stat().st_size > 5000:
        print(f"{name}: cached")
        continue
    for attempt in range(4):
        model = MODEL if attempt < 2 else FALLBACK_MODEL
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
            done = False
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    data = part.inline_data.data
                    img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                    out.write_bytes(img)
                    print(f"{name}: {len(img):,} bytes [model={model}]")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part")
        except Exception as e:
            err = str(e)
            print(f"{name}: attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{name}: all gemini keys exhausted")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{name}: all retries failed")

print("\n=== Overlays Done ===")
