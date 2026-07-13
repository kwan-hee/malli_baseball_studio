# 파울팁과 파울의 차이 — 씬 삽화 10장 생성 (Nano Banana/Gemini, 야구 카툰 톤, 실존 인물·텍스트·숫자 금지)
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
    "s01": "dramatic night stadium moment: a cartoon batter mid-swing with the bat barely grazing a baseball, tiny spark and small sound-wave rings at the graze point, catcher's mitt wide open right behind the ball, umpire silhouette rising behind, frozen tense energy",
    "s02": "playful cartoon split concept: left half a baseball bouncing harmlessly into the stands with a relaxed batter shrugging (soft green mood), right half the same baseball smacking straight into a catcher's mitt with a dismayed batter (intense red-orange mood), sunny stadium, simple friendly comparison feel without any labels",
    "s03": "cartoon extreme closeup of a catcher's mitt snapping firmly shut around a baseball, a short glowing motion trail showing the ball came straight off a bat edge nearby, small dust puff, dramatic spotlight, night stadium",
    "s04": "cartoon contrast scene: on one side a confident batter calmly fouling off pitches with several faded baseballs arcing away out of play, on the other side a shocked batter frozen mid-swing while the catcher behind him holds up a closed mitt in triumph, twilight stadium",
    "s05": "vintage sepia early-1900s baseball scene: a smug old-time batter in vintage wool uniform and pillbox cap slapping yet another ball away foul, several faded balls scattered outside the field lines, an exhausted vintage pitcher slumping on the mound wiping his brow, warm nostalgic light",
    "s06": "vintage sepia scene: stern men in early-1900s suits gathered around a heavy wooden table in a gaslit office, one man holding up a baseball decisively, a thick open rulebook on the table with completely blank pages, cigar smoke, decisive historic mood",
    "s07": "night KBO stadium controversy: a cartoon batter in navy uniform halfway through a checked swing as a baseball barely ticks off the bat toward the catcher, the umpire behind making an emphatic strike call with a raised fist, dugout players leaning out in disbelief, packed stands, tense atmosphere, generic stylized faces, no jersey lettering",
    "s08": "clean cartoon concept on deep blue background: one glowing baseball at center with three glowing trajectory paths splitting apart — one path landing inside a catcher's mitt, one path bouncing off the dirt first, one path missing everything into empty air, mysterious decision mood, simple infographic feel without any labels",
    "s09": "dynamic cartoon wide shot: a base runner sprinting and sliding into second base with a dust cloud in the foreground, while far in the background at home plate the catcher snaps his mitt shut on a barely-tipped ball, split-second stolen-base drama, night stadium lights",
    "s10": "warm closing scene: a catcher's mitt resting on home plate under calm night stadium lights, one baseball tucked safely inside the mitt and a second baseball lying on the dirt just outside it, peaceful satisfied end-of-game mood",
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
