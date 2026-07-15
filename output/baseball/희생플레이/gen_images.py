# 희생플레이 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 기록(타율·출루율)·연도 주제라 AI가 숫자를 넣기 쉬움 → 수치 표현 금지, 개수·비유로만 표현
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
    "s01": "paradox moment in a cartoon night stadium: a batter jogging back toward the dugout with a calm proud smile right after being called out at first base, his whole team leaning out of the dugout clapping and cheering warmly for him, umpire's fist raised in an out call, a runner meanwhile standing safely on a plain white base bag, warm puzzled-but-happy energy, the field ground and all base bags are completely plain with NO markings, NO letters, NO base labels",
    "s02": "cartoon bunt scene in daylight: a batter squaring around and gently tapping a soft bunt that dribbles slowly up the first-base line, while a runner sprints hard from first toward second base with a soft glowing arrow showing his path, fielders charging in, teamwork sacrifice mood",
    "s03": "cartoon tag-up concept: an outfielder catching a deep fly ball at the warning track, while a runner pushes off third base at the same moment and dashes home along a glowing golden path, catcher waiting at the plate too late, trade concept of one out for one run, dynamic but friendly",
    "s04": "vintage sepia 1880s baseball scene: an old-time batter in a pillbox cap laying down a bunt while a mustached runner in knickers scampers to second base, spectators in bowler hats politely applauding, an old scorekeeper at a wooden desk with a completely blank paper sheet and a quill looking thoughtful, nostalgic warm tone, the paper is entirely BLANK with no writing",
    "s05": "whimsical cartoon concept: a glowing baseball with tiny angel wings flying along a wavy path that repeatedly rises into warm light and dips into cool shadow bands, three stern rulemakers in old-fashioned suits below alternately giving thumbs up and thumbs down, humorous indecision mood, gentle comedy",
    "s06": "respectful cartoon portrait mood: a veteran generic infielder in a plain white-and-navy uniform executing a perfect delicate bunt with soft focused eyes, behind him a huge neat mountain of baseballs stacked like a monument glowing softly, quiet craftsman dignity, night stadium rim light",
    "s07": "walk-off drama in a cartoon night stadium: a center fielder making the catch very deep near the wall, while a runner from third crosses home plate with arms spread wide in joy, teammates bursting out of the dugout throwing gloves and water in celebration behind him, fireworks bloom over the stands, climactic jubilant energy",
    "s08": "cartoon comparison concept: two batters side by side under spotlights — on the left a bunting batter fully wrapped in a complete glowing golden shield aura, on the right a fly-ball batter wrapped in a shield aura that is only HALF lit with the other half dim, a curious referee-like figure inspecting the half shield with a magnifying glass, playful rule-detail mood, no labels",
    "s09": "cartoon two-panel contrast: left panel in cool grey tones a runner tagging up from second base to third base with a grey dotted path and a neutral shrugging umpire, right panel in warm golden tones a runner tagging up from third base and stomping on home plate with a golden path and a beaming umpire, clear visual contrast without any words",
    "s10": "warm closing scene: a wooden bat leaning against home plate under calm night stadium lights, a single baseball resting beside it and a first base bag glowing softly in the background distance, peaceful satisfied end-of-story mood",
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
