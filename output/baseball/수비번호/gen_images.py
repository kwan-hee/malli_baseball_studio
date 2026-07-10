# 수비번호 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 이 편은 '번호' 주제라 AI가 영문/숫자 텍스트를 넣기 쉬움 → 텍스트 금지를 강하게 명시
import base64
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

ENV = Path(r"C:\youtube_longform_agent\.env")
API_KEY = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith(("GEMINI_API_KEY=", "gemini=")):
        API_KEY = line.split("=", 1)[1].strip()
        break
if not API_KEY:
    sys.exit("GEMINI_API_KEY not found")

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # pro 504 연발 시 Nano Banana 폴백 (GA 모델명, preview는 404)

STYLE = (
    "bright cheerful cartoon illustration, clean bold outlines, dynamic sports composition, "
    "vivid colors, warm stadium mood, generic stylized faces, no real person likeness. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO jersey numbers, NO scoreboard digits anywhere in the image"
)

SCENES = {
    "s01": "dramatic infield double play at a night stadium: a cartoon shortstop flipping the baseball toward second base while another infielder relays it on to first, three glowing motion-arc lines connecting the infield bases showing the ball whipping around, packed crowd, bright stadium lights, energetic broadcast mood",
    "s02": "top-down cartoon diagram of a baseball diamond with nine stylized fielder figures each glowing at their own position (pitcher, catcher, the four infielders, three outfielders), clean colorful infographic mood, soft glowing position dots, no labels",
    "s03": "a cartoon shortstop fielding a ground ball and throwing to the first baseman, a bright glowing dotted trajectory line tracing the ball's path from shortstop to first base, clean explanatory sports composition, night stadium",
    "s04": "split contrast illustration: on the left a single baseball jersey hanging on a hook representing a personal player, on the right a glowing marker pinned to a spot on the baseball field representing a fixed position, clearly two different concepts, clean cheerful cartoon, no readable text",
    "s05": "vintage sepia scene: a 19th-century American sportswriter in old-fashioned clothes sitting at a wooden desk with a quill pen, a cricket-style scoresheet and an old baseball on the desk, warm nostalgic lamplight, historical mood",
    "s06": "vintage 1900s baseball scene: an old-time team manager in a woolen uniform carefully writing tiny pencil marks into a leather scorebook in the dugout, a classic early ballpark behind, warm sepia nostalgic tone",
    "s07": "explosive triple play action at a KBO night stadium: a third baseman touching third base then firing the ball, the baseball rocketing around the infield with bright glowing speed trails linking third, second and first base, three base runners caught out, dramatic high-energy composition",
    "s08": "playful puzzle illustration: a baseball infield seen from above with the first, second and third basemen lined up in neat left-to-right order, while the shortstop figure stands slightly apart highlighted by a glowing question-mark aura, a friendly 'why is this one different' mood, clean cartoon, no text",
    "s09": "early baseball history scene, sepia vintage: a shortstop standing shallow in the outfield grass acting as a relay man, catching a ball thrown from deep outfield to pass it toward the infield bases, a big old-fashioned open field, showing him as a half-outfielder, nostalgic historical tone",
    "s10": "warm closing scene: a single baseball resting on home plate at golden sunset, faint glowing position dots of a baseball diamond gently fading in the background, an empty peaceful stadium, hopeful end-of-game mood",
}

client = genai.Client(api_key=API_KEY, http_options={"timeout": 300000})

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
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                sys.exit(f"{sid}: quota exceeded - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed")

print("ALL DONE")
