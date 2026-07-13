# 아웃의 종류 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 판정·다이어그램 주제라 AI가 영문 라벨을 넣기 쉬움 → 텍스트·숫자 금지 강하게 명시
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
    "s01": "dramatic night stadium moment at home plate: a cartoon runner sliding into home with a dust cloud while a pitcher stretches out an EMPTY open glove to tag him, a baseball lying far away on the grass glinting under the lights, umpire silhouette mid-out-call behind, tense controversial freeze-frame energy",
    "s02": "playful cartoon concept: four floating panels around one glowing baseball at center — a swinging batter missing, a fielder catching a high fly ball, a fielder stepping on a base, a fielder touching a sliding runner with a glove, bright sunny stadium, simple friendly icon-style composition without any labels",
    "s03": "cartoon wide shot: an outfielder catching a high fly ball at the warning track while far away a runner crouches with one foot planted firmly back on third base ready to sprint, coiled-spring tension, bright daylight stadium, dynamic diagonal composition",
    "s04": "dynamic cartoon double-play sequence feel: an infielder stamping his foot decisively on second base while relaying a throw toward first, a sliding runner arriving a beat too late in a dust cloud, another runner far down the first-base line, twilight stadium, crisp speed lines",
    "s05": "cartoon closeup drama: a fielder's glove clearly bulging with a baseball inside pressed against the leg of a sliding runner, dust bursting around the slide, spotlight from stadium lights, the tag moment frozen, night stadium",
    "s06": "vintage sepia 1840s New York scene: gentlemen in top hats and old suits playing early baseball on an open grass field, one man at a small wooden desk writing with a quill into a thick blank ledger, elm trees and simple rope boundaries, warm nostalgic light",
    "s07": "night KBO stadium climax: a cartoon runner in blue uniform sliding headfirst toward home plate as a pitcher in red uniform sweeps an empty open glove across him, the baseball visibly lying on the grass a few steps away glinting, umpire lunging forward mid-call, packed stands, tense atmosphere, generic stylized faces, no jersey lettering",
    "s08": "cartoon broadcast-replay concept: a huge stadium jumbotron showing a zoomed replay of an empty glove and a separate glowing baseball (screen contains only pictures, absolutely no letters), below it umpires huddling and pointing while players watch from the dugout, deep blue night mood, simple clean composition without any labels",
    "s09": "cartoon split concept: left half a runner joyfully sprinting from third base toward home after a caught fly ball with a soft green hopeful mood, right half an infielder chasing and reaching to tag a hesitant runner stuck between bases with an intense orange mood, sunny stadium, simple friendly comparison feel without any labels",
    "s10": "warm closing scene: three baseballs resting in a row on home plate under calm night stadium lights — one beside a fielder's glove, one on the corner of a white base bag, one below a tall foul pole in the distance, peaceful satisfied end-of-game mood",
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
