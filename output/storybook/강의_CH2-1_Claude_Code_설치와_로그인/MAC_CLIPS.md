# 맥 미니에서 CH2-1 새 클립 4개 만들기 (C20~C23)

준비물(Windows 에서 이미 생성 — Z: 드라이브 = 맥 HDD 라 그대로 보임):
`clip_prompts.json`(16개), `images/C20.png` ~ `images/C23.png`(시작 그림 = P01~P04), 점수판 = `make_clip_inputs.py` 의 `CLIPS`

- 2026-10-30 사용자: **전체 Wan 3.0.** 예전에 복사해 둔 1-2 Kling 클립 12개(C05·C07~C17)는 `clips_kling/` 로 옮김.
  그 12개는 여기서 만들지 않는다 → **CH1-2 Wan 정식 클립이 나온 뒤 CH1-2 `clips/` 에서 C05·C07~C17 을 이 폴더 `clips/` 로 복사**한다.
  ⚠ `--scenes` 를 빼고 실행하면 그 12개까지 새로 만들어 크레딧이 두 번 든다.
- 새로 만들 클립은 `--scenes C20,C21,C22,C23` 으로 **반드시 범위를 지정**한다.

## 1) 테스트 버전 — Wan 3.0 · 480p · 소리 켬 (고정)

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
EP=output/storybook/강의_CH2-1_Claude_Code_설치와_로그인
hfmalli whoami                                   # higgsfield.study 확인
# 시험 실행 — 크레딧 0. cost·balance 확인
python3 scripts/hf_web_clips.py "$EP" --test --scenes C20
# 비용 보고·승인 후 제출
python3 scripts/hf_web_clips.py "$EP" --test --scenes C20,C21,C22,C23 --submit
```

- 결과: `clips/C20_1080p.mp4` ~ `clips/C23_1080p.mp4` (이름의 1080p 는 관례)
- 클립이 오면 Windows 에서 `python compose.py` 만 다시 실행 → 시작 그림 자리가 클립으로 바뀜
- 클립에 사람 목소리·음악이 섞였으면 그 클립만 compose 에서 현장음 0 처리

## 2) 정식 버전 — 테스트본 확인 후 사용자 결정

정식 설정 = **`--final` 고정: Wan 3.0 · 720p · 소리 켬** (2026-10-29 CLAUDE.md 확정, 다른 모델·해상도 금지).
Wan 720p 가격은 아직 미확인 → 시험 실행의 cost 로 확인해 보고한다. 1-2 재사용 12개는 CH1-2 Wan 정식 클립을 복사해 쓴다(위 안내).
Wan 테스트 클립 4개는 `clips_wan_test/` 로 옮긴 뒤 시험 실행 → 비용 보고 → 제출.

```bash
mkdir -p "$EP/clips_wan_test" && mv "$EP"/clips/C2[0-3]_1080p.mp4 "$EP/clips_wan_test/"
python3 scripts/hf_web_clips.py "$EP" --final --scenes C20 --max-credits 15                  # 시험 실행
python3 scripts/hf_web_clips.py "$EP" --final --scenes C20,C21,C22,C23 --max-credits 15 --submit  # 승인 후
```
