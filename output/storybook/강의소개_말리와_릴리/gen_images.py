# 강의 소개 영상 「말리의 동화나라」 — 이미지 생성 (Gemini Nano Banana, 2차 게이트 승인 2026-10-22)
# B: 16:9 배경(B1 표지·B3 펼친 책 = Veo 클립 시작 프레임) / M: 말리 포즈(흰 배경 → cutout.py 가 오려 합성)
# E: 예시 주인공·동화 표지(카드로 합성)
# 말리 = prompts/malli_character.txt 캐릭터 문구 + malli_reference.png 멀티모달 참조 (CLAUDE.md 규칙)
# 그림체는 기준 시트(2026-10-22 갱신, 수채화)와 릴리 시트에 맞춘 수채화 — 콘티 지시 "따뜻한 수채화 동화풍"
# 글자는 render.py 가 렌더 — 이미지에는 어떤 글자도 넣지 않는다 (말리 태그 제외)
import base64
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
IMG = BASE / "images"
IMG.mkdir(exist_ok=True)

ROOT = [_p for _p in BASE.resolve().parents if (_p / "AGENTS.md").is_file()][-1]
MALLI_REF = ROOT / "images/style_ref/malli_reference.png"

MALLI = (
    "a fluffy cream-colored Maltipoo puppy named Malli with a red bow ribbon, "
    "pink collar with a gold bone-shaped tag engraved \"Malli\", soft curly fur, big dark expressive eyes"
)
STYLE = (
    "soft hand-drawn watercolor and pencil illustration on warm cream textured paper, gentle Japanese animation "
    "storybook style, clean delicate linework, pastel palette, soft shadows"
)
MATCH_REF = ", exactly matching the attached sheet's art style"
NO_TEXT = "absolutely NO text, no letters, no words, no numbers, no signature anywhere"
WHITE = ("alone on a completely plain flat pure white background, no floor, no ground shadow, no props other than "
         "the ones described, whole body fully visible with generous empty white space around her")

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

