# 맥 미니에서 말리 동화 작업하기

이 폴더는 Windows `C:\PROJECT` 를 맥 미니용으로 옮긴 사본입니다 (2026-10-21).
완성 영상(mp4)과 씬 이미지(png/jpg)는 용량 때문에 빼고, 코드·문서·목소리(wav)·음악(mp3)·폰트만 옮겼습니다.

## 처음 한 번만: 설치

맥 미니의 **터미널** 앱에서 아래를 실행합니다 (`setup_mac.sh` 파일을 터미널 창으로 끌어다 놓아도 됩니다).

```bash
bash "/Volumes/맥 매니 HDD/말리동화(교육용)/setup_mac.sh"
```

스크립트가 하는 일:
1. 외장 HDD용 Git 설정(safe.directory) + `storybook-lazy-ox` worktree 를 맥 경로로 다시 연결
2. Homebrew 로 ffmpeg, Python 3.12 설치
3. `~/.venvs/malli-donghwa` 에 파이썬 가상환경 + 패키지 설치 (Whisper, Gemini 등)

## 매번: 작업 시작

```bash
source ~/.venvs/malli-donghwa/bin/activate
cd "/Volumes/맥 매니 HDD/말리동화(교육용)/output/storybook/<편명>"
python make_narration.py   # 목소리 (Gemini TTS)
python compose.py          # 조립 (BGM·자막 포함)
```

## Windows 원본과 달라진 점

- 스크립트 안의 `C:\PROJECT\...` 경로 → 프로젝트 루트(`AGENTS.md` 위치)를 자동으로 찾도록 변경
- WinGet ffmpeg 경로 → `ffmpeg` / `ffprobe` (Homebrew)
- `C:\youtube_longform_agent` (gemini_pool, src, `.env`) → 이 폴더의 `youtube_longform_agent/`
- `C:\말리\HF_API_Key*.txt` → `youtube_longform_agent/` 안
- 맑은 고딕(`C:\Windows\Fonts`) → `fonts/`
- `youtube_longform_agent/`(API 키), `fonts/`(MS 폰트)는 `.gitignore` 로 GitHub 업로드 제외
