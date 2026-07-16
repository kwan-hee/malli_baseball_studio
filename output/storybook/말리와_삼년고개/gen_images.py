# 말리와 삼년고개 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
GRANDPA = (
    "a kind gentle old Korean grandfather with a white topknot and short white beard, wearing a simple hanbok"
)
GRANDPA_SICK = "looking pale, worried and gloomy"
GRANDPA_HAPPY = "looking cheerful, healthy and laughing brightly"
BOY = (
    "a clever bright cheerful young Korean boy with a smart lively face, wearing a simple hanbok and a topknot"
)
HILL = "a grassy Korean hillside path (Samnyeon Gogae) winding over a gentle slope, autumn mountains and a village in the distance"
HOME = "a cozy traditional Korean thatched cottage room with a warm floor and bedding, absolutely NO European houses"
VILLAGE = "a peaceful Korean mountain village of thatched-roof cottages, absolutely NO European houses"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy hilltop under a bright blue sky, a peaceful Korean village and a winding hillside path visible below in the valley, cheerful curious storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"scenic view of {HILL}: Korean villagers in hanbok carefully and nervously tiptoeing along the hillside path as if afraid of falling, cautious gentle daytime mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"{GRANDPA}, {GRANDPA_SICK}, having just stumbled and fallen on {HILL} with a shocked frightened face, a market bundle dropped beside him, dramatic worried mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"inside {HOME}: {GRANDPA}, {GRANDPA_SICK}, lying in bed under a blanket sick with worry, refusing food, his worried family standing helplessly nearby, gloomy tender mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"heartwarming scene inside {HOME}: the clever {BOY} sitting cheerfully beside the sick {GRANDPA} in bed, holding up a finger as if explaining a bright clever idea, the grandfather listening with dawning curiosity, cozy hopeful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"joyful scene inside {HOME}: {GRANDPA}, now {GRANDPA_HAPPY}, springing up from bed slapping his knee with a delighted 'aha' expression as the clever {BOY} smiles beside him, bright happy realization mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"funny lively scene on {HILL}: {GRANDPA}, {GRANDPA_HAPPY}, happily and deliberately rolling and tumbling down the grassy slope on purpose laughing out loud, delighted villagers watching and clapping, hilarious cheerful mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"warm scene in {VILLAGE}: {GRANDPA}, {GRANDPA_HAPPY}, fully healthy and beaming, walking spryly through the village greeting smiling neighbors, bright peaceful happy mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop, the peaceful Korean village and hillside path glowing below under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
