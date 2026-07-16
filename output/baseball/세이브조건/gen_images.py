# 세이브조건 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
# 주의: 기록(세이브 개수)·연도 주제라 AI가 숫자를 넣기 쉬움 → 수치 표현 금지, 개수·비유로만 표현
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
    "s01": "cartoon night stadium: a determined relief pitcher (closer) walking in from the bullpen gate toward the mound under bright stadium lights, his team leading, a blank scoreboard glowing in the background with NO numbers, tense-but-cool late-game mood, spotlight rim light",
    "s02": "cartoon concept of guarding a lead: a calm closer pitcher on the mound protecting a slim lead, a base runner leading off a plain white base as a threat, a glowing golden shield aura around home plate showing the lead being protected, night stadium, tense focused mood, NO numbers anywhere",
    "s03": "cartoon closer pitcher throwing the final pitch and the catcher leaping up in relief as the last out is made, teammates starting to smile, a soft glowing golden shield shattering the tension, warm relieved victory-protected mood, night stadium, NO numbers",
    "s04": "vintage sepia 1960s scene: an old-time newspaper sports writer in a fedora sitting at a wooden desk with a typewriter and a blank paper, thoughtfully inventing a new baseball statistic, a faded relief pitcher illustration on the wall behind, nostalgic warm tone, the paper is entirely BLANK with no writing or numbers",
    "s05": "whimsical cartoon concept: a single glowing question mark hovering over a puzzled closer pitcher standing on the mound scratching his head under stadium lights, curious mysterious mood, warm spotlight, NO text NO numbers",
    "s06": "respectful cartoon hero mood: a dominant generic closer pitcher in a plain uniform hurling a blazing fastball with a fiery glowing trail while a batter swings and misses completely, behind the pitcher a huge neat monument-like mountain of glowing baseballs symbolizing many saves, powerful legendary night-stadium mood, NO numbers NO names",
    "s07": "cartoon split concept: on the LEFT a dejected closer pitcher hanging his head as a runner celebrates scoring behind him (a blown save), in cool blue tones; on the RIGHT a middle-relief pitcher smiling and handing the baseball to the next pitcher like a relay baton in warm golden tones (a hold), clear contrast, no words no numbers",
    "s08": "cartoon concept of a relay of pitchers: three relief pitchers standing in a row passing a glowing baseball like a relay, only the LAST pitcher who finishes the game holds up a single big glowing golden trophy while the earlier ones hold smaller glowing badges, teamwork bullpen mood, night stadium, NO text NO numbers",
    "s09": "cartoon two-panel contrast: LEFT panel in dim cool grey tones a closer pitcher finishing an easy comfortable game with a relaxed yawn and NO trophy, a neutral shrugging umpire; RIGHT panel in bright warm golden tones a closer pitcher finishing a nail-biting tight game with intense sweat and a big glowing trophy, a beaming umpire, clear visual contrast without any words or numbers",
    "s10": "warm closing scene: a baseball glove and a single baseball resting on the pitcher's mound under calm night stadium lights, the scoreboard glowing softly and completely blank in the far background, peaceful satisfied end-of-story mood, NO numbers",
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
