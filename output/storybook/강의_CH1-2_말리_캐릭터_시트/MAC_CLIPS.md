> ⚠ 2026-10-30 사용자: **전체 클립을 Wan 3.0 으로 다시 만든다.** 10-29 에 만든 Kling 3.0 정식 클립 19개(제출 기록 `hf_web_jobs.json` 포함)는 `clips_kling/` 로 옮겨 보관(삭제 안 함). `clips/` 는 비어 있음 → 아래 1)테스트 → 사용자 확인 → 2)정식 순서.
> 이 폴더 클립은 **CH1-3(compose 가 직접 읽음)·CH2-1(C05·C07~C17 복사)** 도 쓴다.

# 1) 맥 미니에서 CH1-2 테스트 클립 19개 만들기 (Wan 3.0 · 480p · 소리 켬 고정)

준비물(이 폴더, Windows 에서 이미 생성 — Z: 드라이브 = 맥 HDD 라 그대로 보임):
`clip_prompts.json`(C01~C19), `images/C01.png` ~ `images/C19.png`, 점수판 = `make_clip_inputs.py` 의 `CLIPS`

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
hfmalli whoami                       # ok:true, higgsfield.study 확인 (아니면 docs/14_HIGGSFIELD_WEB.md '막혔을 때')
# 1) 시험 실행 — 크레딧 0. --test = Wan 3.0 · 480p · 소리 켬 고정 (다른 옵션으로 못 바꿈)
python3 scripts/hf_web_clips.py output/storybook/강의_CH1-2_말리_캐릭터_시트 --test --scenes C01
#    확인할 것: 화면에 Wan 3.0 이 잡히는지, 480p·소리 켬이 잡히는지, 버튼 비용(cost)·잔액(balance)
#    hfmalli 가 --model 옵션을 모르면 여기서 오류 → hfmalli 에 Wan 모델 선택 추가 필요(맥 ~/.local/bin/hfmalli, 이 리포 밖)
# 2) 비용 보고 후 제출
python3 scripts/hf_web_clips.py output/storybook/강의_CH1-2_말리_캐릭터_시트 --test --submit
```

- 결과: `clips/C01_1080p.mp4` ~ `clips/C19_1080p.mp4` (이름의 1080p 는 관례, 실제 480p)
- 클립이 오면 Windows 에서 `python compose.py` 만 다시 실행 → 시작 그림 자리가 클립으로 바뀜
- C04·C05·C07·C08 은 1-1 의 K12·K15·K13·K14 와 같은 그림·동작 → 1-1 을 다시 조립할 때 복사해서 재사용 가능
- 클립에 사람 목소리·음악이 섞였으면 그 클립만 compose 에서 현장음 0 처리

---

# 2) 정식 버전: Wan 3.0 · 720p · 소리 켬 (`--final` 고정) — 테스트본을 사용자가 통과시킨 뒤에만

같은 그림(`images/C01~C19.png`)·같은 프롬프트(`clip_prompts.json`)로 19개. Wan 720p 가격 미확인 → 시험 실행 cost 로 확정해 보고(참고: Kling 3.0 은 8.75크레딧/클립이었음).

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
EP=output/storybook/강의_CH1-2_말리_캐릭터_시트
hfmalli whoami                                   # higgsfield.study 확인

# 0) Wan 테스트 클립을 옆으로 치움 — 안 치우면 C01_1080p.mp4 가 있어서 건너뛰고,
#    hf_web_jobs.json 에 같은 씬 기록이 있으면 재제출도 안 됨
mv "$EP/clips" "$EP/clips_wan_test" && mkdir "$EP/clips"

# 1) 시험 실행 — 크레딧 0
python3 scripts/hf_web_clips.py "$EP" --final --scenes C01 --max-credits 15
#    확인: Wan 3.0 · 720p · 소리 켬, 버튼 cost, balance (cost×19 ≤ 잔액인지)
#    → cost·balance 를 사용자에게 보고하고 승인받은 뒤 2)

# 2) 제출 (19개). --max-credits 는 1)에서 본 cost 이상으로
python3 scripts/hf_web_clips.py "$EP" --final --submit --max-credits 15
```

- 결과: `clips/C01_1080p.mp4` ~ `C19_1080p.mp4` (실제 720p) → Windows 에서 CH1-2·CH1-3 `python compose.py` 재실행, CH2-1 은 C05·C07~C17 을 `clips/` 로 복사 후 재실행 → 프레임 추출로 확인
- 얼굴이 바뀐 클립만 해당 mp4 삭제 후 `--scenes Cxx` 로 재생성(재생성 전 비용 보고)
- C04·C05·C07·C08 은 1-1 K12·K15·K13·K14 로 복사해 1-1 재조립에 재사용 가능
