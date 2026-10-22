# 말리와 북풍과 해님 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 북풍과 해님. 이솝 우화, 밝고 따뜻한 그림책 톤.
NORTH_WIND = "a comically fierce cartoon North Wind character depicted as a big puffed-cheek blue-gray cloud face blowing hard, NOT scary just boastful and dramatic, cartoon storybook style"
SUN = "a warm kind smiling cartoon Sun character with a gentle golden glowing round face and soft rays, friendly and maternal, cartoon storybook style"
TRAVELER = "a cheerful cartoon traveler man in a thick brown coat and hat walking on a country road, generic friendly face, cartoon storybook style"
FIELD = "a bright green countryside meadow with rolling hills, wildflowers, and a winding path under a wide sky"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop with a bright blue sky and fluffy white clouds, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"scene high in the sky: {NORTH_WIND} on the left boasting with puffed cheeks and {SUN} on the right smiling calmly, the two facing each other in a friendly rivalry, bright blue sky with fluffy clouds, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"scene: {NORTH_WIND} and {SUN} looking down from the sky at a small {TRAVELER} walking along a winding country road in a {FIELD}, the wind points at the traveler challengingly, bright daylight, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"dramatic windy scene: {NORTH_WIND} blowing fiercely with huge puffed cheeks, leaves and branches flying everywhere, trees bending, the {TRAVELER} clutching his thick coat tightly against the gale with a determined face, wild stormy mood but NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"scene: {NORTH_WIND} blowing even harder with maximum effort, the {TRAVELER} hunched over gripping his coat collar tightly refusing to let go, hat almost flying off, leaves swirling, the wind looks exhausted and frustrated, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s06": f"warm sunny scene: {SUN} peeking out from behind clouds with a gentle smile, golden warm sunlight flooding a {FIELD}, colorful flowers blooming, butterflies fluttering, everything bright and beautiful, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"heartwarming scene: the {TRAVELER} happily taking off his thick coat by himself with a relieved joyful smile, folding it over his arm, under warm golden sunshine in a beautiful {FIELD}, {SUN} beaming proudly in the sky, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"touching scene: {NORTH_WIND} looking down humbly with a sheepish expression while {SUN} speaks kindly to him with a warm gentle smile, the two reconciling in a peaceful sky, soft golden light, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"peaceful happy ending scene: {NORTH_WIND} now blowing a gentle cool breeze and {SUN} shining warmly together over a beautiful {FIELD} with happy villagers enjoying the pleasant weather, harmonious and content mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop with a bright sky and gentle breeze, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed - stop, report to user")

print("ALL DONE")
