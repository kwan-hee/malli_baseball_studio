# 보크 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

STYLE = (
    "bright cheerful cartoon illustration, clean bold outlines, friendly beginner-friendly sports composition, "
    "vivid warm colors, sunny baseball stadium mood, generic stylized faces, no real person likeness. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO labels, "
    "NO scoreboard digits, NO plus signs, NO X marks, NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": (
        "cartoon dramatic hook scene: a pitcher on the mound frozen mid-motion looking shocked and confused, "
        "with a stern umpire pointing and signaling a violation, runners on base celebrating as they jog to the "
        "next base, a packed stadium with surprised reactions, generic faces no real person, "
        "absolutely NO text NO numbers NO letters"
    ),
    "s02": (
        "cartoon concept: a pitcher on the mound with a cunning sneaky expression trying to trick a baserunner "
        "who is taking a lead off first base, the baserunner looks nervous and suspicious, a big red prohibition "
        "circle overlay suggesting this deceptive move is not allowed, bright field generic faces "
        "NO numbers NO text NO letters"
    ),
    "s03": (
        "cartoon teaching scene showing three panels side by side: left panel a pitcher starting to throw then "
        "stopping mid-motion awkwardly, middle panel a pitcher faking a throw to first base without actually "
        "releasing the ball, right panel a pitcher delivering the ball without fully stopping in set position, "
        "each showing a common balk type, bright field generic faces NO numbers NO text NO letters"
    ),
    "s04": (
        "cartoon comical scene: a pitcher on the mound accidentally dropping the baseball from his hand with a "
        "small puff of dust, looking embarrassed and shocked, the umpire immediately signaling a violation, "
        "runners on base grinning and jogging forward, humorous mood, bright stadium generic faces "
        "NO numbers NO text NO letters"
    ),
    "s05": (
        "cartoon historical scene: a chaotic 1980s-style baseball game with multiple umpires signaling violations "
        "all over the field, a frustrated pitcher throwing his arms up in disbelief, runners happily advancing "
        "on bases, suggesting a season of many balks, vintage warm-toned stadium, generic faces "
        "NO numbers NO text NO letters"
    ),
    "s06": (
        "cartoon dramatic action scene: a pitcher on the mound looking horrified as three ghostly translucent "
        "baserunner silhouettes advance from second to third to home plate in sequence suggesting three consecutive "
        "balks scoring a run, the catcher face-palming behind home plate, dramatic spotlight mood, "
        "generic faces no real person NO numbers NO text NO letters"
    ),
    "s07": (
        "cartoon tense playoff scene: a pitcher on the mound in a dark navy uniform sweating heavily under "
        "bright night stadium lights, an umpire dramatically pointing to signal a violation, a runner on third "
        "base crossing home plate while the opposing dugout erupts in celebration, heartbreaking intense mood, "
        "generic faces no real person NO numbers NO text NO letters"
    ),
    "s08": (
        "cartoon dramatic scene: a pitcher angrily slamming a baseball into the ground in frustration on the "
        "mound while the umpire signals a violation and runners advance, tense emotional playoff atmosphere "
        "under night stadium lights, another smaller inset showing a pitcher accidentally dropping the ball "
        "from his glove on the mound looking shocked, generic faces no real person NO numbers NO text NO letters"
    ),
    "s09": (
        "cartoon clever strategy scene: a pitcher on the mound deliberately stepping off and gesturing toward "
        "third base with a knowing smirk, a runner reluctantly moving from second to third base, the catcher "
        "giving a subtle thumbs-up suggesting this was an intentional strategic move, smart tactical mood, "
        "bright stadium generic faces NO numbers NO text NO letters"
    ),
    "s10": (
        "warm closing scene: a baseball resting on a pitcher's mound rubber plate under calm evening stadium "
        "lights, a soft golden hopeful glow, peaceful satisfied end-of-story mood, "
        "NO numbers NO letters NO digits"
    ),
}

pool = GeminiPool()
client = pool.client()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue
    prompt = f"{scene}. {STYLE}. WIDE LANDSCAPE 16:9 horizontal orientation, the image MUST be wider than tall, aspect ratio 16:9, resolution 1920x1080."
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
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed")

print("ALL DONE")
