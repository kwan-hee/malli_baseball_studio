# 강의 CH1-3 「그림체 기준 그림 정하기」 — 이미지 생성 (Gemini, 2026-10-29 2차 게이트 승인)
# N: 릴리 교실 장면 = 클립 시작 프레임 / W: 일부러 틀린 그림체 / T: 호랑이 X·O / V1·V2: 실습 결과(실제 생성)
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

# id: (릴리 등장, 말리 등장, 장면)
# 1-1·1-2 그림(I04·I06·I09·I15~I18·J05·M01~M08·B01)은 다시 만들지 않고 images/ 로 복사해 재사용
SCENES = {
    "N01": (True, True, "Lily walks into the classroom from the right side holding two sheets of cream paper "
            "(a small character sheet and a small landscape painting, both too small to see details) against her "
            "chest with one arm, waving hello at the viewer with her other hand, bright welcoming smile; Malli sits "
            "on the teacher's desk wagging her tail"),
    "N02": (True, True, "Lily stands at a small wooden easel beside the desk holding a paintbrush and a little "
            "watercolor palette, gently painting soft pale color washes on a sheet of cream paper (only blurry soft "
            "color patches, nothing recognizable), her body half-turned so her smiling face is visible; Malli sits "
            "on the desk watching curiously"),
    "N03": (True, True, "Lily stands in front of the blank chalkboard holding up one sheet of cream paper in each "
            "hand toward the viewer: the left sheet shows tiny soft blurry puppy sketches, the right sheet shows a "
            "tiny soft blurry pastel landscape, both too small to recognize details; warm smile; Malli sits on the "
            "desk looking up at the papers"),
    "N04": (True, True, "Lily stands beside the desk holding up two round wooden paddle signs, one in each hand: "
            "the left paddle shows a big simple red X mark, the right paddle shows a big simple green circle O mark "
            "(only these simple shapes, no letters); playful smile; Malli sits on the desk looking at the signs"),
    # 그림체만 틀린 말리 (일부러 틀린 예시) — 4번째 칸은 지금 수채화 말리(기존 M 그림)를 로컬 합성
    "W01a": (False, True, "Malli sitting and facing the viewer on a plain soft background. DELIBERATELY DIFFERENT "
             "ART STYLE: glossy 3D render like a plastic toy figure, shiny smooth surfaces, CGI lighting"),
    "W01b": (False, True, "Malli sitting and facing the viewer on a plain soft background. DELIBERATELY DIFFERENT "
             "ART STYLE: flat bold Japanese TV cel animation, thick black outlines, hard two-tone cel shading, "
             "saturated bright colors"),
    "W01c": (False, True, "Malli sitting and facing the viewer. DELIBERATELY DIFFERENT ART STYLE: dark heavy "
             "gloomy painting, very dark brown-black background, harsh deep shadows across her face, muddy thick "
             "oil paint, somber mood (but Malli herself calm, not hurt)"),
    # 호랑이 X·O (무섭지 않은 그림 기준 비교) — X 도 피·상처 없이 약하게
    "T01": (False, False, "a tiger standing in a DARK night forest with black shadows, showing its sharp white "
            "teeth in a snarl, narrowed glaring eyes, sharp claws visible, cold harsh lighting, a scary mood for "
            "small children (no blood, no wounds, no other animals)"),
    "T02": (False, False, "a chubby round-faced tiger with puffy cheeks standing in a bright sunny daytime forest, "
            "pouting with a grumpy, sulky, mischievous expression, arms crossed, mouth closed (no teeth shown), soft "
            "rounded paws, funny and not scary at all"),
    # 계획서 v2 (2026-10-29 승인) — 티키타카 소품 장면 + 실제 있었던 실수를 다시 그린 예시
    "M09": (False, True, "Malli sits on the teacher's desk proudly holding open a small sketchbook with her front "
            "paws, showing it toward the viewer; the sketchbook page shows only a blurry orange-and-black striped "
            "scribble, nothing recognizable; excited proud open-mouth smile, tail up"),
    "M10": (False, True, "Malli sits on the teacher's desk holding a big round magnifying glass with both front "
            "paws, peering through it at the viewer like a playful little detective, one eye looking huge through "
            "the lens, curious happy expression"),
    "D01": (False, False, "a traditional Korean folk tale scene inside a thatched-roof house: a middle-aged woman "
            "and a girl in simple hanbok bow slightly toward a kind girl, as if saying sorry, BUT both of them are "
            "deliberately drawn with grumpy scowling glaring eyes and pouting mouths (a WRONG example: the "
            "expression does not match an apology)"),
    "D02": (False, False, "a WRONG example for a traditional Korean folk tale: Korean villagers in simple hanbok "
            "walking on a country path, but the village houses behind them are clearly European fairy-tale "
            "cottages with steep pointed roofs, half-timbered walls and brick chimneys (NOT Korean houses at all)"),
}
# 실습 결과 V1·V2 — 강의 화면에 보여 주는 실제 생성 결과 (콘티 S06-05·S06-07)
PRACTICE_PROMPT = (BASE / "practice_prompt.txt")
V2_REQUEST = "Fix only this: {fix}. Keep everything else exactly the same."

pool = GeminiPool()
client = pool.client()
malli_bytes = MALLI_REF.read_bytes()
lily_bytes = LILY_REF.read_bytes()

only = set(sys.argv[1:])
jobs = list(SCENES.items()) + [("V1", None), ("V2", None)]
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
        style = STYLE
        if sid.startswith("W01"):  # 일부러 틀린 그림체 — 시트는 생김새만 참고, 수채화 STYLE 을 붙이지 않음
            ref_note = ref_note.replace("for character design and art style", "for character design (NOT its art style)")
            style = "follow the deliberately different art style described in the scene, NOT watercolor"
        prompt = (f"{ref_note}Characters: {'; '.join(cast) if cast else 'none'}. Scene {CLASSROOM if sid[0] in 'NM' else ''}: "
                  f"{scene}. {FRAME}. Art style: {style}. {NO_TEXT}{' except the tiny Malli tag' if with_malli else ''}. "
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
