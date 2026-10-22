# 더블플레이 — 씬 삽화 10장 생성 (화이트보드 마커 스타일 파일럿)
# 스타일: 깨끗한 화이트보드 + 검정/파랑/빨강 마커 스케치
# 텍스트·숫자 금지 규칙 유지, 가로(16:9) 강제
import base64
import sys
import time
from pathlib import Path

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

# cp949 콘솔 print 크래시 방지
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

STYLE = (
    "clean whiteboard marker sketch on a pristine white dry-erase board surface, "
    "hand-drawn style with black marker for main outlines, blue marker for arrows and paths, "
    "red marker for highlights and emphasis circles, minimal shading, "
    "visible marker stroke texture, simple stick-figure style players, "
    "baseball diamond diagrams drawn with clean marker lines, "
    "no photorealistic elements, looks like a coach drew it on a whiteboard to explain. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, NO digits, NO jersey numbers, NO labels, "
    "NO scoreboard digits, NO diagram captions anywhere in the image"
)

SCENES = {
    "s01": "whiteboard sketch of a confused stick figure with a big question mark above their head, a speech bubble with cryptic dashes drawn in it (no actual text), a TV showing a baseball game in the background sketched simply, curious hook mood",
    "s02": "whiteboard diagram showing a baseball diamond from above with two X marks on the basepaths being crossed out simultaneously by a red marker circle, representing two outs in one play, simple clean explanation mood",
    "s03": "whiteboard baseball field diagram viewed from above showing all nine defensive positions marked with simple stick figures, each position indicated by its spot on the diamond and outfield, clean instructional layout like a coach teaching",
    "s04": "whiteboard baseball diamond with three stick-figure defenders highlighted: one at shortstop position catching a ground ball, a bold blue arrow going to second base figure, then another bold blue arrow going to first base figure, showing the classic 6-4-3 relay path, dynamic marker arrows with motion lines",
    "s05": "whiteboard showing three mini baseball diamond diagrams side by side, each with different colored arrow paths showing alternative double play relay routes (one going 4-6-3 path, one going 5-4-3 path, one going 1-4-3 path), comparison layout, blue and red arrows",
    "s06": "whiteboard split into two panels: left panel shows a force play diagram with arrows pushing runner forward to next base, right panel shows a reverse force with a tag symbol (hand touching runner), simple comparison teaching diagram",
    "s07": "whiteboard sketch of a line drive being caught by an infielder (straight blue arrow from batter to fielder glove), with a runner caught off base unable to return shown by a red X, dramatic caught-stealing moment drawn simply",
    "s08": "whiteboard dramatic scene: a baseball diamond with bases loaded (dots on all bases), a batter hitting a ground ball shown with arrow, and a double play relay path drawn in bold red showing the rally-killing moment, emphasis circles and exclamation drawn around the play",
    "s09": "whiteboard before-and-after comparison: left side shows bases with happy runner dots and momentum arrows, right side shows empty bases with the runners crossed out, a big sad face doodle, showing how double play kills a rally instantly",
    "s10": "whiteboard closing scene: a marker cap being placed back on a marker next to a completed baseball diamond diagram, a small hand-drawn thumbs up in the corner, satisfied teaching-complete mood, clean whiteboard with slight marker residue",
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
                    print(f"{sid}: {len(img):,} bytes [model={model}]")
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
                    client = pool.rotate()
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed")

print("\n=== Done ===")
