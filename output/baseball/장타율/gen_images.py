# 장타율 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
        "cartoon hook split scene: LEFT a batter hits a short soft single and stops at first base with a small tap, "
        "RIGHT another batter smashes a towering home run far over the outfield fence with a bright powerful impact, "
        "same batting average but hugely different power, bright packed stadium, generic faces no real person, "
        "plain white bases NO numbers NO letters"
    ),
    "s02": (
        "cartoon concept: a batter swinging powerfully and the ball rocketing deep into the outfield, "
        "glowing base-path markers lighting up many bases gained, emphasizing average bases per at-bat, "
        "a sense of measuring the weight of each hit, bright field powerful mood, NO numbers NO text"
    ),
    "s03": (
        "cartoon teaching WITHOUT any numbers or letters: four escalating hits shown by growing colored base-path "
        "lengths — a single reaching one base, a double two bases, a triple three bases, and a home run circling all "
        "four bases around the diamond, growing glowing arrows around the infield, no digits no letters no symbols"
    ),
    "s04": (
        "cartoon split comparison WITHOUT text: LEFT a batting-average view where a single and a home run appear as "
        "two identical plain baseballs of equal size, RIGHT a slugging view where the home run glows about four times "
        "larger and brighter than the single, contrast of equal versus weighted value, bright field NO numbers NO text"
    ),
    "s05": (
        "cartoon vintage 1860s baseball history scene: a distinguished gentleman in a Victorian-era suit with a bowler hat "
        "studying baseball records at a wooden desk, old-fashioned baseball field in the background with players in "
        "classic 19th century uniforms, warm nostalgic sepia-toned mood, generic face NO text NO numbers NO digits"
    ),
    "s06": (
        "cartoon tier concept: three escalating levels of slugger power shown by glow intensity only — a modest "
        "batter with a small aura at bottom, a strong batter with a medium bright aura in the middle, and a dominant "
        "slugger radiating a massive golden power aura at the top, bright stadium NO text NO numbers NO digits"
    ),
    "s07": (
        "cartoon KBO highlight scene: a powerful slugger in a light sky-blue baseball uniform crushing a gigantic "
        "home run deep into a cheering stadium crowd, a triumphant record-breaking swing with a bright impact and "
        "soaring ball, generic face no real person, bright daytime stadium, plain white bases NO numbers NO letters"
    ),
    "s08": (
        "cartoon legendary MLB scene: a powerful vintage-era slugger in classic pinstripe uniform hitting a mammoth "
        "home run that soars far beyond the stadium walls with a dramatic impact trail, an awe-inspiring untouchable "
        "record-setting mood, warm golden lighting, generic face NO text NO numbers NO digits"
    ),
    "s09": (
        "cartoon concept: a batter at the plate with a glowing power meter beside him — the meter shows slugging power "
        "minus a smaller batting average bar peeled away, revealing the pure isolated extra-base power underneath, "
        "bright instructive teaching mood, clean composition NO text NO numbers NO digits"
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
