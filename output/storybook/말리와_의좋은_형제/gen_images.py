# 말리와 의좋은 형제 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 형제 — 외모 구분 고정. 실존 인물 아님, 한복 입은 카툰 형제. 형=수염/든든, 아우=젊음/앳됨
BRO_OLDER = "the OLDER brother, a warm sturdy young Korean man in a beige hanbok with a short beard and a topknot"
BRO_YOUNGER = "the YOUNGER brother, a gentle youthful clean-shaven Korean man in a light-blue hanbok with a topknot"
RICE_FIELD = "golden rice paddies at harvest time between two neighboring traditional Korean thatched cottages, NO European houses"
RICE_STACKS = "two big neat stacks of harvested rice-straw bundles (natgari) standing side by side in a Korean farmyard"
NIGHT = "under a big bright full moon in a starry night sky over a quiet Korean farm village"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop under a bright blue sky, a peaceful Korean thatched-roof farm village with golden rice fields visible below in the valley, cheerful warm storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"warm scene in a Korean village: {BRO_OLDER} and {BRO_YOUNGER} standing together as close affectionate neighbors in front of their two side-by-side thatched cottages, smiling fondly at each other, the older brother's larger family and the younger brother's new bride faintly visible, tender brotherly mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"daytime harvest scene at {RICE_FIELD}: {BRO_OLDER} and {BRO_YOUNGER} happily harvesting golden rice together and building {RICE_STACKS} of equal size, looking content and proud, bright warm autumn mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"tender night scene {NIGHT}: {BRO_OLDER} carrying a big armful of rice-straw bundles quietly and secretly toward his younger brother's rice stack, a caring thoughtful look on his face, moonlit gentle mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin in an adorable thinking pose, looking at the viewer as if sharing a secret, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"tender night scene {NIGHT}: {BRO_YOUNGER} carrying a big armful of rice-straw bundles quietly and secretly toward his older brother's rice stack, a caring gentle look on his face, moonlit warm mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"morning scene at a Korean farmyard: {BRO_OLDER} standing beside his rice stack scratching his head with a puzzled surprised face because it has NOT shrunk at all, {RICE_STACKS} still equal, comical wondering daytime mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"emotional climactic scene {NIGHT}: {BRO_OLDER} and {BRO_YOUNGER}, each carrying a big armful of rice-straw bundles, suddenly meeting face to face on a narrow paddy path in the bright moonlight, both stunned and moved as they realize the truth, deeply touching tender mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"heartwarming scene {NIGHT}: {BRO_OLDER} and {BRO_YOUNGER} dropping their rice bundles and warmly embracing each other in a big hug under the full moon, tears of joy, overflowing brotherly love, deeply moving warm mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop, the peaceful Korean farm village and golden rice fields glowing below under a gentle sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
