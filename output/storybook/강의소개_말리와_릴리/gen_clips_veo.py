# 강의 소개 영상 「말리의 동화나라」 — 클립 2개 (2차 게이트 승인 2026-10-22)
# open : S01-02~03 책이 펼쳐지고 말리가 책장 속에서 튀어 올라 착지 (시작 프레임 B1 표지)
# close: S06-13 말리가 동화책 안으로 쏙 들어가고 책이 닫힘 (시작 프레임 B3)
# 폴백 체인: Veo 3.1 Fast → Veo lite → (render.py 정지 화면 폴백). 키/시크릿은 절대 출력하지 않는다.
# Higgsfield 는 웹 전용 규칙(2026-10-22, CLAUDE.md) → 챕터1 템플릿의 Seedance API 폴백은 뺐다.
import sys
import time
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
VEO_FAST_CREDITS = 20   # 추정치
VEO_LITE_CREDITS = 12   # 추정치


class VeoHardFail(Exception):
    """Veo 명확한 기술적 실패 (제출 실패 / op error / 영상 없음 / 저장 실패)."""


class VeoInProgress(Exception):
    """Veo 작업 ID 발급됨 + 재조회 후에도 진행/미완. 재제출 금지 (중복 과금 방지)."""


STYLE = (
    "soft hand-drawn watercolor storybook animation on warm cream paper, pastel colors, gentle and cozy, "
    "keep Malli's design exactly as shown (cream curly fur, red bow on pink collar, gold bone tag), "
    "only ONE puppy, no text anywhere, no people"
)
START_FRAME = {"open": "B1.png", "close": "B3.png"}
CLIP_PROMPTS = {
    "open": (
        "The closed picture book on the wooden table slowly opens by itself, its pages reveal a soft watercolor "
        "meadow, then a fluffy cream Maltipoo puppy with a red bow on her pink collar bounces up out of the pages "
        "and lands softly in the middle of the open book with a few tiny sparkles. Static camera. "
        f"{STYLE}"
    ),
    "close": (
        "The fluffy cream Maltipoo puppy standing on the open book waves happily, then hops down into the pages and "
        "disappears into the watercolor meadow, and the big book slowly closes by itself. Static camera. "
        f"{STYLE}"
    ),
}


# ---------------------------------------------------------------------------
# Veo (Gemini API)
# ---------------------------------------------------------------------------

def try_veo(client, model, sid, prompt, out, est_credits):
    img_bytes = (IMG / START_FRAME[sid]).read_bytes()
    # 클립 생성 전 사용 모델·예상 크레딧 로그 (사용자 요구)
    print(f"{sid}: [CLIP] model={model} est_credits~{est_credits} (추정치, 실제는 Flow 대시보드 확인)")

    try:
        op = client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=types.Image(image_bytes=img_bytes, mime_type="image/png"),
        )
    except Exception as e:
        # 제출 자체 실패 = 작업 ID 미발급 → 명확한 기술적 실패 → 폴백 허용
        raise VeoHardFail(f"submit failed: {type(e).__name__}: {e}") from e

    op_id = getattr(op, "name", None) or "issued"
    print(f"{sid}: veo operation issued (id={op_id}) — polling (작업 ID 발급됨)")
    t0 = time.time()
    timed_out = False
    while not op.done:
        if time.time() - t0 > 600:
            timed_out = True
            break
        time.sleep(15)
        op = client.operations.get(op)

    if timed_out:
        # 타임아웃만으로 즉시 폴백 금지 — 상태를 한 번 더 조회한 뒤 판단 (사용자 요구)
        print(f"{sid}: veo 10m 경과 — 폴백 전 상태 1회 재조회")
        time.sleep(15)
        op = client.operations.get(op)
        if not op.done:
            # 작업 ID 발급됨 + 여전히 진행 중 → Seedance 호출 금지 (중복 과금 방지)
            raise VeoInProgress(
                f"veo op {op_id} 재조회 후에도 진행 중 — Seedance 폴백 안 함 (중복 과금 방지)"
            )

    # op.done — 결과 검증. 실패/영상없음/저장실패는 '명확한 기술적 실패'로 폴백 허용
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
# 체인 실행: Veo Fast → Veo lite → (render.py 정지 화면 폴백)
# ---------------------------------------------------------------------------

def generate_clip(pool_holder, sid, prompt):
    out = CLIPS / f"{sid}.mp4"
    if out.exists() and out.stat().st_size > 100000:
        print(f"{sid}: cached")
        return True
    veo_steps = [(VEO_FAST, VEO_FAST_CREDITS), (VEO_LITE, VEO_LITE_CREDITS)]
    mi, quota_rotations = 0, 0
    while mi < len(veo_steps):
        model, est = veo_steps[mi]
        try:
            try_veo(pool_holder["client"], model, sid, prompt, out, est)
            return True
        except VeoInProgress as e:
            print(f"{sid}: {e} - 재제출 안 함, 정지 화면 폴백")
            return False
        except VeoHardFail as e:
            err = str(e)
            print(f"{sid}: {model} hard-fail - {err[:200]}")
            if out.exists() and out.stat().st_size <= 100000:
                out.unlink()
            if is_quota_error(err) and quota_rotations < 6:
                try:
                    pool_holder["client"] = pool_holder["pool"].rotate()
                    quota_rotations += 1
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
    print("CLIPS DONE" if ok else "CLIPS PARTIAL/FAILED (render.py still-frame fallback)")
