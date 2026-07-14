# 볼넷 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 볼 개수 주제라 AI가 숫자를 넣기 쉬움 → 개수는 공 무더기로만 표현, 텍스트·숫자 금지 강명시
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

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # pro 504 연발 시 Nano Banana 폴백 (GA 모델명, preview는 404)

STYLE = (
    "bright cheerful cartoon illustration, clean bold outlines, friendly beginner-friendly sports composition, "
    "vivid warm colors, sunny baseball stadium mood, generic stylized faces, no real person likeness. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO labels, "
    "NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": "curious night stadium moment: a cartoon batter calmly laying down his bat and strolling toward first base with a relaxed smile, while the pitcher on the mound stands dumbfounded still holding the baseball in his glove, umpire pointing toward first base, crowd tilting heads, gentle mystery energy",
    "s02": "playful cartoon concept: four glowing baseballs floating in a curved trail that all clearly missed a glowing translucent box above home plate, the batter lowering his bat with a satisfied nod, the umpire extending an arm toward first base, sunny stadium, simple friendly feel without any labels",
    "s03": "cartoon diamond overview from high angle: runners standing on every base of a glowing diamond, soft glowing arrows pushing each runner one base forward, the runner from third stepping onto home plate, a worried pitcher covering his face with his glove on the mound, twilight stadium, no labels",
    "s04": "vintage sepia 1870s baseball scene: an exhausted old-time batter leaning on his bat like a cane at home plate, a big messy pile of many old baseballs scattered around the plate, an underhand pitcher winding up far away, spectators in bowler hats dozing off on wooden bleachers, comically long at-bat mood",
    "s05": "vintage sepia scene: a fierce old-time pitcher throwing overhand with a huge windmill motion, speed lines around the ball, while in the foreground a row of baseball piles gets visibly smaller from left to right — a big pile, then smaller, then just a few balls, rulemakers in suits pointing at the piles, warm nostalgic light, absolutely no numbers anywhere",
    "s06": "cartoon night scene: a catcher standing fully upright far outside home plate catching a wide lazy pitch, the batter at the plate shrugging with the bat resting on his shoulder, pitcher tossing the ball with a bored face, old-style intentional walk mood, gentle humor",
    "s07": "modern KBO night stadium: a manager at the dugout rail calmly raising four fingers toward the umpire, the umpire pointing to first base, the batter already walking toward first with his bat handed to a bat boy, the pitcher standing idle on the mound never throwing, crowd looking amused, friendly cartoon mood, no text anywhere",
    "s08": "cartoon closeup concept: a batter's calm focused eye in profile with a tiny glowing zone box reflected in the pupil, several baseballs whizzing past OUTSIDE the reflected box with dull trails, patient discipline mood, deep blue background, no labels",
    "s09": "cartoon comparison: left half a batter jogging to first while rubbing his forearm guard with a wry smile after being grazed by a pitch (soft, comical, not painful), right half a batter walking to first calmly after four wide pitches, both arriving at the same first base bag, sunny stadium, simple friendly comparison without any labels",
    "s10": "warm closing scene: a white first base bag under calm night stadium lights with four baseballs resting in a neat row beside a wooden bat, soft glow, peaceful satisfied end-of-game mood",
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
