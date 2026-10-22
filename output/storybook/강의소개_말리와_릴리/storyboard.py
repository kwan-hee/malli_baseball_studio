# 강의 소개 영상 — 기준 콘티(수업/MALI_STORYBOARD_01-06.md) 파서
# 콘티가 대본·화면·소리의 단일 출처. 대사는 원문 그대로 읽어 온다 (2026-10-22 사용자 지시: "md 대본 그대로").
import re
from pathlib import Path

ROOT = [_p for _p in Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1]
MD = ROOT / "수업" / "MALI_STORYBOARD_01-06.md"

# 낭독하지 않는 대사 칸 표기
NON_SPEECH = re.compile(r"^(-|\(쉼.*\)|\(영상 클립:.*\))$")


def _sec(mmss):
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


def load():
    text = MD.read_text(encoding="utf-8")
    scenes = []
    stage = None
    for block in re.split(r"\n(?=## STAGE |### S\d\d-\d\d )", text):
        m = re.match(r"## STAGE (\d)", block)
        if m:
            stage = int(m.group(1))
            continue
        m = re.match(r"### (S\d\d-\d\d) \| (\d\d:\d\d)–(\d\d:\d\d)", block)
        if not m:
            continue

        def field(name):
            f = re.search(rf"- \*\*{name}:\*\* (.*)", block)
            return f.group(1).strip() if f else ""

        speaker_raw = field("화자")
        speaker = "malli" if speaker_raw.startswith("말리") else "lily" if speaker_raw.startswith("릴리") else None
        line = field("대사")
        scenes.append({
            "id": m.group(1),
            "stage": stage,
            "t0": _sec(m.group(2)),
            "t1": _sec(m.group(3)),
            "dur": _sec(m.group(3)) - _sec(m.group(2)),
            "speaker": speaker if not NON_SPEECH.match(line) else None,
            "line": line,
            "screen": field("화면 지시"),
            "sound": field("소리"),
            "memo": field("원문 제작 메모"),
        })
    return scenes


SCENES = load()

if __name__ == "__main__":
    sp = {}
    for s in SCENES:
        sp[s["speaker"]] = sp.get(s["speaker"], 0) + 1
    print(len(SCENES), "scenes", sp, "end", SCENES[-1]["t1"])
