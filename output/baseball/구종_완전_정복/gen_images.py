# 구종 완전 정복 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 그립·궤적 다이어그램 주제라 AI가 영문 라벨을 넣기 쉬움 → 텍스트·숫자 금지 강하게 명시
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

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # pro 504 연발 시 Nano Banana 폴백 (GA 모델명, preview는 404)

STYLE = (
    "bright cheerful cartoon illustration, clean bold outlines, friendly beginner-friendly sports composition, "
    "vivid warm colors, sunny baseball stadium mood, generic stylized faces, no real person likeness. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO labels, "
    "NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": "dramatic side view of a cartoon pitch sliding sharply sideways past a lunging batter who swings and misses, glowing curved motion trail behind the ball, night stadium lights, dynamic surprising energy",
    "s02": "playful cartoon concept: a big closeup baseball with prominent red stitching floating above an open restaurant-style menu board held by a cartoon pitcher (menu board completely blank, no letters), warm sunny stadium background",
    "s03": "cartoon closeup of a pitcher's hand gripping a baseball across four visible red seam lines, next to it a straight glowing trajectory line flying flat and fast toward a catcher's mitt, bright daylight stadium",
    "s04": "cartoon closeup of a pitcher's hand with two fingers resting along two parallel red seam lines of a baseball, next to it a glowing trajectory line that tails sideways and sinks downward near home plate, batter hitting a weak ground ball, sunny field",
    "s05": "clean cartoon comparison of two glowing pitch trajectories over one home plate: one line sliding sharply sideways, the other arcing up then dropping steeply down like a rainbow, a crouching catcher watching both, twilight stadium, simple friendly infographic feel without any labels",
    "s06": "comedic decisive moment: a cartoon batter swinging way too early at a slow floating ball that is still far from the plate, his body twisted around from the wasted swing, catcher calmly waiting with open mitt, night stadium, funny exaggerated timing",
    "s07": "vintage sepia 1860s scene: a young man in old 19th-century clothes on a seaside beach throwing a clam shell that curves visibly through the air, wide-eyed wonder on his face, other boys watching, warm nostalgic light",
    "s08": "night KBO stadium mound montage: three cartoon pitchers seen from behind in different generic uniforms (blue, red, green), each releasing a ball with a differently curving glowing trail, packed cheering stands, heroic atmosphere, faces not visible",
    "s09": "educational cartoon closeup of a baseball spinning rapidly with strong backspin, curved white motion arcs around it showing rotation, air flow lines streaming past the red seams, deep blue background, sense of hidden physics",
    "s10": "warm closing scene: five baseballs resting in a neat row on the pitcher's mound of a calm night stadium, each ball glowing softly in a different color, peaceful satisfied end-of-game mood",
}

pool = GeminiPool()
client = pool.client()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue
    prompt = f"{scene}. {STYLE}. Aspect ratio 16:9, resolution 1920x1080."
    for attempt in range(4):
        model = MODEL if attempt < 2 else FALLBACK_MODEL
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
            done = False
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    data = part.inline_data.data
                    img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                    out.write_bytes(img)
                    print(f"{sid}: {len(img):,} bytes")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part")
        except Exception as e:
            err = str(e)
            print(f"{sid}: attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()  # 키 소진 → 다음 계정으로
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed")

print("ALL DONE")
