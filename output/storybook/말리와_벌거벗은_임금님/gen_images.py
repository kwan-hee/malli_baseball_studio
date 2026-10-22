# 말리와 벌거벗은 임금님 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 안데르센 '벌거벗은 임금님'. 밝고 유쾌한 그림책 톤, 실존인물 아님. 임금님은 속옷 차림으로 표현(선정성 없음).
EMPEROR = "a plump vain cartoon emperor with a big golden crown and a fancy colorful royal robe, a silly proud face, standing upright, comical and cute NOT scary, cartoon storybook style"
EMPEROR_UNDER = "the same plump cartoon emperor now wearing only comical old-fashioned white long johns underwear and his golden crown, looking proud and blissfully unaware, fully child-friendly and modest NOT inappropriate, cartoon storybook style"
TAILORS = "two sly clever cartoon tailors with mischievous playful grins, cartoon storybook style, comical NOT scary"
MINISTER = "a worried royal minister in fancy court robes, cartoon storybook style"
CHILD = "a small innocent honest village child with a bright surprised face pointing a finger, cartoon storybook style"
PALACE = "a grand fancy old-fashioned royal palace interior with tall mirrors and rich drapes, warm storybook setting"
STREET = "a cheerful old-fashioned town street lined with crowds of cheering townspeople, bright festive storybook setting"
LOOM = "an empty wooden weaving loom with absolutely nothing on it"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop with a fairytale kingdom castle in the distance under a bright blue sky, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"scene in a {PALACE}: the vain {EMPEROR} admiring himself proudly in front of a tall mirror surrounded by wardrobes overflowing with fancy clothes, loving his outfits, comical proud mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"scene in a {PALACE}: the two sly {TAILORS} bowing before the {EMPEROR} on his throne, describing a magical cloth with grand gestures, the emperor leaning in intrigued and delighted, lively persuading mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"scene in a {PALACE}: the two {TAILORS} pretending to weave busily at {LOOM}, while a {MINISTER} stares at the empty loom seeing nothing yet forcing a fake admiring smile, awkward funny mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin looking puzzled and curious at the viewer, big warm dark eyes, gentle wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"scene in a {PALACE}: the {EMPEROR} looking at the empty {LOOM} seeing nothing at all, secretly shocked but forcing a big approving smile while handing a bag of gold coins to the two grinning {TAILORS}, comical mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"comical scene in a {PALACE}: {EMPEROR_UNDER} striking a proud vain pose before a tall mirror as if wearing magnificent clothes, while ministers around him clap and praise him, funny mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"lively parade scene on a {STREET}: {EMPEROR_UNDER} proudly parading down the street as crowds of townspeople clap and cheer while secretly astonished, festive comical procession mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"comical reveal scene on a European old-fashioned cobblestone town street with half-timbered houses (same European town setting, townspeople in simple European medieval peasant clothes, NOT Asian): a small honest {CHILD} pointing at {EMPEROR_UNDER} and shouting the truth, the surrounding crowd bursting into surprised laughter, the emperor's face turning red with embarrassment, funny lively mood, {NO_MALLI}, {NO_TEXT}, no banners no signs, {STYLE}",
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
