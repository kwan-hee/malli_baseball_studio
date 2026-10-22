# 말리와 신데렐라 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 첨부 + 지브리 스타일 고정: ghibli_scene_ref.png(스타일 앵커) 첨부
# STYLE 문구는 C:/PROJECT/prompts/ghibli_style.txt 단일 출처 (2026-07-12 스타일 필수화)
# 가로(16:9) 강제 문구 필수 — flash 폴백 세로 드리프트 방지 (2026-07-16 임금님귀 편 교훈)
import base64
import sys
import time
from pathlib import Path

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

REF = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/malli_reference.png"))          # 캐릭터 시트
STYLE_REF = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/ghibli_scene_ref.png"))   # 지브리 스타일 앵커(사용자 제공)
STYLE = Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "prompts/ghibli_style.txt")).read_text(encoding="utf-8").strip()  # 단일 출처

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백. 주의: flash는 16:9 무시 경향 → 가로 강제 문구 필수
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게 (최종 출력은 720p — compose가 축소)

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
# 페로 '신데렐라'. 따뜻하고 화려한 그림책 톤, 실존인물 아님. 순화: 계모·언니 심술쟁이지만 마지막 화해.
CINDERELLA = "a kind gentle cartoon girl named Cinderella with a sweet warm face and tied-up hair, in humble patched work clothes, cartoon storybook style, NOT a real person"
CINDERELLA_GOWN = "the same gentle cartoon girl Cinderella now radiant in a beautiful sparkling light-blue ball gown with shining glass slippers, cartoon storybook style"
STEPMOTHER = "a stern haughty cartoon stepmother in a fancy dark dress, comical NOT scary, cartoon storybook style"
SISTERS = "two vain comical cartoon stepsisters in overdone frilly fancy dresses, silly NOT scary, cartoon storybook style"
FAIRY = "a kind sparkling fairy godmother with a magic wand and a gentle warm smile, surrounded by glowing magic sparkles, cartoon storybook style"
PRINCE = "a handsome kind young cartoon prince in a royal blue outfit, cartoon storybook style"
COTTAGE = "a humble old cottage interior with a fireplace and cleaning chores, warm storybook setting"
BALLROOM = "a grand sparkling palace ballroom with glittering chandeliers and elegant dancing guests, magical storybook setting"
CARRIAGE = "a magical golden pumpkin-shaped carriage pulled by white horses"
SLIPPER = "a single sparkling glass slipper"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop with a fairytale kingdom castle in the distance under a bright blue sky, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"scene inside a {COTTAGE}: the kind {CINDERELLA} cheerfully sweeping and doing chores by the fireplace, while the haughty {STEPMOTHER} and the two {SISTERS} lounge and order her around, gentle sympathetic mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"scene at the door of a {COTTAGE}: the two {SISTERS} in fancy dresses excitedly heading off to the palace ball holding an invitation, while the kind {CINDERELLA} stands behind in her patched clothes with sad teary eyes, wistful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"magical fairytale scene in a moonlit cottage yard: a kind sparkling fairy godmother waving a glowing magic wand, a big pumpkin magically turning into a golden pumpkin carriage while little mice turn into white horses, bright swirling magic sparkles filling the air, a joyful wondrous magical moment, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin looking curious and excited at the viewer, big warm dark eyes, gentle wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"scene in a {BALLROOM}: {CINDERELLA_GOWN} dancing gracefully hand in hand with the kind {PRINCE} while elegant guests admire them, a dreamy magical romantic mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"fairytale scene on a grand palace staircase at night: a big clock striking midnight, a single sparkling glass slipper left behind on a stone step, {CARRIAGE} waiting at the bottom, and a girl in a blue dress hurrying down the stairs, moonlit storybook mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"scene: the kind {PRINCE} holding {SLIPPER} going house to house with attendants, trying the glass slipper on the feet of the two {SISTERS} who do not fit it, hopeful determined mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"heartwarming wide scene inside a {COTTAGE}: a gentle girl joyfully holding a sparkling glowing glass slipper, while a stepmother and two stepsisters around her clap and celebrate warmly in happy reconciliation and a kind young prince smiles nearby, cheerful bright group celebration, cartoon storybook style, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop with the fairytale kingdom castle behind under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
