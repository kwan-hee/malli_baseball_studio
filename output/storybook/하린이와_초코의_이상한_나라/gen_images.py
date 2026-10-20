# 하린이와 초코의 이상한 나라 (강의 샘플) — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 캐릭터 일관성: characters/ 시트 3장(하린·초코·앨리스) 첨부, s10 은 엄마 사진(AI 예시) 추가 첨부
# 그림체: 수채화 2D 그림책 (사용자 선택 — 채널 지브리 앵커 미사용, 설계 문서 참조)
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

CHAR = BASE / "characters"
REFS = [CHAR / "harin_sheet.png", CHAR / "choco_sheet.png", CHAR / "alice_sheet.png"]
MOM_REF = Path(r"C:\PROJECT\images\portraits\mom.png")  # s10 전용
STYLE = (
    "soft hand-painted watercolor children's picture book illustration, gentle wet-on-wet watercolor washes "
    "with visible paper texture, delicate thin pencil-like outlines, warm pastel palette, soft rounded cute "
    "proportions, cozy dreamy bedtime mood, match the art style of the attached character sheets EXACTLY, "
    "NOT 3D render, NOT anime cel shading, NOT photorealistic, absolutely NO text, no letters, no words anywhere"
)

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백. 주의: flash는 16:9 무시 경향 → 가로 강제 문구 필수
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게 (최종 출력은 720p — compose가 축소)

HARIN = "Harin (the 6-year-old Korean girl from the FIRST sheet: black low pigtails with YELLOW pom-pom ties, PINK dress)"
CHOCO = "Choco (the chestnut-brown curly toy poodle puppy from the SECOND sheet: long floppy curly ears, thin RED collar, on four legs)"
ALICE = "Alice (the girl from the THIRD sheet: long wavy golden hair, YELLOW ribbon headband, MINT GREEN dress with white collar)"
BEDROOM = "a cozy child's bedroom at night, warm small bedside lamp glow, soft blue moonlight through the window, quilted blanket"
WONDER = "a whimsical dreamy wonderland"

SCENES = {
    "s01": f"{BEDROOM}: {HARIN} wearing her pink dress sitting up in bed yawning sleepily, an open picture book on the blanket whose painted rabbit hole is glowing with sparkling golden light, {CHOCO} wagging his tail and leaping head-first into the glowing hole in the book, magical cozy mood, ONE single full-bleed illustration filling the whole frame edge to edge, NO white border, NO extra small character figures or inset sketches on the side",
    "s02": f"{HARIN} and {CHOCO} gently floating down a deep round magical rabbit hole like feathers, Harin's dress billowing softly, surrounded by drifting teacups, pocket watches, clocks and open storybooks floating in the air, warm lantern light on the earthy walls, calm wonder-filled not-scary mood",
    "s03": f"a tiny whimsical room with a very small arched door and a little glass table holding a small bottle with a paper tag (no readable text), {HARIN}, {CHOCO} and {ALICE} are ALL equally tiny (Alice the SAME small scale as Harin, only slightly taller) beside the huge table leg, {ALICE} walking toward them with a kind welcoming smile, friendly first-meeting mood",
    "s04": f"a soft misty forest path in {WONDER}: {HARIN}, {CHOCO} and {ALICE} walking side by side looking up at a tree branch where a pink-and-purple striped Cheshire Cat grins widely while its body fades into sparkles leaving only the big smile, curious playful mood",
    "s05": f"a merry outdoor tea party in a forest clearing of {WONDER}: a long table with mismatched teapots and cakes, a friendly Hatter in an enormous top hat handing a golden clock-shaped key to {HARIN}, {CHOCO} sitting happily on a chair, {ALICE} raising a teacup and singing, joyful festive mood",
    "s06": f"the Queen of Hearts' rose garden: playing-card soldiers painting white roses red with brushes, {CHOCO} has accidentally knocked over a pot of red paint spilling across the white path, {HARIN} and {ALICE} gasping, a round comical grumpy Queen of Hearts stamping her feet with puffed red cheeks (silly, NOT scary, no weapons), funny chaotic mood",
    "s07": f"a joyful escape through the rose garden: {HARIN}, {ALICE} and {CHOCO} running and laughing between rose bushes, behind them flustered playing-card soldiers being blown up into the sky by a swirling breeze, cards tumbling and fluttering like leaves, rose petals flying, exciting funny NOT scary mood",
    "s08": f"at the end of the garden a small round wooden door open with warm golden light pouring out, a golden clock-shaped key in the lock, {HARIN} and {ALICE} hugging each other goodbye, {CHOCO} sitting beside them looking up, tender bittersweet warm mood",
    "s09": f"{BEDROOM}, early dawn: {HARIN} lying in bed just opening her eyes with a soft smile, {CHOCO} curled up asleep beside her, a small red heart playing card resting next to the pillow, Harin's hand reaching for it, gentle wondering mood",
    "s10": f"{BEDROOM}: a gentle mother (from the FOURTH attached image: Korean woman, dark hair in a low ponytail with a mustard ribbon, mustard yellow cardigan) tucking a blanket around {HARIN} who is falling asleep hugging {CHOCO}, the small red heart card on the bedside table, deeply peaceful sleepy loving mood",
}

pool = GeminiPool()
client = pool.client()
ref_bytes = [r.read_bytes() for r in REFS]
mom_bytes = MOM_REF.read_bytes()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

    prompt = (
        "CRITICAL: The attached images are the OFFICIAL character reference sheets — FIRST = Harin, SECOND = Choco, "
        "THIRD = Alice. Whenever a character appears you MUST reproduce their appearance EXACTLY as on their sheet "
        "(face, hair, clothes, colors, Choco's floppy ears and chestnut fur). Each character appears exactly ONCE — "
        "never duplicate anyone. Use the sheets ONLY for character design and art style, never copy the sheet layout. "
        f"Scene: {scene}. Art style: {STYLE}. "
        f"WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall, "
        f"aspect ratio 16:9, resolution {W}x{H}."
    )
    contents = [types.Part(inline_data=types.Blob(data=b, mime_type="image/png")) for b in ref_bytes]
    if sid == "s10":
        contents.append(types.Part(inline_data=types.Blob(data=mom_bytes, mime_type="image/png")))
    contents.append(types.Part(text=prompt))

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
