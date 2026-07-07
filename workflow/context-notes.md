# 컨텍스트 노트 (결정 기록)

작업 중 결정사항과 이유를 시간순으로 기록. 다음 세션이 이 파일부터 읽음.

## 2026-07-07 — 프로젝트 초기 구축

- **두 채널(야구사전, 말리 동화)을 한 PROJECT로 통합.** 이유: 영상 파이프라인(이미지→TTS→조립→썸네일)을 공유하므로 공통 문서 중복 방지.
- **AGENTS.md는 라우팅 전용으로 얇게 유지.** 상세 규칙은 docs/. 이유: 매 세션 전체 로드 방지, 토큰 절약.
- **03_MALLI는 캐릭터 정의만, 채널 규칙은 04/09에 분리.** 이유: 캐릭터 문서 비대화 방지.
- **09_STORYBOOK.md 추가** (원안 8개에 없던 문서). 이유: 야구사전만 채널 문서(04)가 있고 동화 채널 규칙 문서가 없었음.
- **산출물 이원화 규칙 확정:** 중간산출물 output/, 최종본 Obsidian 50_Outputs/ (야구사전 → 50_Outputs/야구사전, 동화 → 50_Outputs/말리동화).
- 미확정 값은 각 문서에 (TODO)로 표기. 목록은 checklist.md 참조.

## 2026-07-07 — 말리 캐릭터·동화 포맷 확정 (사용자 캐릭터 시트 제공)

- **말리 = 크림색 말티푸 새끼 강아지, 암컷.** 캐릭터 시트 영문 표기는 LILY(リリー) — 목걸이 태그 텍스트는 "LILY" 그대로 유지하기로 함.
- **외형 고정:** 곱슬 크림색 털, 큰 검은 눈, 분홍 목걸이 + 빨간 리본, 뼈다귀 모양 LILY 태그.
- **성격·말투:** 밝고 맑고 활발 / 여성스럽고 귀여운 말투.
- **동화 포맷:** 타깃 5~7세, 편당 3~4분 (원안 5~7분에서 단축 → 인사 15초, 편당 8~10컷으로 조정).
- **그림체:** 지브리풍 일본 애니메이션 + 수채화 질감. 기준 프롬프트 prompts/malli_character.txt 작성 완료 — 모든 말리 이미지는 여기서 파생.
- **예산:** 제한 없음. 단 무료 우선·재생성 금지 원칙은 낭비 방지 위해 유지.
- 남은 TODO: TTS 보이스 선정, 캐릭터 시트 원본을 images/style_ref/ 에 저장, 썸네일 고정 색.

## 2026-07-07 — 영문 이름 LILY → MALLI 변경 (사용자 지시)

- 태그 텍스트 포함 전부 MALLI 로 통일. docs/03_MALLI.md, prompts/malli_character.txt 수정 완료.
- 주의: 사용자 보유 캐릭터 시트 원본에는 LILY 표기가 남아 있음 — 그림체 레퍼런스로만 사용하고, 태그 텍스트는 생성 시 MALLI 로. 가능하면 MALLI 표기 새 캐릭터 시트 재생성 권장.

## 2026-07-07 — 기존 파이프라인(C:\youtube_longform_agent) 분석 후 검증값 이식

- 기존 말리 동화는 CapCut/Ken Burns 방식이 아니었음. **주제 한 줄 → StoryWriter(Gemini) → scenes.json(~10씬) → Gemini 이미지(gemini-3-pro-image-preview, 캐릭터 시트 multimodal 참조) → Seedance 1.5 image-to-video(720p·8초) → Edge TTS → Whisper 자막 → FFmpeg 합성** 파이프라인. 완성 에피소드 다수 (mali_forest_secret, 달님이 하루 동안 사라진 이유 등, 시즌2 폴더 존재).
- 이식한 검증값: 캐릭터 프롬프트·스타일 서픽스(지브리 anime style) → prompts/malli_character.txt / TTS(Edge SunHiNeural -5%, 대안 Gemini Kore 3청크+Whisper 분할) → 07_AUDIO / BGM(Whisper of the Wind @15%)·자막 폰트(MemomentKkukkukk) → 07_AUDIO / 기존 파이프라인 요약 → 02_VIDEO_POLICY.
- 캐릭터 시트 원본 복사: youtube_longform_agent/assets/character/malli_reference.png → PROJECT/images/style_ref/.
- 미해결: 기존 방식은 720p 출력(Seedance 한계), 새 공통 규격은 1080p — Seedance 계속 쓰면 720p 유지 또는 업스케일 필요. Ken Burns 방식 선택 시 1080p 가능.
- 기존 프롬프트의 이름 표기는 "Mali" — 새 기준은 "Malli"/태그 MALLI 로 통일함.

