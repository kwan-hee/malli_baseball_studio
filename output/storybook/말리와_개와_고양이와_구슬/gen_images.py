# 말리와 개와 고양이와 구슬 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 첨부 + 지브리 스타일 고정: ghibli_scene_ref.png(스타일 앵커) 첨부
# STYLE 문구는 C:/PROJECT/prompts/ghibli_style.txt 단일 출처 (2026-07-12 스타일 필수화)
import base64
import sys
import time
from pathlib import Path

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, r"C:\youtube_longform_agent")
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

REF = Path(r"C:\PROJECT\images\style_ref\malli_reference.png")          # 캐릭터 시트
STYLE_REF = Path(r"C:\PROJECT\images\style_ref\ghibli_scene_ref.png")   # 지브리 스타일 앵커(사용자 제공)
STYLE = Path(r"C:\PROJECT\prompts\ghibli_style.txt").read_text(encoding="utf-8").strip()  # 단일 출처

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
DOG = (
    "a cheerful sturdy golden-yellow Korean Jindo dog named Nureongi with a friendly smile, "
    "perky ears and a small blue neckerchief, clearly a DOG much bigger than the cat, NOT a puppy like Malli"
)
CAT = "a dainty elegant white cat with soft grey tabby patches, bright green eyes and a tiny pink ribbon on one ear"
FOX = "a mischievous comical orange fox with a sneaky playful grin, cartoonish and funny, NOT scary"
MICE = "small cute friendly grey mice with round ears and tiny pink noses"
GRANDPARENTS = "a kind elderly Korean grandfather and grandmother in cozy traditional hanbok, warm gentle smiles"
ORB = "a glowing magical pearl orb shimmering with soft golden light"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer on a sunny riverside village path with traditional Korean hanok houses and a wide sparkling river behind her, a few golden sparkles drifting in the air, bright playful treasure-hunt morning mood, {STYLE}",
    "s02": f"{GRANDPARENTS} sitting happily on the wooden porch of a cozy hanok house, {DOG} and {CAT} sitting side by side in the sunny yard, between them {ORB} on a small cushion, an overflowing rice jar and a persimmon tree with plump orange persimmons nearby, warm abundant happy mood, {NO_MALLI}, {STYLE}",
    "s03": f"moonlit night at the hanok yard: {FOX} tiptoeing away along the top of a low stone wall clutching {ORB}, while {DOG} and {CAT} notice him from the porch with wide surprised eyes, comical caper mood, deep blue night with warm lantern light, {NO_MALLI}, {STYLE}",
    "s04": f"{CAT} riding on the back of {DOG} as he swims bravely across a wide sparkling river, gentle splashes around them, both looking ahead with determined adorable faces, far bank with trees ahead, warm daylight, dynamic diagonal composition, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} crouching behind a leafy bush near the riverbank, one paw raised to her mouth in a cute shushing gesture, looking toward a funny fox den built under tree roots across a clearing in the distance, playful sneaky evening mood, {STYLE}",
    "s06": f"in front of a fox den under big tree roots, several {MICE} rolling {ORB} out through a narrow gap at the bottom of a wooden door toward {DOG} and {CAT} who wait with delighted faces, teamwork moment, soft twilight, {NO_MALLI}, {STYLE}",
    "s07": f"dramatic moment mid-river: {CAT} on the swimming {DOG}'s back with her mouth open in shock as {ORB} falls from her mouth into the river making a splash with ripple rings, both wide-eyed in comical panic, water sparkling, the dog MUST have upright perky triangular ears and the same Jindo face as in other scenes (NOT floppy ears, NOT a retriever), {NO_MALLI}, {STYLE}",
    "s08": f"on the riverbank, {DOG} and {CAT} looking amazed at a plump friendly fish whose round belly glows with warm golden light, {ORB} revealed shining beside it, joyful relieved discovery moment, sunset sparkle on the water, {NO_MALLI}, {STYLE}",
    "s09": f"warm night at the hanok yard: {GRANDPARENTS} hugging {DOG} and {CAT} tightly with happy tears, {ORB} glowing softly on the porch lighting the whole yard, persimmon tree silhouette and starry sky above, heartwarming reunion, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the riverside under a starry night sky, with {DOG} and {CAT} sitting close together like best friends behind her watching the stars, {ORB} glow on the horizon, peaceful happy ending mood, {STYLE}",
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
