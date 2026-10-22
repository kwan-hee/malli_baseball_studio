# 타점 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 계산식·비교 주제라 AI가 숫자/기호 삽입 쉬움 → 수치·라벨 금지, 화살표·색·아이콘으로만 표현
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
        "cartoon hook scene: bases loaded, a batter hits a clean single and three baserunners come pouring across home "
        "plate scoring together in a joyful rush, the batter proud at first base, teammates cheering from the dugout, "
        "bright packed stadium, generic faces no real person, plain white bases NO numbers NO letters"
    ),
    "s02": (
        "cartoon concept: a batter at the plate connecting with the ball while a glowing golden path leads a runner all "
        "the way home to score, emphasizing driving a runner in for a run, bright field warm mood, plain white home "
        "plate NO numbers NO text"
    ),
    "s03": (
        "cartoon concept of ways to drive in a run WITHOUT text: on one side a batter hitting a solid RBI single, on "
        "another a batter hitting a deep sacrifice fly caught in the outfield while a runner tags up and scores, on "
        "another a bases-loaded walk pushing a runner home, all paths lead a runner to home plate, bright instructive "
        "mood, generic faces NO numbers NO letters"
    ),
    "s04": (
        "cartoon concept: a run scores on a fielding error — a fielder fumbling and dropping the ball with a small puff "
        "while a runner crosses home plate, and a soft faint grey dimming shadow over the batter at the plate showing he "
        "gets no credit, teaching that error runs give no credit, bright field generic faces NO numbers NO letters NO text"
    ),
    "s05": (
        "cartoon double play action: two infielders completing a double play, one throwing the ball to second base and "
        "on to first base for two outs, while in the background a runner quietly crosses home plate and the batter near "
        "home plate looks a little disappointed, plain bright stadium, generic faces no real person, "
        "absolutely NO circle NO cross NO X mark NO symbols NO glow badge NO numbers NO letters NO text"
    ),
    "s06": (
        "cartoon concept: with fewer than two outs a runner on third base trots home easily and safely to score with a "
        "bright confident golden glow, a tiny harmless fielding bobble in the background that did not matter, teaching "
        "the run counts anyway, bright field generic faces NO numbers NO text"
    ),
    "s07": (
        "cartoon concept: a clutch batter smashing a big hit in a tense moment as runners score, glowing hero aura, but "
        "beside him a subtle thoughtful hint that he needed teammates on base first shown by faint glowing footprints of "
        "runners ahead of him, teaching team dependence, bright stadium generic faces NO numbers NO text"
    ),
    "s08": (
        "cartoon vintage 1920s concept: an old-time baseball scorekeeper in a flat cap writing in a big blank scorebook "
        "(no readable text no digits) under warm sepia light, an antique ballpark behind, a nostalgic historical mood "
        "of an early official statistic being born, generic faces NO text NO numbers"
    ),
    "s09": (
        "cartoon KBO highlight scene: a powerful slugger in a bright red baseball uniform driving in runs with a big hit "
        "as runners score and the crowd erupts in celebration, a triumphant record-breaking moment, generic face no real "
        "person, bright daytime stadium, plain white bases NO numbers NO letters"
    ),
    "s10": (
        "warm closing scene: a baseball bat and ball resting on home plate under calm evening stadium lights, "
        "a soft golden hopeful glow, peaceful satisfied end-of-story mood, NO numbers NO letters NO digits"
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