## 2026-07-07 — 야구사전 기존 파이프라인(C:\야구사전) 분석 후 검증값 이식

- 완성 에피소드 5편: 보크, 인필드플라이, 징크스, 낫아웃, 지명타자 (output/{날짜}_{용어}/).
- **중요 발견: 야구사전의 "말리"는 강아지 캐릭터가 아니라 해설자 페르소나** ("야구 20년 본 동네 형/누나", 존댓말, InJoonNeural 남성 보이스). 동화 채널 강아지 말리(SunHiNeural)와 이름만 같고 성격 다름 → 03_MALLI에 주의 문구, 04_BASEBALL에 페르소나 정의 이식.
- 영상 방식: 씬 점수판(emotion/motion/importance)으로 엔진 결정 — motion 7~10 & importance 85+ 만 Seedance, 나머지 정지 삽화(nano_banana_2) + Ken Burns 홀짝 교대 줌. 1280x720 30fps.
- 자막: 글자수 비례 SRT, Malgun Gothic 18, MarginV=10 바닥 밀착 (2026-07-05 상시 지시).
- BGM: The Diamond.mp3 @15% 루프. → 04_BASEBALL, 07_AUDIO, 02_VIDEO_POLICY 반영 완료.
- 텍스트 단계(리서치+대본+SEO)는 기존 /야구사전 스킬이 이미 처리 — 새 PROJECT는 스킬 산출물 이후의 영상 제작 단계를 담당.

## 2026-07-07 — 영상 생성 플랫폼 정책 수신 (사용자 작성 정책 원문 반영)

- 보유 서비스: Google AI Pro(Flow), Higgsfield Ultra, Nano Banana, Hedra, FFmpeg.
- 채널별 영상 플랫폼: 동화 = Google Flow(Flow Credits 우선 소진) → Higgsfield / 야구사전 = Higgsfield Ultra → Google Flow.
- (2026-07-07 정정) 사용자 정책 원문의 "Google Flow (Seedance)" 표기는 오기 — **Flow의 모델은 Veo 3.1** (Seedance는 Flow에 없음, Higgsfield 쪽 모델). 확정: 동화 기본 Google Flow/Veo 3.1 (평상 씬 Fast, 절정 씬 고품질), 폴백 Higgsfield/Seedance.
- 이미지 전 작업 = Nano Banana 기본. 음성 = **Hedra 기본** (기존 검증 Edge TTS는 무료 대안으로 강등). 최종 편집 = FFmpeg.
- 예외 허용: Flow 사용량 부족, Higgsfield 장애, 특정 모델 필요, 사용자 직접 지정.
- 목표: 사용자는 주제만 입력, 플랫폼 선택은 Claude 자동 (적합성·비용·안정성).
- 반영 파일: 01_COST_POLICY(정책 본문), 02_VIDEO_POLICY(동화 Flow 우선), 04_BASEBALL(Higgsfield 우선), 06_IMAGE(Nano Banana), 07_AUDIO(Hedra 기본).
- 미해결 TODO: Hedra 채널별 보이스 선정 (동화용 귀여운 여성 톤 / 야구용 해설 톤).

## 2026-07-07 — 음성 정책 수정 (사용자 확정)

- 롱폼은 **두 채널 모두 Edge TTS** (동화 SunHi / 야구 InJoon — 기존 검증값 그대로).
- **Hedra는 되도록 야구 쇼츠 전용.** 쇼츠용 보이스 선정만 남음.
- 반영: 01_COST_POLICY, 04_BASEBALL, 07_AUDIO, checklist.

## 2026-07-07 — 첫 동화 에피소드 "말리와 느림보 달팽이" 파이프라인 테스트 (게이트 검증 완료)

