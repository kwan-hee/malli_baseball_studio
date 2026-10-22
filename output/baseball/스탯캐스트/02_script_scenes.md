# 스탯캐스트 — 대본 + 점수표 + 배정표 (2차 게이트 산출물)

- 상태: 게이트 자동승인 (2026-07-07 사용자 확정) — 이미지·영상 생성 진행
- 총 10씬 / 발화 약 1,250자 ≈ 2분 40초 (Puck 약 490자/분)
- 나레이션: Gemini TTS **Puck** + 해설자 연기 지시 (전체 대본 단일 호출 + Whisper 씬 분할)
- 대본 텍스트 단일 출처 = make_narration.py SCENES (여기는 검토용 사본)

## 점수표 + 배정 (규칙: motion 7~10 그리고 importance 85+ 만 영상)

| 씬 | 내용 | emotion | motion | importance | 배정 |
|----|------|---------|--------|-----------|------|
| s01 | 훅 — 홈런 타구에 트래킹 라인이 그려짐 | 8 | 9 | 92 | **영상 — Higgsfield (Seedance)** |
| s02 | 정의 — 경기장 카메라·레이더가 공·선수 추적 | 6 | 5 | 85 | 이미지 + Ken Burns |
| s03 | 규칙 아님, 감→숫자 측정 장비 | 5 | 3 | 80 | 이미지 + Ken Burns |
| s04 | 기원 — 2015 전구장 도입 | 6 | 4 | 80 | 이미지 + Ken Burns |
| s05 | 트랙맨→2020 호크아이(테니스 기술) | 6 | 4 | 82 | 이미지 + Ken Burns |
| s06 | KBO 세계최초 ABS(2024), 판정 순간 | 8 | 7 | 90 | **영상 — Higgsfield (Seedance)** |
| s07 | 2025 KBO 중계 트래킹 데이터 표출 | 7 | 5 | 84 | 이미지 + Ken Burns (motion 미달) |
| s08 | 오해 1 — 세이버메트릭스와 차이 | 6 | 4 | 85 | 이미지 + Ken Burns |
| s09 | 오해 2 — KBO는 트랙맨/PTS, 2만 fps | 6 | 4 | 80 | 이미지 + Ken Burns |
| s10 | 마무리 + 다음 편(발사각) + CTA | 6 | 3 | 70 | 이미지 + Ken Burns |

## 생성 계획

- 이미지 10장: Nano Banana(Gemini), 야구장 카툰 + 데이터 시각화 톤, 1920x1080
  - 실존 선수 얼굴 금지 (초상권) — 상황·유니폼·트래킹 그래픽으로 표현. 텍스트·숫자 금지
- 영상 2편: s01(홈런 트래킹 훅), s06(KBO ABS 판정 순간) — **Higgsfield Ultra / Seedance 2.0**, 8초, 1080p std
- 나레이션: Gemini TTS Puck, 해설자 연기 지시문, 전체 단일 호출 + Whisper 분할
- 자막: Malgun Gothic 18pt, 바닥 밀착(MarginV=10) / BGM: The Diamond.mp3 @15%
- compose: PAD 0.15 / delay 0 (씬 경계 무음 최소화 — tts-scene-gap 규칙)

## 제작 체크리스트

- [ ] 이미지 10장 (gen_images.py)
- [ ] TTS 나레이션 (make_narration.py — 단일 호출 + Whisper)
- [ ] Seedance 클립 2편 (s01, s06 — 1080p std)
- [ ] 조립 (compose.py)
- [ ] 프레임 검증
- [ ] 썸네일 (gen_thumbnail.py + compose_thumbnail.py) + Obsidian 50_Outputs/야구사전 저장
