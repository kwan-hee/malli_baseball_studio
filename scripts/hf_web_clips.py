#!/usr/bin/env python3
"""말리동화 — Higgsfield '웹' 으로 절정 씬 클립 생성 (MCP·API 사용 안 함).

hfmalli 명령(맥 전용, 말리 Chrome 포트 9341, yookwanhee6@gmail.com 로그인 — 2026-10-30 확정. Windows 는 higgsfield.study 계정으로 웹 직접 조작)을 호출해 Wan 3.0 이미지→영상 클립을 만든다
(2026-10-30 사용자: Wan 3.0 으로 통일 — --test 또는 --final 필수, 옵션 없는 Kling 실행은 막음).
gen_clips_veo.py 의 CLIP_PROMPTS 를 그대로 재사용하고, 결과는 compose.py 가 읽는 clips/sXX_1080p.mp4 로 저장한다.

사용 (편 폴더 경로를 인자로):
  python3 scripts/hf_web_clips.py output/storybook/<편명>                 # 시험 실행: 업로드·설정·비용만 확인 (크레딧 0)
  python3 scripts/hf_web_clips.py output/storybook/<편명> --submit        # 2차 게이트 승인 후 실제 제출
  옵션: --scenes s04,s09   --max-credits 10   --aspect 16:9   --res 720p   --duration 5   --wait 900   --sound off
  테스트 버전: --test  →  Wan 3.0 · 480p · 소리 켬 으로 고정 (2026-10-29 사용자 확정, 다른 값으로 덮어쓰지 못함)
  정식 버전:   --final →  Wan 3.0 · 720p · 소리 켬 으로 고정 (2026-10-29 사용자 확정, 테스트 통과 후에만 사용)

규칙
- 이미 clips/sXX_1080p.mp4 가 있으면 건너뜀(재생성 금지).
- clips/hf_web_jobs.json 에 제출 기록. 같은 씬이 이미 제출돼 있으면 재제출하지 않고 결과만 받음.
- 버튼 표시 비용이 --max-credits 보다 크거나, 계정이 yookwanhee6 가 아니거나, 자동충전이 켜져 있으면 제출하지 않음.
- 제출 후 접수 확인이 안 되면 UNKNOWN 으로 기록하고 재제출하지 않음.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

HFMALLI = str(Path.home() / ".local/bin/hfmalli")
DEFAULT_MODEL = "kling-3.0"
# 테스트 버전 클립 설정 — 사용자 확정(2026-10-29): 테스트할 때는 항상 Wan 3.0 · 480p · 소리 켬
TEST_PRESET = {"model": "wan-3.0", "res": "480p", "sound": "on"}
# 정식 버전 클립 설정 — 사용자 확정(2026-10-29): 테스트 통과 후 정식 제작은 항상 Wan 3.0 · 720p · 소리 켬
FINAL_PRESET = {"model": "wan-3.0", "res": "720p", "sound": "on"}


def load_clip_prompts(ep: Path) -> dict:
    """편 폴더의 clip_prompts.json 우선, 없으면 gen_clips_veo.py 의 CLIP_PROMPTS 를 의존성 없이 읽는다."""
    j = ep / "clip_prompts.json"
    if j.exists():
        return json.loads(j.read_text(encoding="utf-8"))
    src = ep / "gen_clips_veo.py"
    if not src.exists():
        raise SystemExit(f"CLIP_PROMPTS 를 찾을 수 없음: {src} 또는 {j}")
    # gemini_pool / google.genai 없이도 상수만 읽을 수 있게 가짜 모듈을 넣는다
    gp = types.ModuleType("gemini_pool"); gp.GeminiPool = object; gp.is_quota_error = lambda e: False
    google = types.ModuleType("google"); genai = types.ModuleType("google.genai"); genai.types = types.ModuleType("types"); google.genai = genai
    for name, mod in {"gemini_pool": gp, "google": google, "google.genai": genai}.items():
        sys.modules.setdefault(name, mod)
    spec = importlib.util.spec_from_file_location("ep_clips", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.CLIP_PROMPTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--scenes", default="")
    ap.add_argument("--max-credits", default="10")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--res", default="720p")
    ap.add_argument("--duration", default="5")
    ap.add_argument("--wait", default="900")
    ap.add_argument("--sound", default="off")  # 강의 CH1-1(2026-10-29): 현장음 켬 요청 시 --sound on
    ap.add_argument("--model", default=DEFAULT_MODEL)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--test", action="store_true", help="테스트 버전: TEST_PRESET 고정")
    mode.add_argument("--final", action="store_true", help="정식 버전(테스트 통과 후): FINAL_PRESET 고정")
    a = ap.parse_args()
    preset = TEST_PRESET if a.test else FINAL_PRESET if a.final else None
    if not preset:  # 2026-10-30 사용자: 클립은 Wan 3.0 으로 통일 → --test / --final 없이는 실행하지 않음
        raise SystemExit("--test(Wan 3.0·480p) 또는 --final(Wan 3.0·720p) 중 하나를 지정하세요. Kling 기본 실행은 막혀 있습니다.")
    if preset:
        a.model, a.res, a.sound = preset["model"], preset["res"], preset["sound"]
    tag = " (테스트 고정)" if a.test else " (정식 고정)" if a.final else ""
    print(f"설정: {a.model} · {a.res} · 소리 {a.sound} · {a.duration}초{tag}")

    ep = Path(a.episode).resolve()
    prompts = load_clip_prompts(ep)
    if a.scenes:
        want = [s.strip() for s in a.scenes.split(",") if s.strip()]
        prompts = {k: v for k, v in prompts.items() if k in want}
    clips = ep / "clips"; clips.mkdir(exist_ok=True)
    ledger = clips / "hf_web_jobs.json"
    ok = True
    for sid, prompt in prompts.items():
        out = clips / f"{sid}_1080p.mp4"
        if out.exists() and out.stat().st_size > 100000:
            print(f"{sid}: 이미 있음 → 건너뜀")
            continue
        img = ep / "images" / f"{sid}.png"
        if not img.exists():
            print(f"{sid}: 시작 이미지 없음 {img} → 건너뜀 (compose 가 Ken Burns 로 대체)")
            ok = False
            continue
        pf = clips / f"{sid}_prompt.txt"
        pf.write_text(prompt, encoding="utf-8")
        cmd = [HFMALLI, "clip", "--start", str(img), "--prompt-file", str(pf), "--out", str(out),
               "--aspect", a.aspect, "--res", a.res, "--duration", a.duration, "--sound", a.sound,
               "--max-credits", a.max_credits, "--ledger", str(ledger), "--key", sid, "--wait", a.wait]
        if a.model != DEFAULT_MODEL:  # 기본(Kling)일 때는 hfmalli 기존 호출과 완전히 같게
            cmd += ["--model", a.model]
        if a.submit:
            cmd.append("--submit")
        print(f"{sid}: {'제출' if a.submit else '시험 실행(제출 안 함)'} …", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        line = (r.stdout.strip().splitlines() or [""])[-1]
        print(f"{sid}: {line}")
        if r.returncode != 0:
            print(r.stderr.strip()[-800:])
            ok = False
            if "ACCOUNT_MISMATCH" in r.stdout or "NOT_RUNNING" in r.stderr:
                break
    print("HF WEB CLIPS DONE" if ok else "HF WEB CLIPS PARTIAL (빠진 씬은 compose 가 Ken Burns 로 대체)")


if __name__ == "__main__":
    main()
