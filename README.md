# PROJECT — 말리 동화 · 야구사전 콘텐츠 스튜디오

두 유튜브 채널(말리 동화, 야구사전)의 영상을 자동 생산하는 파이프라인.

## 구조

- `AGENTS.md` — 라우팅 문서. 제작 승인 게이트(2단계) 포함. 여기부터 읽을 것.
- `docs/` — 정책 문서 9개 (비용/플랫폼, 영상, 캐릭터, 채널 규칙, 썸네일, 이미지, 오디오, ffmpeg, 동화)
- `prompts/` — 말리 캐릭터 기준 프롬프트 (모든 이미지의 파생 원본)
- `workflow/` — checklist.md, context-notes.md (진행 상황·결정 기록)
- `output/{storybook|baseball}/{편명}/` — 에피소드별 산출물 + 제작 스크립트
  - `gen_images.py` 이미지 생성 / `make_narration*.py` TTS / `compose.py` ffmpeg 조립
  - 영상·음성·이미지 산출물은 용량 문제로 리포 제외 (.gitignore)

## 파이프라인 요약

주제 입력 → ①리서치/개요 (승인) → ②씬 분할 + 점수표 + 배정 (승인) →
이미지(Nano Banana) + 영상(동화: Flow/Veo 3.1, 야구: Higgsfield/Seedance 2.0) →
Gemini TTS 성우 연기 나레이션 → ffmpeg 조립(자막 바닥, BGM, 엔딩 CTA) → 최종 MP4

## 완성 에피소드

- 말리 동화: 말리와 느림보 달팽이 (1:56)
- 야구사전: 사이클링 히트 (2:31)
