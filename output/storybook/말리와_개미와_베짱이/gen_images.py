# 말리와 개미와 베짱이 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 이솝 우화 '개미와 베짱이'. 아늑한 그림책 톤, 동물 의인화, 실존인물 아님.
ANT = "cute hardworking little ants (gaemi) with round friendly bodies, big kind eyes and tiny work aprons, standing upright like storybook characters, diligent and sturdy, cartoon storybook style"
ONE_ANT = "a cute hardworking little ant (gaemi) with a round friendly body, big kind eyes and a tiny work apron, standing upright like a storybook character, cartoon storybook style"
GRASS = "a cheerful bright-green grasshopper (bejjangi) holding a small wooden violin, big happy eyes and slender long legs, carefree and merry, standing upright like a storybook character, cartoon storybook style"
SUMMER = "a bright sunny summer meadow with tall green grass, colorful wildflowers and warm golden sunlight"
WINTER = "a cold snowy winter landscape with soft white falling snow, bare frosty trees and chilly pale-blue light"
ANT_HOME = "a cozy warm ant's cottage home with a small table, a glowing hearth fire and neatly stored grain, homey storybook setting"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop beside {SUMMER} under a bright blue sky, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"scene in {SUMMER}: a busy line of {ANT} carrying heavy golden wheat grains and working hard under the hot summer sun, while in the cool shade of a tree a single {GRASS} happily plays the violin, contrast of busy ants and carefree grasshopper, warm lively mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"scene in {SUMMER}: the {GRASS} cheerfully gesturing come-and-play toward {ONE_ANT} who is carrying a grain, and the little ant politely shaking its head and pointing ahead to keep working, friendly talking moment, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"joyful lively scene in {SUMMER}: the {GRASS} dancing and playing the violin merrily with butterflies swirling around it, splashing by a sparkling stream, pure carefree summer fun, bright happy mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin looking thoughtful and a little worried at the viewer, big warm dark eyes, gentle wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"scene in {WINTER}: the poor {GRASS} shivering and hugging itself in the deep snow, cold and hungry with no food and no home, gently sad wistful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"night scene in {WINTER}: the shivering {GRASS} timidly knocking on the warmly glowing wooden door of {ANT_HOME} seen from outside with snow softly falling, cold but hopeful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"heartwarming scene at the open door of {ANT_HOME}: a kind {ONE_ANT} opening the door wide and warmly welcoming the shivering {GRASS} inside with a gentle smile, offering a bowl of warm soup and bread, cozy caring mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"joyful spring scene in a green flowering meadow: the {GRASS} playing the violin while cheerful {ANT} dance and work together happily side by side, everyone celebrating as friends, warm festive mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop by the sunny meadow under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
