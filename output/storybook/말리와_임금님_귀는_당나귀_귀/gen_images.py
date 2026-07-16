# 말리와 임금님 귀는 당나귀 귀 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
KING = (
    "a kind dignified Korean king with a warm face, wearing an ornate royal red-and-gold hanbok robe, "
    "his ears hidden under a very tall large black royal headband/hat pulled low"
)
KING_EARS = (
    "a kind Korean king in an ornate royal red-and-gold hanbok robe with big long fuzzy DONKEY-LIKE ears "
    "showing on his head, gentle slightly embarrassed then happy expression"
)
MAKER = (
    "a gentle kind old Korean craftsman (hat maker) with a warm modest face, wearing a plain grey hanbok, "
    "working with cloth and thread"
)
PALACE = "an elegant traditional Korean palace hall with painted wooden pillars and a royal throne, absolutely NO European architecture"
BAMBOO = "a deep green bamboo grove with tall slender bamboo stalks swaying, soft sunlight filtering through"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy palace-garden hilltop under a bright blue sky, an elegant Korean palace roof visible behind her, cheerful curious storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"inside {PALACE}: {KING} sitting on his throne looking a little self-conscious, one hand touching his tall headband as if hiding something underneath, dignified but secretly embarrassed mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"inside {PALACE}: {KING} leaning down earnestly to speak with {MAKER} who is bowing and promising to keep a secret while holding a finished royal hat, serious hushed confidential mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"{MAKER} at his small home looking pale, troubled and unwell, sitting with a hand on his chest as if bursting with an unspoken secret, a lonely lamp-lit room, wistful frustrated mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy palace-garden hilltop with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"{MAKER} standing alone deep in {BAMBOO}, cupping his hands around his mouth and shouting upward with his whole heart, a look of huge relief on his face, liberating cathartic mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"magical scene in {BAMBOO}: the tall bamboo stalks bending and swaying in a gust of wind as if whispering and singing a secret, soft motion lines and drifting leaves, wondrous mysterious mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"inside {PALACE}: {KING} with a flushed red embarrassed face reacting with dismay as he hears the rumor, courtiers murmuring nearby, flustered upset but gentle mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"joyful scene in {PALACE} courtyard: {KING_EARS} bravely taking off his tall headband so his big donkey-like ears show, smiling with relief while happy townspeople around him smile and cheer warmly (NOT mocking), bright accepting heartwarming mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy palace-garden hilltop, the elegant Korean palace and green bamboo grove behind her under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
