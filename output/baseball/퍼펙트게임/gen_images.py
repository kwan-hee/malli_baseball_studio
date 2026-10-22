# 퍼펙트게임 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
    "s01": "cartoon dramatic baseball moment: a bang-bang close play at first base, a batter-runner sprinting hard toward first base while the first baseman stretches out to catch the throw, the whole play hanging in the balance, a tense pitcher watching from the mound in the background, dramatic spotlight, packed bright stadium crowd, the perfect game on the line, generic faces no real person, plain white base NO numbers NO letters NO digits",
    "s02": "cartoon concept scene: a confident pitcher standing tall on the mound with arms slightly raised, behind him nine defensive fielders all firmly in position, completely empty bases with no baserunners anywhere, an aura of a flawless untouchable game, bright clean stadium, proud perfect mood, plain white bases NO numbers NO letters NO digits",
    "s03": "cartoon comparison concept: a split scene, on the LEFT a batter drawing a walk and trotting to first base as a runner, on the RIGHT completely empty bases with absolutely no runners, a glowing contrast between allowing some runners and allowing zero runners, clear instructive teaching mood, bright field, plain white bases NO numbers NO letters",
    "s04": "cartoon vintage concept: two proud old-time baseball pitchers from the 1880s wearing old-fashioned wool uniforms and small caps, standing on a dusty antique ballfield, warm sepia-toned nostalgic historical atmosphere, an old wooden ballpark grandstand behind them, generic faces no real person, NO numbers NO letters NO text",
    "s05": "cartoon early-1900s concept: a classic vintage pitcher in an old grey wool uniform winding up to throw on the mound in a historic early ballpark, warm sepia nostalgic tone marking a first milestone of a new era, generic face no real person, NO numbers NO letters NO text",
    "s06": "cartoon concept of rarity: a modern pitcher in a clean pinstripe-style uniform being joyfully lifted and celebrated by rushing teammates after an extremely rare flawless game, glowing confetti, only a small handful of shining stars in the sky suggesting how seldom it happens, historic joyful mood, generic faces no real person, NO numbers NO letters NO digits",
    "s07": "cartoon legendary concept: a 1950s pitcher in a classic pinstripe uniform throwing the decisive final pitch of a huge championship game under bright autumn stadium lights, a grand old-time World Series atmosphere with a packed vintage crowd, once-in-history legendary mood, generic face no real person, NO numbers NO letters NO text",
    "s08": "cartoon dramatic controversial moment: a very close play at first base, the first baseman clearly catching the ball with his foot on the bag while the batter-runner arrives a moment later, and the first base umpire spreading both arms wide in a big SAFE gesture, a shocked heartbroken pitcher reacting in the background, tense dramatic controversial mood, bright stadium, generic faces no real person, plain white base NO numbers NO letters",
    "s09": "cartoon bittersweet concept: a Korean baseball pitcher in a KBO-style uniform standing on the mound looking upward with a mix of hope and frustration, so close yet not quite there, a single glowing baseball, a blank empty scoreboard behind, the feeling of a record never yet achieved in decades, wistful mood, generic face no real person, NO numbers NO letters NO digits",
    "s10": "warm closing scene: a baseball and a pitcher's leather glove resting on the pitching mound under calm evening stadium lights, a blank dark scoreboard far in the background, a soft golden hopeful glow, peaceful satisfied end-of-story mood, NO numbers NO letters NO digits",
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
