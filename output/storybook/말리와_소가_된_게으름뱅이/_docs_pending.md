# 문서 반영 대기 (2026-10-15, 동화 42편) — 원본 체크아웃 미커밋 수정과 충돌 방지 위해 별도 보관

## 1) docs/10_TALE_LIBRARY.md — 소가 된 게으름뱅이 행 교체
| 소가 된 게으름뱅이 ✅(말리와_소가_된_게으름뱅이) | 소 탈을 쓰고 일해보고 게으름을 뉘우침 | 부지런함 | 상 | 2026-10-15 제작. "무 먹으면 죽는다" 죽음 모티프 제거 → 무 = 일하는 기쁨을 깨달은 보상. 파는 장면→농부네로 데려감, 매질 없음 |

## 2) workflow/context-notes.md — 끝에 추가
## 2026-10-15 — 동화 42편 「말리와 소가 된 게으름뱅이」 제작
- 소재: 사용자 "후보 제시 후 선택" 방식 확인 → 미제작 "상" 4택(소가된게으름뱅이·달콤한죽·돌멩이수프·미녀와야수) 중 **소가 된 게으름뱅이** 선택. 게이트 2회 승인 후 자동 진행.
- 순화(1차 게이트 승인): 원작 "무를 먹으면 죽는다 → 죽으려고 무를 먹음"(죽음·자해 모티프) 제거 → 할아버지가 "일하는 기쁨을 알게 되는 날 무 한 입이 너를 돌려보내 줄 거란다" 예고 → 무 = 깨달음의 보상.
- 인물 연결 장치: 돌쇠 파란 허리띠 = 소 목의 파란 천. 이미지 10장·클립·썸네일 전부 일관 유지됨 — **변신 이야기는 사람↔동물 공통 소품을 정해 두면 동일 인물 인식이 쉬움.**
- **★Veo 변신 클립 함정**: "he transforms into an ox" 만 쓰면 사람이 그대로 남고 별도 마스코트 소가 생김(변신이 아닌 소환처럼 보임). **"HIS OWN BODY morphs… after the transformation the young man is GONE, only ONE ox remains, no second person/extra animal, natural four-legged ox(not a standing mascot)"** 로 명시하자 해결. 썸네일 이미지도 같은 문제 → "the ONLY ox-like figure, NO separate ox" 로 해결.
- s04 재생성 시 Veo 3.1 Fast 수요폭주(op error code 14) → 스크립트 폴백으로 Veo 3.1 Lite 성공, 화질 차이 육안 무.
- **★Whisper 환각(3.8 TTS 음성은 정상)**: 전체 269s 전사에서 54~85s 가 "chronoscmd/Shock at" 등 쓰레기 → s04 접두어 매칭 실패(0.21) → 비례 폴백 64.23s(오답, s03 마지막 대사가 s04로 넘어감). **해당 구간만 잘라 condition_on_previous_text=False 로 재전사하면 정상.** 편 폴더 `fix_boundaries.py`(경계 66.97s 무음 스냅) + `fix_words.py`(48~92s 단어 타임스탬프 교체, 원본 .orig.json 백업). 교체 전 compose 자막은 해당 구간 0.5s 큐로 붕괴했었음 — **비례 폴백 로그가 뜨면 자막도 반드시 확인.**
- 공통 로직 개선 후보(미적용, 사용자 결정 필요): ① split_scenes 에서 prefix match weak 시 해당 구간 자동 재전사 ② compose 클립 반복 재생 — 8s 클립이 30s 씬에서 루프해 변신 전 대사에 소가 보이는 순간 발생(클립 1회 재생 후 마지막 프레임 정지 or Ken Burns 이어붙이기 검토).
- Gemini 4 재확인(사용자 요청): models.list 에 Gemini 4 는 `gemini-4-argon`(텍스트 전용) 하나뿐 → 교체 지점 없음. 이미지 `gemini-3-pro-image`(정식판) 존재 — 다음 편 템플릿 교체 여부 사용자 결정 대기.
- 산출: 4:31(270.6s), 클립 s04·s09, 쇼츠 s04 단독 30.1s, 썸네일 "탈을 썼더니, / 소가 됐다?!". 베스트 제목 "소가 된 게으름뱅이, 탈을 썼더니 소가?! | 전래동화". 브랜치 worktree-storybook-lazy-ox.

## 3) workflow/checklist.md — 동화 진행 목록에 추가
- [x] 동화 42편 말리와 소가 된 게으름뱅이 (2026-10-15, 4:31, 클립 s04·s09, 쇼츠·썸네일·Obsidian 완료)
