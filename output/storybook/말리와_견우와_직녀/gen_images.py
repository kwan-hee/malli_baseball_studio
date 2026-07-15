# 말리와 견우와 직녀 — 씬 이미지 10장을 Gemini(Nano Banana)로 생성하는 스크립트
# 말리 캐릭터 일관성: malli_reference.png 첨부 + 지브리 스타일 고정: ghibli_scene_ref.png(스타일 앵커) 첨부
# STYLE 문구는 C:/PROJECT/prompts/ghibli_style.txt 단일 출처 (2026-07-12 스타일 필수화)
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

REF = Path(r"C:\PROJECT\images\style_ref\malli_reference.png")          # 캐릭터 시트
STYLE_REF = Path(r"C:\PROJECT\images\style_ref\ghibli_scene_ref.png")   # 지브리 스타일 앵커(사용자 제공)
STYLE = Path(r"C:\PROJECT\prompts\ghibli_style.txt").read_text(encoding="utf-8").strip()  # 단일 출처

MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # 504 연발 시 폴백 (7편 검증)
W, H = 1920, 1080  # Ken Burns 줌 여유 위해 원본 크게 (최종 출력은 720p — compose가 축소)

MALLI = (
    'a fluffy cream-colored Maltipoo puppy named Malli with a large red bow ribbon on her head, '
    'pink collar with a gold bone-shaped tag engraved "MALLI", soft curly fur, big dark expressive eyes'
)
GYEONU = (
    "a kind young celestial cowherd named Gyeonu around 18 years old with black hair in a small topknot, "
    "wearing a simple beige-and-blue traditional hanbok with rolled sleeves, warm honest smile, holding a wooden staff"
)
JIKNYEO = (
    "a graceful young celestial weaver girl named Jiknyeo around 18 years old with long black braided hair "
    "and a small flower hairpin, wearing an elegant soft pink-and-violet hanbok, gentle bright face"
)
KING = (
    "a wise gentle Heavenly King with a long white beard, wearing a majestic gold-trimmed deep-blue robe "
    "and a traditional Korean crown, kind warm eyes, dignified but grandfatherly, NOT scary"
)
GALAXY = "a wide glittering Milky Way river of stars flowing across the night sky between soft glowing cloud fields"
COWS = "gentle brown cows grazing on rolling cloud pastures"
NO_MALLI = "NO dog puppy Malli in this scene, Malli does NOT appear"
NO_TEXT = "absolutely NO text, no letters, no words, no banner"

