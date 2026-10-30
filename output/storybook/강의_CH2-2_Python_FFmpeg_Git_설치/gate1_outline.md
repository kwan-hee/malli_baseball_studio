# 강의 CH2-2 「Python · FFmpeg · Git 설치」 — 1차 게이트 개요 (2026-10-30)

- 커리큘럼 위치: CHAPTER 2 「도구 세팅 완벽 가이드」 · 2번 강의 (커리큘럼 html 권장 12:00, "설치 후 터미널에서 버전이 나오는지 확인합니다")
- 등장: 릴리 선생(강사, Leda) + 말리(Kore, 강아지 보조). CH2-1과 같은 교실·연출(이름표, 카드 장면 작은 화면, "잠깐 멈추고 따라 해 보세요").
- CH2-1 엔딩 예고("이 일꾼이 쓸 도구들, 파이썬과 에프에프엠펙, 그리고 깃")와 이어짐.
- 목표: 수강생이 ①세 도구가 각각 무슨 일을 하는지 한 문장으로 알고 ②설치 명령을 붙여 넣고 ③**새 창**에서 `python --version` · `ffmpeg -version` · `git --version` 세 줄이 모두 숫자를 보여 주게 한다.

## 확인한 공식 사실 (2026-10-30 조회)

| 도구 | 공식 출처 | 내용 |
|---|---|---|
| Python | docs.python.org/3/using/windows.html, python.org/downloads/windows | **Windows 권장 = Python install manager(26.4)**. 예전 .exe 설치 파일은 3.14부터 "deprecated", 3.16부터 만들지 않음. 설치 후 `python` · `py` · `pymanager` 명령 사용. 처음 설치 때 PATH 추가 여부를 물어봄. 받는 곳 = python.org/downloads · Microsoft Store · winget(`9NQ7512CXL7T`). 최신: 3.15.2 / 3.14.10 (10-25) |
| FFmpeg | gyan.dev/ffmpeg/builds | `winget install Gyan.FFmpeg` (커리큘럼과 같음). 최신 9.0.2 (09-19). 자막 입히기(libass)는 essentials·full 모두 포함 |
| Git | git-scm.com/install/windows | `winget install --id Git.Git -e --source winget`. 최신 2.56.0 (10-26). Claude Code 도 Windows 에서 Git Bash 를 쓰면 더 많은 일을 할 수 있음(CH2-1 에서 "다음 강의"로 넘김) |
| winget | Windows 10 1809 이상·11 기본 포함(앱 설치 관리자) | 이 PC v1.12.350 |

**이 PC 실측**: Python 3.14.4(install manager 방식) · Git 2.52.0 · FFmpeg 8.1.1(Gyan.FFmpeg full). 강의 파이프라인 전체가 이 조합에서 돌아감.
**★발견 1**: 커리큘럼 html 의 "python.org (설치 때 PATH 추가 체크)"는 예전 설치 파일 기준 → 지금 공식 권장과 다름. 개요는 install manager 기준으로 씀.
**★발견 2**: 이 PC 에서 `py list` 를 쳤더니 "legacy py.exe … 'Python Launcher' 를 지우라"는 경고가 나옴 → 예전에 Python 을 설치했던 수강생이 똑같이 막힐 수 있음. ⑦ 막혔을 때에 넣음.
**★발견 3**: 최신은 3.15 지만 Whisper(CH2-4)·Gemini 패키지는 이 강의에서 **3.14 로 검증**됨 → 수강생도 3.14 로 맞추는 것을 제안(확인 질문 2).

## 강의 흐름 (7파트, 약 12분)

