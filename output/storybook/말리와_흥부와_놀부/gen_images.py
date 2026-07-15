# 말리와 흥부와 놀부 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게 (최종 출력은 720p — compose가 축소)

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
HEUNGBU = (
    "a kind gentle Korean man named Heungbu around 35 years old with a warm humble smile, "
    "wearing a simple patched beige traditional hanbok and a small topknot (sangtu)"
)
NOLBU = (
    "a plump greedy Korean man named Nolbu around 40 years old with a scraggly thin mustache, "
    "wearing a fancy shiny navy-and-gold silk hanbok, comically grumpy sulky expression, funny NOT scary"
)
WIFE = "Heungbu's kind wife in a plain worn jade hanbok with a gentle face"
KIDS = "two cheerful little Korean children in simple patched hanbok"
SWALLOW = "a small cute swallow bird with glossy dark-blue back, white belly and forked tail"
POORHOUSE = "a small humble Korean thatched-roof cottage (chogajip) with a low wooden fence"
RICHHOUSE = "a large fancy Korean tile-roofed house (giwajip) with a tall wooden gate"
GOURD = "a huge round pale-green gourd (bak)"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer on a sunny old-Korea village path, a cute swallow flying above her carrying a tiny seed in its beak, thatched cottages and a big tile-roofed house in the background, huge pale-green gourds resting on a thatched roof, bright curious storybook morning mood, {NO_TEXT}, {STYLE}",
    "s02": f"contrast scene in old Korea: {NOLBU} standing with arms crossed and nose in the air in front of {RICHHOUSE}, while {HEUNGBU} bows politely with a warm smile beside {KIDS} in front of {POORHOUSE} across the path, morning light, comical but warm sibling-contrast mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"tender moment under the eaves of {POORHOUSE}: {HEUNGBU} kneeling and gently wrapping a tiny cloth bandage around the leg of a small baby swallow held softly in his hands, {WIFE} and {KIDS} watching with caring worried faces, a swallow nest above under the eaves, soft warm light, gentle healing mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"joyful spring return: {SWALLOW} swooping down through blue sky toward the yard of {POORHOUSE} carrying a small gourd seed in its beak, {HEUNGBU}, {WIFE} and {KIDS} below reaching up with delighted faces, spring blossoms drifting, dynamic hopeful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on a low stone wall by the village path with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, a cute swallow perched on the wall right next to her tilting its head, giant pale-green gourds on the thatched roof behind, warm afternoon glow, playful wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"climax celebration in the yard of {POORHOUSE}: {HEUNGBU} and {WIFE} sawing {GOURD} split wide open with treasure bursting out — glittering gold coins, jewels, silk rolls and sacks of rice spilling everywhere with warm sparkles, {KIDS} jumping with joy, magical golden light, jubilant mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"comedy moment in the yard of {RICHHOUSE}: {NOLBU} clumsily wrapping a long bandage around a perfectly healthy confused swallow that tilts its head with big puzzled eyes, bandage tangled everywhere comically, {NOLBU} grinning slyly, silly mischievous mood, funny NOT cruel, the swallow is NOT hurt, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"quiet lesson moment in the yard of {RICHHOUSE} at dusk: {NOLBU} sitting deflated beside his own {GOURD} split open and completely empty with only puffs of grey dust drifting out, his head bowed with teary remorseful eyes, soft twilight, gentle remorse mood, NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"heartwarming reconciliation feast under glowing paper lanterns: {HEUNGBU} warmly holding the hands of a PLUMP heavy-set MIDDLE-AGED Korean man named Nolbu around 40 years old (NOT old, NOT elderly, NOT grey-haired) with BLACK hair in a small topknot (sangtu), a scraggly thin black mustache, round chubby cheeks and a big belly, wearing his fancy navy-and-gold silk hanbok, Nolbu's face is soft and touched — gently RAISED soft eyebrows, moist grateful teary eyes, a small warm thankful smile, embarrassed blushing cheeks, his whole expression humble and moved, absolutely NO furrowed brows, NO scowl, NO frown, NO pout, sacks of rice and silk rolls being shared between them, {WIFE} and {KIDS} dancing gently behind, festive tables with fruit, forgiving joyful evening mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the old-Korea village path at sunset, behind her in the distance a humble Korean thatched-roof cottage (chogajip) and a Korean tile-roofed house (giwajip) side by side glowing with warm lantern light — traditional KOREAN houses only, absolutely NO European or Western houses — swallows flying across the golden sky, a small gourd seed sprouting a tiny green shoot on the low stone wall beside her, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
