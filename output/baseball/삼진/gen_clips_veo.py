# 삼진 - 절정 씬(s01 볼넷 걸어 1루 훅, s08 안타 vs 볼넷 둘 다 1루) 이미지→영상 클립 생성기
# 비용 정책(01_COST_POLICY): 야구사전 = Higgsfield(Seedance) 우선, Google Flow(Veo) 대안. (2026-07-18 사용자 "문서대로")
# 폴백 체인: Seedance 1.5(Higgsfield 직접 REST) → Veo 3.1 Fast → Veo lite → (compose.py Ken Burns)
# 주의: Seedance 직접 REST 는 과거 submit 404 이력(희생플레이 편) — 실패 시 Higgsfield MCP 로 피벗(사용자 보고).
# 키/시크릿은 절대 출력하지 않는다.
import base64
import glob
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))
from gemini_pool import GeminiPool, is_quota_error
from google.genai import types

# cp949 콘솔에서 비-cp949 문자 print 시 크래시 방지 — 유료 루프 보호 (2026-07-18 교훈)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
IMG = BASE / "images"
CLIPS = BASE / "clips"
CLIPS.mkdir(exist_ok=True)

VEO_FAST = "veo-3.1-fast-generate-preview"
VEO_LITE = "veo-3.1-lite-generate-preview"

HF_BASE = "https://platform.higgsfield.ai"
SEEDANCE_MODEL = "bytedance/seedance/v1/pro/image-to-video"
HF_KEY_GLOB = next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()) + "/HF_API_Key*.txt"  # 키 파일(값은 로그에 안 남김). 환경변수 HF_API_KEY 우선.
HF_UA = "malli-storybook/1.0 (python)"    # 기본 urllib UA 는 Cloudflare 1010 차단 → 명시 필수

# 클립당 예상 크레딧 (추정치 — 정확한 청구액은 각 플랫폼 대시보드. 클립 생성 전 로그 기록: 사용자 요구)
SEEDANCE_CREDITS = 20   # 추정: Seedance 1.5 5s 1080p (Higgsfield 크레딧 — 야구 우선)
VEO_FAST_CREDITS = 20   # 추정: Veo 3.1 Fast 5s (Flow 크레딧 — 폴백)
VEO_LITE_CREDITS = 12   # 추정: Veo 3.1 Lite 5s (Flow 크레딧 — 폴백)

CARTOON = (
    "bright cheerful 2D cartoon sports animation, clean bold outlines, vivid warm colors, "
    "generic stylized faces with no real person likeness, smooth simple motion, "
    "static locked camera with no camera shake, no text or numbers anywhere"
)

CLIP_PROMPTS = {
    "s01": (
        "A batter swings hard and completely whiffs on strike three as the catcher's mitt pops catching the ball, the "
        "batter's head lowered in defeat and the pitcher pumped up, bright packed cheering stadium, generic faces no "
        "real person, plain white home plate. "
        f"Snappy, dramatic, decisive. {CARTOON}"
    ),
    "s09": (
        "A dominant power pitcher in a light sky-blue baseball uniform hurls a blazing fastball for a record-breaking "
        "strikeout as the crowd erupts in celebration, a triumphant record moment, generic face no real person, bright "
        "daytime stadium. "
        f"Explosive, triumphant, record-breaking. {CARTOON}"
    ),
}


class VeoHardFail(Exception):
    """Veo 명확한 기술적 실패 (제출 실패 / op error / 영상 없음 / 저장 실패). 다음 폴백 허용."""


class VeoInProgress(Exception):
    """Veo 작업 ID 발급됨 + 재조회 후에도 진행/미완. 추가 폴백 금지 (중복 과금 방지)."""


# ---------------------------------------------------------------------------
# Seedance 1.5 (Higgsfield 직접 REST API) — 야구 우선
# ---------------------------------------------------------------------------

def _hf_auth():
    """인증 토큰 "key:secret" 반환. 값은 절대 print 하지 않는다."""
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
# Veo (Gemini API) — 폴백. 타임아웃 즉시 폴백 금지 + 진행중 op 는 추가 폴백 금지(중복과금 방지)
# ---------------------------------------------------------------------------

