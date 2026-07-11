# 말리와 호랑이와 곶감 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 멀티모달 첨부, 내부 씬은 NO_MALLI 규칙
import base64
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

# API 키: 기존 파이프라인 .env 재사용
# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, r"C:\youtube_longform_agent")
from gemini_pool import GeminiPool, is_quota_error

REF = Path(r"C:\PROJECT\images\style_ref\malli_reference.png")

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
TIGER = (
    "a big cartoon tiger with orange fur and black stripes, round friendly face, NOT scary, "
    "a little silly and cute, expressive big eyes"
)
MOTHER = "a gentle Korean mother in soft traditional hanbok"
BABY = "a chubby cute baby"
TRAVELER = "a friendly traveler man in old Korean hanbok clothes with a cloth bundle on his back"
HOUSE = "a cozy old Korean village house at night with warm glowing paper windows"
NO_MALLI = "NO dog in this scene, Malli does NOT appear"
STYLE = (
    "Studio Ghibli anime style, soft painterly backgrounds, warm pastel colors, watercolor texture "
    "with painterly brush strokes, gentle expressive characters, clean composition, "
    "absolutely NO text, no letters, no words anywhere, do not change character design"
)

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer at the edge of a cozy old Korean mountain village at dusk, traditional thatched-roof houses with warm lantern light, gentle evening sky, {STYLE}",
    "s02": f"{TIGER} sneaking down a snowy moonlit mountain toward a small village at night, looking hungry and curious, big careful paws, quiet night atmosphere, {NO_MALLI}, {STYLE}",
    "s03": f"inside a warm cozy old Korean house at night, {MOTHER} gently holding a crying {BABY}, soft lamplight, and outside the paper window {TIGER}'s big eyes peeking in curiously, {NO_MALLI}, {STYLE}",
    "s04": f"{MOTHER} comforting the still-crying {BABY} inside the warm house, while just outside the window {TIGER} looks surprised and confused that the baby did not stop crying, night, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} sitting outside a glowing village house at night, tilting her head curiously with one paw near her chin, a wondering expression, warm window light behind her, {STYLE}",
    "s06": f"inside the warm house, {MOTHER} offering a bright orange dried persimmon to the {BABY}, the baby instantly calm and happily reaching for it, cozy lamplight, {NO_MALLI}, {STYLE}",
    "s07": f"{TIGER} outside the window at night, eyes wide with comical fear, trembling and shaking, imagining a scary unknown thing, funny terrified expression, {NO_MALLI}, {STYLE}",
    "s08": f"a dark moonlit night: {TRAVELER}, unable to see well in the dark, mistakenly climbing onto the back of the big {TIGER} thinking it is an ox, the tiger's eyes going wide with shock, {NO_MALLI}, {STYLE}",
    "s09": f"{TIGER} bolting away in terror at full speed across the moonlit countryside, a dust trail behind, while {TRAVELER} tumbles off safely onto soft grass, very dynamic frantic motion, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly at sunrise over the peaceful village, with {TIGER} tiny and safe far away up on the mountain, soft warm morning colors, {STYLE}",
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
