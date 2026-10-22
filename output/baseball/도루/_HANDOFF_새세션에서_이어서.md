# ▶ 도루 편 — 새 세션 핸드오프 (프리미엄 · Kling/Seedance)

야구사전 30편 "도루"를 **프리미엄(1080p, 영상 4씬)**으로 만드는 중.
Higgsfield(Kling/Seedance)가 이전 세션에서 끊겨, **새 Claude Code 세션에서 이어서** 완성한다.

## 이미 끝난 것 (이 폴더에 저장됨)
- ✅ 리서치: `01_research.md` / 대본: `02_script_scenes.md`
- ✅ 스크립트 전부 도루+1080p로 세팅 완료: gen_images.py / make_narration.py(Puck) / compose.py(**1920×1080**, VIDEO_SCENES=s01·s04·s06·s09) / gen_clips_veo.py(CLIP_PROMPTS 4개) / gen_thumbnail.py / compose_thumbnail.py
- ✅ **삽화 10장(images/) + Puck 나레이션(audio/, word_timestamps.json) 생성 완료(캐시)** ← 이전 세션에서 미리 만들어 둠. 다시 안 만들어도 됨.

## 새 세션이 할 일 (순서대로)
1. **Higgsfield 잔액 확인** (`balance`). 프리미엄이므로 넉넉한지 체크.
2. **영상 4씬 클립 생성** — s01·s04·s06·s09. start_image = `images/sXX.png`. 프롬프트 = gen_clips_veo.py 의 CLIP_PROMPTS[sid].
   - 엔진: **Kling 3.0 또는 Seedance 2.0**, **1080p**, 가능하면 8초. (사용자 희망: 제일 좋은 것)
   - `models_explore(action:'recommend')` 로 image-to-video 최적 모델 확인 후 결정 권장.
   - 절차(퍼펙트게임/OPS 편 참고): media_upload(files[] presigned)→curl PUT 200→media_confirm→generate_video(model, start_image, 1920×1080, get_cost 프리플라이트)→job_status(sync) 폴링→rawUrl curl 다운로드.
   - **저장 파일명: `clips/s01_1080p.mp4`, `clips/s04_1080p.mp4`, `clips/s06_1080p.mp4`, `clips/s09_1080p.mp4`** (compose.py 가 이 이름을 찾음). 프리셋 추천 뜨면 declined_preset_id 로 literal 강제.
3. **조립**: `python -u compose.py` → `✅도루_final.mp4` (1080p). 자막은 audio/word_timestamps.json 로 실측 생성됨.
4. **썸네일**: `python gen_thumbnail.py && python compose_thumbnail.py` (이전 세션에서 이미 생성했을 수 있음 — thumbnail.png 있으면 생략 가능).
5. **검증**: ffmpeg 로 s01·s04·s06·s09 프레임 추출, 자막·화면 일치 + 클립 모션 확인. 실존 얼굴/숫자/영문 없나 확인.
6. **저장**: Obsidian `50_Outputs/야구사전/` 에 `2026-08-0X_도루_final.mp4`(✅) + 썸네일 + md. TALE 아님(야구 카탈로그 없음).
7. **기록**: context-notes.md 에 제작 완료 로그(프리미엄 사양·엔진·크레딧) 추가.

## 주의
- 실존 선수 얼굴 금지 → 유니폼 색·상황으로. 전광판 숫자·영문 텍스트 금지.
- 영상 배정: s01(2루 슬라이딩 세이프)·s04(스타트·리드·슬라이딩)·s06(포수 송구·태그아웃)·s09(전설 질주).
- 제목(초안): "도루, 안타 없이 베이스를 훔치는 법 | 야구 룰". 썸네일 문구: "안타 없이 / 베이스를 훔친다?!". 다음 편 예고는 미정(마무리 s10에 예고 문구 없음).
- 이 편은 **1회 한정 프리미엄 1080p** — 다음 편부터는 다시 720p 기본 규칙으로.
