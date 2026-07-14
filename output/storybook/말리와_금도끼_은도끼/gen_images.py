# 말리와 금도끼 은도끼 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
WOODCUTTER = (
    "a kind young Korean woodcutter in simple beige traditional hanbok work clothes with a straw hat, "
    "warm honest smile, carrying a worn old iron axe"
)
GREEDY = "a plump greedy woodcutter in patched brown hanbok with a scraggly mustache and shifty comical eyes, funny NOT scary"
GRANDPA = (
    "a mysterious gentle pond grandfather spirit with a very long flowing white beard, hair drifting like water mist, "
    "pale blue-white robe, kind twinkling eyes, rising gracefully from the pond water, magical but warm, NOT scary"
)
POND = "a deep emerald forest pond surrounded by mossy rocks and tall pine trees"
GOLDAXE = "a shining golden axe glowing warmly"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer on a sunny forest path with tall pine trees and a sparkling emerald pond glimpsed behind her, a few golden sparkles drifting in the air, bright curious storybook morning mood, {STYLE}",
    "s02": f"{WOODCUTTER} happily chopping wood beside {POND}, wood chips flying gently, a small pile of firewood beside him, morning sunbeams through the pines, diligent cheerful mood, {NO_MALLI}, {STYLE}",
    "s03": f"comical mishap moment: the old iron axe flying out of {WOODCUTTER}'s hands in a high arc toward {POND} with a big splash beginning, the woodcutter reaching out in dismay with wide eyes, water droplets sparkling, {NO_MALLI}, {STYLE}",
    "s04": f"magical moment at {POND}: {GRANDPA} rising from parting glowing water holding up {GOLDAXE}, gentle light rays and drifting mist around him, {WOODCUTTER} kneeling at the pond edge looking up in awe, sparkling ripples, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} sitting by the mossy pond edge with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, the glow of the golden axe reflecting softly on the water behind her, playful wondering mood, {STYLE}",
    "s06": f"heartwarming moment at {POND}: {GRANDPA} laughing warmly while presenting three axes laid before {WOODCUTTER} — a golden axe, a silver axe and the old iron axe — the woodcutter bowing with grateful hands together, soft golden light, {NO_MALLI}, {STYLE}",
    "s07": f"comedy moment at {POND}: {GREEDY} deliberately hurling his own axe into the pond with an exaggerated throw and a sneaky grin, big cartoon splash, while a little squirrel on a branch watches with a doubtful face, {NO_MALLI}, {STYLE}",
    "s08": f"quiet lesson moment at {POND}: {GREEDY} standing empty-handed with a slumped guilty posture and teary eyes beside the calm pond as {GRANDPA} sinks back into the misty water with a gentle sad look, soft twilight, remorse mood, NOT scary, {NO_MALLI}, {STYLE}",
    "s09": f"warm reconciliation: {WOODCUTTER} handing his old iron axe kindly to {GREEDY} whose face brightens with hope, both standing on the sunny forest path with firewood bundles, birds circling, friendly forgiving mood, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the forest path at sunset with the emerald pond glowing softly behind her, the two woodcutters walking home together with firewood in the distance, golden evening light, peaceful happy ending mood, {STYLE}",
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
