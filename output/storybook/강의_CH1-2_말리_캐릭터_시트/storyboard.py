# 강의 CH1-2 「말리 캐릭터 시트 만들기」 — 콘티(STORYBOARD_CH1-2.md) 파서
# 콘티가 대본·화면·클립·소리의 단일 출처 (강의 소개 영상 storyboard.py 방식)
import re
from pathlib import Path

MD = Path(__file__).parent / "STORYBOARD_CH1-2.md"


def _sec(mmss):
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


def load():
    text = MD.read_text(encoding="utf-8")
    scenes = []
    part = None
    for block in re.split(r"\n(?=## PART |### S)", text):
        m = re.match(r"## PART (\d)", block)
        if m:
            part = int(m.group(1))
            continue
        m = re.match(r"### (S[\w-]+) \| (\d\d:\d\d)–(\d\d:\d\d)", block)
        if not m:
            continue

        def field(name):
            f = re.search(rf"- \*\*{name}:\*\* (.*)", block)
            return f.group(1).strip() if f else ""

        speaker_raw = field("화자")
        speaker = "malli" if speaker_raw.startswith("말리") else "lily" if speaker_raw.startswith("릴리") else None
        clip = re.match(r"(C\d\d) \(([A-Z]\d\d)\) (.*)", field("클립"))
        scenes.append({
            "id": m.group(1),
            "part": part,
            "dur_est": _sec(m.group(3)) - _sec(m.group(2)),
            "speaker": speaker,
            "line": field("대사") if speaker else "",
            "screen": field("화면"),
            "clip": clip.group(1) if clip else None,
            "clip_img": clip.group(2) if clip else None,
            "clip_action": clip.group(3) if clip else "",
            "sound": field("소리"),
        })
    return scenes


SCENES = load()

if __name__ == "__main__":
    sp = {}
    for s in SCENES:
        sp[s["speaker"]] = sp.get(s["speaker"], 0) + 1
    print(len(SCENES), "scenes", sp, "clips", sum(1 for s in SCENES if s["clip"]),
          "parts", sorted({s["part"] for s in SCENES}))
