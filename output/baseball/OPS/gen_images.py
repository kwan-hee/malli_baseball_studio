# OPS — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
    "s01": "cartoon baseball comparison moment: two batters side by side, one on the left mid-swing crushing a powerful home run with a bright hit spark, the other on the right hitting a modest single and running to first base, a big glowing golden question mark floating between them above a blank empty scoreboard, bright daytime stadium, curious comparing mood, plain white bases NO letters NO numbers NO digits",
    "s02": "cartoon explainer scene: a friendly batter standing at home plate with two glowing icons merging above him, one icon showing a runner safely reaching base and one icon showing a ball flying far, the two merging into one bright combined glow, clear friendly teaching mood, bright field, plain bases NO numbers NO letters",
    "s03": "cartoon concept scene: a patient batter calmly drawing a walk and trotting to first base after the pitcher misses, a soft glowing path leading him to the base, emphasizing getting on base by any means, cheerful instructive mood, bright stadium, plain white bases NO numbers NO letters",
    "s04": "cartoon power scene: a strong slugger batter finishing a huge swing as the ball rockets over the outfield fence for a home run, a bold glowing arc trail on the ball and a burst of impact, dynamic powerful mood, bright stadium, plain bases NO numbers NO letters NO digits",
    "s05": "cartoon tier concept: a proud elite batter standing tall on a small podium with a glowing golden crown and a shining trophy beside him, radiating a top-hitter aura, celebratory admiring mood, bright stadium background, NO numbers NO letters NO digits",
    "s06": "cartoon vintage concept: an old worn open baseball statistics ledger book lying on a wooden desk under warm sepia light, a pencil and an old-time baseball beside it, a nostalgic 1980s historical mood evoking the birth of a new stat, NO readable text NO numbers NO letters on the pages, just blank aged pages",
    "s07": "cartoon KBO highlight scene: a powerful slugger in a light sky-blue baseball uniform crushing a massive home run, the ball soaring into a cheering stadium crowd, triumphant record-breaking mood, generic stylized face no real person likeness, bright daytime stadium, plain bases NO numbers NO letters NO digits",
    "s08": "cartoon math concept: a cheerful friendly batter standing beside a big bright glowing green PLUS sign shaped like a cross of one vertical bar and one horizontal bar (the addition symbol, like +), the plus sign upright and clearly a PLUS, absolutely NOT an X, NOT a diagonal cross, NOT a multiplication mark, clean bright teaching mood, bright baseball field, only the upright plus symbol and NO other text NO numbers NO letters",
    "s09": "cartoon balance concept: a large glowing scale where the on-base side sits a little heavier than the slugging side showing they are not perfectly equal, a thoughtful clever mood suggesting a more refined measure, bright stadium background, NO numbers NO letters NO readable text",
    "s10": "warm closing scene: a baseball bat and a single baseball resting on home plate under calm evening stadium lights with a blank dark scoreboard in the far background, a soft golden glow, peaceful satisfied end-of-story mood, NO numbers NO letters NO digits",
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