# id: (비율, 말리 참조 첨부 여부, 장면)
SCENES = {
    "B1": ("16:9", False, "a closed hardcover children's picture book lying flat in the CENTER of a warm wooden table, "
           "seen from slightly above, the cover shows a soft pastel meadow with flowers and a big empty pale sky area "
           "(space for a title to be added later), cozy warm lamp light, the book fills about half of the frame"),
    "B2": ("16:9", False, "a wide gentle watercolor meadow inside a storybook world: soft rolling green hills, little "
           "wildflowers, a few round trees on the far sides, light pastel blue sky with fluffy clouds, the center and "
           "lower middle are open calm grass with nothing in it (space for characters), dreamy and warm"),
    "B3": ("16:9", True, "a big open hardcover picture book lying on a warm wooden table, seen from slightly above, "
           "its two open pages show a soft watercolor meadow with flowers; Malli stands happily ON the open pages in "
           "the middle of the book, small relative to the book, smiling at the viewer"),
    "M1": ("1:1", True, f"Malli sitting upright facing the viewer, happily wagging her tail, cheerful open-mouth smile, {WHITE}"),
    "M2": ("1:1", True, f"Malli jumping joyfully in the air with all four paws off the ground, ears flying, big happy smile, {WHITE}"),
    "M3": ("1:1", True, f"Malli sitting and raising one front paw high, waving hello at the viewer, bright friendly smile, {WHITE}"),
    "M4": ("1:1", True, f"Malli sitting and looking up and to the side with a dreamy curious wondering expression, {WHITE}"),
    "M5": ("1:1", True, f"Malli sitting, nodding with a confident reassuring smile and sparkling eyes, {WHITE}"),
    "M6": ("1:1", True, f"Malli standing and pointing one front paw toward the LEFT of the image, excited smile, looking LEFT, {WHITE}"),
    "M7": ("1:1", True, f"Malli sitting calmly and contentedly, gentle smile, body turned slightly toward the LEFT, {WHITE}"),
    # M8 v1: 귀가 치와와처럼 뾰족 → 늘어진 귀 고정 명시 (2026-10-22 QC)
    "M8": ("1:1", True, f"Malli standing up suddenly on her hind legs, alert and excited surprised expression, her ears stay LONG FLOPPY HANGING curly ears exactly like the sheet (only lifted a little, NEVER pointed or upright), {WHITE}"),
    "M9": ("1:1", True, f"Malli running happily toward the viewer, mid-stride, ears bouncing, joyful expression, {WHITE}"),
    "M10": ("1:1", True, f"Malli sitting and hugging a small closed picture book with plain cover to her chest, eyes sparkling with joy, {WHITE}"),
    "M11": ("1:1", True, f"Malli sitting and bowing her head deeply in a polite thank-you bow, eyes closed peacefully, {WHITE}"),
    "M12": ("1:1", True, f"Malli standing on her hind legs with one front paw raised in a determined cheering fist pose, sparkling eyes, {WHITE}"),
    "E1": ("1:1", False, "an imaginary cute little child (not a real person, simple storybook character) dressed as the "
           "brave hero of a fairy tale with a small cape, standing happily in a tiny storybook landscape, "
           "soft vignette fading to cream paper at the edges"),
    "E2": ("1:1", False, "an imaginary cute little child storybook character (not a real person) smiling and waving, "
           "simple outfit, full body, on plain cream paper background"),
    "E3": ("1:1", False, "a cute small puppy and a cute small kitten sitting side by side as storybook characters, "
           "full body, on plain cream paper background"),
    "E4": ("1:1", False, "a cute imaginary fantasy creature storybook character, a small round fluffy cloud-dragon "
           "with tiny wings and a friendly smile, full body, on plain cream paper background"),
    "E5": ("3:4", False, "front cover art of a Korean traditional folktale picture book: two brothers in hanbok, "
           "a swallow and big round gourds on a thatched roof, warm traditional mood, no title"),
    "E6": ("3:4", False, "front cover art of a Western fairy tale picture book: a small castle on a hill, a forest "
           "path and a little red-hooded girl from behind, classic European fairy tale mood, no title"),
    "E7": ("3:4", False, "front cover art of an original new picture book: a little bunny riding a paper boat on a "
           "moonlit river under big stars, fresh imaginative mood, no title"),
}

pool = GeminiPool()
client = pool.client()
ref_bytes = MALLI_REF.read_bytes()

only = set(sys.argv[1:])
for sid, (ratio, with_ref, scene) in SCENES.items():
    if only and sid not in only:
        continue
    out = IMG / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

    orient = {"16:9": "WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall",
              "1:1": "SQUARE 1:1 image",
              "3:4": "PORTRAIT 3:4 vertical orientation, the image MUST be taller than wide"}[ratio]
    if with_ref:
        prompt = (
            "The attached image is the OFFICIAL character reference sheet of Malli. Reproduce her appearance EXACTLY "
            "(cream curly fur, red bow ribbon on her pink collar, gold bone-shaped tag reading Malli). "
            "Use the sheet ONLY for character design and art style, never copy its layout, labels or extra small figures. "
            "Malli appears exactly ONCE. "
            f"{MALLI}, {scene}. Art style: {STYLE}{MATCH_REF}. {NO_TEXT} except the tiny Malli tag. {orient}, aspect ratio {ratio}."
        )
        contents = [types.Part(inline_data=types.Blob(data=ref_bytes, mime_type="image/png")), types.Part(text=prompt)]
    else:
        prompt = (f"{scene}. Art style: {STYLE}. "
                  f"{NO_TEXT}. {orient}, aspect ratio {ratio}.")
        contents = [types.Part(text=prompt)]

    for attempt in range(4):
        model = MODEL if attempt < 2 else FALLBACK_MODEL
        try:
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"],
                                                   image_config=types.ImageConfig(aspect_ratio=ratio)),
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
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed - stop, report to user")

print("ALL DONE")
