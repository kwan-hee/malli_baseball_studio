# 말리와 도깨비 방망이 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
WOODCUTTER = (
    "a kind poor young Korean woodcutter with a gentle honest face, wearing a simple worn hanbok and carrying "
    "a wooden A-frame carrier (jige) with firewood, hair in a topknot"
)
GOBLINS = (
    "friendly comical Korean goblins (dokkaebi) — chubby round bodies, one small horn, colorful reddish-blue skin, "
    "big goofy grins and cheerful eyes, each holding a knobby magic club (bangmangi), playful and funny NOT scary NOT menacing, cartoonish and cute"
)
GREEDY = (
    "a greedy sly old Korean man with a grey topknot and thin beard, wearing a slightly fancier brown hanbok, "
    "cunning scheming expression"
)
HUT = "an old empty thatched-roof mountain hut (chogajip) with a wooden loft, lit by warm moonlight, deep forest night outside"
VILLAGE = "a peaceful Korean mountain village of thatched-roof cottages (chogajip), absolutely NO European houses"
TREASURE = "glittering piles of gold and silver ingots, rice sacks and treasure spilling out"
HAZELNUT = "a small round hazelnut"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy hilltop under a big bright moon, below her {VILLAGE} nestled in the valley, fireflies drifting, cozy warm storybook night mood, {NO_TEXT}, {STYLE}",
    "s02": f"{WOODCUTTER} in a sunlit mountain forest, pausing from gathering firewood to happily pick up a few small hazelnuts from the ground and tuck them into his shirt with a kind smile, thinking of his parents, warm gentle daytime mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"night scene inside {HUT}: a whole crowd of {GOBLINS} tumbling in and starting a merry feast with dancing, while {WOODCUTTER} peeks nervously from a wooden loft above, lively funny lantern-lit mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"lively magical scene inside {HUT}: the goblin leader of the {GOBLINS} raising a magic club high and striking it as {TREASURE} bursts and pours out in heaps, the goblins cheering and dancing around the growing pile of gold and silver, joyful wondrous mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on a grassy hilltop under the moonlit night sky with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"funny climax inside {HUT}: {WOODCUTTER} in the loft biting down hard on {HAZELNUT} with a loud crack, while the startled crowd of {GOBLINS} scramble and flee in comical panic out the door and windows, leaving a magic club behind, hilarious lively mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"heartwarming morning scene in {VILLAGE}: {WOODCUTTER} happily using the magic club to provide a warm home and rice for his elderly parents and sharing with grateful smiling neighbors, bright cheerful daytime mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"scheming scene: {GREEDY} clutching a handful of hazelnuts and sneaking eagerly toward {HUT} in the dark forest with a greedy grin, imagining treasure, sly comical mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"funny lesson scene inside {HUT}: the crowd of {GOBLINS} frowning and advancing with their magic clubs toward the frightened {GREEDY} who bit a hazelnut, the greedy old man fleeing in comical panic and regret, comical NOT scary mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop at night, the big bright moon glowing above {VILLAGE} in the valley below, fireflies around her, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
