# 말리와 토끼와 거북이 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
RABBIT = "a cheerful fluffy white rabbit with long ears, bright eyes, quick lively posture"
TORTOISE = "a friendly green tortoise with a round patterned shell, a gentle smiling face, slow steady posture"
TREE = "a big leafy tree on top of a grassy hill (the finish line)"
NO_MALLI = "NO dog in this scene, Malli does NOT appear"
STYLE = (
    "Studio Ghibli anime style, soft painterly backgrounds, warm pastel colors, watercolor texture "
    "with painterly brush strokes, gentle expressive characters, clean composition, do not change character design"
)

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer at the edge of a bright green forest meadow, a sunny path winding toward a distant hill, bright morning light, {STYLE}",
    "s02": f"{RABBIT} hopping energetically on the left and {TORTOISE} walking slowly on the right in a sunny green meadow, showing fast vs slow, {NO_MALLI}, {STYLE}",
    "s03": f"the {RABBIT} laughing and playfully teasing the {TORTOISE}, while the tortoise calmly smiles and proposes a race, a grassy hill with {TREE} in the background, {NO_MALLI}, {STYLE}",
    "s04": f"the {RABBIT} dashing off at super speed in a burst of motion with a dust trail, leaving the slow {TORTOISE} far behind at the starting line, dynamic action, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} sitting and watching the race curiously, one paw near her chin, a wondering expression, sunny meadow with a hill in the distance, {STYLE}",
    "s06": f"the {RABBIT} napping lazily and cozily in the cool shade of a big tree on the hill, sleeping peacefully with a happy face, {NO_MALLI}, {STYLE}",
    "s07": f"the {TORTOISE} steadily climbing the grassy hill one step at a time, determined effort, a tiny sweat drop, warm afternoon light, {NO_MALLI}, {STYLE}",
    "s08": f"the {TORTOISE} quietly passing right by the sleeping {RABBIT} under the tree, the tortoise still walking forward determined, the rabbit fast asleep unaware, {NO_MALLI}, {STYLE}",
    "s09": f"the {TORTOISE} walking on four legs joyfully crossing a simple white finish ribbon at {TREE} FIRST, while the startled {RABBIT} dashes in from behind too late, celebration and surprise, warm golden light, absolutely NO text, no letters, no banner words, no writing anywhere, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly at the meadow at sunset, with the {RABBIT} and the {TORTOISE} standing together happily as friends behind her, ONLY the rabbit and the tortoise, no other animals, soft warm sunset colors, {STYLE}",
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
