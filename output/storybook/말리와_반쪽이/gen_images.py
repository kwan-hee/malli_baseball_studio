# 말리와 반쪽이 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 반쪽이 = 세로로 반쪽인 몸(눈 하나·팔 하나·다리 하나)이지만 귀엽고 당당하게. 무섭거나 징그럽지 않게 필수
BANJJOG = ("Banjjogi, an ADORABLE cheerful cartoon Korean boy who is a charming HALF-body character "
           "(one eye, one arm, one leg — a whole person split down the middle) hopping energetically on his one leg, "
           "bright confident happy smile, cute storybook style, absolutely NOT scary NOT creepy NOT gory, wearing a simple hanbok")
BROTHERS2 = "his two normal whole-bodied older brothers in hanbok"
TIGER = "a big cartoon tiger with a comical grumpy face, NOT scary, storybook style"
RICH = "a wealthy proud old Korean village elder (buja) with a long beard and fine silk hanbok"
VILLAGE = "a peaceful Korean village of thatched-roof cottages and green hills, absolutely NO European houses"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop under a bright blue sky, a peaceful Korean thatched-roof village visible below in the valley, cheerful warm storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"warm scene inside a cozy Korean thatched cottage: a kind old Korean couple receiving three live carp (fish) from a gentle traveling Buddhist monk at their door, the wife holding a bowl with the fish, warm hopeful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"tender family scene in a Korean home: a loving Korean mother and father holding their three baby sons — two whole healthy babies and {BANJJOG} as a cute baby half-body — the parents cradling all three with deep love and tenderness, warm gentle NOT scary mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"lively daytime scene in {VILLAGE}: {BANJJOG} cheerfully lifting a huge heavy boulder over his head with his one arm showing amazing strength, showing off happily while village children watch amazed, some teasing kids nearby, {BANJJOG} smiling confidently NOT sad, bright spirited mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"nighttime scene in {VILLAGE}: {TIGER} prowling through the moonlit village while frightened villagers peek fearfully from behind their shut doors, {RICH} trembling too, tense suspenseful but NOT scary storybook mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"triumphant comical action scene in {VILLAGE}: {BANJJOG} cleverly yanking a rope snare tight so that {TIGER} is caught and dangling tangled in the rope, the tiger's eyes wide in comic surprise as it flees, {BANJJOG} grinning proudly and confidently, exciting funny heroic mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"scene in {VILLAGE}: the amazed villagers and {RICH} staring wide-eyed in astonishment and admiration at {BANJJOG}, who stands proudly after defeating the tiger, the rich elder looking impressed and a little ashamed of himself, warm respectful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"joyful celebration in {VILLAGE}: {RICH} warmly clasping {BANJJOG}'s one hand with a grateful respectful smile, cheering villagers and the once-teasing children now happily gathering around {BANJJOG} as their hero, bright triumphant happy mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop, the peaceful Korean village glowing below under a gentle sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
