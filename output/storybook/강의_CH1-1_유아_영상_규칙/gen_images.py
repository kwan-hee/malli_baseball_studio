# 강의 CH1-1 「5~7세 영상 규칙」 — 이미지 생성 (Gemini, 2차 게이트 승인 2026-10-29, A안)
# I: 릴리(+말리) 교실 장면 16:9 = Kling 클립 시작 프레임·릴리 정지 장면 / M: 말리 단독 리액션 16:9 / B: 빈 교실(카드 배경)
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
SCENES = {
    "I01": (True, True, "Lily has just opened the classroom door on the right side and is stepping in, waving hello "
            "at the viewer with a bright welcoming smile; Malli sits on the floor near the desk looking at her happily"),
    "I02": (True, True, "Malli is crouched on the floor right next to the teacher's desk, about to jump up onto it, "
            "tail up; Lily stands beside the desk smiling down at her warmly, hands lightly clasped"),
    "I03": (True, True, "Lily stands in the middle of the room facing the viewer, a few steps away from the "
            "chalkboard, turning her body toward it with one open hand starting to gesture at the board; Malli sits "
            "on the teacher's desk watching"),
    "I04": (True, True, "Lily stands near the desk, one hand gently on her chest, smiling kindly and sincerely at "
            "the viewer as if reassuring the audience; Malli sits on the desk beside her"),
    "I05": (True, True, "Lily kneels down on one knee at a small child's eye level in the front of the room, holding "
            "a closed picture book with a plain pastel cover in both hands toward the viewer, gentle smile; Malli "
            "sits next to her knee"),
    "I06": (True, True, "Lily sits on a small chair and gently strokes Malli, who sits on her lap looking content; "
            "Lily looks at the viewer with a soft smile"),
    "I07": (True, True, "Lily stands behind the teacher's desk holding a wooden hourglass in one hand at chest "
            "height, smiling; Malli sits on the desk looking at the hourglass curiously"),
    "I08": (True, True, "Lily stands at the chalkboard holding a piece of white chalk against the blank board, "
            "her body half-turned so her smiling face is visible; Malli sits on the floor below watching"),
    "I09": (True, True, "Lily stands next to the desk giving a cheerful thumbs-up to the viewer with a playful wink; "
            "Malli sits on the desk wagging her tail"),
    "I10": (True, True, "Lily stands behind the desk with a small wicker basket of red apples on it, one hand "
            "reaching into the basket; Malli sits on the desk peeking into the basket"),
    "I11": (True, True, "Lily stands in the front center with both hands pressed together in front of her chest as "
            "if about to do a little magic trick, excited playful smile; Malli sits at her feet looking up"),
    "I12": (True, True, "Malli looks a little startled with big round eyes on the floor and Lily is bending down "
            "with both arms reaching out to gently pick her up, caring reassuring smile"),
    "I13": (True, True, "Lily stands in the front holding two round blank paddle signs (plain round boards on short "
            "handles, one pale green, one pale red, nothing written on them), one in each hand at shoulder height, "
            "playful quizzing expression; Malli sits on the desk thinking hard"),
    "I14": (True, True, "Lily crouches down holding up one open palm toward Malli, and Malli stands on her hind "
            "legs raising one front paw toward Lily's palm, about to high-five, both smiling"),
    "I15": (True, True, "Lily sits at the teacher's desk with an open notebook and a pen, writing; Malli stands "
            "on the desk beside the notebook peeking at it"),
    "I16": (True, True, "Lily bends down with one hand gently reaching toward Malli's head to pat her; Malli sits "
            "on the floor looking up at her lovingly"),
    "I17": (True, True, "Lily and Malli stand side by side in the front center of the classroom facing the viewer, "
            "Lily raising one hand and Malli sitting up raising one front paw, both about to wave goodbye, big smiles"),
    "I18": (True, True, "Lily stands behind the teacher's desk with a silver laptop on it, its screen turned toward "
            "the viewer showing only a plain bright blank screen, Lily pointing at the screen with one finger and "
            "smiling; Malli sits on the desk next to the laptop"),
    "M01": (False, True, "close-up of Malli sitting on the teacher's desk tilting her head to one side with a "
            "puzzled curious expression"),
    "M02": (False, True, "close-up of Malli peeking out from under a soft small blanket on a cushion, covering her "
            "floppy ears with both front paws, a little scared but cute"),
    "M03": (False, True, "close-up of Malli sitting proudly on the desk with one front paw raised confidently and "
            "a proud happy smile"),
    "M04": (False, True, "close-up of Malli on the desk with a playful mischievous grin, eyes half closed, "
            "pretending to be lazy like a cow, sprawled cutely"),
    "M05": (False, True, "close-up of Malli standing on the desk wagging her tail very fast with a huge happy "
            "open-mouth smile, motion lines on the tail"),
    "M06": (False, True, "close-up of Malli with sparkling starry eyes and an amazed delighted expression, ears "
            "lifted just slightly but still long and floppy"),
    "M07": (False, True, "close-up of Malli sitting and crossing both front paws in an X shape in front of her "
            "chest, serious cute determined face"),
    "M08": (False, True, "Malli jumping joyfully in the air above the classroom floor with all four paws off the "
            "ground, floppy ears flying, big happy smile"),
    "M09": (False, True, "close-up of Malli on the desk yawning widely with sleepy half-closed eyes, a tiny tear "
            "in the corner of one eye"),
    "B01": (False, False, "the empty classroom with nobody in it, calm and bright, slightly soft and blurred like a "
            "background, the center area plain and open"),
}

pool = GeminiPool()
client = pool.client()
malli_bytes = MALLI_REF.read_bytes()
lily_bytes = LILY_REF.read_bytes()

only = set(sys.argv[1:])
for sid, (with_lily, with_malli, scene) in SCENES.items():
    if only and sid not in only:
        continue
    out = IMG / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

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
    prompt = (f"{ref_note}Characters: {'; '.join(cast) if cast else 'none'}. Scene {CLASSROOM}: {scene}. {FRAME}. "
              f"Art style: {STYLE}. {NO_TEXT}{' except the tiny Malli tag' if with_malli else ''}. "
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