| 파트 | 시간 | 내용 | 화면 |
|---|---|---|---|
| ① 오프닝 | 0:00–1:00 | 말리 "일꾼이 왔는데 또 설치해요?" → 릴리 "일꾼한테 연장을 쥐여 줘야죠". 연장 3개 비유: **Python = 일꾼의 손**(그림·목소리 스크립트 실행) / **FFmpeg = 가위와 풀**(그림+소리 → 영상, 자막·음악) / **Git = 사진첩**(어제 상태로 되돌리기). CH2 지도 2번 칸 | 교실 + 연장 3개 카드 + CH2 지도 |
| ② 심부름꾼 winget | 1:00–2:00 | "가게에 안 가도 이름만 말하면 설치해 주는 심부름꾼". PowerShell(지난 시간에 연 그 창) → `winget --version` → 숫자 확인. 처음 쓸 때 "약관 동의(Y)" 질문이 나온다는 예고 | PowerShell 화면 |
| ③ Python | 2:00–5:00 | python.org/downloads → **Python install manager** 받기 → 설치 → 처음 실행 때 질문(PATH 추가 = Y) → `py install 3.14` → **창 닫고 새로** → `python --version` → `Python 3.14.x`. 말리 실수: `python` 쳤더니 Microsoft Store 가 열림 → "install manager 를 먼저 설치해야 해요" | 공식 페이지 캡처 → 설치 창 → 터미널 순서 |
| ④ FFmpeg | 5:00–7:30 | 말리 "에프에프… 엠펙? 이름이 너무 어려워요!" → 릴리 "영상 만드는 가위와 풀". `winget install Gyan.FFmpeg` → 약관 Y → 내려받는 막대 → "설치 성공" → 새 창 → `ffmpeg -version` → 첫 줄 `ffmpeg version …` 만 보면 됨(아래 긴 글은 무시) | 터미널 화면 + "첫 줄만 보세요" 강조 |
| ⑤ Git | 7:30–9:30 | 말리 "사진첩은 왜 필요해요?" → 릴리 "Claude 가 실수해도 어제로 돌아갈 수 있게". `winget install --id Git.Git -e --source winget` → 설치 창이 잠깐 뜨면 그대로 둠 → 새 창 → `git --version`. Claude Code 도 Git 이 있으면 더 잘 일한다는 한 마디 | 터미널 화면 + 사진첩 비유 그림 |
| ⑥ 세 줄 점검 | 9:30–10:30 | 새 창 하나에서 세 줄을 차례로 → 숫자 3개에 도장 쾅. **티키타카: 심사위원 말리 O/X** — "숫자가 나왔다 O / 빨간 글자 X" 화면 3장을 말리가 판정 | 점검 카드 + O/X 카드 |
| ⑦ 막혔을 때 + 정리 | 10:30–12:00 | ①"인식할 수 없습니다" → 새 창(지난 시간과 같은 답) ②`python` 이 Store 를 엶 → install manager 설치 확인 ③"Python Launcher 를 지우라"는 경고 → 설정 > 앱에서 예전 Python Launcher 제거 ④winget 이 없음 → Microsoft Store 에서 "앱 설치 관리자" 업데이트. Mac 한 장 요약. 다음 강의 예고(Gemini API 키) + 구독·좋아요 | FAQ 카드 4장 → Mac 카드 → 손 흔들기 |

## 화면 이미지 제작 방법 (CH2-1 과 같은 원칙)

| 화면 | 방법 |
|---|---|
| python.org · git-scm.com · gyan.dev 페이지 | 크롬 실제 캡처 |
| 버전 확인 화면(`python --version` 등) | CH2-1 처럼 가상 터미널로 **이 PC 실제 출력**을 기록해 재현 |
| 설치 진행 화면(winget 내려받기 막대, install manager 첫 질문) | 이 PC 엔 이미 설치돼 있어 새 설치 화면이 안 나옴 → **winget·pymanager 실제 출력 형식 그대로 재현**(확인 질문 4) |
| 릴리·말리 장면, 연장 3개 비유 | Gemini 이미지(기존 시트·참조 첨부) |

- ⚠ 이 PC 의 FFmpeg 는 **업그레이드·재설치하지 않음**: compose.py 가 `ffmpeg-8.1.1-full_build` 경로를 직접 쓰므로 버전이 바뀌면 모든 편의 조립이 멈춤.

## 비용 예상 (2차 게이트에서 확정)

- 화면 카드 약 20~24장: 캡처·재현이라 **무료**
- 새 캐릭터 그림 약 4~5장(Gemini): 연장 3개 들고 있는 릴리, 이름이 어려워 혀 꼬인 말리, 사진첩 든 말리, 심사위원 말리(O/X 팻말)
- 클립: 1-2·2-1 재사용 우선 + 새 그림 몫만 Wan 테스트(맥 hfmalli 준비 후)
- TTS·카드·조립은 무료/승인 불필요

## 확인이 필요한 점

1. **설치 방법**: Python 은 python.org 의 install manager, FFmpeg·Git 은 winget 명령 한 줄(제안) / 셋 다 winget / 셋 다 웹사이트 설치 파일
2. **Python 버전**: 강의에서 검증한 **3.14 로 맞추기**(`py install 3.14`, 제안) / 최신 3.15 그대로
3. **Claude Code 에게 설치 시키기 장면**을 넣을지: 넣지 않음, 직접 붙여 넣기만(제안 — 처음엔 손으로 해 봐야 막혔을 때 알 수 있음) / ⑥ 뒤에 "다음부턴 Claude 에게 시켜도 돼요" 30초 맛보기
4. 설치 진행 화면: 실제 출력 형식 재현(제안) / 이 PC 에서 Git·Python 만 지웠다 다시 설치해 실제 캡처(FFmpeg 는 제외 — 위 ⚠)
5. Git 첫 설정(`git config user.name` 등)은 이번에 하지 않고 CH2-5 폴더 만들기에서(제안) / 이번 강의 끝에 같이
