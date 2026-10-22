# 말리와 욕심쟁이 개(졸라맨 버전) — 화이트보드 마커 + 졸라맨 스타일
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

STYLE = (
    "clean whiteboard marker sketch on a pristine white dry-erase board surface, "
    "hand-drawn style with black marker for main outlines, blue marker for water and paths, "
    "red marker for highlights and emphasis, green marker for grass and nature, "
    "minimal shading, visible marker stroke texture, "
    "simple cute stick-figure style characters, storybook doodle mood, "
    "no photorealistic elements, looks like a child or teacher drew it on a whiteboard. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO labels anywhere in the image"
)

# 말리(진행자) = 졸라맨 강아지 with 빨간 리본 + 분홍 목걸이 (구별용)
# 주인공 개 = 갈색 졸라맨 강아지 (말리 아님)
MALLI_STICK = "a simple cute stick-figure puppy with a big red bow on its head and a pink collar, round head with big dot eyes, wagging tail doodle"
DOG_STICK = "a simple stick-figure dog (brown marker outline, NOT Malli, NO bow, NO collar) with floppy ears and a round nose"
MEAT_STICK = "a big piece of meat drawn with red marker, simple steak shape"
BRIDGE_STICK = "a simple wooden plank bridge drawn with brown marker lines over wavy blue water"

SCENES = {
    "s01": (
        f"whiteboard doodle: {MALLI_STICK} waving hello cheerfully on a grassy hilltop "
        "with a small house and trees drawn simply in the background, "
        "happy storybook opening mood, flower doodles around"
    ),
    "s02": (
        f"whiteboard doodle: {DOG_STICK} trotting along a path proudly carrying {MEAT_STICK} in its mouth, "
        "musical note doodles around its head showing happiness, "
        "green marker grass and simple trees along the path, cheerful mood"
    ),
    "s03": (
        f"whiteboard doodle: {DOG_STICK} standing in the middle of {BRIDGE_STICK} "
        "looking down at wavy blue water below, in the water a mirror reflection of the same stick dog "
        "also holding meat is drawn with lighter marker strokes, "
        "surprised exclamation doodle above the dog's head, curious mood"
    ),
    "s04": (
        f"whiteboard doodle: close view of {DOG_STICK} on the bridge peering down at the water "
        "where the reflected stick dog's meat looks bigger (drawn larger with red marker), "
        "the dog's eyes are drawn as big sparkly circles showing greed, "
        "red emphasis arrows pointing at the reflection's bigger meat, covetous mood"
    ),
    "s05": (
        f"whiteboard doodle: {MALLI_STICK} sitting to the side with a worried expression "
        "and a paw on its chin, a thought bubble with a danger sign doodle, "
        "looking toward the audience as if warning them, concerned mood"
    ),
    "s06": (
        f"whiteboard doodle: {DOG_STICK} on the bridge growling angrily at the water, "
        "jagged red anger lines around its head, teeth bared as simple zigzag mouth, "
        "the reflection in the blue water also shows teeth back, "
        "tense confrontation mood with red emphasis marks"
    ),
    "s07": (
        f"whiteboard doodle dramatic moment: {DOG_STICK} on the bridge with its mouth wide open (big circle), "
        f"{MEAT_STICK} falling down with motion lines toward the blue wavy water, "
        "a big SPLASH effect drawn with blue marker splatter doodles, "
        "the reflection in the water breaking apart into wavy lines, "
        "shocking dramatic mood with red emphasis burst"
    ),
    "s08": (
        f"whiteboard doodle: {DOG_STICK} on the bridge with an empty mouth (small sad circle), "
        "staring down at empty rippling blue water with no reflection anymore, "
        "tear drop doodles near its eyes, droopy ears and tail, "
        "sad regretful mood, muted marker strokes"
    ),
    "s09": (
        f"whiteboard doodle: {DOG_STICK} walking away along a path with drooping shoulders "
        "and a droopy tail, small cloud doodle above its head showing sadness, "
        "but a tiny light bulb doodle appearing suggesting a lesson learned, "
        "reflective mood, simple path leading home"
    ),
    "s10": (
        f"whiteboard doodle: {MALLI_STICK} waving goodbye warmly with a big heart doodle, "
        "surrounded by small star and flower doodles, "
        "peaceful happy ending mood, clean whiteboard with slight marker residue"
    ),
}

pool = GeminiPool()
client = pool.client()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue
    prompt = f"{scene}. {STYLE}. WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall, aspect ratio 16:9, resolution 1920x1080."
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
                    print(f"{sid}: {len(img):,} bytes [model={model}]")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part")
        except Exception as e:
            err = str(e)
            print(f"{sid}: attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed")

print("ALL DONE")
