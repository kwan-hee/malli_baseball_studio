# 스탯캐스트 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물 얼굴 금지)
import base64
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

ENV = Path(next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()) + "/.env")
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
    "vivid colors, high-tech data visualization mood, glowing neon tracking lines, "
    "no text, no letters, no numbers, no real person likeness, generic stylized faces"
)

SCENES = {
    "s01": "dramatic night game: a cartoon batter finishing a powerful swing as the baseball soars over the outfield fence, a bright glowing curved tracking line following the ball's arc through the air, holographic data glow around it, packed crowd, giant stadium lights, high-tech broadcast mood",
    "s02": "concept illustration: a baseball stadium ringed with stylized cameras and radar dishes emitting glowing scan beams that trace a baseball and running players, a web of neon tracking lines covering the field, futuristic measurement mood",
    "s03": "split contrast illustration: on the left a fuzzy vague thought-cloud over a coach guessing, on the right the same play turned into crisp glowing data lines and a clean tracked trajectory, transformation from guesswork to precise data, clear explanatory mood",
    "s04": "a modern MLB stadium in 2015 with sleek radar units and cameras mounted around the stands, a baseball flying with a glowing measured trail, sense of a new tracking era beginning, bright optimistic tech mood",
    "s05": "technology handoff scene: on one side a radar dish device, on the other a multi-camera array like the ones used in tennis line-calling, glowing tracking lines morphing from a tennis-court style grid into a baseball diamond, clean conceptual composition",
    "s06": "electric KBO night game: a pitch flying toward home plate with a glowing rectangular strike-zone box lighting up around it as a tracking system judges the pitch, a home plate umpire with an earpiece raising his hand to call, futuristic automated umpire mood, dynamic",
    "s07": "a Korean baseball broadcast look: a home run replay over a night stadium with a bright glowing trajectory arc and abstract holographic data panels (no readable text) floating over the field, sleek TV graphics mood",
    "s08": "playful metaphor illustration split in two halves: on the left a smiling cartoon chef holding a blank glowing recipe scroll with only abstract chart icons (no words), on the right a smiling cartoon player presenting a wooden crate full of fresh glowing vegetables mixed with baseballs, contrasting a thinking-analysis side versus a raw-ingredients side, absolutely NO text, NO letters, NO words anywhere, clean cheerful cartoon",
    "s09": "high-speed capture concept: a baseball frozen in mid-air surrounded by dozens of overlapping camera-shutter frames and glowing scan lines radiating outward, an ultra-fast tracking feeling, techy energetic composition",
    "s10": "warm closing scene: a baseball resting on home plate at golden sunset with faint glowing data lines gently fading around it, an empty peaceful stadium behind, hopeful end-of-game mood",
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
