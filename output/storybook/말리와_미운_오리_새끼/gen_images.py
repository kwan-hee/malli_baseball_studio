# 말리와 미운 오리 새끼 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 첨부 + 지브리 스타일 고정: ghibli_scene_ref.png(스타일 앵커) 첨부
# STYLE 문구는 C:/PROJECT/prompts/ghibli_style.txt 단일 출처 (2026-07-12 스타일 필수화)
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
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
GREY = (
    "a big fluffy grey duckling with soft downy feathers, gentle shy dark eyes, "
    "slightly bigger than the other ducklings, lovable and endearing, just different, NOT ugly"
)
MOM = "a warm mother duck with soft brown feathers and a kind gentle face"
YELLOW = "small cute yellow ducklings"
SWANS = "elegant white swans with graceful long necks and snow-white feathers"
YOUNGSWAN = "a beautiful young white swan with bright gentle eyes and pure snow-white feathers"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully at the viewer beside a sunny farm pond with reeds and water lilies, far away in the sky a line of white swans flying, bright hopeful morning mood, {STYLE}",
    "s02": f"{MOM} sitting on a cozy nest by a sunny farm pond, several {YELLOW} freshly hatched around cracked eggshells chirping happily, one noticeably bigger egg still unhatched in the nest, warm soft light, {NO_MALLI}, {STYLE}",
    "s03": f"{GREY} standing among {YELLOW} by the pond, clearly bigger and grey while the others are small and yellow, the grey duckling waddling cheerfully after {MOM} into the water, gentle sweet scene, {NO_MALLI}, {STYLE}",
    "s04": f"{GREY} walking away alone along the pond edge at dusk with a small teardrop, looking back sadly one last time, while in the far background pond animals whisper among themselves, melancholy but soft warm dusk colors, {NO_MALLI}, {STYLE}",
    "s05": f"{MALLI} sitting quietly among tall reeds at the water's edge, watching with a thoughtful caring face as {GREY} floats alone on the calm evening water in the distance, tender emotional scene, {STYLE}",
    "s06": f"{GREY} standing on a lakeshore in autumn, gazing up in wonder at a flock of {SWANS} flying across a golden sunset sky, fallen leaves drifting, longing and dreamy atmosphere, {NO_MALLI}, {STYLE}",
    "s07": f"{GREY} huddled small and warm inside a snowy reed thicket in winter, snowflakes gently falling, wrapped in his own fluffy feathers with hopeful closed eyes, soft blue-white winter light with a hint of warmth, {NO_MALLI}, {STYLE}",
    "s08": f"{GREY} lowering his head shyly toward sparkling spring pond water, and the water reflection clearly shows a beautiful white swan instead, while {SWANS} glide closer around him, magical emotional moment, glittering light on water, {NO_MALLI}, {STYLE}",
    "s09": f"{YOUNGSWAN} spreading large white wings taking off from the pond together with a flock of {SWANS}, flying gracefully over sparkling blue water into a bright spring sky, children on the shore pointing up joyfully, triumphant uplifting scene, {NO_MALLI}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly at the edge of a bright spring pond, with {YOUNGSWAN} gliding gracefully on the water behind her among swan friends, cherry blossom petals in the air, peaceful happy ending mood, {STYLE}",
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
