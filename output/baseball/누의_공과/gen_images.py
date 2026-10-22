# 누의 공과 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 규칙 설명 주제라 AI가 다이어그램 글자/숫자를 넣기 쉬움 → 수치·라벨 금지, 화살표·색으로만 표현
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

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # pro 504 연발 시 Nano Banana 폴백 (GA 모델명, preview는 404)

STYLE = (
    "bright cheerful cartoon illustration, clean bold outlines, friendly beginner-friendly sports composition, "
    "vivid warm colors, sunny baseball stadium mood, generic stylized faces, no real person likeness. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO labels, "
    "NO scoreboard digits, NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": "cartoon baseball mystery moment: a base runner sprinting past second base without touching it and dashing straight toward third base, the umpire standing with arms spread wide calling SAFE while clearly watching, a big glowing golden question mark floating above, bright daytime stadium, puzzled-but-fun mood, plain white bases with NO letters NO numbers",
    "s02": "cartoon concept of base order: a runner running the infield diamond path with bright glowing arrows connecting first, second, third and home in sequence, one base along the way glowing red and being skipped over as the runner steps past it, clean explainer mood, plain bases NO numbers NO letters",
    "s03": "cartoon concept of an appeal play: a runner standing casually safe on a base while a fielder holding the ball turns toward the umpire pointing to make a claim, the umpire waiting with a neutral gesture, a soft glowing spotlight on the fielder's appeal, tricky-rule explainer mood, no words no numbers",
    "s04": "cartoon two-way comparison of appeal methods: on the LEFT a fielder with the ball stepping firmly on a base bag that glows, on the RIGHT a fielder reaching out to physically TAG a runner between bases with a glowing glove, clear visual contrast of the two ways to appeal, no words no numbers",
    "s05": "whimsical cartoon concept: an umpire behind the plate calmly folding his arms and doing nothing even though he clearly saw a rule break, while a small glowing thought bubble hints that the defense must speak up, playful puzzled mood, bright stadium, NO text NO numbers",
    "s06": "cartoon concept of a time limit: a fielder holding the ball with a glowing hourglass floating beside him, the pitcher on the mound about to throw the next pitch as a glowing arrow shows the appeal window closing, urgent tricky-rule mood, plain field NO numbers NO letters",
    "s07": "cartoon stadium scene setting a stage: a runner leading off first base ready to run while the batter swings and drives a deep fly ball toward the right-center outfield gap, bright afternoon ballpark, energetic anticipation mood, plain bases NO numbers NO letters",
    "s08": "dynamic cartoon base running chaos: a runner rounding second base then suddenly reversing direction and scrambling back as outfielders nearly catch the ball, dust kicking up, confused hurried motion, tense exciting infield mood, plain bases NO numbers NO letters",
    "s09": "dramatic cartoon climax: a runner cutting across the grass beside the pitcher's mound taking a shortcut straight to third base while clearly skipping second base, a second baseman holding the ball stepping on second base and pointing to appeal, the umpire punching a big OUT call, a glowing trail marking the illegal shortcut path, surprising game-changing mood, NO text NO numbers",
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
