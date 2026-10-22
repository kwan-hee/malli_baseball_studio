# 강의 챕터1 「시작하기 전에」 — 말리 프레젠테이션 이미지 생성 (Gemini Nano Banana)
# s01·s08: 전체 화면 교실 장면(16:9, 왼쪽은 제목 카드 자리로 비움) → images/  (Veo 클립 시작 프레임)
# s02~s07: 슬라이드 오른쪽에 붙일 말리 포즈(3:4 세로, 단색 크림 배경) → malli/  (make_slides 가 합성)
# 말리 프롬프트는 prompts/malli_character.txt 에서만 파생 + malli_reference.png 멀티모달 참조 (CLAUDE.md 규칙)
# 글자는 make_slides.py 가 렌더 — 이미지에는 어떤 글자도 넣지 않는다
import base64
import sys
import time
from pathlib import Path

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
IMG = BASE / "images"
MALLI_DIR = BASE / "malli"
IMG.mkdir(exist_ok=True)
MALLI_DIR.mkdir(exist_ok=True)

REFS = [Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/style_ref/malli_reference.png"))]
# prompts/malli_character.txt 캐릭터 프롬프트 + 스타일 서픽스 그대로
MALLI = (
    "a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, "
    "pink collar with a gold bone-shaped tag engraved \"MALLI\", soft curly fur, big dark expressive eyes"
)
STYLE = (
    "hand-drawn 2D animation in the style of a Studio Ghibli / Hayao Miyazaki film, "
    "lush hand-painted gouache backgrounds, soft natural lighting and gentle warm atmosphere, "
    "clean confident linework with cel-shaded characters, soft rounded faces and large gentle expressive eyes, "
    "warm nostalgic pastel color palette, cozy whimsical storybook mood, cinematic anime film look, "
    "NOT watercolor, NOT 3D render, NOT generic cartoon, do not change character design"
)

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

CLASSROOM = ("a bright cozy little classroom with soft morning sunlight, a wooden floor, a small potted plant and "
             "a few closed picture books on a low shelf showing only plain colored spines and simple drawn pictures with "
             "ABSOLUTELY NO writing, no letters, no Japanese, no Korean, no characters of any language on any book, "
             "no chalkboard writing")
# v1 은 책 표지에 일본어 같은 가짜 글자가 생겨 재생성 (2026-10-20 QC)
# 포즈 공통: 슬라이드 오른쪽에 합성 → 단색 배경, 몸 전체, 왼쪽(슬라이드 쪽)을 향함
POSE_BG = ("standing alone on a completely plain flat warm cream background (#FBF3E4), no floor line, no shadow "
           "shapes, no props other than the ones described, full body visible with space around her, "
           "she faces slightly toward the LEFT side of the image")

# sid: (출력 폴더, 비율, 장면)
SCENES = {
    "s01": (IMG, "16:9", f"{CLASSROOM}: Malli stands on her hind legs on the RIGHT third of the image next to a small "
            "teacher's easel, happily waving one front paw at the viewer with a big welcoming smile; the LEFT half "
            "of the image is a calm softly blurred pastel wall with nothing on it (empty space for a title card)"),
    "s02": (MALLI_DIR, "3:4", f"Malli standing on her hind legs, cheerfully pointing her right front paw toward the "
            f"LEFT as if introducing a presentation slide, bright excited smile, {POSE_BG}"),
    "s03": (MALLI_DIR, "3:4", f"Malli standing on her hind legs, raising both front paws in a confident cheer, "
            f"eyes sparkling, reassuring 'you can do it!' expression, {POSE_BG}"),
    "s04": (MALLI_DIR, "3:4", f"Malli standing on her hind legs holding a small wooden pointer stick in one paw, "
            f"pointing it toward the LEFT like a little teacher, smart proud smile, {POSE_BG}"),
    "s05": (MALLI_DIR, "3:4", f"Malli sitting and hugging a small round pink piggy bank, relieved gentle smile, "
            f"calm reassuring mood, {POSE_BG}"),
    "s06": (MALLI_DIR, "3:4", f"Malli sitting and holding an open small notebook with blank pages, head tilted "
            f"curiously to one side, friendly helpful expression, {POSE_BG}"),
    "s07": (MALLI_DIR, "3:4", f"Malli standing on her hind legs raising one front paw like making a solemn promise, "
            f"other paw on her chest, sincere earnest but cute expression, {POSE_BG}"),
    "s08": (IMG, "16:9", f"{CLASSROOM}: Malli stands on her hind legs on the RIGHT third of the image, happily "
            "waving goodbye with one front paw, joyful proud smile, a few soft sparkles in the air; the LEFT half "
            "of the image is a calm softly blurred pastel wall with nothing on it (empty space for a title card)"),
}

pool = GeminiPool()
client = pool.client()
ref_bytes = [r.read_bytes() for r in REFS]

for sid, (folder, ratio, scene) in SCENES.items():
    out = folder / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

    orient = ("WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall"
              if ratio == "16:9" else "PORTRAIT 3:4 vertical orientation, the image MUST be taller than wide")
    prompt = (
        "The attached image is the OFFICIAL character reference sheet of Malli. Reproduce her appearance EXACTLY "
        "(cream curly fur, big red bow ribbon on her head, pink collar, gold bone-shaped tag reading MALLI). "
        "Use the sheet ONLY for character design, never copy its layout, labels or extra small figures. "
        "Malli appears exactly ONCE. "
        f"{MALLI}, {scene}. Art style: {STYLE}. "
        "absolutely NO text, no letters, no words anywhere except the tiny MALLI tag. "
        f"{orient}, aspect ratio {ratio}."
    )
    contents = [types.Part(inline_data=types.Blob(data=b, mime_type="image/png")) for b in ref_bytes]
    contents.append(types.Part(text=prompt))

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
                    client = pool.rotate()  # 키 소진 → 다음 계정으로
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed - stop, report to user")

print("ALL DONE")