- 승인 게이트 2개 모두 정상 작동: ①개요 승인 → ②씬 배정표 승인 → 생성.
- 이미지 10장: Gemini(gemini-3-pro-image-preview) + 캐릭터 시트 참조, gen_images.py 로 생성. 캐릭터 일관성 우수 (MALLI 태그 정확).
- 영상 2편: Google Flow 웹을 Chrome 자동화로 조작. s07=Veo 3.1 Fast(20cr), s08=Veo 3.1 Quality(100cr), 각 1080p 업스케일 다운로드 → clips/.
- **Flow 자동화 제약 발견: 로컬 파일 업로드만 자동화 불가** (확장 보안 제한) — 사용자가 수동 업로드 필요. 이후 단계(프레임 선택→모델 설정→프롬프트→생성→1080p 다운로드)는 전부 자동화 성공.
- Flow 다운로드는 그리드 타일 ⋮ 메뉴에서만 동작 (에디터 상단 아이콘은 무반응). 1080p 업스케일 무료 제공.
- 남은 제작 단계: TTS 나레이션 → Ken Burns 클립 8개 → ffmpeg 조립 → 자막 → BGM → 썸네일.

## 2026-07-07 — 첫 동화 에피소드 완성 (말리와_느림보_달팽이_final.mp4)

- 1920x1080 30fps, 2분 19초, 344MB (ultrafast CRF20 — 업로드용은 재인코딩으로 ~축소 가능).
- 파이프라인 전 구간 검증: 이미지(Gemini) → 영상(Flow/Veo 3.1) → TTS(edge SunHi -5%) → Ken Burns+Veo 혼합 조립 → 자막(MemomentKkukkukk, 글자수 비례 SRT) → BGM(Whisper of the Wind 15%, 끝 2초 페이드).
- 스크립트 3종 재사용 가능: gen_images.py / make_narration.py / compose.py (다음 에피소드 템플릿).
- 교훈: 대본 1,000자 → 실측 2:19. 3분 이상 원하면 대본 1,300자+ 필요. cp949 콘솔 print에 한자 경로 넣지 말 것 (수정 완료).
- 남은 것: 썸네일, 최종본 Obsidian 50_Outputs/말리동화 이동 여부 결정.

## 2026-07-07 — 프로젝트 폴더 이동 (사용자 수행)

- 위치 변경: C:\Users\user\OneDrive\文档\Capcut\PROJECT → **C:\PROJECT** (접근성 때문. 사용자가 직접 이동, 64파일 무결성 확인 완료).
- 주의: OneDrive 밖이라 클라우드 백업 안 됨 — 완성본은 Obsidian 저장 규칙으로 커버.
- 스크립트(gen_images.py 등)는 자기 위치 기준 경로라 수정 불필요. compose.py의 FFMPEG 절대경로도 영향 없음.

## 2026-07-07 — 나레이션 전면 개정 (사용자 피드백: "기계 같다")

- **원인**: v1은 Edge TTS 사용 (기존 config 기본값을 검증값으로 오판). 예전 좋았던 목소리는 Gemini TTS(Kore)였음.
- **v2 개정 (두 채널 공통 규칙화)**:
  1. 롱폼 TTS 기본 = Gemini TTS + 성우 연기 지시문 (동화 Kore / 야구 남성 Charon 후보). Edge는 쿼터 폴백으로 강등.
  2. 행동 지문("폴짝폴짝 뛰어갔어요")은 나레이션에서 제거 — 행동은 화면, 나레이션은 대사+감정.
- 동화 1편 v2 재제작 완료: 말리와_느림보_달팽이_final_v2.mp4 (1:53, 298MB). make_narration_v2.py 가 표준 템플릿.
- 야구사전 기존 5편도 전부 Edge InJoon(기계식)이었음 — 다음 편부터 Gemini 적용, 남성 보이스는 첫 편에서 Charon/Puck/Fenrir 샘플 비교 후 확정.
- v2가 1:53으로 짧아짐 (지문 삭제 영향) — 다음 편은 이야기 자체를 더 길게 (대사·에피소드 추가로 1,300자+).

## 2026-07-07 — 야구사전 6편 "사이클링 히트" 제작 완료 (신규 파이프라인 첫 야구 에피소드)

- 게이트 2개 통과 → 최종본: output/baseball/사이클링_히트/사이클링_히트_final.mp4 (2:31, 1080p).
- 구성: 삽화 8장(Nano Banana, 야구 카툰 톤, 실존 얼굴 금지) + **Seedance 2.0** 클립 2편(s01 훅, s07 김도영 홈런 — 1080p, 기존 1.5/720p에서 업그레이드) + Puck 나레이션 + Malgun Gothic 바닥 자막 + The Diamond BGM.
- 야구사전 보이스 확정: **Gemini TTS Puck** (샘플 3종 중 사용자 선택).
- Higgsfield MCP 503 장애 발생 → 웹(higgsfield.ai/assets)에서 video src URL 추출해 우회 다운로드 (javascript_tool로 <video> src 읽기 — 재사용 가능한 우회법).
- 남은 것: SEO 패키지 + Obsidian 50_Outputs/야구사전 저장, 썸네일.

