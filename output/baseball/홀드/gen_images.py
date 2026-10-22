# 홀드 — 씬 삽화 10장 생성 (Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
        "cartoon dramatic hook scene: a relief pitcher bursting out of the bullpen gate sprinting toward "
        "the mound under bright stadium lights, the starting pitcher walking off exhausted with head down, "
        "runners on base looking tense, the stadium crowd buzzing with anticipation, fiery determined expression "
        "on the reliever, generic faces no real person, "
        "absolutely NO text NO numbers NO letters"
    ),
    "s02": (
        "cartoon concept scene: a heroic middle reliever standing tall on the mound like a firefighter, "
        "metaphorical small flames on the bases being extinguished, a baton handoff visual between two relievers "
        "suggesting teamwork relay, bright warm stadium mood, "
        "generic faces NO numbers NO text NO letters"
    ),
    "s03": (
        "cartoon teaching scene showing four condition panels: top-left a scoreboard showing a narrow lead "
        "with no digits just colored bars, top-right a batter being struck out suggesting one out minimum, "
        "bottom-left a reliever walking off with a thumbs up suggesting lead maintained, bottom-right another "
        "pitcher taking the mound suggesting no game finish, bright educational layout, "
        "generic faces NO numbers NO text NO letters"
    ),
    "s04": (
        "cartoon comparison scene split into three sections with visual dividers: left section a closer "
        "celebrating on the mound after the final out with confetti suggesting save, middle section a reliever "
        "high-fiving the next pitcher coming in suggesting hold, right section a dejected pitcher with opposing "
        "runners crossing home plate suggesting blown save, three clear outcomes side by side, "
        "generic faces NO numbers NO text NO letters"
    ),
    "s05": (
        "cartoon historical scene set in a 1980s retro office: two enthusiastic statisticians in glasses and "
        "suspenders sitting at a desk covered with baseball scoresheets and early computer monitors, one pointing "
        "excitedly at a chart showing a new statistic concept, warm nostalgic lighting, vintage baseball posters "
        "on the wall, NO text NO numbers NO letters NO readable documents"
    ),
    "s06": (
        "cartoon ironic contrast scene split in two halves: left half showing an American MLB stadium with a "
        "confused shrugging umpire suggesting the stat is not official, right half showing a Korean KBO stadium "
        "with a proud official holding up a golden trophy or certificate suggesting official recognition, "
        "bright contrasting mood, generic faces NO numbers NO text NO letters"
    ),
    "s07": (
        "cartoon epic celebration scene: a veteran pitcher in a dark navy uniform on the mound pumping his fist "
        "triumphantly, teammates rushing from the dugout and bullpen to congratulate him, bright golden spotlight "
        "from above suggesting a historic record-breaking moment, packed night stadium with fans cheering, "
        "emotional proud expression, generic faces no real person, "
        "absolutely NO text NO numbers NO letters"
    ),
    "s08": (
        "cartoon emotional storytelling scene: a montage of three stages of a pitcher's career, left showing "
        "a young pitcher sadly packing his bag being released from a team, middle showing the same pitcher "
        "training alone on an empty field with determination, right showing an older veteran pitcher triumphantly "
        "on the mound with teammates celebrating around him, journey from rejection to glory, "
        "generic faces NO numbers NO text NO letters"
    ),
    "s09": (
        "cartoon intense action scene: a dominant setup reliever on the mound throwing a powerful pitch with "
        "motion blur speed lines, batters swinging and missing one after another, a long line of defeated batters "
        "walking back to the dugout suggesting many games of dominance, fiery competitive mood, "
        "bright stadium generic faces NO numbers NO text NO letters"
    ),
    "s10": (
        "warm closing scene: a baseball bullpen phone hanging on the wall under calm evening stadium lights, "
        "a row of relievers sitting ready on the bullpen bench looking confident, soft golden hopeful glow, "
        "peaceful satisfied end-of-story mood, "
        "NO numbers NO letters NO digits"
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
