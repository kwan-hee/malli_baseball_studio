# 삼진 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
        "cartoon dramatic strikeout hook: a batter swinging hard and completely whiffing on strike three while the "
        "catcher catches the ball in his mitt, the batter's head lowered in defeat, a pumped-up pitcher in the "
        "background, bright packed cheering stadium, generic faces no real person, plain white home plate, "
        "absolutely NO sound-effect text, NO onomatopoeia words, NO letters, NO numbers, NO text"
    ),
    "s02": (
        "cartoon concept: on one side a triumphant pitcher pumping his fist after a strikeout, on the other side a "
        "batter walking away with his head down, the same moment seen two ways, bright field generic faces "
        "NO numbers NO text"
    ),
    "s03": (
        "cartoon comparison WITHOUT text: on one side a batter swinging and missing the ball wildly (a swinging "
        "strikeout), on the other side a batter standing frozen with the bat still on his shoulder as the umpire calls "
        "him out (a looking strikeout), teaching two kinds of strikeout, bright field generic faces NO numbers NO letters"
    ),
    "s04": (
        "cartoon concept: a batter squaring to bunt and tapping the ball into foul territory with a small puff near the "
        "foul line while the umpire signals him out, teaching a two-strike bunt foul is an out, bright field generic "
        "face NO numbers NO text NO letters"
    ),
    "s05": (
        "cartoon action: a catcher fumbling and dropping the third-strike ball with a small puff while the batter dashes "
        "toward first base, teaching a dropped third strike lets the batter run, bright stadium generic faces "
        "NO numbers NO letters"
    ),
    "s06": (
        "cartoon lively scene: a stadium crowd cheering wildly as a happy pitcher celebrates a strikeout, and in the "
        "foreground a comically dejected batter sitting and wearing an oversized golden sombrero hat as a lighthearted "
        "gag, a small pile of baseballs nearby, bright fun mood, generic faces no real person, "
        "absolutely NO letter K, NO letters, NO numbers, NO text, NO symbols anywhere"
    ),
    "s07": (
        "cartoon concept: a dominant power pitcher on the mound radiating a strong fiery aura, glowing abstract tally "
        "sparks trailing behind him suggesting many strikeouts (no digits no letters), triumphant powerful mood, bright "
        "stadium generic face no real person NO numbers NO text"
    ),
    "s08": (
        "cartoon concept: a blazing fastball rocketing toward home plate with bright speed lines while a batter takes a "
        "huge full power swing, suggesting modern fast pitching and big swings, energetic dynamic mood, bright stadium "
        "generic faces no real person NO numbers NO text"
    ),
    "s09": (
        "cartoon highlight scene: a dominant power pitcher in a light sky-blue baseball uniform hurling a blazing fastball "
        "for a record-breaking strikeout as the crowd erupts in celebration, a triumphant record moment, generic face no "
        "real person, bright daytime stadium, plain white home plate NO numbers NO letters"
    ),
    "s10": (
        "warm closing scene: a baseball and a catcher's mitt resting on home plate under calm evening stadium lights, "
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
