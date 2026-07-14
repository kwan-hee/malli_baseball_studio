# 볼넷 — 썸네일 배경 생성 (텍스트 없는 배경, 글자는 ffmpeg drawtext로 후합성)
import base64
import sys
import time
from pathlib import Path

# 다중 구글 계정 Gemini 키 자동 페일오버 풀 (429 소진 시 다음 키로 전환)
sys.path.insert(0, r"C:\youtube_longform_agent")
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
OUT = BASE / "thumb_bg.png"

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

PROMPT = (
    "YouTube thumbnail background, bright cheerful cartoon illustration, clean bold outlines: "
    "cartoon home-plate moment: a batter calmly walking toward first base tossing his bat aside with "
    "four glowing baseballs arcing past a translucent zone box behind him, a dumbfounded pitcher on the mound, "
    "night stadium lights, strong color contrast (deep blue night sky, warm glow, green field), "
    "composition leaves the RIGHT THIRD of the image relatively empty and dark for large text overlay. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, no real person likeness, face not visible. "
    "Aspect ratio 16:9, resolution 1280x720."
)

pool = GeminiPool()
client = pool.client()

for attempt in range(4):
    model = MODEL if attempt < 2 else FALLBACK_MODEL
    try:
        resp = client.models.generate_content(
            model=model,
            contents=PROMPT,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        done = False
        for part in resp.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                data = part.inline_data.data
                img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                OUT.write_bytes(img)
                print(f"thumb_bg: {len(img):,} bytes ({model})")
                done = True
                break
        if done:
            break
        raise RuntimeError("no image part")
    except Exception as e:
        err = str(e)
        print(f"attempt {attempt+1} failed - {type(e).__name__}: {err[:100]}")
        if is_quota_error(err):
            try:
                client = pool.rotate()  # 키 소진 → 다음 계정으로
                continue
            except RuntimeError:
                sys.exit("thumbnail: all gemini keys exhausted")
        time.sleep(10 * (attempt + 1))
else:
    sys.exit("thumbnail bg: all retries failed")