## 2026-07-07 — 엔딩 CTA 상시 규칙 (사용자 확정)

- 두 채널 모두 영상 마무리에 **구독·좋아요 요청 필수**. 동화 = 말리 말투로 귀엽게, 야구 = 해설자 말투로 한 문장. 09_STORYBOOK / 04_BASEBALL 마무리 단계에 반영 완료.

## 2026-07-07 — 야구사전 7편 "자책점 vs 비자책점" 텍스트 단계 완료 (2차 게이트 대기)

- 1차 게이트(리서치) 사용자 승인 → 대본 10씬(약 1,250자) + 점수표 + 배정표 작성.
- 산출물: output/baseball/자책점_vs_비자책점/01_research.md, 02_script_scenes.md + Obsidian 50_Outputs/야구사전/2026-07-07_자책점_vs_비자책점.md (리서치·대본·SEO 단일 파일).
- 영상 배정 2씬: s01(홈런+전광판 훅), s07(실책 후 홈런 재구성 리플레이) — Seedance. 나머지 8씬 이미지+Ken Burns.
- **KBO 국내 기록 정정 사례 검색 실패** → 류현진 2019 MLB 사례(ERA 1.66→1.53)로 대체. 날조 금지 원칙 적용. 국내 사례 발견 시 대본 s06 교체 여지.
- s06 류현진 씬: 실존 얼굴 금지 → 파란 유니폼 투수 뒷모습 + 기록지로 표현하기로.

## 2026-07-07 — 게이트 자동 승인 전환 (사용자 지시)

- 사용자: "더이상 나에게 묻지 말고 무조건 승인할께" — 이후 1·2차 게이트는 보고만 하고 대기 없이 진행.
- 게이트 산출물(리서치·배정표)은 계속 만들어 기록하되, 승인 대기 단계 생략.

## 2026-07-07 — 야구사전 7편 "자책점 vs 비자책점" 제작 완료

- 최종본: output/baseball/자책점_vs_비자책점/자책점_vs_비자책점_final.mp4 (3:00, 388MB, 1080p) + thumbnail.png. Obsidian 50_Outputs/야구사전 에 복사 완료.
- 구성: 삽화 10장 + Seedance 2.0 클립 2편(s01 훅, s07 재구성 리플레이 — 1080p) + Puck 나레이션 + 바닥 자막 + The Diamond BGM. 프레임 4장 추출 검증 통과.
- **Gemini 이미지 504 장애 대응 (재사용)**: gemini-3-pro-image-preview 가 504 연발 → 타임아웃 300초 + 폴백 모델 추가. 폴백 정확한 GA 모델명 = `gemini-2.5-flash-image` (`-preview` 붙이면 404).
- Seedance 주의: resolution 파라미터 안 주면 **720p 기본** — 1080p는 `resolution:"1080p", mode:"std"` 명시 필수. 초기 2건 720p로 나가 크레딧 낭비 (재요청 2건).
- generate_audio:false 로 요청해야 함 (나레이션 별도라 네이티브 오디오 불필요).
- 첫 썸네일 파이프라인 확립: Gemini 배경(좌측 1/3 어둡게 비우는 프롬프트) → ffmpeg drawtext(malgunbd.ttf, 2줄) → output/{편명}/thumbnail.png.
- TTS 실측 3:00 (대본 예상 4:10보다 짧음) — Puck 발화 속도 분당 약 420자. 다음 편 분량 산정 시 참고.

## 2026-07-07 — 동화 라이브러리 구축 (docs/10_TALE_LIBRARY.md)

