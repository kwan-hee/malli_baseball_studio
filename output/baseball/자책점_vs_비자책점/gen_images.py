# 자책점 vs 비자책점 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물 얼굴 금지)
import base64
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

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
FALLBACK_MODEL = "gemini-2.5-flash-image"  # pro 504 연발 시 Nano Banana 폴백 (GA 모델명, preview는 404)

STYLE = (
    "bright cheerful cartoon illustration, clean bold outlines, dynamic sports composition, "
    "vivid colors, Korean baseball stadium atmosphere, no text, no letters, no numbers, "
    "no real person likeness, generic stylized faces"
)

SCENES = {
    "s01": "dramatic night game: a cartoon pitcher on the mound looking back over his shoulder as a baseball sails over the outfield fence with a glowing trail, giant stadium scoreboard looming in the background, packed crowd, tense mood",
    "s02": "clean two-panel concept illustration: left side a confident pitcher releasing a glowing red baseball (his own responsibility), right side an infielder fumbling and dropping a glowing blue baseball (team's mistake), baseball diamond backdrop, simple contrast composition",
    "s03": "cozy press box high above the field: a cartoon official scorer at a desk with scoresheets and a pencil, a large thought bubble above showing a translucent ghost replay of the baseball field below, warm lamp light, studious mood",
    "s04": "vintage sepia-toned early 1900s baseball scene: a lone pitcher in an old-fashioned wool uniform standing tall on the mound of a wooden-fence ballpark, complete-game era, retro halftone texture, nostalgic mood",
    "s05": "1910s office scene: a thick leather-bound record ledger lying open on a wooden desk with a fountain pen, a vintage baseball resting beside it, old stadium visible through the window, official and historic mood",
    "s06": "quiet dramatic scene: a pitcher in a blue uniform seen from behind in the dugout, in the foreground a large paper scoresheet where two glowing marks are being erased by a giant pencil eraser, particles fading away, sense of records changing",
    "s07": "dramatic replay simulation: a cartoon outfielder dropping an easy pop fly shown as a translucent ghost overlay, while in the foreground a batter crushes a towering home run under dramatic split lighting, motion lines, stormy night stadium",
    "s08": "playful two-panel contrast: left panel a pitcher throwing a wild ball bouncing in the dirt far from the plate, right panel a catcher flinching as an easy catchable ball slips past his mitt, cartoon exaggeration, clear visual opposition",
    "s09": "evening bullpen scene: a relief pitcher walking from the bullpen gate toward the mound, on the basepath behind him a translucent ghost runner standing on second base, dramatic stadium lights, sense of inherited burden",
    "s10": "warm closing scene: a baseball and a folded scoresheet resting together on green outfield grass at golden sunset, stadium lights glowing softly in the background, peaceful end-of-game mood",
}

client = genai.Client(api_key=API_KEY, http_options={"timeout": 300000})

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue
    prompt = f"{scene}. {STYLE}. Aspect ratio 16:9, resolution 1920x1080."
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
                    print(f"{sid}: {len(img):,} bytes")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part")
        except Exception as e:
            err = str(e)
            print(f"{sid}: attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                sys.exit(f"{sid}: quota exceeded - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed")

print("ALL DONE")
