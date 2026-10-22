# 타율 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 계산식·비교 주제라 AI가 숫자/기호 삽입 쉬움 → 수치·라벨 금지, 화살표·색·아이콘으로만 표현
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
    "bright cheerful cartoon illustration, clean bold outlines, friendly beginner-friendly sports composition, "
    "vivid warm colors, sunny baseball stadium mood, generic stylized faces, no real person likeness. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO labels, "
    "NO scoreboard digits, NO plus signs, NO X marks, NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": (
        "cartoon hook scene: a confident batter cleanly smacking a sharp line-drive base hit and sprinting toward first "
        "base with a bright determined smile, bright packed cheering stadium, generic face no real person, "
        "plain white bases NO numbers NO letters"
    ),
    "s02": (
        "cartoon concept: a friendly batter squarely connecting with the ball for a clean hit, a simple bright teaching "
        "mood suggesting hits per at-bats shown only with cheerful colorful icons and arrows, no digits, bright field "
        "generic face NO numbers NO text"
    ),
    "s03": (
        "cartoon concept WITHOUT symbols: on one side a batter hitting a ball is brightly highlighted as counted, on the "
        "other side a batter drawing a walk and trotting to first base is gently set aside in a soft faint grey area to "
        "show a walk is not counted in the batting-average tally, teaching walks are excluded, bright field generic faces "
        "absolutely NO circle NO cross NO X mark NO numbers NO letters NO text"
    ),
    "s04": (
        "cartoon concept: a batter beside a glowing three-step measuring gauge shown only as three ascending colored "
        "bars of light (no digits no letters), representing reading a batting average to three decimal places, clean "
        "bright teaching mood, bright stadium generic face NO numbers NO text NO letters"
    ),
    "s05": (
        "cartoon tier concept: a batter climbing an ascending glowing staircase of achievement, higher steps glowing "
        "brighter and grander suggesting ordinary, good and legendary hitting tiers by brightness only, celebratory "
        "admiring mood, bright stadium generic face no real person NO numbers NO text NO digits"
    ),
    "s06": (
        "cartoon vintage 1940s concept: a classic old-time baseball batter in a 1940s grey wool uniform smacking a clean "
        "hit with a proud legendary aura, warm sepia nostalgic tone, a packed vintage crowd behind, generic face no real "
        "person, NO numbers NO letters NO text"
    ),
    "s07": (
        "cartoon 1980s retro KBO concept: a batter in a retro early-1980s style baseball uniform smacking a beautiful "
        "clean hit with a triumphant once-in-history aura, a cheering old-time stadium crowd, warm proud mood, generic "
        "face no real person, bright stadium NO numbers NO letters NO text"
    ),
    "s08": (
        "cartoon concept: two batters from different eras standing proudly side by side, surrounded by many small glowing "
        "hit sparks trailing around them suggesting a long career of consistent hitting, warm admiring mood, generic "
        "faces no real person, bright stadium NO numbers NO text"
    ),
    "s09": (
        "cartoon concept: a single plain small hitting icon on the left being joined by two additional glowing pieces — "
        "one showing a runner reaching base and one showing a powerful long hit — all merging into one bigger bright "
        "combined glowing orb, teaching that batting average is just the basic piece of a bigger picture, bright field "
        "generic faces NO numbers NO text"
    ),
    "s10": (
        "warm closing scene: a baseball bat and ball resting on home plate under calm evening stadium lights, "
        "a soft golden hopeful glow, peaceful satisfied end-of-story mood, NO numbers NO letters NO digits"
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
                    print(f"{sid}: {len(img):,} bytes")
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
