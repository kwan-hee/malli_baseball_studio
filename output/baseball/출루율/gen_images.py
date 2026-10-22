# 출루율 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
        "cartoon hook scene: a patient batter in a white and navy baseball uniform calmly watches four baseballs "
        "pass outside the strike zone without swinging, then trots confidently to first base on a walk, "
        "no home run swing just disciplined eye at the plate, bright packed stadium, generic face no real person, "
        "plain white first base NO numbers NO letters"
    ),
    "s02": (
        "cartoon concept: three ways to reach first base shown with colorful arrows — a solid hit ball to the field, "
        "a batter trotting after balls outside the zone, a batter rubbing arm after being hit by pitch — "
        "all paths lead to first base, bright instructive teaching mood, plain white base NO numbers NO text"
    ),
    "s03": (
        "cartoon teaching diagram WITHOUT any numbers or letters: on top row glowing baseballs and walking figures "
        "flow into a bright numerator area, on bottom row bat symbols balls and a small fly-ball icon flow into a "
        "denominator area, simple colorful arrows only, no digits no math symbols, clean educational layout"
    ),
    "s04": (
        "cartoon split comparison: LEFT side shows only bat hitting ball equals one path to first base labeled by "
        "color only no text, RIGHT side shows bat hits plus walking figure plus bumped batter all flowing to first "
        "base with more glowing paths, contrast between narrow and wide paths to first, bright field NO numbers"
    ),
    "s05": (
        "cartoon sacrifice fly concept: a deep fly ball caught by an outfielder while a runner tags up and scores "
        "at home plate, the batter is out but looks proud, a subtle visual hint that this out still counts against "
        "a stat using a downward red arrow on the batter side with NO text NO numbers, bright stadium"
    ),
    "s06": (
        "cartoon vintage 1950s concept: a thoughtful baseball executive in a suit pointing at charts with colored dots "
        "only no numbers, beside him a Korean baseball league founding celebration scene with 1980s retro uniforms "
        "and cheering crowd, warm nostalgic historical mood, generic faces NO text NO digits"
    ),
    "s07": (
        "cartoon legendary batters concept: two generic silhouetted hitters in different era uniforms side by side "
        "one in classic 1940s style one in 2000s KBO style both standing confidently on first base frequently, "
        "many small glowing footsteps leading to first base suggesting constant reaching base, NO faces NO numbers"
    ),
    "s08": (
        "cartoon moneyball concept split: LEFT a batter hits a single and arrives at first base, RIGHT another batter "
        "walks calmly to the same first base, both end at identical first base position emphasized with equal golden "
        "glow, teaching that both ways reach first equally, bright stadium generic faces NO text NO numbers"
    ),
    "s09": (
        "cartoon KBO eye-discipline scene: a focused batter in white and navy uniform refusing to swing at bad pitches "
        "outside the zone, many baseballs floating outside, then happily standing on first base, disciplined patient "
        "mood, bright LG-style white navy uniform colors only no logos no numbers, generic face NO text"
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
