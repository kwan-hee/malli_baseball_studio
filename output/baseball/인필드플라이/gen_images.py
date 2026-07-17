# 인필드플라이 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
    "s01": "cartoon baseball paradox moment: a high pop fly ball floating in the infield sky, an infielder standing under it with his glove up but the ball NOT yet caught, while the umpire dramatically punches an out call with one arm raised, base runners looking confused, a big glowing golden question mark floating above, bright daytime stadium, puzzled-but-fun mood, plain white bases NO letters NO numbers",
    "s02": "cartoon explainer scene: an infielder camped comfortably under a high pop fly with his glove ready, runners standing on first and second base, an umpire raising one arm high to the sky to signal, clear friendly rulebook mood, bright infield, plain bases NO numbers NO letters",
    "s03": "cartoon sneaky trick concept: a sly grinning infielder deliberately letting a pop fly drop to the ground on purpose instead of catching it, scheming to scoop it up for a double play, a small mischievous sparkle, runners looking alarmed, tricky cunning mood, NO numbers NO letters",
    "s04": "cartoon tense infield scene: runners on first and second base crouching hesitantly near their bases unsure whether to run as a pop fly hangs in the air above the infield, fielders waiting beneath it, suspenseful frozen moment, bright stadium, plain bases NO numbers NO letters",
    "s05": "cartoon concept: an umpire firmly raising one arm to the sky declaring the batter out while a glowing protective shield appears over the two base runners keeping them safe, the batter walking away already out, reassuring clear mood, bright infield, NO text NO numbers",
    "s06": "cartoon umpire close-up action: an umpire emphatically thrusting one arm straight up to the sky to signal infield fly, mouth open shouting the call, a pop fly high in the background sky and an infielder settling under it, dramatic decisive officiating mood, bright stadium, NO text NO numbers",
    "s07": "cartoon in-play action: the batter already out and walking off, while a base runner boldly dashes toward the next base as a pop fly drops near an infielder, the ball still live, energetic risky base-running mood, glowing motion trail on the runner, plain bases NO numbers NO letters",
    "s08": "cartoon comparison concept: on the LEFT a sharp straight line-drive zipping flat and a bunt popped up softly, both marked with a soft grey X to show they do NOT count; on the RIGHT a nice high arcing pop fly with an infielder under it marked with a bright glowing check-like glow to show it DOES count, clear visual contrast, no words no numbers",
    "s09": "cartoon explainer contrast: a runner clearly standing on FIRST base and another on second base with bright glowing arrows showing they would be forced to run, an infielder grinning at the double-play chance, illustrating why a first-base runner is required, bright infield teaching mood, plain bases NO numbers NO letters",
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
