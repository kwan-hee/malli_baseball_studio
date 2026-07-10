# 말리와 호랑이와 곶감 — 이야기 개요 + 대본 + 점수표 + 배정표 (게이트 산출물)

- 상태: 게이트 자동승인 (2026-07-07 사용자 확정) — 이미지·영상 생성 진행
- 소재: 한국 전래동화 "호랑이와 곶감" (TALE_LIBRARY "상"). 교훈=지레짐작 말고 잘 살펴보기.
- 총 10씬 / 발화 약 1,750자 ≈ 3분 (Kore 약 600자/분)
- 나레이션: Gemini TTS **Kore** + 동화 구연 연기 지시 (전체 대본 단일 호출 + Whisper 씬 분할)
- 대본 텍스트 단일 출처 = make_narration.py SCENES (여기는 검토용 사본)

## 각색 방침 (09_STORYBOOK 금지 규칙 대응)

- **말리 = 진행자/관찰자** (s01·s05·s10만 등장, 내부 이야기 씬은 호랑이·아기·엄마·나그네만 — 프롬프트 NO_MALLI).
- **순화**: 원작의 소도둑 → "길 잃은 나그네"로 완화. 폭력·죽음 없음. 호랑이는 다치지 않고 그냥 도망, 나그네는 폭신한 풀밭에 굴러 무사. 아기 안전.
- 호랑이는 "무섭게 생겼지만 겁 많고 우스운" 톤. 결말은 마을에 평화가 오는 밝은 마무리.
- 후렴/포인트: "어흥!" / "곶감이 나보다 더 무서운 놈인가 봐!" 지레짐작 유머.

## 점수표 + 배정 (규칙: motion 7~10 그리고 importance 85+ 만 영상)

| 씬 | 내용 | emotion | motion | importance | 배정 |
|----|------|---------|--------|-----------|------|
| s01 | 말리 인사 + 오늘 이야기 예고 | 7 | 3 | 80 | 이미지 + Ken Burns |
| s02 | 호랑이가 밤에 마을로 내려옴 | 6 | 6 | 84 | 이미지 + Ken Burns |
| s03 | 아기 울음 + 호랑이 창밖 엿듣기 | 6 | 3 | 82 | 이미지 + Ken Burns |
| s04 | "호랑이 왔다"에도 안 그침 | 6 | 4 | 84 | 이미지 + Ken Burns |
| s05 | 말리 관찰 (왜 안 그칠까) | 6 | 3 | 78 | 이미지 + Ken Burns |
| s06 | "곶감!" 에 아기 뚝 | 7 | 4 | 86 | 이미지 + Ken Burns |
| s07 | 호랑이 지레짐작 (곶감이 더 무섭다) | 8 | 5 | 88 | 이미지 + Ken Burns |
| s08 | 나그네가 호랑이 등에 올라탐 | 8 | 8 | 90 | **영상 — Higgsfield (Seedance)** |
| s09 | 호랑이 놀라 질주 + 나그네 굴러떨어짐 | 9 | 9 | 92 | **영상 — Higgsfield (Seedance)** |
| s10 | 말리 마무리 + 교훈 + CTA | 7 | 3 | 72 | 이미지 + Ken Burns |

## 생성 계획

- 이미지 10장: Gemini(gemini-3-pro-image-preview) + **malli_reference.png 멀티모달 첨부**, 지브리풍 수채화, 1920x1080
  - 말리 등장 씬(s01·s05·s10)만 강아지, 내부 씬은 NO_MALLI. 텍스트 금지.
- 영상 2편: s08(나그네 올라타는 순간 호랑이 놀람), s09(호랑이 질주 절정) — **Higgsfield Ultra / Seedance 2.0**, 8초, 1080p std
  - Flow 웹 자동화 불가 세션이라 Higgsfield 폴백 (3·4편 동일). **generate_video params 안에도 "model" 키 필요.**
- 나레이션: Gemini TTS Kore, 동화 구연 연기 지시문, 전체 단일 호출 + Whisper 분할
- 자막: MemomentKkukkukk 20pt, 바닥 밀착(MarginV=10) / BGM: Whisper of the Wind @15%
- compose: PAD 0.15 / delay 0 (씬 경계 무음 최소화)

## 제작 체크리스트

- [ ] 이미지 10장 (gen_images.py — 말리 일관성·등장규칙 QC)
- [ ] TTS 나레이션 (make_narration.py — Kore 단일 호출 + Whisper)
- [ ] Seedance 클립 2편 (s08, s09 — 1080p std)
- [ ] 조립 (compose.py)
- [ ] 프레임 검증
- [ ] 썸네일 (gen_thumbnail.py + compose_thumbnail.py) + Obsidian 50_Outputs/말리동화 저장
