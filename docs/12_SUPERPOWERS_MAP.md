<!-- superpowers 스킬 중 이 콘텐츠 파이프라인에 실제 쓸모 있는 것만 골라 작업별로 매핑한 표 -->
# 12. Superpowers 스킬 매핑 (이 프로젝트 전용)

superpowers 플러그인은 전역 활성. 스킬 대부분은 일반 소프트웨어 코딩용이라 이 콘텐츠 파이프라인엔 일부만 맞는다.
이 문서는 "이 프로젝트의 어떤 작업에서 어떤 superpowers 스킬을 쓸지"만 정한다.

## 우선순위 (충돌 시)

1. **프로젝트 규칙이 최우선** — 2단계 승인 게이트(AGENTS.md), 한국어 출력, 확정 제작 규칙(CLAUDE.md).
2. superpowers 스킬 — 위와 안 부딪히는 선에서 방법론 보강.
3. 기본 동작.

superpowers 자체 규칙도 "user 지침(CLAUDE.md/AGENTS.md)이 스킬보다 우선"이라 명시. 게이트를 건너뛰는 스킬 동작은 무시한다.

## 작업별 매핑

| 이 프로젝트 작업 | 쓸 superpowers 스킬 | 비고 |
|------|------|------|
| 새 에피소드 소재·기획, 새 채널/포맷 아이디어 | `brainstorming` | 1차 게이트(조사·개요) **전** 의도·요구 정리용. 게이트 대체 아님, 앞단 보강 |
| 완료 선언 직전 (mp4·대본 "다 됐어" 하기 전) | `verification-before-completion` | 프로젝트 검증 규칙(ffmpeg -ss 프레임 추출→자막·화면 눈확인, 야구 사실 교차검증)과 직결. 증거 없이 완료 선언 금지 |
| 파이프라인 스크립트 오류 (TTS 잘림, whisper 경계 붕괴, 클립 실패, compose 깨짐) | `systematic-debugging` | 로그 실제로 읽고 원인 확인 후 수정 (CLAUDE.md "에러는 읽고 고친다"와 동일). 무한 재시도 금지 |
| 파이프라인 공통 로직 변경 (경계 로직·compose 등 다단계) | `writing-plans` → `executing-plans` | 요청 없이 공통 로직 건드리지 않는 게 원칙. 손대야 하면 플랜부터 |
| 격리 필요한 큰 변경 | `using-git-worktrees` | 편별 산출과 안 섞이게 |
| 새 스킬/슬래시 명령 제작·수정 | `writing-skills` | /야구사전·/제목 류 스킬 손댈 때 |
| 스크립트 변경 리뷰 요청/수령 | `requesting-code-review` / `receiving-code-review` | 파이프라인 코드 한정 |

## 안 쓰거나 제한적인 스킬

- `test-driven-development` — 이 리포는 테스트 없음(검증=mp4 프레임 눈확인). 파이프라인 스크립트 순수 로직 바꿀 때만 부분 적용.
- `dispatching-parallel-agents` / `subagent-driven-development` — 독립 작업 여러 개 동시일 때만. 편별 제작은 대개 순차·게이트라 기본 안 씀.
- `finishing-a-development-branch` — 코드 브랜치 마무리용. 콘텐츠 산출엔 무관.

## 요약

- **콘텐츠 제작 흐름**: `brainstorming`(기획) → [1차 게이트] → 배정 → [2차 게이트] → 생성 → `verification-before-completion`(완료 전 검증).
- **스크립트 손볼 때**: `systematic-debugging`(오류) / `writing-plans`(다단계 변경) / `writing-skills`(스킬 제작).
