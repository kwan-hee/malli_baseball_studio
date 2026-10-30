# 맥(Orca) 붙여 넣기용 — 클립 전체 Wan 3.0 전환 (2026-10-30)

아래 블록을 그대로 Orca 에이전트에게 붙여 넣는다.

```
리포: /Volumes/맥 매니 HDD/말리동화(교육용)
먼저 읽을 것: CLAUDE.md, docs/14_HIGGSFIELD_WEB.md, workflow/context-notes.md 마지막 부분.
크레딧이 드는 제출(--submit)은 반드시 시험 실행 cost·balance 를 나에게 보고하고 승인받은 뒤에만 한다.

0) hfmalli 정비 (~/.local/bin/hfmalli, 리포 밖)
   - 기대 계정을 yookwanhee6 → higgsfield.study@gmail.com 으로
   - Chrome 포트를 9341 → 9338 (런웨이 Chrome 공유) 으로
   - 작업기록 경로를 "/Volumes/맥 매니 HDD/Higgsfield 계정별/higgsfield.study/malli/작업기록.md" 로
   - --model wan-3.0 을 받아 화면에서 Wan 3.0 을 고를 수 있는지 확인 (없으면 추가)
   - 고친 뒤 `hfmalli whoami` → ok:true, higgsfield.study 인지 확인
   - 9338 창에서 절대 로그아웃하지 않는다 (런웨이 작업도 같이 로그아웃됨). 런웨이 탭은 건드리지 않는다.

1) 시험 실행 (크레딧 0) — 두 편
   EP1=output/storybook/강의_CH1-2_말리_캐릭터_시트
   EP2=output/storybook/강의_CH2-1_Claude_Code_설치와_로그인
   python3 scripts/hf_web_clips.py "$EP1" --test --scenes C01
   python3 scripts/hf_web_clips.py "$EP2" --test --scenes C20
   → 화면에 Wan 3.0 · 480p · 소리 켬이 잡혔는지, 버튼 cost, balance 를 나에게 보고하고 멈춘다.
     (필요 크레딧 = cost × 23개: CH1-2 19개 + CH2-1 4개)

2) 승인을 받은 뒤에만 제출
   python3 scripts/hf_web_clips.py "$EP1" --test --submit
   python3 scripts/hf_web_clips.py "$EP2" --test --scenes C20,C21,C22,C23 --submit
   ⚠ EP2 는 --scenes 를 절대 빼지 않는다 (빼면 CH1-2 와 같은 12개를 또 만들어 크레딧이 두 번 든다).
   끝나면 받은 클립 목록·실패 씬·쓴 크레딧을 보고한다.

3) 여기서 멈춘다. 정식(--final, 720p)은 내가 테스트본을 확인한 뒤 따로 지시한다.
   순서는 각 편 MAC_CLIPS.md 의 "2) 정식 버전" 항목을 따른다.
```

## Windows 쪽 후속 (클립이 Z: 에 들어온 뒤)

1. CH2-1 `clips/` 에 CH1-2 `clips/` 의 C05·C07~C17 복사
2. CH1-2 · CH1-3 · CH2-1 `python compose.py` 재실행 (클립 장면 `_build/` 캐시 삭제 후)
3. 클립 장면 프레임 추출로 확인 → 사용자에게 테스트본 보고 → 정식 여부 질문
