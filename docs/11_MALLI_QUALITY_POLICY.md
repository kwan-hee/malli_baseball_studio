# 11. 말리 동화 선별 고품질 정책 (Malli Quality Policy)

말리 동화 채널의 "선별 품질 업그레이드" 정책 단독 문서 (2026-07-12 도입, Phase 1).
전 씬 AI 영상 생성 없이 체감 품질을 올리는 규칙. 기계 판독본 = `presets/approved/malli_video.json`,
순수 헬퍼 = `scripts/malli_quality.py` (테스트 `scripts/test_malli_quality.py`).

주의: 기존 문서 번호 `11_TITLE_ENGINE.md` 와 접두어가 겹침 — 후속 페이즈에서 번호 정리 예정.

## 원칙 — 선별 품질 업그레이드

- 유료 AI 영상은 편당 **권장 3씬, 최대 4씬**. 절대 전 씬 업그레이드 금지.
- 나머지 씬 전부 = 생성 이미지 + FFmpeg 모션 (Ken Burns 줌, compose.py 기존 방식).
- 크레딧 물량보다 프롬프트 품질·캐릭터 일관성이 우선.

## 유료 영상을 받을 씬 (우선순위)

1. 캐릭터의 중요한 큰 움직임
2. 감정 절정
3. 마법·변신 이벤트
4. 이야기 전환점·주요 액션

적격 문턱은 기존 배정 규칙과 동일: **motion 7~10 그리고 importance 85+**.
선택은 결정적 랭킹으로: importance 내림차순 → motion 내림차순 → emotion 내림차순 → 씬 ID 오름차순.
같은 에피소드·같은 점수표면 resume 시에도 항상 같은 씬이 선택된다.

## 이미지 모션으로 갈 씬

- 오프닝 풍경, 나레이션 위주 씬, 움직임 적은 대화
- 배경 설명, 조용한 감정 여백, 마무리 메시지, 타이틀·엔드 카드

FFmpeg 모션은 아동용 잔잔한 효과만: 느린 줌인/줌아웃(현행 홀짝 교대), 완만한 팬, 느린 푸시, 정적 페이드.
금지: 급줌, 흔들림, 과도한 크롭, 빠른 움직임, 캐릭터 왜곡. 인접 씬 간 효과 교대 권장.

## 이미지 승인 게이트 (유료 발주 전 필수)

선택된 씬이라도 아래 7항목 전부 통과 전에는 유료 영상 요청 금지.

1. 원본 이미지 존재
2. 검증 통과 (스타일 게이트 — docs/09 지브리 검수)
3. 말리 정체성 승인 (크림 털·빨간 리본·핑크 목걸이·뼈다귀 태그·눈)
4. 의상·색상 일관성 승인
5. 손(발)·얼굴 이상 없음
6. 씬 구도 승인
7. 유료 영상 적격 마크

미통과 시: 유료 요청 발주 금지 → 이미지 모션 사용 또는 수동 검토 대기, 사유는 안전하게 로그
(`[Malli Quality]` 접두어, 자격증명·계정 식별자 절대 미기록).

## 재시도·폴백 규칙

- 유료 생성 실패 시 **재시도 1회만**.
- 2차 실패 → 해당 씬은 이미지 모션으로 확정 대체. 추가 크레딧 지출 금지.
- 폴백 체인(기존 gen_clips_veo.py 검증): Veo 3.1 Fast → Seedance(REST) → Veo lite → 이미지 모션.

## 크레딧 예비 정책

- 가용 크레딧의 **15~20% (기본 20%)** 를 예비로 상시 보존. 전액을 제작 목표로 쓰지 않는다.
- 생성 전 프리플라이트: provider 잔액 조회 가능 시 실측 잔액 사용, 불가 시 로컬 추정 사용.
  보고서에 반드시 `provider` 실측 vs `local_estimate` 추정을 구분 표기.
- MCP 경로는 `get_cost: true` 로 과금 없는 비용 사전 확인 가능.
- **크레딧 단가 하드코딩 금지** — 가격은 변동. 잔액·비율만 계산.
- 편 완료 시마다 사용 보고 (무엇을 몇 회 생성 — 기존 01_COST_POLICY 기록 의무와 동일).

## 재사용·resume 정책

- 완성된 클립·이미지·오디오는 resume 시 무조건 재사용 (파일 존재+크기 캐시 — 기존 스크립트 방식).
- 성공한 클립을 불필요하게 재생성하지 않는다. 재생성은 명시적 품질 사유가 있을 때만.

## Higgsfield 미지원 설정 — 프롬프트로만 표현

MCP `generate_video`·직접 REST 모두 아래 개념을 파라미터로 지원하지 않는다.
프리셋의 `prompt_quality_block` / `avoid_in_prompt` 문구로만 표현할 것.

| 개념 | 표현 방법 |
|------|-----------|
| negative_prompt | avoid_in_prompt 문구를 프롬프트에 포함 |
| motion_strength | "gentle child-friendly movement, smooth slow" 서술 |
| camera_movement | "smooth slow cinematic camera movement, no shake, no aggressive zoom" 서술 |
| quality_level | 해상도(`resolution: 1080p, mode: std`)로만 제어 |
| character_consistency | start_image 참조 + "keep identity EXACTLY" 서술 |
| seed | 미지원 — 결정성은 씬 선택 단계에서만 보장 |

지원 확인된 파라미터: REST = `image_url, prompt, duration, resolution` /
MCP = `model, prompt, duration, aspect_ratio, medias(start_image), get_cost` (+검증된 `resolution, mode, generate_audio`).

## 듀얼 계정 라우팅 제한

계정별 독립 인증이 검증되기 전에는 듀얼 계정 라우터를 실제 생성 경로에 연결하지 않는다.
(현행: Higgsfield 키 1개 경로만 검증됨. Gemini 쪽 gemini_pool 페일오버와 별개.)

## 적용 범위 (Phase 1)

- 이 문서 + 프리셋 JSON + 헬퍼/테스트만 추가. 기존 에피소드 스크립트·기존 문서 무수정.
- 기존 에피소드 파이프라인 연결은 후속 페이즈에서 승인 후 진행.
