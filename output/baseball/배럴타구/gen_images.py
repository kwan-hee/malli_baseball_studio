# 배럴타구 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 데이터 지표(그래프·각도·수치) 주제라 AI가 영문/숫자 텍스트를 넣기 쉬움 → 텍스트 금지 강하게 명시
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
    "vivid colors, high-tech data visualization mood, glowing neon tracking lines, "
    "generic stylized faces, no real person likeness. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO scoreboard, NO chart labels anywhere in the image"
)

SCENES = {
    "s01": "dramatic night game: a cartoon batter making perfect contact, the baseball exploding off the thick barrel of the bat with a bright glowing impact flash and a brilliant curved glowing trajectory line rocketing into the sky, packed cheering crowd, stadium lights, high-energy broadcast mood",
    "s02": "concept illustration: a single baseball flying along a glowing optimal arc that lands as a clean hit, a translucent holographic data-graph glow (curves and glowing dots only, no labels) framing the trajectory, futuristic 'best possible hit' mood, neon tracking lines",
    "s03": "a joyful cartoon batter watching a towering deep hit sail away, a burst of glowing golden success aura, several baseballs turning into glowing hit-streaks across the field, upbeat celebratory mood",
    "s04": "a cartoon data analyst sitting at a glowing computer surrounded by floating holographic baseball trajectory graphs and arcs (curves and dots only, no labels), a bright eureka glow on his face as he discovers a pattern, techy discovery mood",
    "s05": "clean concept diagram: a baseball launching off a bat at an upward angle with a glowing wedge shape between the ball's path and the ground line marking the launch angle, bright speed lines behind the ball showing exit velocity, minimal techy composition, NO numbers, NO labels",
    "s06": "concept illustration of an expanding range: a hard bat impact with multiple glowing trajectory lines fanning out from low to high, a glowing angle wedge visibly widening, showing how the acceptable window grows, neon energetic tech mood, NO numbers",
    "s07": "split venn-diagram style illustration on a plain solid dark-blue gradient background: on the left a glowing muscular flexing-arms power symbol inside a glowing circle, on the right a glowing bullseye precision target symbol inside a glowing circle, the two circles overlapping in the middle into one bright glowing baseball, contrasting raw power versus precision. Plain clean background only, NO circuit board patterns, NO binary code, NO digits, absolutely NO text, NO letters, NO words, NO numbers",
    "s08": "explosive home run: a powerful cartoon slugger finishing a huge swing as the baseball rockets high into the night sky with a bright glowing trail, roaring packed crowd, giant stadium lights, epic power-hitter mood, generic stylized face, no real person likeness",
    "s09": "split contrast illustration: on the left a big stadium with many glowing barrel-hit trajectory lines everywhere, on the right another stadium with only one or two faint glowing hit lines, visually showing that barrels are far rarer on one side, clean conceptual composition, NO text, NO numbers",
    "s10": "warm closing scene: a baseball bat resting across home plate at golden sunset with the thick barrel sweet-spot gently glowing, faint fading trajectory lines in the background, an empty peaceful stadium, hopeful end-of-game mood",
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
