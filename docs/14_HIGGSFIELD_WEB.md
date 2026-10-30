# 14. Higgsfield 웹으로 영상 클립 만들기 (MCP·API 없이)

2026-10-22 사용자 지시: 말리동화 영상 클립은 Higgsfield **MCP·API·CLI 생성 없이**, Higgsfield 웹사이트를 직접 조작해서 만든다.
Orca 의 에이전트는 아래 `hfmalli` 명령과 `scripts/hf_web_clips.py` 만 쓴다.

> **2026-10-30 사용자 지시: Higgsfield 계정 2개를 기기별로 나눠 쓴다.**
> - **Windows = higgsfield.study@gmail.com** — Windows Chrome + Claude in Chrome 확장으로 Higgsfield 웹 직접 조작(hfmalli 미사용).
> - **맥 = yookwanhee6@gmail.com** — 맥 전용 Chrome(포트 9341) + `hfmalli` + `scripts/hf_web_clips.py`.
> - 화면 왼쪽 위 "streamingruler1405's workspace" 는 higgsfield.study 계정의 워크스페이스 이름이다(10-30 프로필 화면에서 확인, 같은 계정). 제출 전 그 기기의 로그인 계정이 위와 맞는지 확인, 다르면 제출 금지.
> 규칙은 그대로: 시작 그림 업로드·Wan 3.0·해상도·소리 설정 후 버튼 비용을 먼저 보고 → 승인 후에만 Generate. 결과는 편 폴더 `clips/Cxx_1080p.mp4`.
> 두 계정은 크레딧 잔액이 따로다 — 비용·잔액 보고 때 어느 계정인지 함께 적는다.

## 맥 실행 환경 (yookwanhee6)

| 항목 | 값 |
|---|---|
| 계정 | **yookwanhee6@gmail.com** (2026-10-30 사용자 지시: 맥 전용) |
| Chrome | **말리 전용 Chrome, 포트 9341** (127.0.0.1 전용, 프로필 `~/.higgsfield-accounts/malli-yookwanhee6/chrome-profile`, yookwanhee6 로그인됨 — 10-30 `hfmalli whoami` ok:true). 런웨이 Chrome(9338)은 쓰지 않음 |
| 켜는 법 | 바탕화면 `Higgsfield 말리동화 브라우저 열기.command` (9341) |
| 명령 | `~/.local/bin/hfmalli` (whoami / credits / clip / fetch / shot / login) — 기대 계정 yookwanhee6, 포트 9341 |
| 기록 | `/Volumes/맥 매니 HDD/Higgsfield 계정별/yookwanhee6/malli/작업기록.md`, 편 폴더 `clips/hf_web_jobs.json` |

- 절대 다른 계정으로 로그인하지 않는다. `hfmalli` 는 계정이 yookwanhee6 가 아니면 `ACCOUNT_MISMATCH` 로 아무 것도 하지 않는다.

## 편 하나의 클립 만들기 (2차 게이트와 함께)

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
hfmalli whoami                                                   # ok:true 확인
python3 scripts/hf_web_clips.py output/storybook/<편명> --test    # 시험 실행: 업로드·설정·버튼 비용만 확인, 크레딧 0
#   → 결과의 cost(버튼 표시 크레딧), balance 를 2차 게이트 배정표와 함께 사용자에게 보고하고 승인받는다
python3 scripts/hf_web_clips.py output/storybook/<편명> --test --submit  # 승인 후 실제 제출 → clips/sXX_1080p.mp4 저장
#   테스트본 통과 후 정식은 --test 대신 --final (순서는 아래 '정식 버전' 항목)
python compose.py                                                # 기존대로 조립
```

- 프롬프트는 편 폴더의 `gen_clips_veo.py` 의 `CLIP_PROMPTS` 를 그대로 재사용한다(또는 `clip_prompts.json`).
- 시작 이미지는 `images/sXX.png`, 결과는 compose 가 읽는 `clips/sXX_1080p.mp4`.
- **모델은 Wan 3.0 으로 통일 (2026-10-30 사용자 확정).** `--test` 또는 `--final` 없이 실행하면 스크립트가 멈춘다(예전 기본값 Kling 3.0 실행 차단). 공통: 5초, 16:9. `--max-credits` 기본 10.
- **테스트 버전 = `--test` 고정 (2026-10-29 사용자 확정): Wan 3.0 · 480p · 소리 켬.** `TEST_PRESET` 에 박혀 있어 다른 옵션으로 바꿀 수 없다.
- **정식 버전 = `--final` 고정 (2026-10-29 사용자 확정): Wan 3.0 · 720p · 소리 켬.** `FINAL_PRESET` 에 박혀 있다. 테스트본을 사용자가 통과시킨 뒤에만 쓴다. 순서: `--test` 시험 실행 → `--test --submit` → 테스트본 확인 → 사용자 통과 → 테스트 클립을 `clips_wan_test/` 로 옮김 → `--final` 시험 실행(비용 확인) → `--final --submit`. `--max-credits` 기본 10 이라 720p 소리 켬 비용이 넘으면 시험 실행 cost 를 보고한 뒤 올린다. hfmalli 에 `--model` 이 전달되므로 맥 hfmalli 가 Wan 선택을 지원해야 한다(시험 실행으로 확인).
- 시험 실행 화면 캡처: `clips/sXX_1080p_form_check.png`.

## 안전 규칙

- 이미 `clips/sXX_1080p.mp4` 가 있으면 다시 만들지 않는다.
- `hf_web_jobs.json` 에 제출된 씬은 재제출하지 않고 `fetch` 로 결과만 받는다.
- 제출 직전 확인: 계정 = 맥 yookwanhee6 / Windows higgsfield.study, 시작 프레임 업로드됨, 비율·길이·소리 설정, 버튼 비용 ≤ max-credits, 잔액 충분, 자동충전 꺼짐. 하나라도 틀리면 제출하지 않는다.
- 제출 후 job 접수가 확인되지 않으면 `UNKNOWN` 으로 기록하고 재제출하지 않는다(중복 과금 방지).
- 크레딧 구매·자동충전·요금제 변경은 하지 않는다.
- 실패한 씬은 compose.py 가 Ken Burns 정지 이미지로 대체하므로 제작은 멈추지 않는다.

## 막혔을 때

| 메시지 | 조치 |
|---|---|
| `MALLI_BROWSER_NOT_RUNNING` | 사용자에게 바탕화면 `Higgsfield 말리동화 브라우저 열기.command` 로 말리 Chrome(9341)을 띄워 달라고 요청 |
| `ACCOUNT_MISMATCH` (null 포함) | `hfmalli login` 후 사용자가 그 창(9341)에서 yookwanhee6@gmail.com 으로 로그인 |
| 봇 확인(슬라이드) 화면 | `hfmalli shot <png>` 로 확인 후 사용자에게 직접 통과 요청 |
| 이미 제출된 job 결과만 받기 | `hfmalli fetch <jobId> --out clips/sXX_1080p.mp4` |
