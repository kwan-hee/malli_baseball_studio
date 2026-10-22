# 말리와 양치기 소년 - 절정 씬(s06 늑대 등장, s08 양 흩어짐) 클립 생성
import base64, glob, json, os, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
IMG = BASE / "images"
CLIPS = BASE / "clips"
CLIPS.mkdir(exist_ok=True)

VEO_FAST = "veo-3.1-fast-generate-preview"
VEO_LITE = "veo-3.1-lite-generate-preview"
VEO_FAST_CREDITS, VEO_LITE_CREDITS, SEEDANCE_CREDITS = 20, 12, 20

class VeoHardFail(Exception): pass
class VeoInProgress(Exception): pass

HF_BASE = "https://platform.higgsfield.ai"
SEEDANCE_MODEL = "bytedance/seedance/v1/pro/image-to-video"
HF_KEY_GLOB = next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()) + "/HF_API_Key*.txt"
HF_UA = "malli-storybook/1.0 (python)"

GHIBLI = (
    "hand-drawn 2D animation in the style of a Studio Ghibli film, cel-shaded characters, "
    "warm pastel colors, gentle storybook mood, static locked camera with no camera shake, "
    "no text anywhere"
)

CLIP_PROMPTS = {
    "s06": (
        "A large cartoon wolf with glowing yellow eyes creeps out of dark forest shadows toward a flock "
        "of cute fluffy white sheep on a green hillside, a young shepherd boy freezes in fear with wide eyes, "
        "tense suspenseful mood but NOT terrifying, cartoon storybook style. "
        f"Suspenseful, creepy, dramatic. {GHIBLI}"
    ),
    "s08": (
        "A cartoon wolf chases a flock of fluffy white sheep who scatter in all directions bleating, "
        "a young shepherd boy runs down the hillside crying with tears streaming, chaotic urgent motion "
        "but NOT violent, green hillside countryside, cartoon storybook style. "
        f"Chaotic, urgent, emotional. {GHIBLI}"
    ),
}


def try_veo(client, model, sid, prompt, out, est_credits):
    img_bytes = (IMG / f"{sid}.png").read_bytes()
    print(f"{sid}: [CLIP] model={model} est_credits~{est_credits}")
    try:
        op = client.models.generate_videos(model=model, prompt=prompt,
            image=types.Image(image_bytes=img_bytes, mime_type="image/png"))
    except Exception as e:
        raise VeoHardFail(f"submit failed: {type(e).__name__}: {e}") from e
    op_id = getattr(op, "name", None) or "issued"
    print(f"{sid}: veo operation issued (id={op_id}) — polling")
    t0 = time.time()
    timed_out = False
    while not op.done:
        if time.time() - t0 > 600:
            timed_out = True; break
        time.sleep(15)
        op = client.operations.get(op)
    if timed_out:
        print(f"{sid}: veo 10m 경과 — 재조회")
        time.sleep(15); op = client.operations.get(op)
        if not op.done:
            raise VeoInProgress(f"veo op {op_id} 진행 중 — 추가 폴백 안 함")
    if getattr(op, "error", None):
        raise VeoHardFail(f"veo op error: {op.error}")
    resp = getattr(op, "response", None) or getattr(op, "result", None)
    vids = getattr(resp, "generated_videos", None)
    if not vids:
        raise VeoHardFail(f"no generated_videos: {resp}")
    video = vids[0].video
    client.files.download(file=video); video.save(str(out))
    if not (out.exists() and out.stat().st_size > 100000):
        raise VeoHardFail("saved file too small")
    print(f"{sid}: {out.stat().st_size:,} bytes ({model}, {time.time()-t0:.0f}s)")


