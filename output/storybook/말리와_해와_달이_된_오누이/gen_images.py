# 말리와 해와 달이 된 오누이 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
BROTHER = (
    "a brave Korean boy around 8 years old with short black hair, "
    "wearing a simple navy vest over a beige traditional hanbok, alert clever eyes"
)
SISTER = (
    "a sweet little Korean girl around 6 years old with black hair in two small buns, "
    "wearing a colorful striped saekdong jeogori hanbok with a pink skirt, round rosy cheeks"
)
MOM = "a kind Korean mother in a plain jade hanbok carrying a big woven basket on her head"
TIGER = (
    "a big plump comical tiger with orange fur and bold black stripes, huge round goofy eyes, "
    "slightly clumsy and greedy but funny NOT scary, cartoon-friendly fangs never bared aggressively"
)
COTTAGE = "a small humble Korean thatched-roof cottage (chogajip) deep in misty green mountains with a big old tree in the yard"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a mountain path at dusk, above her in the twilight sky a warm glowing sun and a gentle crescent moon appear TOGETHER side by side with soft smiling warmth (fairy-tale sky), misty blue-green mountain ridges and a tiny thatched cottage far below, magical storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"warm evening scene at {COTTAGE}: {MOM} waving goodbye with her big basket piled with rice cakes (tteok), while {BROTHER} and {SISTER} wave from the wooden door of the cottage, golden sunset light over the mountain pass behind her, cozy family mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"comical mountain-pass scene at dusk: {TIGER} sitting in the middle of the path with his paw held out and mouth stuffed full of rice cakes with crumbs on his whiskers, while {MOM} nervously tosses him one more rice cake from her nearly empty basket, tall pine trees and winding pass behind, funny greedy mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"suspenseful but comical night scene at the wooden door of {COTTAGE}: a big furry orange striped paw poking through the gap of the slightly open door, {BROTHER} and {SISTER} inside staring at the paw with wide surprised eyes while quietly tiptoeing backward toward the back door holding hands, warm lamplight inside, alert clever mood NOT terrifying, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on a mossy rock on a moonlit mountain path with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, fireflies drifting around her and the big old tree silhouette behind, calm reassuring night mood, {NO_TEXT}, {STYLE}",
    "s06": f"hopeful night scene: {BROTHER} and {SISTER} sitting close together high on a thick branch of the big old tree, hands pressed together praying toward the starry night sky, while {TIGER} paces in comical confusion far below at the tree trunk scratching his head, moonlight rim light on the leaves, brave hopeful mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"magical climax in the night sky: a glowing golden rope descending from parting clouds, {BROTHER} and {SISTER} holding tight onto the rope rising high above the treetops among swirling stars and soft clouds, their hanbok fluttering, the dark mountain ridges tiny far below, wondrous ascending mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"comedy relief at dawn beside {COTTAGE}: {TIGER} sitting bottom-first in a big soft haystack with straw scattered everywhere and a snapped plain rope dangling above him, dizzy swirl eyes and an embarrassed remorseful face with blushing cheeks, head bowed in apology, gentle funny mood NOT scary NO injury, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"heartwarming finale: split heaven-and-earth composition — in the radiant sky {SISTER} glowing warmly inside a soft sun halo and {BROTHER} smiling gently inside a silver moon halo, and far below {MOM} standing in the cottage yard looking up with a happy tearful smile waving at the sky, warm light pouring down over the mountains, tender reunion mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the mountain path at night, a bright gentle full moon and twinkling stars above her, in the valley below a traditional KOREAN thatched-roof cottage (chogajip) with plain clay-and-wood walls glowing warmly — absolutely NO European house, NO half-timbered walls, NO chimney, NO glass lattice windows — a faint warm sun glow just rising behind the far ridge, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
