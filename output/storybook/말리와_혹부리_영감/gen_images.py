# 말리와 혹부리 영감 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 첨부 + 지브리 스타일 고정: ghibli_scene_ref.png(스타일 앵커) 첨부
# STYLE 문구는 C:/PROJECT/prompts/ghibli_style.txt 단일 출처 (2026-07-12 스타일 필수화)
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
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게 (최종 출력은 720p — compose가 축소)

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
HYEOK_GOOD = (
    "a kind cheerful old Korean grandfather (Hyeokburi Yeonggam) with a warm gentle face, white topknot and short white beard, "
    "a large round soft lump (hok) on his LEFT cheek, wearing a plain beige-and-white traditional Korean hanbok, honest happy smile"
)
HYEOK_GREEDY = (
    "a greedy sly old Korean grandfather with a grey topknot and thin beard, a large round lump (hok) on his RIGHT cheek, "
    "wearing a slightly fancier brown traditional hanbok, cunning scheming expression"
)
GOBLINS = (
    "friendly comical Korean goblins (dokkaebi) — chubby round bodies, one small horn, colorful reddish-blue skin, "
    "big goofy grins and cheerful eyes, each holding a knobby magic club, playful and funny NOT scary NOT menacing, cartoonish and cute"
)
HUT = "an old empty thatched-roof mountain hut (chogajip) with a wooden floor, lit by warm candlelight, deep forest night outside"
VILLAGE = "a peaceful Korean mountain village of thatched-roof cottages (chogajip) under a moonlit night sky, absolutely NO European houses"
TREASURE = "glittering piles of gold coins, jade, and treasure jars spilling out"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy hilltop under a big bright moon, below her {VILLAGE} nestled in the valley, fireflies drifting, cozy warm storybook night mood, {NO_TEXT}, {STYLE}",
    "s02": f"{HYEOK_GOOD} standing kindly in the courtyard of his thatched cottage, cheerfully sharing food with smiling neighbors and a happy dog, warm sunny daytime, kindhearted friendly mood, the lump on his cheek clearly visible, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"{HYEOK_GOOD} carrying a small bundle of firewood on his back, caught by nightfall in a dark forest, discovering {HUT} and peeking inside with a tired relieved face, quiet lonely evening mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"lively climax inside {HUT}: {HYEOK_GOOD} singing happily with his mouth open while a whole crowd of {GOBLINS} come tumbling and crowding in through the door and windows, utterly delighted and clapping along to his song, joyful funny lively mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on a grassy hilltop under the moonlit night sky with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"magical climax inside {HUT}: the crowd of {GOBLINS} joyfully pushing {TREASURE} toward {HYEOK_GOOD} while one goblin gently lifts the round lump away from the old man's cheek like a magic trick, the old man amazed and delighted, sparkles in the air, wondrous funny generous mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"joyful morning scene in {VILLAGE}: {HYEOK_GOOD} now with a perfectly smooth cheek (NO lump) walking home carrying {TREASURE}, astonished happy neighbors gathering around him with wide eyes, bright cheerful daytime mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"scheming scene at night: {HYEOK_GREEDY} sneaking eagerly toward {HUT} in the dark forest with a greedy grin, rubbing his hands together, imagining treasure, sly comical mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"funny lesson scene inside {HUT}: the crowd of {GOBLINS} frowning and wagging their fingers playfully at {HYEOK_GREEDY}, one goblin sticking a SECOND round lump onto his OTHER cheek so he now has TWO lumps, the greedy old man looking shocked and regretful, comical not scary mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
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
