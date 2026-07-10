# 말리와 호랑이와 곶감 — 썸네일 배경 생성 (좌측 1/3 비움, 글자는 ffmpeg drawtext 후합성)
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

REF = Path(r"C:\PROJECT\images\style_ref\malli_reference.png")

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)

PROMPT = (
    "CRITICAL: This image is the OFFICIAL Malli character reference sheet. "
    "You MUST reproduce Malli's appearance EXACTLY as shown. "
    f"YouTube thumbnail background for a children's storybook video: {MALLI} looking cheerful, "
    "next to a big cute cartoon tiger (orange with black stripes, funny scared wide-eyed expression) "
    "trembling at a bright orange dried persimmon, a cozy old Korean village at night in the background, "
    "positioned on the RIGHT TWO THIRDS of the frame, bright cheerful colors with strong contrast, "
    "composition leaves the LEFT THIRD of the image relatively simple and soft (plain night sky) for large text overlay, "
    "Studio Ghibli anime style, soft painterly, warm colors, no text, no letters. "
    "Aspect ratio 16:9, resolution 1280x720."
)

client = genai.Client(api_key=API_KEY, http_options={"timeout": 300000})
ref_bytes = REF.read_bytes()
contents = [
    types.Part(inline_data=types.Blob(data=ref_bytes, mime_type="image/png")),
    types.Part(text=PROMPT),
]

for attempt in range(4):
    model = MODEL if attempt < 2 else FALLBACK_MODEL
    try:
        resp = client.models.generate_content(
            model=model,
            contents=contents,
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
