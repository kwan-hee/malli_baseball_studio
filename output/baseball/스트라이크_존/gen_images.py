# 스트라이크 존 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 존 다이어그램·ABS 주제라 AI가 영문 라벨·숫자를 넣기 쉬움 → 텍스트·숫자 금지 강하게 명시
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
    "s01": "dramatic night stadium moment: a cartoon pitch streaking toward the outside corner of home plate where a faint glowing translucent box hovers, the ball clipping the very edge of the glow, batter twisting his head in disbelief while the umpire behind rises mid-call, catcher's mitt low and outside, tense energy",
    "s02": "playful cartoon concept: a glowing translucent glass box floating above home plate at a sunny stadium, one baseball flying THROUGH the box leaving a bright trail, another baseball passing clearly outside it with a dull trail, a crouching catcher and umpire watching, simple friendly comparison feel without any labels",
    "s03": "cartoon comparison: two batters standing side by side at home plate — one very tall, one short — each with a differently sized glowing translucent zone box floating over the plate matched to their body, from mid-chest to below the knees, bright daylight stadium, clean simple concept without any labels",
    "s04": "educational cartoon closeup: home plate seen from a low three-quarter angle with a glowing translucent five-sided prism rising above it like a crystal column, a curving baseball just grazing the FRONT edge of the prism with a small spark, deep blue background, sense of hidden geometry, no labels",
    "s05": "vintage sepia early-1880s baseball scene: an old-time batter in vintage wool uniform and pillbox cap holding his palm flat at waist height as if ordering a pitch, the vintage pitcher shrugging comically mid-windup, spectators in bowler hats watching from wooden bleachers, warm nostalgic light",
    "s06": "vintage sepia scene: a confident old-time pitcher throwing with a huge motion while a batter flails at a high pitch, a wooden scoreboard behind completely blank, other vintage players slumping on a bench, dusty golden afternoon, dominant pitcher mood",
    "s07": "futuristic KBO night stadium: a batter in generic navy uniform standing at home plate as a crisp digital glowing zone box materializes over the plate with thin scanning light lines from small cameras on the stadium roof, the pitch frozen mid-air heading for the box edge, high-tech but friendly cartoon mood, absolutely no text or digits anywhere",
    "s08": "cartoon concept: the glowing translucent zone box above home plate gently sliding slightly downward with soft arrows of light around it, a batter and a pitcher watching it move with curious faces, twilight stadium, calm adjustment mood, no labels no numbers",
    "s09": "comedic cartoon moment: a catcher dramatically yanking his mitt from outside the glowing zone box back toward its center right after catching a ball, while the glowing box stays lit exactly where the ball actually passed (clearly outside), umpire unmoved with arms crossed, night stadium, playful busted-trick mood",
    "s10": "warm closing scene: home plate under calm night stadium lights with a soft glowing five-sided prism of light rising above it into the starry sky, a single baseball resting on the plate corner, peaceful satisfied end-of-game mood",
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
