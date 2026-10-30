# CH2-2 새 클립 3개 만들기 (C30~C32)

> **2026-10-30 변경: 클립은 Windows 에서 만든다** — Windows Chrome + Claude in Chrome 확장으로 Higgsfield 웹 직접 조작,
> 계정 @streamingruler1405 (docs/14_HIGGSFIELD_WEB.md 맨 위). 아래 맥 명령은 예전 방식 기록이고,
> **클립 사양(새 3개만 · 시작 그림 · 프롬프트 = clip_prompts.json · 테스트 Wan 3.0 480p 소리 켬 → 정식 Wan 3.0 720p 소리 켬)은 그대로**다.
> 결과 파일 이름도 같다: `clips/C30_1080p.mp4` ~ `clips/C32_1080p.mp4`.

준비물(Windows 에서 이미 생성 — Z: 드라이브 = 맥 HDD 라 그대로 보임):
`clip_prompts.json`(**새 클립 3개만** 들어 있음), `images/C30.png`·`C31.png`·`C32.png`(시작 그림 = P05·P06·P08), 점수판 = `make_clip_inputs.py` 의 `CLIPS`

- 재사용 클립은 여기서 만들지 않는다. compose.py 가 아래 순서로 찾아 쓴다.
  1. 이 편 `clips/` (C30~C32)
  2. CH2-1 `clips/` (C22·C23 — CH2-1 MAC_CLIPS.md 로 만듦, C05~C17 복사본)
  3. CH1-2 `clips/` (C05·C07~C17 — CH1-2 Wan 정식 클립)
- 2026-10-30 "전체 Wan 3.0" 결정으로 1-2·2-1 클립은 아직 `clips/` 가 비어 있음 → 지금 조립하면 그 장면들은 정지 그림 + 줌.
- 새로 만들 클립은 `--scenes C30,C31,C32` 로 **반드시 범위를 지정**한다.

## 1) 테스트 버전 — Wan 3.0 · 480p · 소리 켬 (고정)

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
EP=output/storybook/강의_CH2-2_Python_FFmpeg_Git_설치
hfmalli whoami                                   # higgsfield.study 확인
# 시험 실행 — 크레딧 0. cost·balance 확인
python3 scripts/hf_web_clips.py "$EP" --test --scenes C30
# 비용 보고·승인 후 제출
python3 scripts/hf_web_clips.py "$EP" --test --scenes C30,C31,C32 --submit
```

- 결과: `clips/C30_1080p.mp4` ~ `clips/C32_1080p.mp4` (이름의 1080p 는 관례)
- 클립이 오면 Windows 에서 `python compose.py` 만 다시 실행 → 시작 그림 자리가 클립으로 바뀜
- 클립에 사람 목소리·음악이 섞였으면 그 클립만 compose 에서 현장음 0 처리
- 확인할 점: C32 팻말에 글자가 생기지 않았는지(동그라미·가위표 모양만), C31 말리 얼굴이 원형으로 돌아오는지

## 2) 정식 버전 — 테스트본 확인 후 사용자 결정

정식 설정 = **`--final` 고정: Wan 3.0 · 720p · 소리 켬** (CLAUDE.md, 다른 모델·해상도 금지).
Wan 테스트 클립 3개는 `clips_wan_test/` 로 옮긴 뒤 시험 실행 → 비용 보고 → 제출.

```bash
mkdir -p "$EP/clips_wan_test" && mv "$EP"/clips/C3[0-2]_1080p.mp4 "$EP/clips_wan_test/"
python3 scripts/hf_web_clips.py "$EP" --final --scenes C30 --max-credits 15                  # 시험 실행
python3 scripts/hf_web_clips.py "$EP" --final --scenes C30,C31,C32 --max-credits 15 --submit  # 승인 후
```
