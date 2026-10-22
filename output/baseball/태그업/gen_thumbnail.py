# 태그업 — 썸네일 배경 생성 (텍스트 없는 배경, 글자는 ffmpeg drawtext로 후합성)
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
OUT = BASE / "thumb_bg.png"

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"

PROMPT = (
    "YouTube thumbnail background, bright cheerful cartoon illustration, clean bold outlines: "
    "an outfielder in the deep outfield has just caught a high fly ball in his glove, while at the same time a base "
    "runner is sprinting hard toward home plate and sliding in to score, a giant glowing golden question mark floating "
    "in the scene, bright stadium, strong color contrast (blue sky, warm golden glow, green field), "
    "composition leaves the RIGHT THIRD of the image relatively empty for large text overlay. "
    "ABSOLUTELY NO text, NO letters, NO words, NO numbers, no real person likeness, face generic cartoon. "
    "WIDE LANDSCAPE 16:9 horizontal orientation, wider than tall, "
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
