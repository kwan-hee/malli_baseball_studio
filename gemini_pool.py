# [버전 백업본] 여러 Gemini API 키(구글 계정 여러 개) 자동 페일오버 풀
# 실행 사본 = C:\youtube_longform_agent\gemini_pool.py (스크립트가 sys.path 로 그 경로를 로드).
# 이 리포 사본은 버전 관리용 백업 — 수정 시 두 곳을 반드시 동기화할 것.
# 429/RESOURCE_EXHAUSTED(할당량 소진) 시 다음 키로 회전, 마지막 성공 키를 상태파일에 기억.
# .env 에 gemini= / gemini2= / gemini3= ... (또는 GEMINI_API_KEY=) 순서로 키를 넣는다.
import json
from pathlib import Path

from google import genai

ENV = Path(r"C:\youtube_longform_agent\.env")
STATE = Path(r"C:\youtube_longform_agent\.gemini_active.json")
TIMEOUT_MS = 300000


def _load_keys():
    # gemini / GEMINI_API_KEY 를 1번, gemini2/gemini3... 을 순서대로. 중복 값 제거, 순서 유지.
    numbered = {}
    first = []
    for raw in ENV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, val = line.split("=", 1)
        name, val = name.strip(), val.strip()
        if not val:
            continue
        if name in ("gemini", "GEMINI_API_KEY"):
            first.append(val)
        elif name.startswith("gemini") and name[6:].isdigit():
            numbered[int(name[6:])] = val  # gemini2, gemini3 ...
    ordered = []
    for v in first:
        if v not in ordered:
            ordered.append(v)
    for n in sorted(numbered):
        if numbered[n] not in ordered:
            ordered.append(numbered[n])
    return ordered


class GeminiPool:
    """활성 키 하나로 client 를 주고, 할당량 소진 시 rotate() 로 다음 키로 넘어간다."""

    def __init__(self):
        self.keys = _load_keys()
        if not self.keys:
            raise SystemExit("gemini_pool: .env 에 gemini= 키가 하나도 없음")
        self.idx = self._load_idx()
        self._exhausted = set()
        self._client = self._make_client()
        print(f"gemini_pool: {len(self.keys)}개 키 로드, 활성=#{self.idx + 1}")

    def _load_idx(self):
        try:
            i = json.loads(STATE.read_text())["idx"]
            return i if 0 <= i < len(self.keys) else 0
        except Exception:
            return 0

    def _save_idx(self):
        try:
            STATE.write_text(json.dumps({"idx": self.idx}))
        except Exception:
            pass

    def _make_client(self):
        return genai.Client(api_key=self.keys[self.idx], http_options={"timeout": TIMEOUT_MS})

    def client(self):
        return self._client

    def rotate(self):
        """현재 키를 소진 처리하고 다음 살아있는 키로 전환. 없으면 RuntimeError."""
        self._exhausted.add(self.idx)
        if len(self._exhausted) >= len(self.keys):
            raise RuntimeError("gemini_pool: 모든 키 소진")
        n = len(self.keys)
        for step in range(1, n + 1):
            cand = (self.idx + step) % n
            if cand not in self._exhausted:
                self.idx = cand
                self._client = self._make_client()
                self._save_idx()
                print(f"gemini_pool: 키 소진 -> #{self.idx + 1} 로 전환")
                return self._client
        raise RuntimeError("gemini_pool: 모든 키 소진")


def is_quota_error(err_str):
    return "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
