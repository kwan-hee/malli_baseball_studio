# 말리와 브레멘 음악대 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 멀티모달 첨부, 내부 씬은 NO_MALLI 규칙
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

REF = Path(r"C:\PROJECT\images\style_ref\malli_reference.png")

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
DONKEY = "a kind old grey donkey with gentle tired eyes, friendly and sturdy"
DOG = "an old brown dog with floppy ears, warm friendly face"
CAT = "a cute old grey cat, a little scruffy, gentle eyes"
ROOSTER = "a colorful proud rooster with bright red comb and shiny tail feathers"
FOUR = "the four animal friends (the grey donkey, the brown dog, the grey cat and the colorful rooster)"
MEN = "a few comical grumpy men in plain old clothes, silly and NOT scary"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
STYLE = (
    "Studio Ghibli anime style, soft painterly backgrounds, warm pastel colors, watercolor texture "
    "with painterly brush strokes, gentle expressive characters, clean composition, "
    "absolutely NO text, no letters, no words anywhere, do not change character design"
)

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer on a bright sunny countryside road at dawn, a few floating musical notes in the air, hopeful cheerful mood, {STYLE}",
    "s02": f"{DONKEY} walking away down a country road carrying a small bundle, a determined hopeful face, leaving an old farm behind him, soft morning light, {NO_MALLI}, {STYLE}",
    "s03": f"{DONKEY} meeting {DOG} who sits tired by the roadside, the donkey kindly inviting the dog to come along to Bremen, warm friendly moment, {NO_MALLI}, {STYLE}",
    "s04": f"{DONKEY} and {DOG} meeting {CAT} sitting on a low stone wall, inviting the cat to join them, three happy animal friends now, sunny path, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} happily watching from the side as {ROOSTER} crows proudly on a fence and joins the grey donkey, brown dog and grey cat — all four animal friends gathering together on the road, cheerful, {STYLE}",
    "s06": f"{FOUR} walking into a dark forest at dusk, tired and hungry, spotting a tiny warm glowing light from a small cottage far away through the trees, {NO_MALLI}, {STYLE}",
    "s07": f"the tall grey donkey peeking through a lit cottage window at night, seeing a table piled with delicious food while {MEN} sit around it noisily, the other hungry animals waiting below, {NO_MALLI}, {STYLE}",
    "s08": f"{FOUR} stacked in a tall funny tower in front of a cottage window at night — the donkey at the bottom, the dog on the donkey, the cat on the dog, and the rooster on top — all singing loudly together with big music notes and sound bursts, dynamic and hilarious, {NO_MALLI}, {STYLE}",
    "s09": f"{MEN} running away in comical fright into the dark forest, while {FOUR} happily celebrate in the warm lit doorway of the cottage, funny dynamic motion, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly in front of the cozy cottage at sunrise, with {FOUR} standing together happily at the door behind her, soft warm morning colors, {STYLE}",
}

pool = GeminiPool()
client = pool.client()
ref_bytes = REF.read_bytes()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

    prompt = (
        "CRITICAL: This image is the OFFICIAL Malli character reference sheet. "
        "When Malli appears you MUST reproduce her appearance EXACTLY as shown — same cream fur, "
        "same red bow, same pink collar, same gold bone tag, same dark eyes. "
        f"Scene: {scene}. "
        f"Aspect ratio 16:9, resolution {W}x{H}."
    )
    contents = [
        types.Part(inline_data=types.Blob(data=ref_bytes, mime_type="image/png")),
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
            print(f"{sid}: attempt {attempt+1} failed — {type(e).__name__}: {err[:120]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()  # 키 소진 → 다음 계정으로
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted — stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed — stop, report to user")

print("ALL DONE")