def try_veo(client, model, sid, prompt, out, est_credits):
    img_bytes = (IMG / f"{sid}.png").read_bytes()
    print(f"{sid}: [CLIP] model={model} est_credits~{est_credits} (추정치, 실제는 Flow 대시보드)")
    try:
        op = client.models.generate_videos(
            model=model, prompt=prompt,
            image=types.Image(image_bytes=img_bytes, mime_type="image/png"),
        )
    except Exception as e:
        raise VeoHardFail(f"submit failed: {type(e).__name__}: {e}") from e

    op_id = getattr(op, "name", None) or "issued"
    print(f"{sid}: veo operation issued (id={op_id}) - polling")
    t0 = time.time()
    timed_out = False
    while not op.done:
        if time.time() - t0 > 600:
            timed_out = True
            break
        time.sleep(15)
        op = client.operations.get(op)

    if timed_out:
        print(f"{sid}: veo 10m 경과 - 폴백 전 상태 1회 재조회")
        time.sleep(15)
        op = client.operations.get(op)
        if not op.done:
            raise VeoInProgress(f"veo op {op_id} 재조회 후에도 진행 중 - 추가 폴백 안 함 (중복 과금 방지)")

    if getattr(op, "error", None):
        raise VeoHardFail(f"veo op error: {op.error}")
    resp = getattr(op, "response", None) or getattr(op, "result", None)
    vids = getattr(resp, "generated_videos", None)
    if not vids:
        raise VeoHardFail(f"no generated_videos in response: {resp}")
    video = vids[0].video
    client.files.download(file=video)
    video.save(str(out))
    if not (out.exists() and out.stat().st_size > 100000):
        raise VeoHardFail("saved file too small")
    print(f"{sid}: {out.stat().st_size:,} bytes ({model}, {time.time()-t0:.0f}s)")


# ---------------------------------------------------------------------------
# 체인: Seedance(우선) → Veo Fast → Veo lite → (compose Ken Burns)
# ---------------------------------------------------------------------------

def generate_clip(holder, sid, prompt):
    out = CLIPS / f"{sid}_1080p.mp4"
    if out.exists() and out.stat().st_size > 100000:
        print(f"{sid}: cached")
        return True

    # 1) Seedance 우선 (문서: 야구 = Higgsfield)
    print(f"{sid}: [CLIP] model=seedance-1.5 est_credits~{SEEDANCE_CREDITS} (야구 우선 정책, 추정치)")
    try:
        try_seedance(sid, prompt, out)
        return True
    except Exception as e:
        print(f"{sid}: seedance failed - {type(e).__name__}: {str(e)[:200]}")
        if out.exists() and out.stat().st_size <= 100000:
            out.unlink()

    # 2) Veo 폴백 (Seedance 실패 시). Fast → lite. 429 소진 시 계정 로테이션.
    veo_steps = [(VEO_FAST, VEO_FAST_CREDITS), (VEO_LITE, VEO_LITE_CREDITS)]
    mi, quota_rotations = 0, 0
    while mi < len(veo_steps):
        model, est = veo_steps[mi]
        try:
            try_veo(holder["client"], model, sid, prompt, out, est)
            return True
        except VeoInProgress as e:
            print(f"{sid}: {e}")
            print(f"{sid}: → 추가 폴백 건너뜀, compose Ken-Burns 폴백 (중복 과금 방지)")
            return False
        except VeoHardFail as e:
            err = str(e)
            print(f"{sid}: {model} hard-fail - {err[:200]}")
            if out.exists() and out.stat().st_size <= 100000:
                out.unlink()
            if is_quota_error(err) and quota_rotations < 6:
                try:
                    holder["client"] = holder["pool"].rotate()
                    quota_rotations += 1
                    print(f"{sid}: gemini 키 로테이션 - 같은 Veo 모델 재시도")
                    continue
                except RuntimeError:
                    print(f"{sid}: 모든 gemini 키 소진")
            mi += 1
    return False


if __name__ == "__main__":
    pool = GeminiPool()
    holder = {"pool": pool, "client": pool.client()}
    ok = True
    for sid, prompt in CLIP_PROMPTS.items():
        if not generate_clip(holder, sid, prompt):
            ok = False
    print("CLIPS DONE" if ok else "CLIPS PARTIAL/FAILED (compose will Ken-Burns fallback)")
