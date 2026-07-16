# 말리와 은혜 갚은 까치 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
NAGNE = (
    "a kind brave young Korean traveler (nagne) with a warm gentle face, wearing a simple beige traditional "
    "Korean hanbok and a small back-bundle, holding a wooden walking staff"
)
MAGPIES = (
    "adorable Korean magpies (kkachi) with glossy black-and-white feathers and blue-tinged wings, "
    "cute round fluffy baby magpies in a twig nest, a caring mother magpie, friendly and endearing NOT scary"
)
SNAKE = (
    "a big comical grumpy mischievous green snake with a silly pouting grumpy face, cartoonish and goofy, "
    "clearly playful and harmless NOT scary NOT menacing NOT realistic, storybook style"
)
FOREST = "a peaceful green Korean mountain forest path with tall pine trees, soft daylight"
BELL = (
    "an old weathered wooden Korean temple bell pavilion (jonggak) housing a large bronze bell, "
    "standing in a quiet mountain forest"
)
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy forest hilltop under a bright blue sky, below her a peaceful Korean mountain valley with pine trees and a small old wooden bell pavilion nestled among them, warm inviting storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"{NAGNE} walking along {FOREST}, carrying his bundle and walking staff, looking up curiously toward the sound of birds, peaceful bright daytime travel mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"tense rescue scene in {FOREST}: {NAGNE} bravely raising his wooden staff high and shouting to shoo away {SNAKE} that is slithering toward a twig nest of frightened {MAGPIES} up in a tree, the snake shrinking back comically, protective heroic mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"heartwarming scene in {FOREST}: the grateful mother of the {MAGPIES} bowing and fluttering happily around {NAGNE} while the fluffy baby magpies chirp joyfully in their nest, the traveler smiling warmly, thankful joyful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy forest hilltop under the bright sky with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"tense night scene: {NAGNE} standing worried inside {BELL} at night, blocked by {SNAKE} that has reappeared and coiled across the path with a grumpy pouting face, moonlight and lantern glow, suspenseful but comical NOT scary mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"dramatic climax at {BELL} at night: a whole flock of the {MAGPIES} flying in together and pushing and striking the large bronze bell with their wings and beaks to make it ring, motion lines and sound ripples, brave stirring triumphant mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"night scene at {BELL}: the ringing bronze bell glowing, {SNAKE} startled with wide shocked eyes hurriedly slithering away into the dark forest, {NAGNE} sighing with relief, comical triumphant mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"warm morning scene at {BELL}: {NAGNE} looking up gratefully at the {MAGPIES} perched all around the bell pavilion in golden morning light, gently thanking them, tender heartwarming mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy forest hilltop, the bright morning sky and the peaceful valley with the bell pavilion behind her, magpies flying in the distance, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
