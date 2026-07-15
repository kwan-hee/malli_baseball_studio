# 말리와 콩쥐팥쥐 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
KONGJWI = (
    "a kind sweet Korean girl named Kongjwi around 10 years old with neat black hair in a low braid, "
    "wearing a simple patched pale-yellow and green hanbok, warm gentle smile, rosy cheeks"
)
PATJWI = (
    "a pouty spoiled Korean girl named Patjwi around 10 years old with two round hair buns, "
    "wearing a fancy bright pink and red hanbok, sulky comical expression, funny NOT scary"
)
STEPMOM = (
    "a haughty Korean stepmother in an elaborate purple hanbok with a tall hairdo, "
    "nose in the air, comically snobby expression, funny NOT scary"
)
MAGISTRATE = (
    "a kind dignified Korean magistrate (wonnim) in a blue official hanbok robe and black gat hat, "
    "gentle warm face"
)
HOUSE = "a humble Korean thatched-roof cottage (chogajip) with a small dirt yard, wooden fence and persimmon tree"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer on a sunny village path in old Korea, thatched-roof cottages and low stone walls behind her, a single pretty embroidered flower shoe (kkotsin) sparkling on a flat stone beside the path, bright curious storybook morning mood, {NO_TEXT}, {STYLE}",
    "s02": f"{KONGJWI} cheerfully carrying a wooden water pail in the dirt yard of {HOUSE}, while {STEPMOM} and {PATJWI} lounge comfortably on the wooden porch fanning themselves and pointing at chores, laundry and firewood piled around, morning light, diligent but unfair mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"gentle magical moment: {KONGJWI} kneeling surprised beside a big brown earthenware jar (hangari) with water leaking from a hole at its bottom, a friendly big green toad with kind eyes pressing itself against the hole to plug it, sparkling water drops, backyard of {HOUSE}, hopeful warm mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"joyful helping scene: a lively flock of small brown sparrows swirling around {KONGJWI} in the yard husking a big mound of rice grains with their beaks, while a large gentle black ox pulls a wooden plow across the field behind her, {KONGJWI} laughing with open arms, straw baskets, golden afternoon light, lively grateful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on a low stone wall by the village path with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, sparrows perched in a row on the wall next to her looking at her, warm afternoon glow, playful wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"magical gift moment in the yard of {HOUSE}: {KONGJWI} gasping with delight at a beautiful jade-green silk hanbok dress and a pair of pretty embroidered flower shoes (kkotsin) laid neatly on a wooden bench glowing softly, the friendly toad, sparrows and black ox gathered proudly around her, gentle sparkles in the air, touched happy mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"climax moment: {KONGJWI} in her beautiful jade-green silk hanbok crossing stepping stones over a clear stream, one pretty embroidered flower shoe slipping off her foot in mid-air falling toward the water with a splash beginning, her hand reaching out in surprise with wide eyes, sparkling stream and dragonflies, dynamic storybook moment, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"warm scene at a festive village feast with colorful cloth canopies and lanterns: {MAGISTRATE} kneeling politely and fitting the pretty embroidered flower shoe onto {KONGJWI}'s foot as it fits perfectly with gentle sparkles, {PATJWI} nearby puffing her cheeks comically holding her own too-big foot, villagers smiling around, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"heartwarming reconciliation at the village feast under paper lanterns: {STEPMOM} and {PATJWI} bowing their heads with genuinely sorry gentle expressions — soft apologetic eyes, embarrassed blushing cheeks, small sad remorseful smiles, absolutely NOT angry, NOT scowling, NOT frowning, NOT pouting — while {KONGJWI} in her jade-green hanbok warmly holds their hands smiling brightly and forgivingly, villagers dancing gently in the background, festive tables with fruit, forgiving joyful evening mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the village path at sunset, the festive feast with glowing lanterns and dancing villagers small in the distance behind her, a pair of pretty embroidered flower shoes placed neatly on the stone wall beside her glowing softly, golden evening light, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
