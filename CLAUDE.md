# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 이 리포가 하는 일

유튜브 채널 2개(말리 동화, 야구사전)의 영상을 생산하는 콘텐츠 파이프라인.
코드보다 **문서가 진실의 원천**이다. 작업 전 반드시 읽을 것:

1. `AGENTS.md` — 문서 라우팅 + **제작 승인 게이트** (아래 요약)
2. `workflow/context-notes.md` — 지금까지의 결정과 이유. 새 세션은 여기부터.
3. 작업 관련 `docs/` 문서 (AGENTS.md 라우팅 표 참조)

## 절대 규칙: 2단계 승인 게이트

콘텐츠 제작 요청을 받아도 곧바로 생성하지 않는다.

1. **1차 게이트**: 리서치(야구)/이야기 개요(동화)만 만들어 보고 → 사용자 승인 대기
2. 승인 후: 대본 + 씬 분할 + 점수표(emotion/motion/importance) + 배정표 작성
3. **2차 게이트**: 배정표 보고 → 승인 대기 → 그 후에만 이미지·영상 생성 (크레딧 소모 단계)
4. TTS·조립·썸네일은 승인 불필요

씬 배정 규칙: **motion 7~10 그리고 importance 85+ 씬만 영상 생성**, 나머지는 정지 이미지 + Ken Burns. (편당 영상 2개 내외 = 크레딧 88% 절감 구조)

## 에피소드 제작 명령

에피소드마다 `output/{storybook|baseball}/{편명}/` 폴더에 스크립트 3종을 복사·수정해 실행한다.
완성 에피소드(말리와_느림보_달팽이, 사이클링_히트)가 템플릿.

```bash
python gen_images.py        # 씬 이미지 생성 (Gemini, API 키는 C:\youtube_longform_agent\.env 재사용)
python make_narration.py    # Gemini TTS 나레이션 (동화: make_narration_v2.py 가 최신 패턴)
python compose.py           # ffmpeg 최종 조립 → {편명}_final.mp4
```

- 부분 재생성: 해당 `audio*/sXX.wav` 와 `scenes*/sXX.mp4` 삭제 후 재실행 (캐시 방식)
- ffmpeg 경로는 compose.py 에 하드코딩 (WinGet 설치 위치)
- 테스트 없음 — 검증은 최종 mp4에서 프레임 추출(ffmpeg -ss N -frames:v 1)해 눈으로 확인

## 확정된 제작 규칙 (어기면 사용자가 되돌림)

- **TTS는 Gemini TTS + 성우 연기 지시문** (동화 Kore / 야구 Puck). Edge TTS는 기계적이라 쿼터 폴백 전용 — 상세 docs/07_AUDIO.md
- **TTS는 전체 대본 단일 호출로 생성** (씬별 호출 금지 — 호출마다 톤이 달라져 목소리가 씬마다 바뀜. Whisper 타임스탬프로 씬 분할)
- **나레이션에 행동 지문 금지** ("폴짝폴짝 뛰어갔어요" X). 행동은 화면이 보여주고, 나레이션은 대사+감정
- **자막은 바닥 밀착** MarginV=10 (두 채널 공통)
- **엔딩에 구독·좋아요 CTA 필수** (동화: 말리 말투 / 야구: 해설자 한 문장)
- 말리 이미지 프롬프트는 `prompts/malli_character.txt` 에서만 파생, `images/style_ref/malli_reference.png` 를 multimodal 참조로 첨부
- 릴리 선생 이미지 프롬프트는 `prompts/lily_character.txt` 에서 파생, `images/style_ref/lily.png` 를 multimodal 참조로 첨부 (2026-10-22 확정)
- 야구사전 삽화에 실존 선수 얼굴 금지 (유니폼 색·상황으로 표현)
- 영상 플랫폼: 동화 = Google Flow(Veo 3.1) 우선 / 야구 = Higgsfield(Seedance) 우선 — docs/01_COST_POLICY.md

## 아키텍처 주의점

- "말리"는 채널마다 다른 존재: 동화 = 강아지 주인공(03_MALLI.md), 야구 = 해설자 페르소나(04_BASEBALL.md). 혼용 금지.
- 대본 텍스트의 단일 출처는 `make_narration*.py` 의 SCENES dict — compose.py 가 import 해서 자막(SRT)도 여기서 생성
- Google Flow는 웹 자동화로 조작하되 **로컬 파일 업로드만 사용자 수동** (브라우저 보안 제한)
- Higgsfield MCP 503 장애 시: higgsfield.ai/assets 웹에서 `<video>` src 추출해 curl 다운로드 (context-notes 참조)
- Windows cp949 콘솔: print에 한자 포함 경로 넣으면 UnicodeEncodeError — 파일명만 출력
- 미디어 산출물(mp4/wav/png)은 .gitignore로 리포 제외. 최종본은 로컬 `output/` + Obsidian `50_Outputs/`

## 기록 의무

결정·발견이 생기면 `workflow/context-notes.md` 에 즉시 추가, 작업 완료 시 `workflow/checklist.md` 갱신. 다음 세션이 이 두 파일로 이어받는다.

## 작업 태도 (행동 가이드라인)

파이프라인 스크립트를 다룰 때 지킬 원칙 (Karpathy LLM 코딩 가이드라인 기반, 상세는 글로벌 `~/.claude/CLAUDE.md`).

- **가정 금지·불확실하면 질문**: 소재의 순화 수위, 죽음·폭력 처리, 대상 파일이 애매하면 멈추고 물어본다. 해석이 여럿이면 임의 선택하지 말고 제시한다. (소재 적합도 "중/하"는 특히)
- **최소 변경 (surgical)**: 편별 스크립트는 템플릿(최신 완성편)을 복사해 **SCENES·STYLE·파일명·VIDEO_SCENES 키만** 고친다. 무관한 부분 "개선"·리팩터 금지, 기존 스타일 유지. 파이프라인 공통 로직(경계 로직·compose)은 요청 없이 건드리지 않는다.
- **검증 가능한 성공 기준**: "영상 만들기" → "compose 산출 mp4에서 클립 씬·핵심 개념 씬 프레임 추출(ffmpeg -ss) → 자막·화면 일치 눈으로 확인". 야구 사실 주장은 웹 리서치 교차검증(나무위키·위키백과) 후 대본에 반영. 완료 선언 전 반드시 검증.
- **에러는 읽고 고친다**: TTS 잘림·whisper 경계 붕괴·클립 실패 시 로그(task output)를 실제로 읽고 원인 확인 후 대응. 같은 작업 무한 재시도 금지 — 실패하면 원인 보고 후 판단.
- **크레딧 소모 인지**: 이미지·TTS·클립은 유료(Gemini/Higgsfield). 크레딧 소진 등 비용 관련 상황은 임의 진행 말고 사용자에게 알린다.
