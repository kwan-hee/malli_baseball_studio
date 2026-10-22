# 말리와 소가 된 게으름뱅이 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 한국 전래동화 '소가 된 게으름뱅이' 배경. 조선 시대 산골 초가 마을 그림책 톤. 실존인물 아님.
# 주의: 주인공 돌쇠·소는 말리가 아님. 말리(크림 말티푸)는 진행자로 s01·s05·s10만 등장.
# 소가 된 돌쇠 = 돌쇠의 파란 허리띠 천을 목에 두른 누렁소 (사람↔소 동일 인물 표식)
DOLSOE = "a young Korean country bachelor named Dolsoe in a plain white Joseon-era hanbok with a BLUE cloth sash tied at the waist, long single black braid down his back, round friendly face, cartoon storybook style"
OX = "a gentle chubby golden-brown Korean ox (hanu) with small curved horns and big soft eyes, wearing a BLUE cloth scarf tied around its neck, cute and friendly, NOT scary"
GRANDPA = "a kind mysterious old Korean grandfather with a very long white beard, white hanbok and a straw hat, gentle smile"
MOTHER = "a warm Korean country mother in a simple beige hanbok with her hair in a low bun"
FARMER = "a friendly sturdy middle-aged Korean farmer in a white hanbok with rolled-up sleeves and a straw hat, warm kind face"
MASK = "a wooden ox-head mask with small horns"
VILLAGE = "a peaceful Joseon-era Korean mountain village with straw-thatched-roof houses, stone walls and green terraced fields"
NO_MALLI = "NO cream Maltipoo puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop overlooking {VILLAGE} under a bright blue sky, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"funny lazy scene inside a cozy thatched-roof Korean house: {DOLSOE} lying under a thick quilt on the floor yawning widely with half-closed sleepy eyes while bright late-morning sun pours through the paper door, {MOTHER} standing at the open door calling him with a hoe in her hand, playful humorous mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"lazy dreamy scene: {DOLSOE} lying on his back in the shade of a big tree on a grassy mountain pass, arms behind his head, watching a calm ox grazing in the meadow below with envy, {VILLAGE} in the distance, sleepy wishful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"magical scene on the grassy mountain pass: {GRANDPA} holding out {MASK} to {DOLSOE}, who is reaching for it with a delighted grin, soft sparkles of magic swirling around the mask, mysterious wondrous mood (not scary), {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with both paws up to her cheeks, looking surprised and curious at the viewer, a white radish lying in the grass beside her, big warm dark eyes, wondering suspenseful mood, {NO_TEXT}, {STYLE}",
    "s06": f"tired working scene in a muddy spring field: {OX} pulling a wooden plow with a little teardrop at the corner of its eye, mouth open as if mooing, {FARMER} walking behind guiding the plow gently, sweaty hard-work mood but soft and pitiable, NOT cruel, no whip, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"heartwarming scene at a farmyard at sunset: {FARMER} gently stroking the back of {OX}, the ox eating fresh hay happily with content eyes, behind them a plowed field with rows of tiny green sprouts, warm proud grateful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"touching scene at the edge of a field under a pink-orange evening glow: {OX} looking wistfully toward the distant {VILLAGE} as if missing home, a plump white Korean radish with green leaves growing in the field right in front of it, nostalgic hopeful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"joyful magical transformation scene in the field: {DOLSOE} turned back into a human, looking at his own hands in amazement and joy, a half-eaten white radish in his hand, {MASK} gently falling away beside him in sparkles of light, overjoyed wondrous mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop overlooking {VILLAGE} at sunrise, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
