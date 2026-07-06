# 사이클링 히트 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물 얼굴 금지)
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

STYLE = (
    "bright cheerful cartoon illustration, clean bold outlines, dynamic sports composition, "
    "vivid colors, Korean baseball stadium atmosphere, no text, no letters, "
    "no real person likeness, generic stylized faces"
)

SCENES = {
    "s01": "energetic montage feeling: a cartoon baseball batter mid-swing at home plate, four baseballs flying in different arcs (short grounder, line drive, deep gap shot, towering home run), packed stadium at dusk",
    "s02": "clean infographic-style illustration of a baseball diamond viewed from above, four glowing baseballs landing at increasing distances from home plate, simple icons marking first second third base and over the fence",
    "s03": "playful concept scene: two cartoon baseball players facing each other with empty speech bubbles, one wearing a USA-style uniform and one wearing a Korean-style uniform, confused expressions, stadium background",
    "s04": "vintage 1930s sepia-toned scene: an old newspaper printing press and a classic-era baseball slugger in old-fashioned uniform finishing a mighty swing, retro halftone texture",
    "s05": "vast empty baseball stadium at night, a single baseball glowing like a gem on the pitcher mound, dramatic spotlight, sense of extreme rarity and preciousness",
    "s06": "retro 1980s Korean baseball scene: a batter in a blue vintage uniform rounding the bases in an old concrete stadium, grainy nostalgic film tone, cheering crowd silhouettes",
    "s07": "dramatic night game climax: a young batter in a red and black uniform launching a home run, ball soaring over the outfield fence with a light trail, fireworks of camera flashes in packed stands",
    "s08": "celebratory scene: a giant stadium scoreboard with four bright lights lighting up in sequence, confetti falling, players cheering from the dugout, triumphant mood",
    "s09": "high-speed action: a cartoon baseball runner sprinting hard around second base toward third, dust kicking up, motion speed lines, determined face, dynamic low camera angle",
    "s10": "warm closing scene: a baseball resting on green outfield grass at golden sunset, stadium lights glowing softly in the background, peaceful end-of-game mood",
}

client = genai.Client(api_key=API_KEY, http_options={"timeout": 90000})

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue
    prompt = f"{scene}. {STYLE}. Aspect ratio 16:9, resolution 1920x1080."
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
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