SCENES = {
    "s01": f"{MALLI}, waving hello cheerfully on a hilltop under a breathtaking starry night sky, {GALAXY} sweeping overhead with two especially bright twinkling stars on opposite sides of the star river, fireflies drifting, magical wondrous mood, {NO_TEXT}, {STYLE}",
    "s02": f"heavenly kingdom scene split by soft clouds: on one side {GYEONU} diligently brushing one of his {COWS} at dawn, on the other side {JIKNYEO} weaving shimmering cloud-like fabric on a wooden loom with threads of starlight, both working happily, warm industrious mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s03": f"playful but troubled scene in the heavenly kingdom: {GYEONU} and {JIKNYEO} laughing together while skipping stones by the starry river bank, while BEHIND them cows wander off trampling cloud fields comically and an abandoned wooden loom sits covered in dust and cobwebs, mischievous carefree mood with gentle warning undertone, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s04": f"gentle serious moment in a heavenly palace hall of clouds: {KING} looking down kindly but firmly from his cloud throne at {GYEONU} and {JIKNYEO} who bow their heads with sorry blushing faces, worried star spirits (small glowing orbs with faces) floating dimly around them, soft golden palace light, remorseful but warm mood NOT scary, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s05": f"{MALLI} sitting on a grassy hilltop under the starry sky with a paw on her chin in an adorable thinking pose, looking at the viewer as if asking a question, the glittering Milky Way reflected in her big dark eyes, calm wondering night mood, {NO_TEXT}, {STYLE}",
    "s06": f"bittersweet scene: {GYEONU} on the left bank and {JIKNYEO} on the right bank of {GALAXY}, each waving farewell across the wide star river while returning to their work — Gyeonu leading his cows, Jiknyeo sitting at her loom — both with gentle determined faces, longing but hopeful mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s07": f"magical climax: a huge flock of magpies and crows sweeping in from both sides of the night sky, linking their spread wings together to form a long glowing bridge arching over {GALAXY}, feathers shimmering with starlight, {GYEONU} and {JIKNYEO} stepping onto each end of the bird bridge from opposite banks, wondrous spectacular mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s08": f"heartwarming reunion at the center of the bird bridge over {GALAXY}: {GYEONU} and {JIKNYEO} running toward each other with arms outstretched and joyful tearful smiles, magpies and crows forming the sturdy bridge beneath their feet glowing warmly, {KING} watching from distant clouds with a gentle proud smile, stars swirling in celebration, joyful reunion mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s09": f"tender origin-tale scene: night sky view of {GALAXY} with the two bright stars now close together above the bird bridge silhouette, and below the sky a peaceful earthly village where soft gentle rain falls on thatched Korean cottages (chogajip) while children hold out their hands to feel the drizzle with smiles, absolutely NO European houses, warm mythical mood, {NO_MALLI}, {NO_TEXT}, {STYLE}",
    "s10": f"{MALLI}, waving goodbye warmly on the grassy hilltop at night, {GALAXY} glowing brilliantly above with the two bright stars twinkling side by side, a faint arc of tiny bird silhouettes across the star river, fireflies around her, peaceful happy ending mood, {NO_TEXT}, {STYLE}",
}

pool = GeminiPool()
client = pool.client()
ref_bytes = REF.read_bytes()
style_bytes = STYLE_REF.read_bytes()

for sid, scene in SCENES.items():
    out = OUT / f"{sid}.png"
    if out.exists() and out.stat().st_size > 10000:
        print(f"{sid}: cached")
        continue

    prompt = (
        "CRITICAL: The FIRST attached image is the OFFICIAL Malli character reference sheet. "
        "When Malli appears you MUST reproduce her appearance EXACTLY as shown — same cream fur, "
        "same red bow ON TOP OF HER HEAD, same pink collar, same gold bone tag, same dark eyes. "
        "There is exactly ONE Malli - never duplicate her, never show two similar puppies. "
        "The SECOND attached image is the STYLE REFERENCE: you MUST match its art style EXACTLY — "
        "same Ghibli cel animation look, same lineart, same background painting style, same palette — "
        "but NEVER copy or include any characters from the style reference. "
        f"Scene: {scene}. "
        f"Aspect ratio 16:9, resolution {W}x{H}."
    )
    contents = [
        types.Part(inline_data=types.Blob(data=ref_bytes, mime_type="image/png")),
        types.Part(inline_data=types.Blob(data=style_bytes, mime_type="image/png")),
        types.Part(text=prompt),
    ]

    for attempt in range(4):
        model = MODEL if attempt < 2 else FALLBACK_MODEL
        try:
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
            done = False
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    data = part.inline_data.data
                    img = bytes(data) if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
                    out.write_bytes(img)
                    print(f"{sid}: {len(img):,} bytes ({model})")
                    done = True
                    break
            if done:
                break
            raise RuntimeError("no image part in response")
        except Exception as e:
            err = str(e)
            print(f"{sid}: attempt {attempt+1} failed - {type(e).__name__}: {err[:120]}")
            if is_quota_error(err):
                try:
                    client = pool.rotate()  # 키 소진 → 다음 계정으로
                    continue
                except RuntimeError:
                    sys.exit(f"{sid}: all gemini keys exhausted - stop")
            time.sleep(10 * (attempt + 1))
    else:
        sys.exit(f"{sid}: all retries failed - stop, report to user")

print("ALL DONE")
