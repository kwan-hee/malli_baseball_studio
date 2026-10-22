#!/bin/bash
# 말리동화(교육용) — 맥 미니 최초 1회 설치 스크립트
# 사용법: 터미널에서  bash "이 파일 경로"   (Finder 에서 이 파일을 터미널 창으로 끌어다 놓아도 됨)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
WT="$ROOT/.claude/worktrees/storybook-lazy-ox"
VENV="$HOME/.venvs/malli-donghwa"
cd "$ROOT"
echo "== 프로젝트 위치: $ROOT"

echo "== 1) macOS 숨김 파일(._*) 정리"
dot_clean -m "$ROOT" 2>/dev/null || true

echo "== 2) Git: 외장 디스크 소유권 허용 + worktree 를 맥 경로로 다시 연결"
git config --global --add safe.directory "$ROOT"
git config --global --add safe.directory "$WT"
if [ -d "$WT" ]; then
  git -C "$ROOT" worktree repair "$WT"
fi
git -C "$ROOT" status --short | head -5
echo "   (main 브랜치 OK)"
[ -d "$WT" ] && git -C "$WT" status --short | head -5 && echo "   (storybook-lazy-ox worktree OK)"

echo "== 3) Homebrew 패키지 (ffmpeg, python 3.12)"
if ! command -v brew >/dev/null 2>&1; then
  echo "!! Homebrew 가 없습니다. https://brew.sh 의 설치 명령을 먼저 실행한 뒤 이 스크립트를 다시 실행하세요."
  exit 1
fi
brew install ffmpeg python@3.12
PY="$(brew --prefix)/bin/python3.12"

echo "== 4) 파이썬 가상환경 ($VENV) + 패키지"
mkdir -p "$HOME/.venvs"
[ -d "$VENV" ] || "$PY" -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r "$ROOT/requirements-mac.txt"

echo "== 5) 점검"
ffmpeg -version | head -1
"$VENV/bin/python" -c "import google.genai, whisper, PIL, edge_tts; print('python 패키지 OK')"
[ -f "$ROOT/youtube_longform_agent/.env" ] && echo ".env OK" || echo "!! youtube_longform_agent/.env 가 없습니다 (Gemini 키)"
echo
echo "설치 완료. 작업할 때는 터미널에서:"
echo "  source \"$VENV/bin/activate\""
echo "  cd \"$ROOT/output/storybook/<편명>\""
echo "  python make_narration.py   # 목소리(TTS)"
echo "  python compose.py          # 조립(음악·자막 포함)"
