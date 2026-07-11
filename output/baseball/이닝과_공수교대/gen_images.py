# 이닝과 공수교대 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 전광판·회 표시 주제라 AI가 영문/숫자 텍스트를 넣기 쉬움 → 텍스트·숫자 금지 강하게 명시
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
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO scoreboard digits anywhere in the image"
)

SCENES = {
    "s01": "a bright cartoon baseball stadium at night with a big glowing scoreboard panel (completely blank, no digits, no text), a giant glowing question mark floating above the field, excited fans in the stands wondering, curious energetic mood",
    "s02": "a clean top-down cartoon baseball diamond split into two halves showing the idea of two teams taking turns batting, one team in blue jerseys and one in red jerseys, simple friendly infographic feel, no labels",
    "s03": "dynamic changeover moment at a sunny stadium: both teams of cartoon players jogging and running across the field to swap sides, one group heading out to field positions and the other running back to the dugout, dust and motion, energetic",
    "s04": "a cheerful row of nine small identical baseball icons arranged in a line representing nine innings (just plain baseballs, no numbers), a simple friendly diagram on a sunny green field background",
    "s05": "vintage sepia 1857 scene: a group of men in old 19th-century clothes gathered around a wooden table agreeing on baseball rules, an open old rulebook and a baseball on the table, warm historical lamplight",
    "s06": "vintage sepia old-time baseball game that has dragged on forever, an exhausted team piling up many runs while the sun sets low, tired players and a nearly empty old ballpark, gently comedic long-game mood",
    "s07": "a modern KBO night stadium in extra innings, a tired but determined relief pitcher on the mound, a glowing blank pitch-clock panel on the wall (no digits), late-night atmosphere with bright lights",
    "s08": "a home team of cartoon players already happily walking off the field because they are winning, relaxed smiling faces as the game simply ends, warm early-evening stadium, satisfied mood",
    "s09": "explosive walk-off home run at a packed night stadium: a home-team cartoon batter crushing the ball high over the outfield fence, teammates rushing out of the dugout to celebrate, confetti and joy, dramatic dynamic motion",
    "s10": "warm closing scene: a calm baseball stadium at night with a softly glowing blank scoreboard, a single baseball resting on the pitcher's mound, peaceful end-of-game mood",
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
