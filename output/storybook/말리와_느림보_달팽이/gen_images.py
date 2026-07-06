# 말리와 느림보 달팽이 — 씬 이미지 10장을 Nano Banana(Gemini)로 생성하는 스크립트
import base64
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

# API 키: 기존 파이프라인 .env 재사용
ENV = Path(r"C:\youtube_longform_agent\.env")
API_KEY = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith(("GEMINI_API_KEY=", "gemini=")):
        API_KEY = line.split("=", 1)[1].strip()
        break
if not API_KEY:
    sys.exit("GEMINI_API_KEY not found in .env")

REF = Path(r"C:\Users\user\OneDrive\文档\Capcut\PROJECT\images\style_ref\malli_reference.png")

MODEL = "gemini-3-pro-image-preview"
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
TOTO = (
    "a tiny gentle snail named Toto with a light brown spiral shell, "
    "soft rounded body, small kind sleepy eyes"
)
STYLE = (
    "Studio Ghibli anime style, soft painterly backgrounds, warm pastel colors, "
    "gentle expressive character, clean composition, do not change character design"
)

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer in front of her cozy house on a sunny morning, small picnic bag beside her",
    "s02": f"{MALLI}, running joyfully along a countryside path with her tail wagging, petals drifting in the breeze, bright morning light",
    "s03": f"{MALLI}, crouching down curiously to look at {TOTO} on the path, friendly first meeting, soft sunlight",
    "s04": f"{MALLI}, dashing ahead alone down the path looking impatient, while {TOTO} slowly follows far behind",
    "s05": f"{MALLI}, standing at a forked path looking lost and teary-eyed, tall grass around, slightly worried atmosphere but not scary",
    "s06": f"{TOTO}, gently comforting a relieved {MALLI} at the forked path, pointing the way past a red flower and a round stone",
    "s07": f"{MALLI}, walking slowly side by side with {TOTO} along the path, sparkling dew drops on grass and a yellow butterfly fluttering around them",
    "s08": f"{MALLI} and {TOTO}, arriving together at a wide colorful flower field in full bloom, both smiling with joy, warm golden light",
    "s09": f"{MALLI}, sitting peacefully in the flower field with {TOTO} beside her, looking at the flowers with a gentle thoughtful smile",
    "s10": f"{MALLI}, waving goodbye warmly among the flowers with {TOTO} on a leaf beside her, soft warm sunset colors",
}

client = genai.Client(api_key=API_KEY, http_options={"timeout": 90000})
ref_bytes = REF.read_bytes()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

    prompt = (
        "CRITICAL: This image is the OFFICIAL Malli character reference sheet. "
        "You MUST reproduce Malli's appearance EXACTLY as shown — same cream fur, "
        "same red bow, same pink collar, same gold bone tag, same dark eyes. "
        f"MAIN CHARACTER: {MALLI}. {STYLE}. Scene: {scene}. "
        f"Aspect ratio 16:9, resolution {W}x{H}."
    )
    contents = [
        types.Part(inline_data=types.Blob(data=ref_bytes, mime_type="image/png")),
        types.Part(text=prompt),
    ]

    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
            done = False
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    data = part.inline_data.data
                    img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                    out.write_bytes(img)
                    print(f"{sid}: {len(img):,} bytes")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part in response")
        except Exception as e:
            err = str(e)
            print(f"{sid}: attempt {attempt+1} failed — {type(e).__name__}: {err[:120]}")
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                sys.exit(f"{sid}: quota exceeded — stop, report to user")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed — stop, report to user")

print("ALL DONE")
