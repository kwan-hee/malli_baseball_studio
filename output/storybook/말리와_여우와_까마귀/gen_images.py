# 말리와 여우와 까마귀 — 씬 이미지 10장 생성 (지브리 스타일)
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
CROW = "a large glossy black crow with bright intelligent eyes, holding a wedge of golden cheese in its beak, cartoon storybook style"
CROW_NO_CHEESE = "a large glossy black crow with bright intelligent eyes, cartoon storybook style"
FOX = "a sly orange-red fox with a fluffy tail, clever sparkling eyes, friendly but cunning smile, cartoon storybook style"
TREE = "a tall leafy oak tree in a sunny meadow with wildflowers, bright blue sky with white clouds"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully in a sunny meadow with a tall oak tree and wildflowers, a black crow perched on a branch above and a fox peeking from behind a bush, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"scene in a sunny meadow: {CROW} sitting proudly on top of a {TREE}, holding a big wedge of golden cheese in its beak, looking very happy and satisfied, bright cheerful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"scene under a {TREE}: {FOX} looking up at the crow on the tree branch, licking its lips hungrily, eyes fixed on the cheese, scheming cunning expression, one paw on chin thinking, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"scene under a {TREE}: {FOX} standing below looking up with an exaggerated admiring expression, gesturing with both paws, flattering the crow above, {CROW} on the branch puffing up its feathers proudly, pleased expression, warm golden light, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"scene under a {TREE}: {FOX} clasping paws together pleadingly looking up, {CROW} on the branch puffing chest out proudly with cheese still in beak, eyes closed smugly, about to sing, anticipation mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s06": f"dramatic action scene under a {TREE}: {CROW_NO_CHEESE} on the branch with beak wide open squawking, a wedge of golden cheese falling through the air tumbling down, {FOX} below looking up with excited eager eyes, dynamic composition showing the cheese mid-fall, surprising moment, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"emotional scene under a {TREE}: {FOX} holding the cheese in its mouth looking back over its shoulder, {CROW_NO_CHEESE} on the branch above drooping its head sadly with slumped wings, regretful melancholy mood, soft evening light, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"heartwarming scene in a meadow: {FOX} offering half a piece of cheese to {CROW_NO_CHEESE} who is coming down from the tree, fox looking apologetic and sincere, warm reconciliation mood, golden sunset light, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"happy scene in a meadow: {FOX} and {CROW_NO_CHEESE} sitting side by side on the grass, each eating a piece of cheese together, smiling at each other, friendship and harmony, warm cozy sunset mood, wildflowers around them, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly in the sunny meadow with the tall oak tree behind, the fox and crow visible in the background sitting together happily, peaceful happy ending mood, sunset sky, {NO_TEXT}, {STYLE}",
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
