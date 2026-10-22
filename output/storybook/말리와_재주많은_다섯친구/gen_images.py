# 말리와 재주많은 다섯 친구 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 다섯 친구 — 재주별로 외모 구분(색·특징 고정). 실존 인물 아님, 한복 입은 카툰 청년들
STRONG = "a burly muscular young Korean man in a brown hanbok, the STRONG friend, huge arms"
WIND = "a lean young Korean man in a green hanbok with a big round nose, the WIND-BREATH friend, puffed cheeks"
WATER = "a chubby round young Korean man in a blue hanbok with a big belly, the WATER friend"
IRON = "a sturdy young Korean man in a dark grey hanbok with a tough square body, the IRON-BODY friend"
EARS = "a slim young Korean man in a yellow hanbok with big pointed ears, the SHARP-EARS friend, hand cupped to his ear"
FIVE = f"the five talented friends together: {STRONG}, {WIND}, {WATER}, {IRON}, and {EARS}"
VILLAGE = "a peaceful Korean village of thatched-roof cottages and green hills, absolutely NO European houses"
FIRE_VILLAGE = "a Korean thatched-roof village with a warm orange wildfire glow (stylized soft flames, NOT scary, no one hurt)"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop under a bright blue sky, a peaceful Korean thatched-roof village visible below in the valley, cheerful curious storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"cheerful group portrait in {VILLAGE}: {FIVE}, each proudly showing off his own special talent, standing in a friendly row smiling, bright lively introduction mood, clearly five DIFFERENT characters, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"daytime scene in {VILLAGE}: {FIVE} looking a little downhearted while a few doubtful Korean villagers point and whisper skeptically at them, the five friends still smiling bravely at each other, gentle bittersweet mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"evening scene: {EARS} cupping his hand to his big ear with a shocked alarmed face having just heard something far away, the other four friends ({STRONG}, {WIND}, {WATER}, {IRON}) reacting with alarm, a faint distant orange glow over the mountains behind, tense NOT scary mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, big curious dark eyes, calm wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"dramatic rescue scene at {FIRE_VILLAGE}: {WIND} standing bravely in front, cheeks hugely puffed, blowing a powerful gust of wind from his big nose that pushes the orange flames back, the other friends behind him, heroic lively mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"heroic scene at {FIRE_VILLAGE}: {STRONG} lifting a huge fallen tree trunk to clear a path, while {IRON} with his tough grey body calmly carries two rescued villagers on his back out of the soft flames, brave teamwork mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"climactic scene at {FIRE_VILLAGE}: {WATER} with a hugely swollen round belly spraying an enormous powerful jet of water from his mouth onto the orange flames, steam rising as the fire fizzles out, triumphant splashy heroic mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"joyful celebration in {VILLAGE}: the grateful Korean villagers cheering and lifting up {FIVE} as heroes, everyone hugging and laughing under a clear sky, warm triumphant happy mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop, the peaceful Korean village glowing below under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
