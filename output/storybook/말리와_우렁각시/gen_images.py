# 말리와 우렁각시 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 첨부 + 지브리 스타일 고정: ghibli_scene_ref.png(스타일 앵커) 첨부
# STYLE 문구는 C:/PROJECT/prompts/ghibli_style.txt 단일 출처 (2026-07-12 스타일 필수화)
# 가로(16:9) 강제 문구 필수 — flash 폴백 세로 드리프트 방지 (2026-07-16 임금님귀 편 교훈)
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
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백. 주의: flash는 16:9 무시 경향 → 가로 강제 문구 필수
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게 (최종 출력은 720p — compose가 축소)

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
CHONG = (
    "a kind gentle young Korean bachelor farmer with a warm honest face, wearing a simple worn beige hanbok, "
    "hair in a topknot"
)
GAKSI = (
    "a beautiful graceful young Korean woman (the snail maiden) with a kind gentle face, wearing a lovely soft "
    "pink-and-mint traditional hanbok, hair in a neat braided bun"
)
SNAIL = "a pretty large river snail with a beautifully swirled shell, softly glowing with a gentle magic light"
HOME = "a humble cozy Korean thatched cottage with a small kitchen and a large earthen water jar (muldok), absolutely NO European houses"
PADDY = "a lush green Korean rice paddy field with water reflecting the sky, gentle hills behind"
MEAL = "a warm Korean meal table (bapsang) full of rice, soup and neat side dishes with steam rising"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy hilltop under a bright blue sky, a peaceful Korean village with rice paddies visible below in the valley, cheerful curious storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"{CHONG} working alone in {PADDY}, wiping his brow, looking a little lonely and wistful under a wide sky, quiet gentle daytime mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"{CHONG} kneeling at the edge of {PADDY}, holding up {SNAIL} cupped gently in his two hands with a delighted tender smile, soft warm daylight, gentle happy mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"inside the kitchen of {HOME}: {CHONG} coming home to find {MEAL} already set out on the floor as if by magic, steam gently rising, he looks around in wonder and confusion, cozy mysterious mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"magical reveal scene inside {HOME}: {CHONG} peeking secretly from behind a door while {GAKSI} gracefully emerges from the softly glowing snail by the water jar and begins cooking rice, sparkles of gentle magic in the air, wondrous surprising mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"heartwarming scene inside {HOME}: {CHONG} happily greeting {GAKSI} with a grateful bow while she smiles warmly and kindly at him, soft golden light, tender thankful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"{CHONG} and {GAKSI} living happily together at {HOME}: he returns from farming with a hoe while she tends the home, both smiling, friendly neighbors waving nearby, warm cheerful daytime mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"joyful scene in the courtyard of {HOME}: {CHONG} and {GAKSI} sitting together sharing {MEAL} at a low table, both laughing happily, bright sunny warm family mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop, the peaceful Korean village and green rice paddies glowing below under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
