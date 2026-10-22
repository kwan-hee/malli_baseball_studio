# 말리와 양치기 소년 — 씬 이미지 10장 생성 (지브리 스타일)
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

REF = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/malli_reference.png"))
STYLE_REF = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/ghibli_scene_ref.png"))
STYLE = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "prompts/ghibli_style.txt")).read_text(encoding="utf-8").strip()

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"
W, H = 1920, 1080

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
BOY = "a young cheerful cartoon shepherd boy with messy brown hair, a simple tunic and a wooden staff, generic friendly face, cartoon storybook style"
SHEEP = "a flock of cute fluffy white cartoon sheep with big round eyes on a green grassy hillside"
WOLF = "a large cartoon wolf with big yellow eyes and sharp teeth, comically menacing but NOT terrifying for children, cartoon storybook style"
VILLAGERS = "a group of friendly cartoon villagers with pitchforks and hoes, worried concerned faces, simple country clothes, cartoon storybook style"
HILL = "a sunny green rolling hillside with wildflowers, a small village with thatched roofs visible in the valley below"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop with a bright blue sky and white fluffy sheep in the background, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"scene on a {HILL}: the {BOY} sitting among {SHEEP}, looking bored and restless, chin on his hand, yawning, peaceful but lonely mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"scene on a {HILL}: the {BOY} standing up and shouting with cupped hands, panicked expression but actually grinning mischievously, the {SHEEP} behind him look calm, below the hill {VILLAGERS} running up urgently with tools, dramatic but playful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"scene on a {HILL}: the {BOY} laughing hard holding his belly, the {VILLAGERS} standing around looking annoyed and exasperated with no wolf anywhere, the {SHEEP} grazing peacefully, frustrated comical mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"scene on a {HILL}: the {BOY} shouting again with cupped hands, below the hill {VILLAGERS} reluctantly climbing up looking angry, one villager shaking a fist, the {SHEEP} grazing calmly, tense annoyed mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s06": f"tense dramatic scene at the edge of a dark forest near a {HILL}: {WOLF} emerging from shadowy trees with glowing yellow eyes and bared teeth, creeping toward the {SHEEP}, the {BOY} frozen in fear with wide eyes, suspenseful mood but NOT too scary for children, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"emotional scene on a {HILL}: the {BOY} desperately shouting and waving arms for help, tears in his eyes, below in the village the {VILLAGERS} turn away shaking their heads dismissively, nobody coming, lonely desperate mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"action scene on a {HILL}: {WOLF} chasing the {SHEEP} who scatter in all directions bleating, the {BOY} running down the hill crying with tears streaming, chaotic urgent mood but NOT violent, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"heartwarming resolution scene on a {HILL}: the {VILLAGERS} chasing away the {WOLF} who flees into the forest, all {SHEEP} safe and gathered, the {BOY} kneeling and crying apologetically while a kind villager pats his head forgivingly, warm reconciliation mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop with the {SHEEP} and the village behind under a sunset sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
}

pool = GeminiPool()
client = pool.client()
ref_bytes = REF.read_bytes()
style_bytes = STYLE_REF.read_bytes()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue
    prompt = (
        "CRITICAL: The FIRST attached image is the OFFICIAL Malli character reference sheet. "
        "When Malli appears you MUST reproduce her appearance EXACTLY as shown — same cream fur, "
        "same red bow ON TOP OF HER HEAD, same pink collar, same gold bone tag, same dark eyes. "
        "There is exactly ONE Malli - never duplicate her, never show two similar puppies. "
        "The SECOND attached image is the STYLE REFERENCE: you MUST match its art style EXACTLY — "
        "same Ghibli cel animation look, same lineart, same background painting style, same palette — "
        "but NEVER copy or include any characters from the style reference. "
        f"Scene: {scene}. "
        f"WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall, "
        f"aspect ratio 16:9, resolution {W}x{H}."
    )
    contents = [
        types.Part(inline_data=types.Blob(data=ref_bytes, mime_type="image/png")),
        types.Part(inline_data=types.Blob(data=style_bytes, mime_type="image/png")),
        types.Part(text=prompt),
    ]
    for attempt in range(4):
        model = MODEL if attempt < 2 else FALLBACK_MODEL
        try:
            resp = client.models.generate_content(
                model=model, contents=contents,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
            done = False
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    data = part.inline_data.data
                    img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                    out.write_bytes(img)
                    print(f"{sid}: {len(img):,} bytes ({model})")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part in response")
        except Exception as e:
            err = str(e)
            print(f"{sid}: attempt {attempt+1} failed - {type(e).__name__}: {err[:120]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed - stop")

print("ALL DONE")
