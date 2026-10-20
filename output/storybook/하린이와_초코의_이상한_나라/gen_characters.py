# 하린이와 초코의 이상한 나라 — 캐릭터 시트 3장(하린·초코·앨리스) 생성 (강의 샘플, 2026-10-20)
# 원본 사진(AI 생성 예시 사진)을 multimodal 참조로 첨부해 수채화 2D 그림책 캐릭터로 변환
# 주의: 이 편은 채널 지브리 앵커(ghibli_style.txt) 대신 수채화 그림책 STYLE 사용 (사용자 선택 — 설계 문서 참조)
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\youtube_longform_agent")
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "characters"
OUT.mkdir(exist_ok=True)

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

STYLE = (
    "soft hand-painted watercolor children's picture book illustration, gentle wet-on-wet watercolor washes "
    "with visible paper texture, delicate thin pencil-like outlines, warm pastel palette, soft rounded cute "
    "proportions, cozy dreamy bedtime mood, NOT 3D render, NOT anime cel shading, NOT photorealistic"
)
SHEET = (
    "character reference sheet on a plain warm off-white paper background: one large full-body front view, "
    "one full-body side view, one back view, and three small head close-ups showing happy, surprised and sleepy "
    "expressions, all of the SAME single character, consistent design across every view, "
    "absolutely NO text, no labels, no names, no letters anywhere"
)

CHARACTERS = {
    "harin": {
        "ref": Path(r"C:\PROJECT\images\portraits\daughter.png"),
        "desc": (
            "a cheerful 6-year-old Korean girl named Harin, based faithfully on the attached photo: "
            "same face shape, same eyes and warm smile, black hair in two low pigtails tied with fluffy "
            "YELLOW pom-pom hair ties, wearing a short-sleeved PINK cotton dress with a gathered skirt, "
            "barefoot-friendly white socks and small pink shoes"
        ),
    },
    "choco": {
        "ref": Path(r"C:\PROJECT\family_test\강아지.jpg"),
        "desc": (
            "a small deep reddish-brown (chestnut, NOT light tan) toy poodle puppy named Choco, based faithfully on the attached photo: "
            "very curly fluffy chestnut-brown coat, LONG FLOPPY HANGING curly ears in EVERY view and EVERY expression (NEVER pointy or upright ears), round teddy-bear face, round fluffy head, shiny black button eyes, "
            "black nose, wearing a thin RED collar, standing on four legs like a real dog (not anthropomorphic)"
        ),
    },
    "alice": {
        "ref": None,
        "desc": (
            "Alice from the 1865 Lewis Carroll book, an original fresh design for this storybook: "
            "a kind 8-year-old girl with long wavy golden hair held by a YELLOW ribbon headband, wearing a "
            "LIGHT GREEN (mint) knee-length dress with puffed sleeves and a small white collar, white stockings, "
            "brown Mary Jane shoes. MUST NOT look like the Disney Alice: NO light-blue dress, NO white pinafore apron, "
            "NO black headband"
        ),
    },
}

pool = GeminiPool()
client = pool.client()

for name, c in CHARACTERS.items():
    out = OUT / f"{name}_sheet.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{name}: cached")
        continue

    parts = []
    if c["ref"]:
        mime = "image/png" if c["ref"].suffix.lower() == ".png" else "image/jpeg"
        parts.append(types.Part(inline_data=types.Blob(data=c["ref"].read_bytes(), mime_type=mime)))
        lead = (
            "The attached photo is the REAL-LIFE MODEL. Turn this exact subject into a storybook character: "
            "keep the recognizable likeness (face, hair, coat, colors) so anyone who knows them recognizes them instantly. "
        )
    else:
        lead = ""
    prompt = (
        f"{lead}Create a {SHEET}. Character: {c['desc']}. Art style: {STYLE}. "
        "WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall."
    )
    parts.append(types.Part(text=prompt))

    for attempt in range(4):
        model = MODEL if attempt < 2 else FALLBACK_MODEL
        try:
            resp = client.models.generate_content(
                model=model,
                contents=parts,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
            done = False
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    data = part.inline_data.data
                    img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                    out.write_bytes(img)
                    print(f"{name}: {len(img):,} bytes ({model})")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part in response")
        except Exception as e:
            err = str(e)
            print(f"{name}: attempt {attempt+1} failed - {type(e).__name__}: {err[:120]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{name}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{name}: all retries failed - stop, report to user")

print("ALL DONE")
