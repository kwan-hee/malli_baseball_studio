# 강의 CH2-1 「Claude Code 설치와 로그인」 — 이미지 생성 (Gemini, 2026-10-29 2차 게이트 승인). 템플릿 = CH1-2
# P: 릴리·말리 노트북 장면 = 클립 시작 프레임 (화면 속 글자 금지 — 정확한 화면은 캡처·재현 카드가 담당)
# 릴리 = prompts/lily_character.txt 외형 + lily.png 참조, 말리 = prompts/malli_character.txt 문구 + malli_reference.png 참조
# 글자는 로컬 렌더 — 이미지에는 어떤 글자도 넣지 않는다 (말리 태그 제외)
import base64
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_agent = next((_p / "youtube_longform_agent" for _p in Path(__file__).resolve().parents
               if (_p / "youtube_longform_agent").is_dir()), Path(r"C:\youtube_longform_agent"))
sys.path.insert(0, str(_agent))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
IMG = BASE / "images"
IMG.mkdir(exist_ok=True)

ROOT = [_p for _p in BASE.resolve().parents if (_p / "AGENTS.md").is_file()][-1]
MALLI_REF = ROOT / "images/style_ref/malli_reference.png"
LILY_REF = ROOT / "images/style_ref/lily.png"

MALLI = (
    "a small fluffy cream-colored Maltipoo puppy named Malli with a red bow ribbon on her pink collar, "
    "a gold bone-shaped tag engraved \"Malli\" hanging from the collar, soft curly fur, long floppy curly ears "
    "(NEVER pointed or upright), big dark expressive eyes, black button nose, fluffy curled tail"
)
LILY = (
    "Lily, a friendly Korean woman teacher: long straight dark brown-black hair past the chest with a center part, "
    "round soft face, dark brown eyes, warm smile, light rosy cheeks, black blazer over a white knit top, "
    "wide black trousers, white sneakers, thin gold necklace with two interlocking rings, small round gold brooch "
    "on the left lapel"
)
CLASSROOM = (
    "inside the same cozy bright storybook classroom: a green chalkboard on the back wall (blank, nothing written), "
    "a wooden teacher's desk, a low bookshelf with colorful picture books (covers and spines show ONLY simple "
    "pictures and plain colors, absolutely no lettering on any book), a big window with soft daylight on the "
    "left, a potted plant, warm wooden floor"
)
STYLE = (
    "soft hand-drawn watercolor and pencil illustration on warm cream textured paper, gentle Japanese animation "
    "storybook style, clean delicate linework, pastel palette, soft shadows, exactly matching the attached reference "
    "sheets' art style, NOT 3D render, NOT generic cartoon"
)
NO_TEXT = "absolutely NO text, no letters, no words, no numbers, no signature anywhere"
FRAME = "medium-wide shot, characters fully inside the frame with space around them for movement"

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

# id: (릴리 등장, 말리 등장, 장면)  — P = 클립 시작 그림 4장 (gate2_plan.md)
# 1-2 그림(I04·I06·I09·I16~I18·J05·M01~M08·B01)은 다시 만들지 않고 images/ 로 복사해 재사용
LAPTOP = ("a small silver laptop whose screen shows only a plain dark or softly glowing color, absolutely no text, "
          "no letters, no symbols on the screen")
SCENES = {
    "P01": (True, True, f"Lily walks into the classroom from the right side hugging {LAPTOP} against her chest with "
            "one arm, waving hello at the viewer with her other hand, bright welcoming smile; Malli trots in right "
            "behind her, tail wagging"),
    "P02": (False, True, f"close-up of Malli sitting on the wooden teacher's desk in front of {LAPTOP}; the laptop "
            "screen is plain BLACK; Malli is startled, ears pulled back, eyes wide, leaning slightly away from the "
            "screen, cute not scary"),
    "P03": (False, True, f"close-up of Malli sitting on the wooden teacher's desk in front of {LAPTOP}; the laptop "
            "screen glows a soft reddish light; Malli tilts her head in confusion, one front paw lifted near her "
            "face, flustered but cute; her only red bow is on her pink collar, NOTHING on top of her head"),
    "P04": (True, True, f"Lily sits at the wooden teacher's desk in front of {LAPTOP} that glows softly; Lily raises "
            "both arms in a happy cheer and Malli, sitting on the desk beside the laptop, raises both front paws, "
            "both beaming; a few tiny sparkles in the air"),
}
# 실습 결과 V1·V2 — 강의 화면에 보여 주는 실제 생성 결과 (콘티 S05-06·S05-08)
PRACTICE_PROMPT = (BASE / "practice_prompt.txt")
V2_REQUEST = "Fix only this: {fix}. Keep everything else exactly the same."

pool = GeminiPool()
client = pool.client()
malli_bytes = MALLI_REF.read_bytes()
lily_bytes = LILY_REF.read_bytes()

only = set(sys.argv[1:])
jobs = list(SCENES.items())
for sid, spec in jobs:
    if only and sid not in only:
        continue
    out = IMG / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

    if sid == "V1":  # 강의 프롬프트 그대로, 첨부 없음 (Gemini 앱에 붙여 넣는 것과 같은 조건)
        parts = [types.Part(text=PRACTICE_PROMPT.read_text(encoding="utf-8"))]
    elif sid == "V2":  # V1 첨부 + 틀린 곳만 고쳐 달라는 한 줄 (v2_fix.txt 는 V1 검수 후 작성)
        fix = BASE / "v2_fix.txt"
        if not fix.exists():
            print("V2: v2_fix.txt 없음 → V1 검수 후 작성하고 다시 실행")
            continue
        parts = [types.Part(inline_data=types.Blob(data=(IMG / "V1.png").read_bytes(), mime_type="image/png")),
                 types.Part(text=V2_REQUEST.format(fix=fix.read_text(encoding="utf-8").strip()))]
    else:
        with_lily, with_malli, scene = spec
        parts, refs, cast = [], [], []
        if with_lily:
            parts.append(types.Part(inline_data=types.Blob(data=lily_bytes, mime_type="image/png")))
            refs.append("the character sheet of Lily the teacher")
            cast.append(LILY)
        if with_malli:
            parts.append(types.Part(inline_data=types.Blob(data=malli_bytes, mime_type="image/png")))
            refs.append("the official character sheet of Malli the puppy")
            cast.append(MALLI)
        ref_note = ""
        if refs:
            ref_note = (f"The attached images are {' and '.join(refs)}. Reproduce each character's appearance EXACTLY. "
                        "Use the sheets ONLY for character design and art style, never copy their layout, labels or "
                        "extra small figures. Each character appears exactly ONCE. ")
        if sid == "W02":  # 일부러 틀린 예시 — 작은 말리 복제를 금지하는 문장을 빼야 함
            ref_note = ref_note.replace(" Each character appears exactly ONCE.", "")
        prompt = (f"{ref_note}Characters: {'; '.join(cast) if cast else 'none'}. Scene {CLASSROOM}: "
                  f"{scene}. {FRAME}. Art style: {STYLE}. {NO_TEXT}{' except the tiny Malli tag' if with_malli else ''}. "
                  "WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall, aspect ratio 16:9.")
        parts.append(types.Part(text=prompt))

    for attempt in range(4):
        model = MODEL if attempt < 2 else FALLBACK_MODEL
        try:
            resp = client.models.generate_content(
                model=model,
                contents=parts,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"],
                                                   image_config=types.ImageConfig(aspect_ratio="16:9")),
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
