# 말리와 사자와 생쥐 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
ENV = Path(next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()) + "/.env")
API_KEY = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith(("GEMINI_API_KEY=", "gemini=")):
        API_KEY = line.split("=", 1)[1].strip()
        break
if not API_KEY:
    sys.exit("GEMINI_API_KEY not found in .env")

REF = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/malli_reference.png"))

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
LION = "a big friendly lion with a magnificent golden mane, warm expressive eyes, gentle rounded features (not scary)"
MOUSE = "a tiny brown mouse with big round ears and a little pink nose"
NET = "a sturdy brown rope net"
NO_MALLI = "NO dog in this scene, Malli does NOT appear"
STYLE = (
    "Studio Ghibli anime style, soft painterly backgrounds, warm pastel colors, watercolor texture "
    "with painterly brush strokes, gentle expressive characters, clean composition, do not change character design"
)

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer at the edge of a deep green forest, a sunlit path winding into the woods, bright morning light, {STYLE}",
    "s02": f"{LION}, sleeping peacefully and cozily under warm sunlight in a green forest clearing, soft dappled light through the trees, {NO_MALLI}, {STYLE}",
    "s03": f"{MOUSE} accidentally scurrying over the nose of the big sleeping {LION}, the lion's eyes snapping wide open in startled surprise, forest clearing, {NO_MALLI}, {STYLE}",
    "s04": f"the big {LION} gently cupping the tiny trembling {MOUSE} in one open front paw, the little mouse clasping its hands and pleading, the lion smiling kindly and warmly, forest, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} sitting thoughtfully at the edge of the forest, one paw near her chin, a curious wondering expression, soft afternoon light, {STYLE}",
    "s06": f"the big {LION} tangled and caught in {NET} in the forest, struggling and pulling hard to break free, worried determined face, dynamic pose, {NO_MALLI}, {STYLE}",
    "s07": f"the big {LION} still trapped inside {NET}, roaring for help, all alone in a quiet empty forest, sad teary eyes, muted afternoon light, {NO_MALLI}, {STYLE}",
    "s08": f"the tiny {MOUSE} busily gnawing through the ropes of {NET} with its little teeth to free the trapped {LION}, determined focused face, close view, {NO_MALLI}, {STYLE}",
    "s09": f"the big {LION} free from the broken {NET}, joyfully and gently hugging the tiny {MOUSE}, both laughing happily, warm golden afternoon light, celebration, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly at the forest at sunset, with the friendly {LION} and the tiny {MOUSE} standing together as friends behind her, ONLY the lion and the mouse, no other animals, soft warm sunset colors, {STYLE}",
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
        "When Malli appears you MUST reproduce her appearance EXACTLY as shown — same cream fur, "
        "same red bow, same pink collar, same gold bone tag, same dark eyes. "
        f"Scene: {scene}. "
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
