# 홀드(졸라맨 버전) — 씬 삽화 10장 (화이트보드 마커 스케치 + 졸라맨 스타일)
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
    "hand-drawn style with black marker for main outlines, blue marker for arrows and paths, "
    "red marker for highlights and emphasis circles, minimal shading, "
    "visible marker stroke texture, simple stick-figure style players (졸라맨), "
    "baseball diamond diagrams drawn with clean marker lines, "
    "no photorealistic elements, looks like a coach drew it on a whiteboard to explain. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO labels, "
    "NO scoreboard digits, NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": (
        "whiteboard sketch hook: a stick-figure relief pitcher bursting out of a bullpen gate door "
        "drawn with bold black marker, sprinting toward the mound with motion lines, "
        "another tired stick-figure pitcher walking off the mound with droopy arms, "
        "stick-figure runners on bases looking nervous, a big red marker question mark hovering: "
        "why no save for this hero? curious dramatic mood"
    ),
    "s02": (
        "whiteboard concept diagram: a baseball diamond drawn from above with marker, "
        "a stick-figure reliever on the mound with a firefighter helmet doodle, "
        "small flame doodles on the bases being crossed out with blue marker, "
        "a bold blue arrow showing the baton handoff to the next pitcher, "
        "simple clean explanation mood, like a coach teaching"
    ),
    "s03": (
        "whiteboard teaching diagram: four condition boxes drawn with marker, "
        "box 1 shows a scoreboard-like bar with a narrow gap suggesting close lead, "
        "box 2 shows a stick batter with an X through it suggesting one out minimum, "
        "box 3 shows a happy stick pitcher walking off with a thumbs up, "
        "box 4 shows another stick pitcher taking the mound (not finishing the game), "
        "clean instructional layout with blue connecting arrows"
    ),
    "s04": (
        "whiteboard comparison diagram split into three columns with red marker dividers: "
        "left column shows a stick closer celebrating after final out with confetti doodles and a trophy labeled 'S' shape, "
        "middle column shows a stick reliever high-fiving the next pitcher coming in with a shield shape, "
        "right column shows a sad stick pitcher with opposing runners crossing home with frown doodles, "
        "three clear outcomes side by side"
    ),
    "s05": (
        "whiteboard historical scene: two stick-figure statisticians sitting at a desk with papers and "
        "an old boxy computer monitor drawn in simple marker, one pointing excitedly at a chart/graph on the wall, "
        "a light bulb doodle above their heads suggesting a new idea, "
        "retro 1980s mood with marker squiggles, clean whiteboard"
    ),
    "s06": (
        "whiteboard ironic contrast split in two halves with a bold red vertical line: "
        "left half shows a stick-figure MLB umpire shrugging with a question mark cloud, "
        "right half shows a stick-figure KBO official proudly holding up a golden star/medal, "
        "blue arrow from left to right suggesting irony that the creator country doesn't recognize it "
        "but Korea does, simple marker doodles"
    ),
    "s07": (
        "whiteboard epic celebration: a veteran stick-figure pitcher on the mound pumping both fists up "
        "with bold motion lines radiating outward, teammate stick figures rushing from the dugout "
        "with arms raised, a big golden star doodle drawn in yellow marker above suggesting a record, "
        "confetti marker squiggles, joyful triumphant mood, clean whiteboard"
    ),
    "s08": (
        "whiteboard emotional timeline drawn left to right with blue arrow: "
        "three stages of a stick pitcher's career, "
        "left: sad stick figure with a suitcase being shown the door (released), "
        "middle: determined stick figure training alone throwing pitches on empty field, "
        "right: triumphant stick figure on mound with teammates cheering, "
        "a journey arc drawn with red marker above"
    ),
    "s09": (
        "whiteboard intense action: a dominant stick-figure setup reliever on the mound throwing "
        "with bold blue speed lines, a row of stick batters walking back to dugout with droopy arms "
        "one after another in a defeated line, showing dominance over many games, "
        "a fire extinguisher doodle near the pitcher suggesting 'firefighter' role, "
        "energetic marker strokes"
    ),
    "s10": (
        "whiteboard closing: a marker cap being placed back on a dry-erase marker next to a "
        "completed diagram showing the three paths (save/hold/blown save) with simple arrows, "
        "a small stick-figure thumbs up in the corner, satisfied teaching-complete mood, "
        "clean whiteboard with slight marker residue"
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
