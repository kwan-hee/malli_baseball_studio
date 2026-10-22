# 14. Higgsfield 웹으로 영상 클립 만들기 (MCP·API 없이)

2026-10-22 사용자 지시: 말리동화 영상 클립은 Higgsfield **MCP·API·CLI 생성 없이**, Higgsfield 웹사이트를 직접 조작해서 만든다.
Orca 의 에이전트는 아래 `hfmalli` 명령과 `scripts/hf_web_clips.py` 만 쓴다.

## 실행 환경

| 항목 | 값 |
|---|---|
| 계정 | yookwanhee6@gmail.com |
| 전용 Chrome | 프로필 `~/.higgsfield-accounts/malli-yookwanhee6/chrome-profile`, 포트 9341 (127.0.0.1 전용) |
| 켜는 법 | 바탕화면 `Higgsfield 말리동화 브라우저 열기.command` 더블클릭 (에이전트는 Chrome을 직접 못 띄움) |
| 명령 | `~/.local/bin/hfmalli` (whoami / credits / clip / fetch / shot / login) |
| 기록 | `/Volumes/맥 매니 HDD/Higgsfield 계정별/yookwanhee6/malli/작업기록.md`, 편 폴더 `clips/hf_web_jobs.json` |

- 이 Chrome은 Aside 브라우저(건축·문화 작업)·런웨이 Chrome(higgsfield.study, 포트 9338)과 쿠키가 완전히 분리된다.
- 다른 Chrome·Aside 탭에서 로그인/로그아웃해도 이 창에는 영향이 없고, 반대도 마찬가지다.
- 절대 다른 계정으로 로그인하지 않는다. `hfmalli` 는 계정이 yookwanhee6 가 아니면 `ACCOUNT_MISMATCH` 로 아무 것도 하지 않는다.

## 편 하나의 클립 만들기 (2차 게이트와 함께)

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
hfmalli whoami                                                   # ok:true 확인
python3 scripts/hf_web_clips.py output/storybook/<편명>           # 시험 실행: 업로드·설정·버튼 비용만 확인, 크레딧 0
#   → 결과의 cost(버튼 표시 크레딧), balance 를 2차 게이트 배정표와 함께 사용자에게 보고하고 승인받는다
python3 scripts/hf_web_clips.py output/storybook/<편명> --submit  # 승인 후 실제 제출 → clips/sXX_1080p.mp4 저장
python compose.py                                                # 기존대로 조립
```

- 프롬프트는 편 폴더의 `gen_clips_veo.py` 의 `CLIP_PROMPTS` 를 그대로 재사용한다(또는 `clip_prompts.json`).
- 시작 이미지는 `images/sXX.png`, 결과는 compose 가 읽는 `clips/sXX_1080p.mp4`.
- 기본 설정: Kling 3.0, 5초, 720p, 16:9, 소리 끔(나레이션·BGM은 compose 가 넣음). `--max-credits` 기본 10.
- 시험 실행 화면 캡처: `clips/sXX_1080p_form_check.png`.

## 안전 규칙

- 이미 `clips/sXX_1080p.mp4` 가 있으면 다시 만들지 않는다.
- `hf_web_jobs.json` 에 제출된 씬은 재제출하지 않고 `fetch` 로 결과만 받는다.
- 제출 직전 확인: 계정 = yookwanhee6, 시작 프레임 업로드됨, 비율·길이·소리 설정, 버튼 비용 ≤ max-credits, 잔액 충분, 자동충전 꺼짐. 하나라도 틀리면 제출하지 않는다.
- 제출 후 job 접수가 확인되지 않으면 `UNKNOWN` 으로 기록하고 재제출하지 않는다(중복 과금 방지).
- 크레딧 구매·자동충전·요금제 변경은 하지 않는다.
- 실패한 씬은 compose.py 가 Ken Burns 정지 이미지로 대체하므로 제작은 멈추지 않는다.

## 막혔을 때

| 메시지 | 조치 |
|---|---|
| `MALLI_BROWSER_NOT_RUNNING` | 사용자에게 바탕화면 실행 파일 더블클릭 요청 |
| `ACCOUNT_MISMATCH` (null 포함) | `hfmalli login` 후 사용자가 그 창에서 yookwanhee6 로 로그인 |
| 봇 확인(슬라이드) 화면 | `hfmalli shot <png>` 로 확인 후 사용자에게 직접 통과 요청 |
| 이미 제출된 job 결과만 받기 | `hfmalli fetch <jobId> --out clips/sXX_1080p.mp4` |
