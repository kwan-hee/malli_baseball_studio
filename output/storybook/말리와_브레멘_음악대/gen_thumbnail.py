# 말리와 브레멘 음악대 — 썸네일 배경 생성 (좌측 1/3 비움, 글자는 ffmpeg drawtext 후합성)
import base64
import sys
import time
from pathlib import Path

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, r"C:\youtube_longform_agent")
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "thumb_bg.png"

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
    "next to four funny animal friends stacked in a tall tower — a grey donkey at the bottom, a brown dog, "
    "a grey cat, and a colorful rooster on top — all singing together with big music notes, in front of a cozy "
    "cottage at night, warm and heartwarming funny scene, positioned on the RIGHT TWO THIRDS of the frame, "
    "bright cheerful colors with strong contrast, "
    "composition leaves the LEFT THIRD of the image relatively simple and soft (plain night sky) for large text overlay, "
    "Studio Ghibli anime style, soft painterly, warm colors, no text, no letters. "
    "Aspect ratio 16:9, resolution 1280x720."
)

pool = GeminiPool()
client = pool.client()
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
        err = str(e)
        print(f"attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
        if is_quota_error(err):
            try:
                client = pool.rotate()  # 키 소진 → 다음 계정으로
                continue
            except RuntimeError:
                sys.exit("thumbnail: all gemini keys exhausted")
        time.sleep(10 * (attempt + 1))
else:
    sys.exit("thumbnail bg: all retries failed")
