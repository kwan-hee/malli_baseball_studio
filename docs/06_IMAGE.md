# 06. 이미지 생성 규칙

## 원칙

- 생성·보정·캐릭터 유지·배경 수정 전부 **Nano Banana 기본** (2026-07-07 플랫폼 정책 — docs/01_COST_POLICY.md)
- 비용 규칙 우선 확인 (docs/01_COST_POLICY.md)
- 말리 등장 이미지는 반드시 캐릭터 시트 프롬프트에서 파생 (docs/03_MALLI.md)
- 생성 전 images/ 에 재사용 가능한 이미지 있는지 먼저 확인

## 규격

| 용도 | 크기 |
|------|------|
| 영상 본문 컷 | 1920x1080 (Ken Burns 줌 여유 위해 원본은 더 크게 권장) |
| 쇼츠 | 1080x1920 |
| 썸네일 배경 | 1280x720 이상 |

## 스타일

- 야구사전: (TODO: 확정 스타일 기입, 예 — 밝은 카툰, 야구장 배경)
- 말리 동화: **확실한 스튜디오 지브리(미야자키 필름) 셀 애니 스타일** — hand-drawn 2D, gouache 배경, 부드러운 자연광, 셀 셰이딩, 큰 눈. 단일 출처 = prompts/malli_character.txt 스타일 서픽스.
  - **⚠ 드리프트 주의 (2026-07-10 사용자 피드백)**: "watercolor texture / painterly brush strokes" 같은 표현을 넣으면 지브리에서 **수채화 그림책** 톤으로 이탈함. 스타일 서픽스에서 watercolor 제거하고 "NOT watercolor, NOT 3D, NOT generic cartoon" 을 명시할 것. 이 강화 서픽스로 지브리 재현 확인 완료.
- 한 편 안에서 그림체 혼용 금지

## 저장·명명

- 저장: images/{채널}/{편명}/
- 파일명: {순번}_{장면설명}.png (예: 01_hook_stadium.png)
- 생성 프롬프트는 같은 폴더에 prompts.md 로 함께 저장 (재생성 대비)
