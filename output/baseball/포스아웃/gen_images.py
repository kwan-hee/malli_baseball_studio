# 포스아웃 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 규칙 설명 주제라 AI가 다이어그램 글자/숫자를 넣기 쉬움 → 수치·라벨 금지, 화살표·색으로만 표현
# 가로(16:9) 강제 문구 필수 — flash 폴백 세로 드리프트 방지 (2026-07-16 임금님귀 편 교훈)
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
    "NO scoreboard digits, NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": "cartoon baseball paradox moment: a first baseman stepping on first base with the ball while the batter-runner arrives, the umpire punching an out call, the fielder clearly NOT touching the runner's body, a big glowing golden question mark floating above, bright daytime stadium, puzzled-but-fun mood, plain white bases with NO letters NO numbers",
    "s02": "cartoon concept of a forced runner: a batter hitting the ball and running toward first base, and a runner on first base being pushed toward second base along a bright glowing arrow as if forced, showing that the runner has nowhere to stay, dynamic teamwork infield mood, plain bases NO numbers NO letters",
    "s03": "cartoon force out at first base: a first baseman firmly stepping on the base bag with the ball in his glove while the batter-runner slides in, the fielder deliberately NOT tagging the runner, a soft glow highlighting the base being touched, clear friendly explainer mood, NO numbers NO letters",
    "s04": "cartoon comparison of two plays side by side: on the LEFT a fielder tapping a base bag to get a forced runner out with a glowing base; on the RIGHT a fielder reaching out to physically TAG a runner who is between bases with a glowing glove, a clear visual contrast between touching-the-base and tagging-the-body, no words no numbers",
    "s05": "whimsical cartoon concept: a big glowing question mark hovering over home plate while a runner slides across it and a blank scoreboard glows in the background unchanged, a puzzled but playful mood, bright stadium, NO text NO numbers",
    "s06": "dynamic cartoon double play: a shortstop stepping on second base to force out a sliding runner and immediately firing the ball toward first base, the ball streaking with a glowing motion trail, two outs on one play, energetic exciting infield action, plain bases NO numbers NO letters",
    "s07": "cartoon concept of a force being removed: a runner sliding into a base looking safe and relaxed while a fielder holding the ball looks frustrated realizing he must TAG the runner now, a broken chain symbol glowing softly above to show the force is released, tricky rule mood, no words no numbers",
    "s08": "cartoon dramatic concept: a runner crossing home plate at the exact same moment a fielder steps on second base forcing out another runner for the third out, a glowing X mark appears over home plate to show the run does NOT count, a blank scoreboard staying unchanged in the background, surprising rule twist mood, NO text NO numbers",
    "s09": "cartoon two-panel contrast: LEFT panel a fielder tapping a base with the ball and an umpire calling OUT even though the runner was not touched (a force out); RIGHT panel a fielder tapping a base while an umpire spreads arms SAFE because the runner was not forced and needed a tag, clear visual contrast without any words or numbers",
    "s10": "warm closing scene: a baseball glove and a single baseball resting on a clean white base bag on an infield under calm stadium lights, a soft golden glow, peaceful satisfied end-of-story mood, NO numbers NO letters",
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
                    client = pool.rotate()  # 키 소진 → 다음 계정으로
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed")

print("ALL DONE")
