# 말리와 욕심쟁이 개 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 이솝 우화 '개와 그림자' 배경. 아늑한 숲속 동물 그림책 톤. 실존인물 아님.
# 주의: 주인공 개(DOG)는 말리가 아님 — 갈색 개. 말리(크림 말티푸)는 진행자로 s01·s05·s10만 등장.
DOG = "a cute chubby brown dog (NOT Malli, NO red bow, NO pink collar) with short fur and floppy ears, standing on four legs like a real dog, expressive eyes, cartoon storybook style"
MEAT = "a big juicy reddish piece of meat"
BRIDGE = "a small narrow wooden plank bridge over a clear calm stream in a green meadow"
STREAM = "a clear calm shallow stream with a smooth mirror-like water surface"
REFLECTION = "the dog's own mirror reflection in the water looking back up, an identical brown dog also holding a piece of meat"
FOREST = "a warm green storybook countryside with soft rolling meadows and gentle trees"
NO_MALLI = "NO cream Maltipoo puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop at the edge of a warm storybook countryside under a bright blue sky, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"happy scene in {FOREST}: the chubby brown {DOG} trotting along a path proudly carrying {MEAT} in its mouth, looking delighted and excited about its big prize, cheerful upbeat mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"curious scene: the brown {DOG} stopping in the middle of {BRIDGE} and looking down at {STREAM}, discovering {REFLECTION}, the dog surprised and staring at the water, wonder-struck mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"greedy scene on {BRIDGE}: close on the brown {DOG} peering down at the water where its reflection holds a piece of meat that looks bigger, the dog's eyes gleaming with greed and desire, covetous tempted mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin looking worried and warning at the viewer, big warm dark eyes, concerned wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"tense scene on {BRIDGE}: the brown {DOG} growling and baring its teeth down at its own reflection in {STREAM}, the reflected dog baring teeth back, the meat still in the dog's mouth, angry greedy mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"dramatic splash moment on {BRIDGE}: the brown {DOG} opening its mouth wide to bark and the piece of meat slipping out and falling with a big SPLASH into {STREAM}, ripples spreading, the reflection breaking apart, startled shocked mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"sad scene on {BRIDGE}: the brown {DOG} with an empty mouth staring blankly down at the now-empty rippling water, realizing both pieces of meat are gone, dismayed regretful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"reflective scene: the brown {DOG} walking home along the meadow path with drooping shoulders and an empty mouth, looking thoughtful and having learned a lesson, gentle wistful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop by the storybook countryside under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
