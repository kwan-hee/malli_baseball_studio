# 승계주자 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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

# cp949 콘솔 print 크래시 방지 (2026-07-18 유료루프 교훈)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    "s01": "cartoon baseball paradox moment: a relief pitcher freshly standing on the mound with a worried look, the bases loaded with three base runners, and the runners all dashing toward home plate to score, a big glowing golden question mark floating above a blank empty scoreboard, bright daytime stadium, exciting puzzling mood, plain white bases NO letters NO numbers NO digits",
    "s02": "cartoon explainer scene: a tired starting pitcher walking off the mound toward the dugout while a fresh relief pitcher walks on to take over, and base runners still standing on the bases being handed over between them, a glowing hand-off arrow, clear friendly rulebook mood, bright field, plain bases NO numbers NO letters",
    "s03": "cartoon concept moment: a base runner crossing home plate to score while a bright glowing arrow curves away from the current relief pitcher on the mound and points back to the previous pitcher who already left toward the dugout, showing the run is charged to the earlier pitcher, clear teaching mood, bright stadium, plain bases NO numbers NO letters",
    "s04": "cartoon vintage concept: an old worn open baseball rulebook lying on a wooden table under warm sepia light, a quill pen and an old-time baseball beside it, a nostalgic historical mood evoking the early days of the rules, NO readable text NO numbers NO letters on the pages, just blank aged pages",
    "s05": "cartoon old-time concept: an old-fashioned official scorer in a vintage cap sitting at a small desk in a wooden press box, scratching his head and hesitating with a pen over a blank scoring sheet, a glowing golden question mark above him showing uncertainty over who is responsible, sepia-tinged historical mood, NO numbers NO letters NO readable text",
    "s06": "cartoon KBO contrast scene: two relief pitchers, one in an orange uniform and one in a blue uniform, looking dismayed on the mound while several base runners stream across home plate scoring behind them, a previous pitcher slumping sadly in the dugout, generic stylized faces no real person, bright stadium, plain bases NO numbers NO letters NO digits",
    "s07": "cartoon metaphor scene: a relief pitcher on the mound smiling and looking clean and proud in front, while behind his back a small hidden fire of runs scoring is quietly tucked away out of sight, a sly accounting-trick mood, bright field, NO text NO numbers NO letters",
    "s08": "cartoon contrast concept: split feeling in one image, on the surface a relief pitcher glowing bright and spotless like a shiny clean shield, while underneath and behind him many base runners are pouring across home plate scoring, revealing the hidden truth, dramatic revealing mood, bright stadium, plain bases NO numbers NO letters",
    "s09": "cartoon heroic scene: a dependable relief pitcher firmly tagging out and shutting down inherited base runners before they can reach home, a defiant confident protective stance with a glowing shield aura, a trustworthy bullpen ace mood, bright stadium, plain bases NO numbers NO letters",
    "s10": "warm closing scene: a baseball glove and a single baseball resting on the pitcher's mound rubber under calm evening stadium lights with a blank dark scoreboard in the far background, a soft golden glow, peaceful satisfied end-of-story mood, NO numbers NO letters NO digits",
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
