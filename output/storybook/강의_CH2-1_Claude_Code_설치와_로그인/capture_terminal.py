# 강의 CH2-1 — Claude Code 첫 실행 화면 기록 (T07~T11 의 원본 글자·색)
# 가상 터미널(pywinpty)에서 claude 를 실행하고 pyte 로 화면을 해석해, 화면이 멈출 때마다 snapshots/NNN.json 저장.
# 키 입력: keys.txt 에 한 줄씩 JSON 문자열을 추가하면 순서대로 보냄 (예: "\r", "\u001b[B", "안녕! 넌 누구야?")
# 기존 로그인을 건드리지 않도록 CLAUDE_CONFIG_DIR 를 임시 폴더로 지정 (2026-10-29 사용자 승인).
import json
import os
import sys
import time
from pathlib import Path

import pyte
from winpty import PtyProcess

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path(__file__).parent
SNAP = BASE / "screens" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)
KEYS = SNAP / "keys.txt"
KEYS.write_text("", encoding="utf-8")
COLS, ROWS = 110, 34

cfg = Path(sys.argv[1])  # 임시 설정 폴더
work = Path(sys.argv[2])  # 작업실 폴더 (malli-studio)
env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg))
env.pop("CLAUDECODE", None)
env.pop("CLAUDE_CODE_ENTRYPOINT", None)
proc = PtyProcess.spawn("claude", cwd=str(work), env=env, dimensions=(ROWS, COLS))
screen = pyte.Screen(COLS, ROWS)
stream = pyte.Stream(screen)


def dump():
    rows = []
    for y in range(ROWS):
        line = screen.buffer[y]
        rows.append([[line[x].data, line[x].fg, line[x].bg, line[x].bold] for x in range(COLS)])
    return {"rows": rows, "cursor": [screen.cursor.x, screen.cursor.y]}


def text():
    return "\n".join(screen.display).rstrip()


import queue
import threading

q = queue.Queue()


def reader():  # read() 가 막히므로 별도 스레드
    while True:
        try:
            q.put(proc.read(65536))
        except EOFError:
            q.put(None)
            return


threading.Thread(target=reader, daemon=True).start()
n, last_text, last_change, done_keys = 0, "", time.time(), 0
while True:
    try:
        data = q.get(timeout=0.1)
        if data is None:
            break
        stream.feed(data)
        last_change = time.time()
        continue
    except queue.Empty:
        pass
    cur = text()
    if cur != last_text and time.time() - last_change > 1.5:
        n += 1
        (SNAP / f"{n:03d}.json").write_text(json.dumps(dump(), ensure_ascii=False), encoding="utf-8")
        (SNAP / f"{n:03d}.txt").write_text(cur, encoding="utf-8")
        print(f"snapshot {n:03d}", flush=True)
        last_text = cur
    keys = [k for k in KEYS.read_text(encoding="utf-8").splitlines() if k.strip()]
    for k in keys[done_keys:]:
        proc.write(json.loads(k))
        time.sleep(0.3)
    done_keys = len(keys)
    time.sleep(0.1)
print("exited", flush=True)
