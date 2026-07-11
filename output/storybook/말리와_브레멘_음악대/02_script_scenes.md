# 말리와 브레멘 음악대 — 이야기 개요 + 대본 + 점수표 + 배정표 (게이트 산출물)

- 상태: 게이트 자동승인 — 이미지·영상 생성 진행.
- 소재: 그림 형제 "브레멘 음악대" (TALE_LIBRARY "상"). 교훈=힘을 합치면 해낼 수 있다(협력).
- 총 10씬 / 발화 약 1,900자 ≈ 3분 (Kore 약 600자/분)
- 나레이션: Gemini TTS **Kore** + 동화 구연 지시 (단일 호출 + Whisper 분할)
- 대본 단일 출처 = make_narration.py SCENES

## 각색 방침 (09_STORYBOOK 금지 규칙 대응)

- **말리 = 진행자/관찰자** (s01·s05·s10 등장, 내부 씬은 당나귀·개·고양이·수탉·심술쟁이들 — NO_MALLI).
- **순화**: 원작 도둑 → "심술궂은 아저씨들(심술쟁이)". 폭력 없음 — 동물들이 **큰 소리(합창)로 놀래켜** 쫓아냄. 아무도 안 다침. 밝은 결말(따뜻한 집·음식 차지).
- 동물들은 "나이 많아 쫓겨날 뻔했지만 힘 합쳐 해내는" 톤. 포인트: 히힝·멍멍·야옹·꼬끼오 대합창.

## 점수표 + 배정 (규칙: motion 7~10 그리고 importance 85+ 만 영상)

| 씬 | 내용 | emotion | motion | importance | 배정 |
|----|------|---------|--------|-----------|------|
| s01 | 말리 인사 + 오늘 이야기 예고 | 7 | 3 | 80 | 이미지 + Ken Burns |
| s02 | 당나귀 쫓겨나 브레멘으로 출발 | 6 | 5 | 84 | 이미지 + Ken Burns |
| s03 | 개 합류 | 6 | 4 | 82 | 이미지 + Ken Burns |
| s04 | 고양이 합류 | 6 | 4 | 82 | 이미지 + Ken Burns |
| s05 | 수탉 합류 + 넷 완성 (말리 관찰) | 7 | 5 | 84 | 이미지 + Ken Burns |
| s06 | 밤 숲, 오두막 불빛 발견 | 6 | 4 | 84 | 이미지 + Ken Burns |
| s07 | 오두막 안 음식+심술쟁이, 꾀 | 6 | 4 | 84 | 이미지 + Ken Burns |
| s08 | 동물 탑 + 히힝멍멍야옹꼬끼오 대합창 | 9 | 9 | 92 | **영상 — Higgsfield (Seedance)** |
| s09 | 심술쟁이 놀라 도망 + 오두막 차지 | 8 | 8 | 90 | **영상 — Higgsfield (Seedance)** |
| s10 | 말리 마무리 + 교훈(협력) + CTA | 7 | 3 | 72 | 이미지 + Ken Burns |

## 생성 계획

- 이미지 10장: Gemini(gemini-3-pro-image-preview) + malli_reference 첨부, 지브리 수채화, 1920x1080. 텍스트 금지. 말리 등장 s01·s05·s10만.
- 영상 2편: s08(동물 탑 대합창), s09(심술쟁이 도망) — Higgsfield Seedance 2.0, 8초, 1080p std. **generate_video params 안에도 "model" 키 필요.**
- 나레이션: Kore + 동화 구연 지시, 단일 호출 + Whisper. **씬 길이 붕괴 시 씬wav 삭제·재실행.**
- 자막: MemomentKkukkukk 20pt 바닥밀착 / BGM Whisper of the Wind @15% / compose PAD 0.15
- **Gemini 다중계정 페일오버 적용** (gemini_pool)

## 제작 체크리스트

- [ ] 이미지 10장 (말리 일관성·등장규칙·순화 톤 QC)
- [ ] TTS 나레이션 (Kore 단일 호출 + Whisper)
- [ ] Seedance 클립 2편 (s08, s09)
- [ ] 조립 (compose.py)
- [ ] 프레임 검증
- [ ] 썸네일 + 제목 최적화 + Obsidian 50_Outputs/말리동화 저장
