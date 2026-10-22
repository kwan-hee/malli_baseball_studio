# 태그업 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
    "s01": "cartoon baseball paradox moment: an outfielder in the deep outfield has just caught a high fly ball in his glove, while at the same time a base runner from third base is sprinting hard toward home plate, a big glowing golden question mark floating above, bright daytime stadium, exciting puzzling mood, plain white bases NO letters NO numbers",
    "s02": "cartoon explainer scene: a base runner standing with one foot firmly planted on a base, waiting and watching a high fly ball hang in the sky above the outfield, fielders under the ball, the runner hesitant and ready, clear friendly rulebook mood, bright field, plain bases NO numbers NO letters",
    "s03": "cartoon action moment: the exact instant an outfielder's glove closes on a fly ball while a base runner explosively pushes off the base to sprint to the next base, a glowing motion burst at the runner's feet, tense timing showdown, bright stadium, plain bases NO numbers NO letters",
    "s04": "cartoon close-up concept: a fly ball just barely touching the tip of an outfielder's glove leather, and at that very first-touch instant a fast base runner bolts off the base, a small bright spark where ball meets glove and a glowing speed trail on the runner, clever timing trivia mood, NO numbers NO letters",
    "s05": "cartoon appeal-play concept: a base runner who left too early, while a fielder holding the ball steps on the runner's original base and turns to appeal to the umpire, the umpire about to raise a fist, slightly tense fair-judgment mood, bright infield, plain bases NO numbers NO letters",
    "s06": "cartoon concept contrast: a runner safely crossing home plate glowing gently to show the run counts, while in the background a fielder appeals at a base, a soft protective glow over the crossed plate showing it is NOT a force out, reassuring clear teaching mood, bright field, NO text NO numbers",
    "s07": "cartoon sacrifice-fly scene: an outfielder catching a deep fly ball while a third-base runner tags up and dashes home to score, the batter walking off having given himself up, warm heroic teamwork mood, glowing motion trail on the scoring runner, plain bases NO numbers NO letters",
    "s08": "cartoon dramatic base-running scene: a clever base runner racing all the way around toward home while the defense is distracted appealing at another base, a mischievous sparkle and a bold motion trail, surprising exciting turnaround mood, bright stadium, plain bases NO numbers NO letters",
    "s09": "cartoon climactic play: a runner from third base sprinting explosively toward home plate as an outfielder throws the ball in, the throw and the runner converging on home plate for a dramatic close play, dust and glowing motion lines, thrilling decisive mood, plain white home plate NO numbers NO letters",
    "s10": "warm closing scene: a baseball glove and a single baseball resting on a clean white base bag on an outfield-edge under calm stadium lights, a soft golden glow, peaceful satisfied end-of-story mood, NO numbers NO letters",
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
