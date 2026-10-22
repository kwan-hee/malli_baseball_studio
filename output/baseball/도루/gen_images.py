# 도루 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
        "cartoon dynamic baseball moment: a baserunner sprinting from first base and diving into second base with a "
        "headfirst slide in a big cloud of dust, safe, the pitcher throwing in the background, bright packed cheering "
        "stadium, generic faces no real person, plain white bases NO numbers NO letters"
    ),
    "s02": (
        "cartoon concept: a baserunner confidently stealing a base, dashing from one base toward the next with a bright "
        "glowing speed trail, emphasizing pure running speed with no hit needed, bright field, plain white bases "
        "NO numbers NO text"
    ),
    "s03": (
        "cartoon comparison WITHOUT symbols: on one side a runner cleanly stealing a base by his own sprint brightly "
        "highlighted, on the other side a ball skipping past the catcher letting a runner advance shown in a soft faint "
        "grey to mark it is NOT a steal, teaching the difference, bright field generic faces "
        "absolutely NO circle NO cross NO X mark NO numbers NO letters NO text"
    ),
    "s04": (
        "cartoon action: a baserunner taking a lead off first base then exploding into a sprint the instant the pitcher "
        "throws home, diving into the next base ahead of the throw with flying dust, dynamic speed, bright stadium, "
        "generic faces no real person, plain white bases NO numbers NO letters"
    ),
    "s05": (
        "cartoon concept: a runner at a base weighing whether to run, a bright green safe path on one side and a risky "
        "red path on the other, teaching that a high success rate matters before stealing, bright field generic face "
        "NO numbers NO text NO letters"
    ),
    "s06": (
        "cartoon action: a catcher firing a rocket throw as the second baseman catches it and tags out the sliding "
        "baserunner at second base, a very close tag play with flying dust, bright stadium, generic faces no real "
        "person, plain white bases NO numbers NO letters"
    ),
    "s07": (
        "cartoon concept: a nimble very fast runner zipping speedily around the bases outsmarting the defense, an "
        "energetic small-ball speed style, lively exciting mood, bright stadium generic face no real person "
        "NO numbers NO text"
    ),
    "s08": (
        "cartoon concept: a modern baseball base shown noticeably bigger than an old smaller base side by side, with a "
        "happy runner dashing off it, suggesting new rules that boosted base stealing, bright field generic face "
        "NO numbers NO text NO letters"
    ),
    "s09": (
        "cartoon highlight scene: a legendary lightning-fast baserunner in a bright uniform stealing a base with blazing "
        "speed trails and a triumphant record-setting slide, a cheering stadium crowd, generic face no real person, "
        "bright daytime stadium, plain white bases NO numbers NO letters"
    ),
    "s10": (
        "warm closing scene: a baseball base and a fielding glove resting on the infield dirt under calm evening stadium "
        "lights, a soft golden hopeful glow, peaceful satisfied end-of-story mood, NO numbers NO letters NO digits"
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
