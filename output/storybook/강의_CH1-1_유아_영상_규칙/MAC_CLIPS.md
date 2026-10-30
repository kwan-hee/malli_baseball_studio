# 맥 미니에서 클립 15개 만들기 (2차 게이트 A안 승인 2026-10-29)

> 2026-10-30 사용자: 클립은 **Wan 3.0 으로 통일**. 테스트 = `--test`(480p·소리 켬), 통과 후 정식 = `--final`(720p·소리 켬). 옵션 없는 실행은 스크립트가 막음.

준비물(이 폴더, Windows에서 이미 생성): `clip_prompts.json`, `images/K01.png` ~ `images/K15.png`

```bash
cd "/Volumes/맥 매니 HDD/말리동화(교육용)"
hfmalli whoami                       # ok:true, higgsfield.study 확인 (아니면 docs/14_HIGGSFIELD_WEB.md '막혔을 때')
# 1) 시험 실행 — 크레딧 0. 버튼 비용·잔액·480p/소리 옵션이 실제로 잡히는지 확인
python3 scripts/hf_web_clips.py output/storybook/강의_CH1-1_유아_영상_규칙 --test
#    결과(cost, balance)를 사용자에게 보고
# 2) 제출 — 시험 결과 보고 후
python3 scripts/hf_web_clips.py output/storybook/강의_CH1-1_유아_영상_규칙 --test --submit
```

- 결과: `clips/K01_1080p.mp4` ~ `clips/K15_1080p.mp4` (이름의 1080p 는 관례, 실제 해상도는 480p)
- `--sound on` 은 hfmalli 가 받는 값인지 시험 실행에서 확인 (안 되면 hfmalli 쪽 옵션 이름 확인)
- 클립 파일을 Windows 쪽 같은 폴더 `clips/` 로 옮긴 뒤 `python compose.py` 만 다시 실행하면 정지 그림 자리가 클립으로 바뀜
- 클립에 사람 목소리·음악이 섞였으면 그 클립만 compose 에서 현장음 0 처리
