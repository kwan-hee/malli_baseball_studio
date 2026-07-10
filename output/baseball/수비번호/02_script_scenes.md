# 수비번호 — 대본 + 점수표 + 배정표 (2차 게이트 산출물)

- 상태: 게이트 자동승인 (2026-07-07 사용자 확정) — 이미지·영상 생성 진행
- 총 10씬 / 발화 약 1,350자 ≈ 3분 20초 (Puck 약 400자/분)
- 나레이션: Gemini TTS **Puck** + 해설자 연기 지시 (전체 대본 단일 호출 + Whisper 씬 분할)
- 대본 텍스트 단일 출처 = make_narration.py SCENES (여기는 검토용 사본)

## 점수표 + 배정 (규칙: motion 7~10 그리고 importance 85+ 만 영상)

| 씬 | 내용 | emotion | motion | importance | 배정 |
|----|------|---------|--------|-----------|------|
| s01 | 훅 — 6-4-3 병살 자막 + 3루5·유격6 미스터리 | 8 | 9 | 92 | **영상 — Higgsfield (Seedance)** |
| s02 | 정의 — 9자리 이름표, 1~9 번호 배치 | 6 | 4 | 86 | 이미지 + Ken Burns |
| s03 | 6-3 / 6-4-3 읽는 법 | 6 | 5 | 84 | 이미지 + Ken Burns |
| s04 | 등번호와 다름 (위치 고정 번호) | 5 | 3 | 78 | 이미지 + Ken Burns |
| s05 | 기원 — 헨리 채드윅, 크리켓 차용 | 6 | 3 | 84 | 이미지 + Ken Burns |
| s06 | 해리 라이트가 3루5·유격6 확립, 1909 표준 | 6 | 3 | 82 | 이미지 + Ken Burns |
| s07 | KBO 5-4-3 삼중살 실제 장면(2016 잠실) | 8 | 9 | 90 | **영상 — Higgsfield (Seedance)** |
| s08 | 오해 — 번호가 위치 순서대로? 아님 | 6 | 4 | 84 | 이미지 + Ken Burns |
| s09 | 유격수 6번의 비밀 (초창기 얕은 외야수) | 7 | 5 | 88 | 이미지 + Ken Burns (motion 미달) |
| s10 | 마무리 + 다음 편(삼중살) + CTA | 6 | 3 | 70 | 이미지 + Ken Burns |

## 생성 계획

- 이미지 10장: Nano Banana(Gemini), 야구장 카툰 + 포지션/기록법 톤, 1920x1080
  - 실존 선수 얼굴 금지 (초상권). **번호 주제 특성상 AI 영문/숫자 텍스트 삽입 위험 큼 → 텍스트·숫자 금지 강하게 명시**
- 영상 2편: s01(6-4-3 병살 훅), s07(5-4-3 삼중살 실제 장면) — **Higgsfield Ultra / Seedance 2.0**, 8초, 1080p std
- 나레이션: Gemini TTS Puck, 해설자 연기 지시문, 전체 단일 호출 + Whisper 분할
- 자막: Malgun Gothic 18pt, 바닥 밀착(MarginV=10) / BGM: The Diamond.mp3 @15%
- compose: PAD 0.15 / delay 0 (씬 경계 무음 최소화 — tts-scene-gap 규칙)

## 제작 체크리스트

- [ ] 이미지 10장 (gen_images.py)
- [ ] TTS 나레이션 (make_narration.py — 단일 호출 + Whisper)
- [ ] Seedance 클립 2편 (s01, s07 — 1080p std)
- [ ] 조립 (compose.py)
- [ ] 프레임 검증
- [ ] 썸네일 (gen_thumbnail.py + compose_thumbnail.py) + Obsidian 50_Outputs/야구사전 저장
