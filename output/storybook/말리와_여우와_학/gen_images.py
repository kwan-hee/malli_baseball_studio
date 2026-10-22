# 말리와 여우와 학 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
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
# 이솝 우화 배경. 아늑한 숲속 동물 그림책 톤. 여우·학 의인화, 실존인물 아님.
FOX = "a friendly clever fox with warm orange fur and a fluffy tail, standing upright like a storybook character, expressive gentle eyes, cute NOT scary, cartoon storybook style"
CRANE = "an elegant tall white crane (durumi) with a very long slender neck, long thin pointed beak and long legs, graceful and gentle, standing upright like a storybook character, cartoon storybook style"
FLAT_DISH = "a wide flat shallow plate of warm soup on a small table"
TALL_JAR = "a tall narrow-necked jar (long thin bottle) of food with a slim opening on a small table"
COTTAGE = "a cozy cottage interior with a small dining table, warm homey storybook setting"
FOREST = "a warm green storybook forest with soft rolling meadows and gentle trees"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a grassy green hilltop at the edge of a warm storybook forest under a bright blue sky, warm cheerful storybook mood, {NO_TEXT}, {STYLE}",
    "s02": f"friendly scene at the edge of {FOREST}: the clever {FOX} warmly inviting the elegant {CRANE} to dinner, gesturing toward his home with a sly cheerful smile while the crane looks happy and excited, warm inviting mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"dinner scene in the fox's {COTTAGE}: the {FOX} happily lapping up soup from {FLAT_DISH} with his tongue, while the {CRANE} beside him taps his long beak helplessly on the wide flat plate unable to eat, subtly awkward mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"quiet sad scene in the fox's {COTTAGE}: the {CRANE} sitting hungry with an empty flat plate looking downcast and disappointed, while the {FOX} licks the last of the soup pretending innocence, gently sad wistful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on the grassy hilltop with a paw on her chin looking thoughtful and a little indignant at the viewer, big warm dark eyes, gentle wondering mood, {NO_TEXT}, {STYLE}",
    "s06": f"elegant dinner scene in the crane's {COTTAGE}: the graceful {CRANE} dipping his long beak into {TALL_JAR} to daintily eat, while the {FOX} sits across the table eyeing the tall narrow jar eagerly, cozy anticipating mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"comical scene in the crane's {COTTAGE}: the {FOX} desperately circling and pawing at {TALL_JAR} with his blunt nose unable to reach the food inside, looking flustered and hungry, while the {CRANE} eats calmly, funny rueful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"touching scene in the crane's {COTTAGE}: the {FOX} lowering his head with a red blushing embarrassed face apologizing sincerely, while the gentle {CRANE} smiles kindly and understandingly at him, warm reconciling mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"heartwarming scene in the crane's {COTTAGE}: the {FOX} and the {CRANE} sitting together happily sharing food from a wide shallow dish that both can eat from, chatting warmly as true friends, cozy joyful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop by the storybook forest under a bright sky, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
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
