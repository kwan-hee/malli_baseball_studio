# 말리와 커다란 순무 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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

REF = Path(r"C:\PROJECT\images\style_ref\malli_reference.png")

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
GRANDPA = "a kind elderly farmer grandpa with a round straw hat, fluffy white beard, brown vest"
GRANDMA = "a gentle elderly grandma with gray bun hair and a warm apron"
RABBIT = "a small white rabbit with long ears"
CAT = "an orange tabby cat"
MOUSE = "a tiny gray mouse with big round ears"
TURNIP = "a gigantic turnip as big as a small hill, round white body with a purple top and huge lush green leaves"
STYLE = (
    "Studio Ghibli anime style, soft painterly backgrounds, warm pastel colors, "
    "gentle expressive character, clean composition, do not change character design"
)

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer on a sunny countryside path leading to a farm, rolling fields and a small farmhouse in the distance, bright morning light",
    "s02": f"{GRANDPA}, alone planting turnip seeds and watering a small sprout in a spring vegetable garden, watering can in hand, gentle sunshine, NO dog in this scene, Malli does NOT appear, soft watercolor texture",
    "s03": f"{MALLI} and {GRANDPA}, staring up in amazement at {TURNIP} growing in the middle of the field, both tiny next to it, wow expression",
    "s04": f"{GRANDPA}, grabbing the giant leaves of {TURNIP} and pulling with all his might, leaning back hard, the turnip not budging at all",
    "s05": f"{GRANDPA}, {GRANDMA} and {MALLI}, pulling {TURNIP} together in a line, everyone straining hard but the turnip still stuck in the ground",
    "s06": f"{GRANDPA}, {GRANDMA}, {MALLI}, {RABBIT} and {CAT}, all five pulling {TURNIP} together in a long line across the field, determined faces, dynamic tug-of-war pose",
    "s07": f"{MOUSE}, arriving shyly while {CAT} laughs dismissively, and {MALLI} kneeling down to welcome the tiny mouse warmly with a kind smile, the giant turnip still stuck in the ground behind them, green field, warm afternoon light, soft watercolor texture with painterly brush strokes, muted warm colors matching a gentle watercolor storybook",
    "s08": f"{TURNIP} popping out of the ground with a burst of soil and leaves flying, {MALLI}, {GRANDPA}, {GRANDMA}, {RABBIT}, {CAT} and {MOUSE} tumbling backward joyfully, celebration, golden afternoon light",
    "s09": f"{MALLI}, {GRANDPA}, {GRANDMA}, {RABBIT}, {CAT} and {MOUSE}, gathered around a wooden table sharing steaming bowls of turnip soup in the evening, warm cozy lamp light, happy faces",
    "s10": f"{MALLI}, waving goodbye warmly in front of the harvested field at sunset, with {RABBIT}, {CAT} and {MOUSE} behind her, ONLY these three animal friends, no other animals, soft warm sunset colors, soft watercolor texture",
}

client = genai.Client(api_key=API_KEY, http_options={"timeout": 300000})
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
                    out.write_bytes(img)
                    print(f"{sid}: {len(img):,} bytes ({model})")
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
