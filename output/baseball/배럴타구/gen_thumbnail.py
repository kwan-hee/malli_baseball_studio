# 배럴타구 — 썸네일 배경 생성 (텍스트 없는 배경, 글자는 ffmpeg drawtext로 후합성)
import base64
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "thumb_bg.png"

ENV = Path(r"C:\youtube_longform_agent\.env")
API_KEY = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith(("GEMINI_API_KEY=", "gemini=")):
        API_KEY = line.split("=", 1)[1].strip()
        break
if not API_KEY:
    sys.exit("GEMINI_API_KEY not found")

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

PROMPT = (
    "YouTube thumbnail background, bright cheerful cartoon illustration, clean bold outlines: "
    "a cartoon batter making perfect contact at a night stadium, the baseball exploding off the thick barrel "
    "of the bat with a brilliant glowing impact flash and a bright curved glowing trajectory line rocketing away, "
    "holographic data glow and neon tracking lines around the impact, "
    "vivid warm stadium lights, strong color contrast (deep blue night sky, yellow-orange impact flash, green tracking lines), "
    "composition leaves the RIGHT THIRD of the image relatively empty and dark for large text overlay. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, no real person likeness, generic stylized face. "
    "Aspect ratio 16:9, resolution 1280x720."
)

client = genai.Client(api_key=API_KEY, http_options={"timeout": 300000})

for attempt in range(4):
    model = MODEL if attempt < 2 else FALLBACK_MODEL
    try:
        resp = client.models.generate_content(
            model=model,
            contents=PROMPT,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        done = False
        for part in resp.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                data = part.inline_data.data
                img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                OUT.write_bytes(img)
                print(f"thumb_bg: {len(img):,} bytes ({model})")
                done = True
                break
        if done:
            break
        raise RuntimeError("no image part")
    except Exception as e:
        print(f"attempt {attempt+1} failed - {type(e).__name__}: {str(e)[:100]}")
        time.sleep(10 * (attempt + 1))
else:
    sys.exit("thumbnail bg: all retries failed")
