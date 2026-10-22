# 말리와 아기 돼지 삼형제 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 첨부 + 지브리 스타일 고정: ghibli_scene_ref.png(스타일 앵커) 첨부
# STYLE 문구는 C:/PROJECT/prompts/ghibli_style.txt 단일 출처 (2026-07-12 스타일 필수화)
import base64
import sys
import time
from pathlib import Path

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

REF = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/malli_reference.png"))          # 캐릭터 시트
STYLE_REF = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/ghibli_scene_ref.png"))   # 지브리 스타일 앵커(승인 프레임)
STYLE = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "prompts/ghibli_style.txt")).read_text(encoding="utf-8").strip()  # 단일 출처

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
PIG1 = "the eldest little pig, a cute chubby pink piglet wearing a yellow straw hat"
PIG2 = "the second little pig, a cute chubby pink piglet wearing a blue cap"
PIG3 = "the youngest little pig, a cute chubby pink piglet wearing red overalls, with a diligent kind face"
PIGS = f"the three little pig brothers ({PIG1}, {PIG2}, and {PIG3})"
MOM = "a gentle mother pig wearing a flower-patterned apron, warm loving face"
WOLF = (
    "a big grey wolf with hugely puffed-up cheeks, comically huffing and puffing, "
    "silly goofy expression, NOT scary, more funny than frightening"
)
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer on a bright sunny green meadow path, three tiny houses visible far in the background (one straw, one wooden, one red brick), cheerful hopeful morning mood, {STYLE}",
    "s02": f"{MOM} waving goodbye at the door of a cozy countryside cottage while {PIGS} walk away down a sunny path carrying small bundles on sticks, waddling cheerfully, warm morning light, {NO_MALLI}, {STYLE}",
    "s03": f"{PIG1} quickly building a small house out of yellow straw on a sunny meadow, straw pieces flying playfully in the air, the pig looking carefree and eager to play, half-finished straw hut, {NO_MALLI}, {STYLE}",
    "s04": f"{PIG2} hammering wooden planks together building a small wooden house, while {PIG1} plays and rolls on the grass nearby next to his finished straw house, sunny cheerful afternoon, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} watching curiously from the side of the path as {PIG3} pushes a heavy wooden cart full of red bricks uphill, sweating but smiling with determination, in the far background the two other pigs play together, warm afternoon light, {STYLE}",
    "s06": f"{PIG3} standing proudly in front of his finished sturdy red brick house with a neat chimney, wiping sweat from his forehead with a happy proud smile, golden sunset light, {NO_MALLI}, {STYLE}",
    "s07": f"{WOLF} blowing a huge gust of wind at a small straw house, straw flying everywhere in a whirlwind, while {PIG1} dashes away comically toward a wooden house in the distance, dynamic funny scene, {NO_MALLI}, {STYLE}",
    "s08": f"{WOLF} blowing hard at a small wooden house that is wobbling and falling apart with planks toppling over, while {PIG1} and {PIG2} dash away comically toward a red brick house in the distance, eyes wide, dynamic and funny, {NO_MALLI}, {STYLE}",
    "s09": f"{WOLF} lying dizzy and exhausted on the ground in front of a completely intact sturdy red brick house, cheeks deflated, swirls above his head, while {PIGS} cheer happily and hug each other at the brick house window, hilarious triumphant scene, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly in front of the cozy red brick house at sunrise, with {PIGS} standing together happily at the doorway behind her, soft warm morning colors, peaceful happy ending mood, {STYLE}",
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
        "same red bow ON TOP OF HER HEAD, same pink collar, same gold bone tag, same dark eyes. There is exactly ONE Malli - never duplicate her, never show two similar puppies. "
        "The SECOND attached image is the STYLE REFERENCE: you MUST match its art style EXACTLY — "
        "same Ghibli cel animation look, same lineart, same background painting style, same palette. "
        f"Scene: {scene}. "
        f"Aspect ratio 16:9, resolution {W}x{H}."
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
                model=model,
                contents=contents,
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
                    client = pool.rotate()  # 키 소진 → 다음 계정으로
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed - stop, report to user")

print("ALL DONE")
