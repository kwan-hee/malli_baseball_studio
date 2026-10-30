# 맥 미니에서 CH1-3 새 클립 6개 만들기

- 새 클립 = C20~C25 만 (`clip_prompts.json` 에 6개만 들어 있음). 시작 그림 `images/C20.png` ~ `images/C25.png`.
- C07~C19 는 **CH1-2 클립을 그대로 재사용** — compose.py 가 `../강의_CH1-2_말리_캐릭터_시트/clips/` 에서 찾는다. 그래서 CH1-2 클립이 먼저 있어야 1-3 도 움직인다.
- 계정 = higgsfield.study (2026-10-29 변경). 런웨이 작업과 크레딧 잔액을 함께 쓴다.

| 클립 | 시작 그림 | 동작 | 재생 |
|---|---|---|---|
| C20 | N01 | 릴리가 그림 두 장 안고 들어오며 손 흔들기 | once |
| C21 | N02 | 릴리가 이젤에 붓질하다 돌아보며 웃기 | loop |
| C22 | N03 | 릴리가 시트와 풍경 그림을 번갈아 들어 보이기 | loop |
| C23 | N04 | 릴리가 O·X 팻말 번갈아 들기 | loop |
| C24 | M09 | 말리가 스케치북을 흔들며 자랑하기 | once |
| C25 | M10 | 말리가 돋보기로 이리저리 살펴보기 | once |

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
EP=output/storybook/강의_CH1-3_그림체_기준_그림
hfmalli whoami                                   # higgsfield.study 확인

# 테스트 (Wan 3.0 · 480p · 소리 켬 고정) — 시험 실행(크레딧 0) → cost·balance 보고 → 제출
python3 scripts/hf_web_clips.py "$EP" --test --scenes C20
python3 scripts/hf_web_clips.py "$EP" --test --submit

# 정식 (--final = Wan 3.0 · 720p · 소리 켬 고정, CLAUDE.md 2026-10-29) — 테스트 확인 후. 테스트 클립은 먼저 옆으로 치움
[ -d "$EP/clips" ] && mv "$EP/clips" "$EP/clips_wan_test"
python3 scripts/hf_web_clips.py "$EP" --final --scenes C20   # 시험 실행 → cost·balance 보고
python3 scripts/hf_web_clips.py "$EP" --final --submit
```

- 클립이 오면 Windows 에서 `python compose.py` 만 다시 실행 → 시작 그림 자리가 클립으로 바뀜
- 클립에 사람 목소리·음악이 섞였으면 그 클립만 compose 에서 현장음 0 처리
