# 02. 영상 정책

## 공통 규격

- 해상도: 1920x1080 (롱폼), 1080x1920 (쇼츠)
- 프레임레이트: 30fps
- 편집 도구: CapCut (기본) + ffmpeg (자동화·후처리)

## 채널별 포맷

| 항목 | 야구사전 | 말리 동화 |
|------|---------|----------|
| 길이 | 3~5분 롱폼 | 3~4분 |
| 구성 | 훅 → 용어 유래 → KBO 사례 → 마무리 | 도입 → 이야기 전개 → 교훈 마무리 |
| 화면 | 이미지 + Ken Burns 줌 + 자막 | 지브리풍 일러스트 + Ken Burns + 자막 |
| 나레이션 | 해설자 보이스 (InJoonNeural) | 말리 목소리 (SunHiNeural) |

## CapCut Ken Burns 키프레임

CapCut 프로젝트 JSON의 `common_keyframes` 에 `KFTypeScale` property_type + `keyframe_list` 사용.
상세 포맷은 메모리 문서 참조 (project_capcut_ken_burns.md). ffmpeg 대안은 docs/08_FFMPEG.md.

## 말리 동화 — 기존 검증 파이프라인 (C:\youtube_longform_agent)

이미 완성 에피소드 다수 산출한 방식. 새 제작도 이 방식을 기본으로 함.

1. 주제 한 줄 → StoryWriter(Gemini)가 scenes.json 생성 (씬 ~10개, narration 한국어 + image_prompt 영어)
2. 이미지: `gemini-3-pro-image-preview` + 캐릭터 시트 multimodal 참조 (prompts/malli_character.txt 조립 규칙)
3. 모션: image-to-video — **Google Flow(Veo 3.1) 우선, Flow 크레딧 부족·장애 시 Higgsfield(Seedance)** (docs/01_COST_POLICY.md). 8초·16:9, 오디오 제거하고 영상만 사용. 크레딧 절약: 평상 씬 Veo 3.1 Fast, 절정 씬만 Veo 3.1
   - 저비용 대안: 이미지 + Ken Burns 줌 (ffmpeg zoompan / CapCut)
4. TTS·자막·BGM: docs/07_AUDIO.md
5. FFmpeg 합성: 씬 페이드 0.5초, 마지막 2초 영상+오디오 동시 페이드아웃
6. 호출 절감: 같은 장소·같은 등장인물 씬은 `image_ref` 로 이전 씬 이미지 재사용 (40~50%), 카메라 워크만 변경

## 제작 순서 (표준 파이프라인)

1. 대본 확정 (채널별 docs 참조)
2. 이미지 준비 → images/ (docs/06_IMAGE.md)
3. 나레이션 생성 → output/ (docs/07_AUDIO.md)
4. CapCut 조립 또는 ffmpeg 자동 조립 (docs/08_FFMPEG.md)
5. 썸네일 (docs/05_THUMBNAIL.md)
6. 최종본 → Obsidian 50_Outputs/
