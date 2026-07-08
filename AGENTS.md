# PROJECT 지침 (라우팅 문서)

말리 동화 채널 + 야구사전 채널 콘텐츠 생산 프로젝트.
이 문서는 얇게 유지한다. 상세 규칙은 docs/ 에 있고, 여기서는 "언제 무엇을 읽을지"만 정한다.

## 문서 라우팅

| 작업 | 먼저 읽을 문서 |
|------|---------------|
| 비용 발생 작업 (API, 생성형 AI 호출) | docs/01_COST_POLICY.md |
| 영상 제작·편집 전반 | docs/02_VIDEO_POLICY.md |
| 말리 캐릭터 등장 콘텐츠 (대본, 이미지) | docs/03_MALLI.md |
| 야구사전 콘텐츠 | docs/04_BASEBALL.md + docs/03_MALLI.md |
| 말리 동화 콘텐츠 | docs/09_STORYBOOK.md + docs/03_MALLI.md |
| 동화 에피소드 소재 선정 | docs/10_TALE_LIBRARY.md (퍼블릭 도메인 150편 카탈로그) |
| 썸네일 제작 | docs/05_THUMBNAIL.md |
| 이미지 생성 | docs/06_IMAGE.md |
| 나레이션·BGM·효과음 | docs/07_AUDIO.md |
| ffmpeg 명령 실행 | docs/08_FFMPEG.md |

## 폴더 경계

- `docs/` — 정책·규칙. 여기 있는 내용이 진실의 원천.
- `prompts/` — 프롬프트 템플릿만. 규칙 넣지 말 것.
- `scripts/` — 자동화 스크립트 (Python, ps1 등).
- `images/` — 생성·수집한 이미지 소스.
- `output/` — 작업 중간산출물. 최종본 아님.
- `workflow/` — 진행상황 파일. checklist.md, context-notes.md 필수 유지.

## 제작 승인 게이트 (상시 규칙 — 2026-07-07 사용자 확정)

두 채널(야구사전, 말리 동화) 모두 콘텐츠 제작 시 아래 2단계 승인을 반드시 거친다.
자율 진행 원칙보다 이 규칙이 우선한다.

1. **1차 게이트 — 조사 승인.** 제작 명령을 받아도 곧바로 실행하지 않는다.
   조사(리서치/스토리 개요)를 먼저 수행하고 결과를 사용자에게 보여준 뒤 승인을 기다린다.
2. 승인 후: 씬 분할 + 점수표(emotion/motion/importance) 채점 →
   점수 낮은 씬 = 이미지(Ken Burns), 점수 높은 씬 = 지정 영상 플랫폼(01_COST_POLICY) 배정.
3. **2차 게이트 — 생성 승인.** 이미지·영상을 실제로 생성하기 전에
   씬별 배정표(어떤 씬을 이미지로, 어떤 씬을 어느 플랫폼 영상으로)를 보고하고 승인을 기다린다.
4. 승인받은 뒤에만 생성 실행. 이후 단계(TTS·조립·썸네일)는 승인 없이 진행 가능.

## 산출물 규칙

- 중간산출물(초안, 리서치 노트, 렌더 전 소스)은 `output/` 에 저장.
- **최종 완성본은 Obsidian vault `50_Outputs/` 에 저장** (야구사전 → `50_Outputs/야구사전`, 동화 → `50_Outputs/말리동화`).
  - Vault 절대경로: `C:\Users\user\Documents\Joy_SecondBrain\50_Outputs` (야구사전/ · 말리동화/ 하위폴더). 신규 주제 추천 전 여기부터 확인해 기존 편과 중복 회피.
- 세션 시작 시 `workflow/checklist.md` 확인, 작업 중 결정사항은 `workflow/context-notes.md` 에 즉시 기록.
