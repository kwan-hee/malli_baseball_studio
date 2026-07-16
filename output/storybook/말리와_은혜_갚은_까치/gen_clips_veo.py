# 말리와 은혜 갚은 까치 - 절정 씬(s04 까치 가족 감사, s07 까치들이 종을 울림) 이미지→영상 클립 생성기
# 폴백 체인: Veo 3.1 Fast → Seedance 1.5(Higgsfield 직접 API) → Veo lite → (compose.py Ken Burns)
# 비용 정책(01_COST_POLICY): Veo 주력, Seedance 보조. 키/시크릿은 절대 출력하지 않는다.
import base64
import glob
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, r"C:\youtube_longform_agent")
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

BASE = Path(__file__).parent
IMG = BASE / "images"
CLIPS = BASE / "clips"
CLIPS.mkdir(exist_ok=True)

VEO_FAST = "veo-3.1-fast-generate-preview"
VEO_LITE = "veo-3.1-lite-generate-preview"

HF_BASE = "https://platform.higgsfield.ai"
SEEDANCE_MODEL = "bytedance/seedance/v1/pro/image-to-video"
HF_KEY_GLOB = r"C:\말리\HF_API_Key*.txt"  # 키 파일(값은 로그에 안 남김). 환경변수 HF_API_KEY 우선.
HF_UA = "malli-storybook/1.0 (python)"    # 기본 urllib UA 는 Cloudflare 1010 차단 → 명시 필수

GHIBLI = (
    "hand-drawn 2D animation in the style of a Studio Ghibli film, cel-shaded characters, "
    "warm pastel colors, gentle storybook mood, static locked camera with no camera shake, "
    "no text anywhere"
)

CLIP_PROMPTS = {
    "s04": (
        "In a sunlit Korean mountain forest, a caring mother magpie with glossy black-and-white feathers flutters "
        "and bows gratefully around a kind young Korean traveler in a beige hanbok, while fluffy baby magpies chirp "
        "happily in their twig nest, the traveler smiling warmly and waving. "
        f"Gentle, heartwarming, joyful. {GHIBLI}"
    ),
    "s07": (
        "At night inside an old wooden Korean bell pavilion, a whole flock of black-and-white magpies flies in "
        "together and pushes and strikes a large hanging bronze bell with their wings and beaks, making it swing "
        "and ring out, soft sound ripples and moonlight glow, brave and stirring. "
        f"Dramatic, triumphant, moving. {GHIBLI}"
    ),
}


# ---------------------------------------------------------------------------
# Veo (Gemini API)
# ---------------------------------------------------------------------------

def try_veo(client, model, sid, prompt, out):
    img_bytes = (IMG / f"{sid}.png").read_bytes()
    print(f"{sid}: requesting {model} ...")
    op = client.models.generate_videos(
        model=model,
        prompt=prompt,
        image=types.Image(image_bytes=img_bytes, mime_type="image/png"),
    )
    t0 = time.time()
    while not op.done:
        if time.time() - t0 > 600:
            raise TimeoutError("veo operation timeout (10m)")
        time.sleep(15)
        op = client.operations.get(op)
    resp = getattr(op, "response", None) or getattr(op, "result", None)
    vids = getattr(resp, "generated_videos", None)
    if not vids:
        raise RuntimeError(f"no generated_videos in response: {resp}")
    video = vids[0].video
    client.files.download(file=video)
    video.save(str(out))
    if not (out.exists() and out.stat().st_size > 100000):
        raise RuntimeError("saved file too small")
    print(f"{sid}: {out.stat().st_size:,} bytes ({model}, {time.time()-t0:.0f}s)")


# ---------------------------------------------------------------------------
# Seedance 1.5 (Higgsfield 직접 REST API)
# ---------------------------------------------------------------------------