def _hf_auth():
    val = os.environ.get("HF_API_KEY", "").strip()
    if val: return val
    files = glob.glob(HF_KEY_GLOB)
    if not files: raise RuntimeError("Higgsfield 키 없음")
    raw = Path(files[0]).read_text(encoding="utf-8", errors="ignore")
    vals = [l.split("=", 1)[1].strip() for l in raw.splitlines() if "=" in l]
    if len(vals) >= 2: return f"{vals[0]}:{vals[1]}"
    body = raw.strip()
    if ":" in body: return body
    raise RuntimeError("Higgsfield 키 파일 형식 인식 실패")

def _hf_request(method, url, payload=None, auth=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json"); req.add_header("Accept", "application/json")
    req.add_header("User-Agent", HF_UA); req.add_header("Authorization", f"Key {auth}")
    with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read().decode())

def try_seedance(sid, prompt, out):
    auth = _hf_auth()
    img_b64 = base64.b64encode((IMG / f"{sid}.png").read_bytes()).decode()
    payload = {"image_url": f"data:image/png;base64,{img_b64}", "prompt": prompt, "duration": 5, "resolution": "1080p"}
    print(f"{sid}: requesting seedance ...")
    sub = _hf_request("POST", f"{HF_BASE}/{SEEDANCE_MODEL}", payload, auth)
    rid = sub.get("request_id") or sub.get("id")
    if not rid: raise RuntimeError(f"no request_id: {list(sub.keys())}")
    t0 = time.time()
    while True:
        if time.time() - t0 > 900: raise TimeoutError("seedance timeout")
        st = _hf_request("GET", f"{HF_BASE}/requests/{rid}/status", None, auth)
        status = st.get("status")
        if status == "completed":
            url = (st.get("video") or {}).get("url")
            if not url:
                vids = st.get("videos") or []
                url = vids[0].get("url") if vids else None
            if not url: raise RuntimeError("completed but no video url")
            dl = urllib.request.Request(url, headers={"User-Agent": HF_UA})
            with urllib.request.urlopen(dl, timeout=300) as r, open(out, "wb") as f: f.write(r.read())
            break
        if status in ("failed", "nsfw"): raise RuntimeError(f"seedance status={status}")
        time.sleep(15)
    if not (out.exists() and out.stat().st_size > 100000): raise RuntimeError("too small")
    print(f"{sid}: {out.stat().st_size:,} bytes (seedance, {time.time()-t0:.0f}s)")


def generate_clip(pool_holder, sid, prompt):
    out = CLIPS / f"{sid}_1080p.mp4"
    if out.exists() and out.stat().st_size > 100000:
        print(f"{sid}: cached"); return True
    veo_steps = [(VEO_FAST, VEO_FAST_CREDITS), (VEO_LITE, VEO_LITE_CREDITS)]
    mi, qr = 0, 0
    while mi < len(veo_steps):
        model, est = veo_steps[mi]
        try:
            try_veo(pool_holder["client"], model, sid, prompt, out, est); return True
        except VeoInProgress as e:
            print(f"{sid}: {e}"); return False
        except VeoHardFail as e:
            err = str(e); print(f"{sid}: {model} hard-fail - {err[:200]}")
            if out.exists() and out.stat().st_size <= 100000: out.unlink()
            if is_quota_error(err) and qr < 6:
                try: pool_holder["client"] = pool_holder["pool"].rotate(); qr += 1; continue
                except RuntimeError: print(f"{sid}: 모든 gemini 키 소진")
            mi += 1
    print(f"{sid}: [CLIP] fallback seedance est_credits~{SEEDANCE_CREDITS}")
    try:
        try_seedance(sid, prompt, out); return True
    except Exception as e:
        print(f"{sid}: seedance failed - {type(e).__name__}: {str(e)[:200]}")
        if out.exists() and out.stat().st_size <= 100000: out.unlink()
    return False


if __name__ == "__main__":
    pool = GeminiPool()
    holder = {"pool": pool, "client": pool.client()}
    ok = True
    for sid, prompt in CLIP_PROMPTS.items():
        if not generate_clip(holder, sid, prompt): ok = False
    print("CLIPS DONE" if ok else "CLIPS PARTIAL/FAILED (compose will Ken-Burns fallback)")