- 사용자 요청 "세계 동화를 말리에게 학습" → 실체화 형태 확인: **퍼블릭 도메인 동화 카탈로그 문서** (파인튜닝 아님), 규모는 1000편 전체가 아닌 **선별 약 150편** (둘 다 사용자 선택).
- 구성: 이솝·그림·안데르센·페로·한국 전래·아시아·세계 민담 7개 섹션. 편당 줄거리 한 줄 + 교훈 + 말리 각색 적합도(상/중/하) + 순화 포인트.
- 적합도 기준 = 09_STORYBOOK 금지 규칙(폭력·공포·죽음 직접 묘사·종교) 대응. 상 ≈ 80편(즉시 제작 풀) / 중 ≈ 55편(순화 필요) / 하 ≈ 15편(제외 — 실수 방지용으로 목록에 유지).
- 저작권 원칙: 퍼블릭 도메인만 등재. 현대 창작 동화(저작권 존속)는 제외.
- 운영 규칙: 에피소드 제작 완료 시 해당 항목 ✅ 표기(중복 방지), 소재 선정은 "상" 우선. AGENTS.md 라우팅 표에 행 추가 완료.

## 2026-07-07 — 동화 2편 "말리와 커다란 순무" 제작 완료 (라이브러리 기반 첫 편)

- 소재: 10_TALE_LIBRARY "상" 커다란 순무 (러시아 민담). 게이트 2개 자동 승인 모드로 보고 후 즉시 진행.
- 최종본: output/storybook/말리와_커다란_순무/말리와_커다란_순무_final.mp4 (2:50, 1080p, 411MB) + thumbnail.png. Obsidian 50_Outputs/말리동화/ 저장 완료 (mp4+썸네일+md).
- **단일 호출 TTS + Whisper 분할 첫 구현** (make_narration.py — 이후 에피소드 템플릿). 문자 누적 방식 씬 경계 탐색, BOUNDARY_MARGIN 0.15s. 주의: whisper가 ffmpeg를 PATH에서 찾음 — WinGet 경로를 os.environ에 추가 필요.
- 분량 학습: Kore 발화 실측 분당 약 690자 (Puck 420자와 다름!). 1,400자→2:01로 짧아서 1,750자+"천천히" 지시로 재생성 → 2:42. **3분 이상 원하면 Kore 기준 대본 2,000자+ 필요.**
- 이미지 QC에서 3장 재생성: s02(프롬프트에 없는 말리 등장 — "NO dog in this scene" 명시로 해결), s07(그림체 셀 톤 이탈 — "watercolor texture, painterly brush strokes" 강조로 해결), s10("animal friends" 모호 표현 → 여우·새 등 임의 동물 생성. **등장 동물은 항상 명시적으로 나열할 것**).
- Flow 자동화: 업로드만 수동(기존 확인), 이후 전 단계 자동 성공. **생성 첫 시도 400 실패 시 재시도 버튼은 같은 요청 반복이라 무익 — 페이지 새로고침 후 새로 구성하면 성공** (reCAPTCHA 503 동반 일시 장애). 1080p 다운로드 파일명은 Flow_1080p_*.mp4 또는 클립 제목 기반 — Downloads 폴더에서 최신 mp4 확인.
- 유료 사용 기록: Flow 크레딧 120 (Veo 3.1 Fast 20 + Quality 100), Gemini 이미지 14회(본편 10+재생성 3+썸네일 1), Gemini TTS 2회(1차 2:01 폐기, 2차 2:42 채택).
- compose.py 백그라운드 실행 시 출력 버퍼링으로 멈춘 듯 보임 — `python -u` 로 실행하면 진행 로그 실시간 확인 가능.

## 2026-07-08 — TTS 씬 경계 무음 개선 규칙 (다음 편부터 적용)

- 증상: 순무 편 최종본에서 목소리가 씬 넘어갈 때마다 뚝뚝 끊김.
- 원인: compose.py 가 씬별로 오디오에 `adelay=AUDIO_DELAY_MS(400)` + `apad`(sdur=adur+PAD(0.8))를 걸어 앞 0.4s·뒤 0.4s 무음을 붙임 → concat 후 씬 경계마다 0.8s 죽은 소리. 원래 단일 호출로 연속이던 나레이션을 잘라 다시 패딩해 붙이는 구조라 발생.
- **다음 편부터: compose.py 의 `PAD 0.8→0.15`, `AUDIO_DELAY_MS 400→0`** 로 시작할 것 (경계 무음 0.8→0.15s). 사용자 지시 — 순무 편 산출물은 그대로 두고 이후 에피소드에만 적용.
- 그래도 끊기면 근본 해결: 최종 단계에서 narration_full.wav 통짜를 입히고 영상 길이만 씬별 정렬(현재 씬별 무음 패딩 폐기).
