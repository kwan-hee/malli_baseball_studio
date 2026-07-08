# 끝내기 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물 얼굴 금지)
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
    "s01": "dramatic night game bottom of the ninth: a cartoon batter finishing a powerful swing as the baseball sails over the outfield fence with a glowing trail, packed crowd erupting, giant stadium lights, walk-off home run mood, triumphant",
    "s02": "clear concept illustration: a home team dugout celebrating as a runner crosses home plate under a big scoreboard, the visiting team walking off the field with slumped shoulders, split mood of joy versus defeat, baseball diamond backdrop",
    "s03": "simple diagram-style scene: a stadium scoreboard showing the top of the ninth just ended with the home team already ahead, an umpire signaling game over while the home dugout does not even come out to bat, calm explanatory mood",
    "s04": "1980s American ballpark scene: a veteran relief pitcher standing on the mound in a green and gold uniform seen from behind, thoughtful vintage mood, retro stadium, sense of a term being born",
    "s05": "melancholy scene: a defeated pitcher walking off the mound with his head hung low toward the dugout, in the background a translucent ghostly home run ball arcs over the fence, dramatic shadows, bittersweet mood",
    "s06": "electric Korean Series night: a cartoon batter crushing a towering walk-off home run as teammates pour out of the dugout, previous batter already celebrating, back-to-back home run energy, explosive crowd, confetti falling",
    "s07": "championship celebration: a Korean baseball team mobbing home plate under fireworks after a walk-off home run wins the series, trophy glow in the sky, rare historic moment, jubilant crowd",
    "s08": "playful explanatory scene: bases loaded in the bottom of the ninth, one runner crossing home plate glowing gold as the winning run while the other runners fade to translucent gray, a single-base hit marked, clever contrast composition",
    "s09": "bright celebratory contrast: a batter rounding the bases after a grand slam walk-off, all four runners glowing gold and fully counted, big number four shown as four glowing bases, exception-to-the-rule mood, joyful stadium",
    "s10": "warm closing scene: a baseball resting on home plate at golden sunset with an empty celebratory stadium behind, soft glowing lights, peaceful end-of-game mood, hopeful atmosphere",
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