def _hf_auth():
    """
    인증 토큰 "key:secret" 반환. 값은 절대 print 하지 않는다.
    소스: HF_API_KEY 환경변수("key:secret") → 키 파일(key=value 줄 2개).
    주의: 2026-07-15 희생플레이 편에서 submit 404 발생 — 엔드포인트/모델명 재검증 필요.
    """
    val = os.environ.get("HF_API_KEY", "").strip()
    if val:
        return val
    files = glob.glob(HF_KEY_GLOB)
    if not files:
        raise RuntimeError("Higgsfield 키 없음 (HF_API_KEY 환경변수 또는 키 파일)")
    raw = Path(files[0]).read_text(encoding="utf-8", errors="ignore")
    vals = [l.split("=", 1)[1].strip() for l in raw.splitlines() if "=" in l]
    if len(vals) >= 2:
        return f"{vals[0]}:{vals[1]}"
    body = raw.strip()
    if ":" in body:
        return body
    raise RuntimeError("Higgsfield 키 파일 형식 인식 실패 (key=value 2줄 또는 key:secret 필요)")


def _hf_request(method, url, payload=None, auth=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", HF_UA)
    req.add_header("Authorization", f"Key {auth}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def try_seedance(sid, prompt, out):
    auth = _hf_auth()
    img_b64 = base64.b64encode((IMG / f"{sid}.png").read_bytes()).decode()
    payload = {
        "image_url": f"data:image/png;base64,{img_b64}",
        "prompt": prompt,
        "duration": 5,
        "resolution": "1080p",
    }
    print(f"{sid}: requesting seedance ({SEEDANCE_MODEL}) ...")
    sub = _hf_request("POST", f"{HF_BASE}/{SEEDANCE_MODEL}", payload, auth)
    rid = sub.get("request_id") or sub.get("id")
    if not rid:
        raise RuntimeError(f"no request_id in submit response: {list(sub.keys())}")
    t0 = time.time()
    while True:
        if time.time() - t0 > 900:
            raise TimeoutError("seedance timeout (15m)")
        st = _hf_request("GET", f"{HF_BASE}/requests/{rid}/status", None, auth)
        status = st.get("status")
        if status == "completed":
            url = (st.get("video") or {}).get("url")
            if not url:
                vids = st.get("videos") or []
                url = vids[0].get("url") if vids else None
            if not url:
                raise RuntimeError(f"completed but no video url: {list(st.keys())}")
            dl = urllib.request.Request(url, headers={"User-Agent": HF_UA})
            with urllib.request.urlopen(dl, timeout=300) as r, open(out, "wb") as f:
                f.write(r.read())
            break
        if status in ("failed", "nsfw"):
            raise RuntimeError(f"seedance status={status}")
        time.sleep(15)
    if not (out.exists() and out.stat().st_size > 100000):
        raise RuntimeError("seedance saved file too small")
    print(f"{sid}: {out.stat().st_size:,} bytes (seedance, {time.time()-t0:.0f}s)")


# ---------------------------------------------------------------------------
# 체인 실행: Veo Fast → Seedance 1.5 → Veo lite → (compose.py가 Ken Burns 폴백)
# ---------------------------------------------------------------------------

def generate_clip(pool_holder, sid, prompt):
    out = CLIPS / f"{sid}_1080p.mp4"
    if out.exists() and out.stat().st_size > 100000:
        print(f"{sid}: cached")
        return True

    steps = [
        ("veo-fast", lambda: try_veo(pool_holder["client"], VEO_FAST, sid, prompt, out)),
        ("seedance", lambda: try_seedance(sid, prompt, out)),
        ("veo-lite", lambda: try_veo(pool_holder["client"], VEO_LITE, sid, prompt, out)),
    ]
    for name, fn in steps:
        try:
            fn()
            return True
        except Exception as e:
            err = str(e)
            print(f"{sid}: {name} failed - {type(e).__name__}: {err[:200]}")
            if out.exists() and out.stat().st_size <= 100000:
                out.unlink()
            if name.startswith("veo") and is_quota_error(err):
                try:
                    pool_holder["client"] = pool_holder["pool"].rotate()
                except RuntimeError:
                    pass  # 키 소진 → 다음 폴백 단계로
    return False


if __name__ == "__main__":
    pool = GeminiPool()
    holder = {"pool": pool, "client": pool.client()}
    ok = True
    for sid, prompt in CLIP_PROMPTS.items():
        if not generate_clip(holder, sid, prompt):
            ok = False
    print("CLIPS DONE" if ok else "CLIPS PARTIAL/FAILED (compose will Ken-Burns fallback)")
