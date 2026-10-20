# 말리 시험 실행 — 그림 1장 + 목소리 1문장
# 규칙서(CLAUDE.md)의 "4. 시험 실행" 항목을 실행하는 프로그램입니다.
# 실행 방법: 이 폴더에서  python 시험실행.py
#
# 규칙서와 프로그램의 관계
#   - 규칙서 = 무엇을, 어떤 순서로, 어디에 저장할지 적은 문서 (사람과 Claude가 읽음)
#   - 프로그램 = 그 규칙을 실제로 실행하는 파일 (컴퓨터가 읽음)
#   - 규칙서가 바뀌면 아래 [설정] 부분만 Claude에게 맞춰 달라고 요청합니다.
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent

# ───────────── [설정] 규칙서에 맞춰 바뀌는 자리 ─────────────
CHARACTER_TEXT = HERE / "말리_연습자료" / "말리_캐릭터시트.txt"     # 캐릭터 시트(글)
CHARACTER_IMAGE = HERE / "말리_연습자료" / "malli_reference.png"    # 캐릭터 시트(그림)
SAVE_DIR = HERE / "결과" / "시험실행"                                # 결과물 저장 위치
IMAGE_FILE = "malli_test.png"
VOICE_FILE = "malli_test.wav"
SCENE = "waving hello cheerfully on a sunny green hilltop, blue sky with soft clouds"
SENTENCE = "안녕하세요, 여러분! 저는 말리예요. 오늘 우리 작업실이 잘 되는지 같이 시험해 볼까요?"
VOICE = "Kore"
VOICE_STYLE = "어린이 동화 구연 성우, 5~7세 아이에게 들려주듯 밝고 사랑스럽게, 또박또박"
IMAGE_MODEL = "gemini-3-pro-image-preview"
TTS_MODEL = "gemini-3.8-flash-tts"
# ─────────────────────────────────────────────────────────


def stop(kind, message, hint):
    """실패하면 어느 쪽 문제인지(설치·규칙서·프로그램) 알려 주고 멈춥니다."""
    print(f"\n[실패] {message}")
    print(f"  ▶ 어디를 볼까요: {kind} 문제")
    print(f"  ▶ 확인할 것: {hint}")
    sys.exit(1)


def stop_api(step, e):
    """그림·목소리 단계 오류: 키·결제 오류는 설치(준비) 문제, 나머지는 프로그램 문제로 나눕니다."""
    text = f"{type(e).__name__}: {e}"
    if any(w in text for w in ("API key", "API_KEY", "PERMISSION_DENIED", "quota", "RESOURCE_EXHAUSTED", "billing", "429", "403")):
        stop("설치", f"{step} 실패 — {text[:200]}",
             "API 키가 맞는지, AI Studio에 결제가 등록됐는지, 사용 한도가 남았는지 확인하세요. 코드는 고치지 마세요.")
    stop("프로그램", f"{step} 실패 — {text[:200]}",
         "코드를 바로 고치지 말고, 정상예시 폴더의 시험실행.py 와 내 파일이 다른 곳이 있는지 비교하세요.")


def load_key():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    env = HERE / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key or key == "여기에_키를_붙여넣기":
        stop("설치", "Gemini API 키를 찾지 못했어요.",
             ".env.예시 파일을 복사해 이름을 .env 로 바꾸고, GEMINI_API_KEY= 뒤에 키를 붙여 넣었는지 확인하세요.")
    return key


# ── 1단계: 준비물 확인 ──
print("[1/4] 준비물 확인")
try:
    from google import genai
    from google.genai import types
except ImportError:
    stop("설치", "google-genai 패키지가 없어요.", "터미널에서  pip install google-genai  를 실행하세요.")
for f in (CHARACTER_TEXT, CHARACTER_IMAGE):
    if not f.exists():
        stop("규칙서", f"캐릭터 시트 파일이 없어요: {f.name}",
             "규칙서에 적은 파일 이름·폴더와 실제 파일 위치가 같은지 비교하세요.")
API_KEY = load_key()
SAVE_DIR.mkdir(parents=True, exist_ok=True)
character = " ".join(
    line.strip() for line in CHARACTER_TEXT.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
)
print("  준비물 OK")

# ── 2단계: 그림 1장 ──
print("[2/4] 그림 1장 만드는 중... (30초~1분)")
prompt = (
    "The attached image is the official Malli character reference sheet. "
    "Draw Malli EXACTLY as shown: same cream fur, same red bow on her head, same pink collar and gold bone tag. "
    f"Character and style: {character}. "
    f"Scene: Malli {SCENE}. Only ONE Malli. Absolutely NO text or letters in the image. "
    "WIDE LANDSCAPE 16:9 horizontal image."
)
try:
    client = genai.Client(api_key=API_KEY)
    resp = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[
            types.Part(inline_data=types.Blob(data=CHARACTER_IMAGE.read_bytes(), mime_type="image/png")),
            types.Part(text=prompt),
        ],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    image = None
    for part in resp.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            data = part.inline_data.data
            image = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
    if image is None:
        raise RuntimeError("응답에 그림이 없어요")
except Exception as e:
    stop_api("그림 만들기", e)
(SAVE_DIR / IMAGE_FILE).write_bytes(image)
print(f"  저장: {IMAGE_FILE} ({len(image):,} bytes)")

# ── 3단계: 목소리 1문장 ──
print("[3/4] 목소리 1문장 만드는 중... (10~30초)")
body = json.dumps({
    "model": TTS_MODEL,
    "input": [{"type": "user_input", "content": [{
        "type": "text",
        "text": SENTENCE,
        "annotations": [{"type": "speech_metadata", "style": VOICE_STYLE}],
    }]}],
    "response_format": {"type": "audio"},
    "generation_config": {"speech_config": [{"voice": VOICE}]},
}).encode("utf-8")
try:
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions", data=body, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as he:
        raise RuntimeError(f"HTTP {he.code}: {he.read().decode('utf-8', 'replace')[:200]}") from he
    audio = next(c for st in resp["steps"] for c in st.get("content", []) if c.get("type") == "audio")
    with wave.open(io.BytesIO(base64.b64decode(audio["data"])), "rb") as src:
        params, pcm = src.getparams(), src.readframes(src.getnframes())
except Exception as e:
    stop_api("목소리 만들기", e)
with wave.open(str(SAVE_DIR / VOICE_FILE), "wb") as dst:
    dst.setparams(params)
    dst.writeframes(pcm)
seconds = len(pcm) / (params.framerate * params.sampwidth * params.nchannels)
print(f"  저장: {VOICE_FILE} ({seconds:.1f}초)")

# ── 4단계: 결과 확인 ──
print("[4/4] 결과 확인")
for name in (IMAGE_FILE, VOICE_FILE):
    f = SAVE_DIR / name
    print(f"  {'있음' if f.exists() and f.stat().st_size > 1000 else '없음'}  {f.relative_to(HERE)}")
print("\n완료! 정상예시 폴더의 파일과 나란히 놓고 비교해 보세요.")
