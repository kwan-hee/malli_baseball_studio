# 배럴타구 — 대본 + 점수표 + 배정표 (2차 게이트 산출물)

- 상태: 게이트 자동승인 (2026-07-07 사용자 확정) — 이미지·영상 생성 진행
- 총 10씬 / 발화 약 1,350자 ≈ 3분 20초 (Puck 약 380자/분)
- 나레이션: Gemini TTS **Puck** + 해설자 연기 지시 (전체 대본 단일 호출 + Whisper 씬 분할)
- 대본 텍스트 단일 출처 = make_narration.py SCENES (여기는 검토용 사본)

## 점수표 + 배정 (규칙: motion 7~10 그리고 importance 85+ 만 영상)

| 씬 | 내용 | emotion | motion | importance | 배정 |
|----|------|---------|--------|-----------|------|
| s01 | 훅 — 배트 심 임팩트 + 배럴 궤적 | 8 | 9 | 92 | **영상 — Higgsfield (Seedance)** |
| s02 | 정의 — 안타 확정에 가장 가까운 타구 | 6 | 4 | 86 | 이미지 + Ken Burns |
| s03 | 증명 — 배럴 타율 0.822 | 6 | 5 | 82 | 이미지 + Ken Burns |
| s04 | 기원 — 톰 탱고, 2016 도입 | 5 | 3 | 82 | 이미지 + Ken Burns |
| s05 | 기준 — 98마일 26~30도 | 6 | 4 | 88 | 이미지 + Ken Burns |
| s06 | 속도↑ 각도창 넓어짐 | 6 | 5 | 86 | 이미지 + Ken Burns (motion 미달) |
| s07 | 오해 — 배럴 vs 하드히트 | 6 | 4 | 85 | 이미지 + Ken Burns |
| s08 | 저지 26% 파워 히터 (홈런 임팩트) | 8 | 9 | 88 | **영상 — Higgsfield (Seedance)** |
| s09 | KBO 한국형 배럴 기준 논의 | 6 | 4 | 84 | 이미지 + Ken Burns |
| s10 | 마무리 + 다음 편(발사각) + CTA | 6 | 3 | 70 | 이미지 + Ken Burns |

## 생성 계획

- 이미지 10장: Nano Banana(Gemini), 데이터 시각화 + 야구장 카툰 톤, 1920x1080
  - 실존 선수 얼굴 금지 (초상권). **데이터 지표 주제(그래프·각도·수치)라 AI 영문/숫자 삽입 위험 큼 → 텍스트·숫자 금지 강하게 명시**
- 영상 2편: s01(배트 심 임팩트 훅), s08(파워 히터 홈런) — **Higgsfield Ultra / Seedance 2.0**, 8초, 1080p std
- 나레이션: Gemini TTS Puck, 해설자 연기 지시문, 전체 단일 호출 + Whisper 분할
- 자막: Malgun Gothic 18pt, 바닥 밀착(MarginV=10) / BGM: The Diamond.mp3 @15%
- compose: PAD 0.15 / delay 0 (씬 경계 무음 최소화 — tts-scene-gap 규칙)
- **generate_video 주의: 최상위 model 외에 params 안에도 "model" 키 필요** (수비번호 편 발견)

## 제작 체크리스트

- [ ] 이미지 10장 (gen_images.py)
- [ ] TTS 나레이션 (make_narration.py — 단일 호출 + Whisper)
- [ ] Seedance 클립 2편 (s01, s08 — 1080p std)
- [ ] 조립 (compose.py)
- [ ] 프레임 검증
- [ ] 썸네일 (gen_thumbnail.py + compose_thumbnail.py) + Obsidian 50_Outputs/야구사전 저장
