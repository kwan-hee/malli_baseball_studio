# 말리와 토끼와 자라 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
RABBIT = (
    "a clever bright-eyed rabbit with soft white-and-grey fur and long upright ears, "
    "a quick-witted lively expression, standing on his hind legs like a storybook character"
)
JARA = (
    "a loyal gentle soft-shell turtle (jara) royal messenger with a kind wise face and a rounded brown shell, "
    "wearing a tiny black traditional Korean official's hat (gat), earnest and dutiful expression"
)
DRAGONKING = (
    "a benevolent majestic Korean Dragon King with a long flowing white beard, wearing an ornate blue-and-gold "
    "royal robe and a jeweled crown, dignified and kindly NOT scary, sitting on a grand throne"
)
PALACE = (
    "a magnificent glowing underwater Dragon Palace built of coral and pearl, shimmering blue water, "
    "drifting jellyfish and schools of colorful fish, rays of light from above, absolutely NO European architecture"
)
SEASIDE = "a peaceful green Korean mountain forest by the seaside, soft grass and pine trees, bright daylight"
HERB = "a small bundle of glowing green medicinal herbs"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy seaside cliff under a big bright sky, below her the deep blue ocean sparkling with the glow of {PALACE} shimmering far beneath the waves, cheerful adventurous storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"inside {PALACE}: {DRAGONKING} looking pale and unwell, resting weakly on his grand throne, worried turtle and fish courtiers gathered around him, an old wise fish physician bowing respectfully, solemn concerned mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"{JARA} bowing bravely before {DRAGONKING} in {PALACE}, volunteering for the journey, then swimming up through the deep blue sea toward the surface with a small travel bundle on his shell, determined dutiful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"in {SEASIDE}: {JARA} standing upright and cheerfully persuading {RABBIT}, gesturing toward the sea as if describing the wonders of the Dragon Palace, the rabbit listening with wide curious eager eyes, lively friendly persuasive mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy seaside cliff under the bright sky with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"climax inside {PALACE}: {RABBIT} standing before {DRAGONKING}, looking momentarily startled then clever and composed as he cleverly explains himself with a sly reassuring smile, the Dragon King and turtle listening intently, tense-then-witty dramatic mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"inside {PALACE}: {DRAGONKING} nodding and kindly gesturing for {RABBIT} to leave, the relieved rabbit climbing onto {JARA}'s back as they set off back toward the surface, hopeful mood, the rabbit hiding a secret little smile, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"on the shore of {SEASIDE}: the clever {RABBIT} standing safely on a rock laughing brightly and calling back, while {JARA} sits in the shallow water below looking up stunned and speechless, bright sunny daytime, comical surprising mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"warm reconciliation scene at {SEASIDE}: the kind {RABBIT} gently handing {HERB} to {JARA} at the water's edge, both looking friendly and touched, soft golden light, heartwarming gentle mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy seaside cliff, the big bright ocean glowing behind her with the Dragon Palace shimmering softly beneath the waves, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
