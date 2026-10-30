# 강의 CH1-2 「말리 캐릭터 시트 만들기」 — 1차 게이트 개요

- 커리큘럼 위치: CHAPTER 1 · 2번 강의 (커리큘럼 html 권장 12:00)
- 등장: 릴리 선생(강사, Leda) + 말리(분위기 담당, Kore). 1-1과 같은 교실·그림체·연출 방식
- 목표: 수강생이 Gemini에서 지금 채널이 쓰는 것과 같은 수준의 말리 캐릭터 시트를 직접 만들고, 검수하고, 저장해서 매번 첨부하는 법까지 익힌다.

## 1. 지금 쓰는 시트 분석 (`images/style_ref/malli_reference.png`)

| 칸 | 내용 |
|---|---|
| 가운데 | 정면 앉은 전신(가장 큼) — 얼굴·목걸이·리본·이름표가 가장 잘 보이는 기준 그림 |
| 오른쪽 위 | 옆모습 · 뒷모습 (꼬리·귀 모양 확인용) |
| 왼쪽 아래 | 얼굴 클로즈업 (표정 기준) |
| 아래 | 걷는 동작 3컷 연필 스케치 |
| 왼쪽 위 | 생활 공간 작은 그림(소파·분홍 담요·장난감) — 성격·세계관 |
| 전체 | 크림 종이 위 수채화·연필, 빈 공간 넉넉 |

**검수에서 걸리는 점 2개 (강의의 실제 사례로 사용)**
- 얼굴 클로즈업만 리본이 머리 위 → 기준(목걸이 리본)과 불일치
- 오른쪽 아래 구석에 토토로 같은 낙서 + "20.18" 서명 → 다른 회사 캐릭터·가짜 서명. 시트에 절대 남기면 안 됨

## 2. 강의 흐름 (약 12분, 6파트)

| 파트 | 시간 | 내용 | 화면 |
|---|---|---|---|
| ① 오프닝 | 0:00–0:50 | 1-1 복습 한 줄 + "말리 얼굴이 매번 달라지면?" | 말리 얼굴이 제각각인 그림 3장(일부러 틀리게 만든 예시) → 말리 깜짝 |
| ② 캐릭터 시트란? | 0:50–2:30 | 배우의 프로필 사진처럼, AI에게 "이 아이를 이렇게 그려"라고 보여 주는 한 장. 그림 + 글 두 개가 한 세트 | 시트 전체 → 칸별 확대 |
| ③ 시트 6칸 구성 | 2:30–4:30 | 정면 / 옆·뒤 / 얼굴 / 동작 / 생활 공간 / 빈 공간. 칸마다 왜 필요한지 | 칸 하나씩 강조 카드 |
| ④ 외형 고정 문장 쓰기 | 4:30–6:30 | 바꾸면 안 되는 5가지: 털 색, 귀 모양(길게 늘어진 곱슬 귀), 리본 위치(분홍 목걸이), 이름표 글자, 꼬리. "한 번 정하면 바꾸지 않기" | 체크리스트 카드 + 귀가 뾰족해진 실패 예시 |
| ⑤ Gemini 실습 | 6:30–9:30 | 프롬프트 붙여넣기 → 생성 → 틀린 곳만 짚어서 다시 요청("리본을 목걸이로만") | 프롬프트 카드(전문) → 실제 생성 결과 v1 → 수정 요청 → v2 |
| ⑥ 검수와 저장 | 9:30–11:20 | 검수 체크리스트 5개(귀·리본·이름표 글자·서명/워터마크/다른 캐릭터 없음·한 마리만) + 위 실제 사례 2개 / 저장 위치와 "매번 첨부" | 체크리스트 → 사례 확대 → 폴더 화면 카드 |
| ⑦ 마무리 | 11:20–12:00 | 정리 + 1-3 그림체 기준 예고 | 함께 손 흔들기 |

- 릴리 행동(클립 후보): 액자 속 사진 보여 주기, 시트를 칠판에 붙이기, 돋보기로 시트 살펴보기, 노트북 화면 가리키기, 체크 표시하기, 말리와 시트 속 말리 번갈아 보기, 인사 등
- 말리: "제 얼굴이 이렇게 많아요?", "제 귀는 늘어진 귀예요!", 검수 퀴즈 답하기

## 3. 실습용 프롬프트 (강의 화면에 그대로 보여 줄 문장 — lily_character.txt 구조 따름)

```
Character design sheet of Malli, a fluffy cream-colored Maltipoo puppy (girl),
soft hand-drawn watercolor and pencil illustration on warm cream textured paper.
Appearance (keep EXACTLY the same in every view): soft curly cream fur, long floppy curly ears
(never pointed), big dark eyes, black button nose, a red bow ribbon on a pink collar,
a gold bone-shaped tag engraved "Malli", fluffy curled tail.
Layout on one wide sheet:
- center: large front view, sitting
- right: side view and back view
- lower left: face close-up with a happy expression
- bottom: three small walking pose sketches
- upper left: small vignette of her cozy room (sofa, pink blanket, toy)
Pastel palette, soft shadows, plenty of empty space, no text except the tag,
no signature, no logos, no other characters.
```

## 4. 제작 방식 (1-1과 동일)

- 목소리 Gemini TTS 화자별 1회, 그림 Gemini(릴리·말리 시트 첨부), 글자 카드 로컬 렌더, Kling 3.0 480p·5초·소리 켬(현장음만)
- **실습 결과 그림(시트 v1·v2)은 실제로 Gemini에서 생성**해 화면에 씁니다(유료 이미지 2~4장 추가). 꾸며 낸 결과가 아니라 실제 결과를 보여 주기 위해서입니다.
- 장면 경계는 1-1 교훈대로 장면 wav 전체를 재전사해 대조합니다.

## 5. 확인이 필요한 점

1. 수강생이 쓰는 Gemini 화면: **Gemini 앱(gemini.google.com)** 인지 **Google AI Studio** 인지 — 강의 대사와 화면 카드의 버튼 이름이 달라집니다.
2. 실습 결과 화면: 실제 생성(유료 2~4장)으로 갈지
3. 현재 시트의 토토로 같은 낙서·"20.18" 서명: 강의 화면에는 가려서 쓰고 "이런 게 나오면 지우세요" 사례로 보여 줄지. 그리고 채널용 원본 시트도 깨끗한 버전으로 다시 만들지
