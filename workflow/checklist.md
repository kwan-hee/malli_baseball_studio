# 프로젝트 체크리스트

## 초기 구축 (2026-07-07)

- [x] 폴더 구조 생성
- [x] AGENTS.md (라우팅 문서)
- [x] docs/01_COST_POLICY.md
- [x] docs/02_VIDEO_POLICY.md
- [x] docs/03_MALLI.md
- [x] docs/04_BASEBALL.md
- [x] docs/05_THUMBNAIL.md
- [x] docs/06_IMAGE.md
- [x] docs/07_AUDIO.md
- [x] docs/08_FFMPEG.md
- [x] docs/09_STORYBOOK.md
- [x] docs/10_TALE_LIBRARY.md — 퍼블릭 도메인 동화 150편 카탈로그 (2026-07-07)

## TODO 확정 필요 (사용자 결정)

- [x] 말리 외형·성격·말투 확정 → docs/03_MALLI.md (2026-07-07: 크림색 말티푸 새끼 암컷, 밝고 활발, 여성스럽고 귀여운 말투)
- [x] 말리 TTS 보이스 확정 → Edge TTS ko-KR-SunHiNeural, -5% (기존 파이프라인 검증값 이식)
- [ ] Hedra 보이스 선정 → 야구 쇼츠 전용 (2026-07-07 확정: 롱폼은 두 채널 모두 Edge TTS)
- [x] 동화 타깃 연령·편당 길이 확정 → docs/09_STORYBOOK.md (5~7세, 3~4분)
- [x] 동화 그림체 확정 → 지브리풍 + 수채화 (docs/09_STORYBOOK.md, 06_IMAGE.md)
- [x] 캐릭터 시트 원본 이미지 저장 → images/style_ref/malli_reference.png (기존 파이프라인에서 복사 완료)
- [ ] 채널별 썸네일 고정 색 확정 → docs/05_THUMBNAIL.md
- [x] 유료 생성 한도·월 예산 확정 → 예산 제한 없음 (docs/01_COST_POLICY.md)
- [x] prompts/malli_character.txt 캐릭터 시트 프롬프트 작성

## 첫 콘텐츠 제작

- [ ] 야구사전 1편 제작 (파이프라인 검증)
- [x] 야구사전 7편 "자책점 vs 비자책점" — 제작 완료 (2026-07-07: final.mp4 3:00 + 썸네일, Obsidian 저장 완료)
- [x] 야구사전 8편 "끝내기(Walk-off)" — 제작 완료 (2026-07-08: final.mp4 2:33 + 썸네일, Obsidian 저장 완료, 단일 호출 TTS·PAD 0.15 첫 야구 적용)
- [x] 야구사전 9편 "스탯캐스트" — 제작 완료 (2026-07-09: final.mp4 3:17 + 썸네일, Obsidian 저장 완료)
- [x] 야구사전 10편 "수비번호" — 제작 완료 (2026-07-10: final.mp4 3:33 + 썸네일, Obsidian 저장 완료, 이미지 QC 재생성 0)
- [x] 야구사전 11편 "배럴타구" — 제작 완료 (2026-07-10: final.mp4 3:09 + 썸네일, Obsidian 저장 완료, s07 이진수 재생성 1회)
- [x] 말리 동화 1편 제작 (파이프라인 검증) → 말리와_느림보_달팽이 (v2)
- [x] 말리 동화 2편 "말리와 커다란 순무" — 제작 완료 (2026-07-07: final.mp4 2:50 + 썸네일, Obsidian 저장 완료, 단일 호출 TTS 첫 적용)
- [x] 말리 동화 3편 "말리와 사자와 생쥐" — 제작 완료 (2026-07-08: final.mp4 3:12 + 썸네일, Obsidian 저장 완료)
- [x] 말리 동화 4편 "말리와 토끼와 거북이" — 제작 완료 (2026-07-09: final.mp4 3:24 + 썸네일, Obsidian 저장 완료)
- [x] 말리 동화 5편 "말리와 호랑이와 곶감" — 제작 완료 (2026-07-10: final.mp4 3:53 + 썸네일, Obsidian 저장 완료, whisper 재분할로 씬 경계 정상화)
