# 이닝과 공수교대 — 대본 + 점수표 + 배정표 (2차 게이트 산출물)

- 상태: 게이트 자동승인 — 이미지·영상 생성 진행. **기초 시리즈 첫 편** (2026-07-10 사용자 방향 전환: 고급/최신 말고 기초 우선).
- 총 10씬 / 발화 약 1,350자 ≈ 3분 20초 (Puck 약 380자/분)
- 나레이션: Gemini TTS **Puck** + 해설자 연기 지시(초보 친화) — 전체 단일 호출 + Whisper 분할
- 대본 텍스트 단일 출처 = make_narration.py SCENES (여기는 검토용 사본)

## 점수표 + 배정 (규칙: motion 7~10 그리고 importance 85+ 만 영상)

| 씬 | 내용 | emotion | motion | importance | 배정 |
|----|------|---------|--------|-----------|------|
| s01 | 훅 — 전광판 + "왜 9회?" | 7 | 4 | 84 | 이미지 + Ken Burns |
| s02 | 정의 — 이닝=초+말, 두 팀 교대 | 6 | 4 | 86 | 이미지 + Ken Burns |
| s03 | 공수교대 — 아웃3개, 선수 우르르 교대 | 7 | 8 | 88 | **영상 — Higgsfield (Seedance)** |
| s04 | 9번 반복 = 한 경기 | 5 | 3 | 80 | 이미지 + Ken Burns |
| s05 | 기원 — 1857 규칙 통일, 9이닝 | 6 | 3 | 84 | 이미지 + Ken Burns |
| s06 | 원래 21점 선취제였다 | 6 | 4 | 82 | 이미지 + Ken Burns |
| s07 | KBO 연장 11회(2025 변경) | 6 | 4 | 84 | 이미지 + Ken Burns |
| s08 | 9회말 건너뛰는 이유 | 6 | 3 | 82 | 이미지 + Ken Burns |
| s09 | 홈팀 끝내기 홈런 (마지막 공격) | 9 | 9 | 90 | **영상 — Higgsfield (Seedance)** |
| s10 | 마무리 + 다음 편(3아웃) + CTA | 6 | 3 | 70 | 이미지 + Ken Burns |

## 생성 계획

- 이미지 10장: Nano Banana(Gemini), 밝은 기초 친화 카툰, 1920x1080
  - 실존 얼굴 금지. **전광판·회 표시 주제라 AI 숫자/텍스트 삽입 위험 → 텍스트·숫자 금지 강하게 명시, 전광판은 blank 지정.**
- 영상 2편: s03(공수교대 선수 우르르), s09(끝내기 홈런) — Higgsfield Seedance 2.0, 8초, 1080p std
- 나레이션: Gemini TTS Puck, 초보 친화 지시, 단일 호출 + Whisper
- 자막: Malgun Gothic 18pt 바닥밀착 / BGM: The Diamond @15% / compose PAD 0.15
- **Gemini 다중계정 페일오버 적용** (gemini_pool) — 크레딧 소진 시 자동 키 전환

## 제작 체크리스트

- [ ] 이미지 10장 (gen_images.py)
- [ ] TTS 나레이션 (make_narration.py)
- [ ] Seedance 클립 2편 (s03, s09 — 1080p std)
- [ ] 조립 (compose.py)
- [ ] 프레임 검증
- [ ] 썸네일 + Obsidian 50_Outputs/야구사전 저장
