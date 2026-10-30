# 강의 CH1-1 「5~7세 영상 규칙」 — 조립 (1280x720 30fps)
# 장면 길이 = 장면 wav + 쉼. 클립 장면: Kling 5초 클립 재생 후 마지막 프레임 정지 + 천천히 줌
#   (clips/Kxx_1080p.mp4 가 없으면 시작 그림 images/Kxx.png 로 Ken Burns — 맥에서 클립이 오면 재실행만 하면 교체됨)
# 카드 장면: 흐린 빈 교실(B01) 위에 cards/*.png. 클립+카드 장면은 클립이 끝난 뒤 카드가 뜬다.
# 소리: 나레이션 + BGM(assets/bgm/storybook b1→b2) + Kling 현장음(작게) + 카드 '퐁'(합성)
# 자막: ASS, 바닥 밀착 MarginV=10, 화자별 색(릴리 흰색 / 말리 노랑). 장면 안 시간은 글자수 비례.
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FFDIR = "C:/Users/user/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin"
FFMPEG, FFPROBE = f"{FFDIR}/ffmpeg.exe", f"{FFDIR}/ffprobe.exe"

from storyboard import SCENES

BASE = Path(__file__).parent
ROOT = [_p for _p in BASE.resolve().parents if (_p / "AGENTS.md").is_file()][-1]
IMG, CARDS, AUD, CLIPS = BASE / "images", BASE / "cards", BASE / "audio", BASE / "clips"
TMP = BASE / "_build"
TMP.mkdir(exist_ok=True)
W, H, FPS, SR = 1280, 720, 30, 48000
PAUSE = 0.45
CLIP_LEN = 5.0
NAME = "강의_CH1-1_유아_영상_규칙"

# 장면 → (바탕, 카드). 바탕: "clip" = 콘티의 클립 / "Ixx"·"Mxx" = 그림 / "last:Kxx" = 그 클립 마지막 프레임 / "card" = 카드만
# 카드: 이름 하나 또는 [(시작 비율, 이름), ...] (장면 길이 비율로 교체)
VIS = {
    "S01-01": ("clip", None), "S01-02": ("last:K01", None), "S01-03": ("clip", None),
    "S01-04": ("clip", "title"), "S01-05": ("M01", None), "S01-06": ("I04", None),
    "S02-01": ("clip", None), "S02-02": ("M02", None), "S02-03": ("I06", [(0.55, "eight")]), "S02-04": ("I04", None),
    "S03-01": ("card", "three"), "S03-02": ("M03", None), "S03-03": ("clip", "rule1"), "S03-03b": ("M09", None),
    "S03-04": ("clip", "rule2"), "S03-05": ("M04", None), "S03-06": ("I09", None), "S03-07": ("clip", "rule3"),
    "S03-08": ("M05", None),
    "S04-01": ("clip", None), "S04-02": ("M06", None), "S04-03": ("card", "rule4"), "S04-04": ("M06", None),
    "S04-05": ("card", "rule5"), "S04-06": ("clip", "rule6"), "S04-07": ("last:K09", None), "S04-08": ("card", "rule7"),
    "S04-09": ("card", "rule8"), "S04-10": ("clip", "quiz1"), "S04-11": ("M07", "quiz1_x"),
    "S04-12": ("card", "quiz1_ans"), "S04-13": ("card", "quiz2"), "S04-14": ("M07", "quiz2_x"),
    "S04-15": ("clip", [(0.0, None), (0.55, "quiz2_ans")]), "S04-16": ("M05", None),
    "S05-A1": ("clip", "rulebook"), "S05-A2": ("M06", None), "S05-A3": ("I09", None),
    "S05-01": ("clip", None), "S05-02": ("card", "check1"), "S05-03": ("card", "check1"),
    "S05-04": ("card", "check2"), "S05-05": ("card", "check2"), "S05-06": ("card", [(0.0, "check3"), (0.7, "check3_pass")]),
    "S05-07": ("M08", None),
    "S06-01": ("card", "summary"), "S06-02": ("M01", None), "S06-03": ("clip", None), "S06-04": ("last:K13", None),
    "S06-05": ("clip", None), "S06-06": ("card", "end"),
}
SILENT_LEN = {"S01-01": 4.0, "S06-06": 5.0}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed: {' '.join(map(str, cmd[:6]))}\n{r.stderr[-1500:]}")


def wav_len(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def clip_path(kid):
    p = CLIPS / f"{kid}_1080p.mp4"
    return p if p.exists() and p.stat().st_size > 100000 else None


def last_frame(kid):
    """클립 마지막 프레임(없으면 시작 그림)."""
    cp = clip_path(kid)
    if not cp:
        return IMG / f"{kid}.png"
    out = TMP / f"{kid}_last.png"
    if not out.exists():
        run([FFMPEG, "-y", "-sseof", "-0.1", "-i", str(cp), "-frames:v", "1", "-update", "1", str(out)])
    return out


def kb_filter(dur, zoom=0.04):
    n = max(1, int(round(dur * FPS)))
    return (f"scale={W * 2}:{H * 2},zoompan=z='1+{zoom}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={n}:s={W}x{H}:fps={FPS},trim=end_frame={n}")


def card_bg():
    out = TMP / "card_bg.png"
    if not out.exists():
        run([FFMPEG, "-y", "-i", str(IMG / "B01.png"), "-vf", f"scale={W}:{H},gblur=sigma=6,eq=brightness=0.03",
             str(out)])
    return out


def render_scene(s, dur, out):
    base, card = VIS[s["id"]]
    cards = [(0.0, card)] if isinstance(card, str) or card is None else card
    inputs, chain = [], []
    clip_dur = 0.0
    if base == "clip":
        kid = s["clip"]
        cp = clip_path(kid)
        if cp:
            clip_dur = min(CLIP_LEN, dur)
            # 클립 재생 → 마지막 프레임 정지 줌
            inputs += ["-i", str(cp), "-loop", "1", "-i", str(last_frame(kid))]
            rest = max(dur - clip_dur, 1 / FPS)
            chain.append(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
                         f"trim=duration={clip_dur},setpts=PTS-STARTPTS[a]")
            chain.append(f"[1:v]{kb_filter(rest, 0.03)},setpts=PTS-STARTPTS[b]")
            chain.append("[a][b]concat=n=2:v=1:a=0[bg]")
        else:
            inputs += ["-loop", "1", "-i", str(IMG / f"{kid}.png")]
            chain.append(f"[0:v]{kb_filter(dur)}[bg]")
    elif base == "card":
        inputs += ["-loop", "1", "-i", str(card_bg())]
        chain.append(f"[0:v]scale={W}:{H},trim=duration={dur},fps={FPS}[bg]")
    else:
        src = last_frame(base[5:]) if base.startswith("last:") else IMG / f"{base}.png"
        inputs += ["-loop", "1", "-i", str(src)]
        chain.append(f"[0:v]{kb_filter(dur)}[bg]")
    cur = "bg"
    n_in = len([x for x in inputs if x == "-i"])
    ok_cards = [(f, c) for f, c in cards if c]
    for j, (frac, c) in enumerate(cards):
        if not c:
            continue
        t0 = max(frac * dur, clip_dur if base == "clip" and frac == 0.0 else 0.0)
        nxt = [f for f, _ in cards if f > frac]
        t1 = nxt[0] * dur if nxt else dur + 1
        inputs += ["-loop", "1", "-i", str(CARDS / f"{c}.png")]
        idx = n_in
        n_in += 1
        dim = "" if base == "card" else f"[{cur}]drawbox=c=black@0.25:t=fill:enable='between(t,{t0:.2f},{t1:.2f})'[d{j}];"
        src = f"d{j}" if dim else cur
        chain.append(f"{dim}[{idx}:v]scale={W}:{H},format=rgba,fade=t=in:st={t0:.2f}:d=0.3:alpha=1[c{j}];"
                     f"[{src}][c{j}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'[o{j}]")
        cur = f"o{j}"
    chain.append(f"[{cur}]format=yuv420p,trim=duration={dur}[v]")
    run([FFMPEG, "-y", *inputs, "-filter_complex", ";".join(chain), "-map", "[v]", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-t", f"{dur:.3f}", str(out)])
    return ok_cards and (base != "clip" or clip_dur == 0)


# ---------- 소리 ----------
def decode(path, start=0.0, dur=None):
    cmd = [FFMPEG, "-v", "error", "-ss", f"{start}", "-i", str(path)]
    if dur:
        cmd += ["-t", f"{dur}"]
    cmd += ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    r = subprocess.run(cmd, capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def pop(freq=880, dur=0.12):
    t = np.arange(int(SR * dur)) / SR
    return (0.25 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 30)).astype(np.float32)


def has_audio(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return bool(r.stdout.strip())


# ---------- 자막 ----------
def chunks(line, maxlen=26):
    words, out, cur = line.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > maxlen:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
        if cur.endswith((".", "?", "!")) and len(cur) > 8:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def ass_time(t):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def write_ass(timeline):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: lily,MemomentKkukkukk,40,&H00FFFFFF,&H000000FF,&H00302020,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,40,40,10,1
Style: malli,MemomentKkukkukk,40,&H0080EEFF,&H000000FF,&H00302020,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,40,40,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for s, t0, speech in timeline:
        if not s["speaker"]:
            continue
        parts = chunks(s["line"].replace("·", "ㆍ"))
        total = sum(len(p) for p in parts)
        t = t0
        for p in parts:
            d = speech * len(p) / total
            ev.append(f"Dialogue: 0,{ass_time(t)},{ass_time(t + d)},{s['speaker']},,0,0,0,,{p}")
            t += d
    (BASE / "subs.ass").write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


def main():
    timeline, segs, t = [], [], 0.0
    for s in SCENES:
        wav = AUD / f"{s['id']}.wav"
        speech = wav_len(wav) if s["speaker"] else 0.0
        dur = speech + PAUSE if s["speaker"] else SILENT_LEN[s["id"]]
        if VIS[s["id"]][0] == "clip" and clip_path(s["clip"]):
            dur = max(dur, CLIP_LEN + 0.5)
        timeline.append((s, t, speech))
        seg = TMP / f"{s['id']}.mp4"
        card_pop = render_scene(s, dur, seg)
        segs.append((s, t, dur, card_pop))
        print(f"{s['id']}: {t:7.2f}s +{dur:5.2f}s  {VIS[s['id']][0]}")
        t += dur
    total = t

    lst = TMP / "concat.txt"
    lst.write_text("".join(f"file '{(TMP / (s['id'] + '.mp4')).as_posix()}'\n" for s, *_ in segs), encoding="utf-8")
    video = TMP / "_video.mp4"
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(video)])

    # 소리 믹스
    n = int(total * SR) + SR
    voice, amb, sfx = np.zeros(n, np.float32), np.zeros(n, np.float32), np.zeros(n, np.float32)
    for s, t0, dur, card_pop in segs:
        i0 = int(t0 * SR)
        if s["speaker"]:
            a = decode(AUD / f"{s['id']}.wav")
            voice[i0:i0 + len(a)] += a[: n - i0]
        if VIS[s["id"]][0] == "clip":
            cp = clip_path(s["clip"])
            if cp and has_audio(cp):
                a = decode(cp, 0, CLIP_LEN)
                fade = np.minimum(1, np.linspace(CLIP_LEN, 0, len(a)) / 0.6).astype(np.float32)
                amb[i0:i0 + len(a)] += (a * fade)[: n - i0] * 0.35
        if card_pop or s["id"] in ("S04-11", "S04-14"):
            p = pop(660 if s["id"] in ("S04-11", "S04-14") else 880)
            sfx[i0:i0 + len(p)] += p
    bgm = np.concatenate([decode(ROOT / "assets/bgm/storybook/b1.mp3"), decode(ROOT / "assets/bgm/storybook/b2.mp3")])
    reps = int(np.ceil(n / len(bgm)))
    bgm = np.tile(bgm, reps)[:n] * 0.10
    env = np.ones(n, np.float32)
    fi, fo = int(2 * SR), int(4 * SR)
    env[:fi] = np.linspace(0, 1, fi)
    env[int(total * SR) - fo:int(total * SR)] = np.linspace(1, 0, fo)
    env[int(total * SR):] = 0
    mix = voice + amb + sfx + bgm * env
    peak = np.max(np.abs(mix)) or 1
    mix = (mix / max(peak, 1.0) * 0.95)[: int(total * SR)]
    mixwav = TMP / "_mix.wav"
    with wave.open(str(mixwav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

    write_ass(timeline)
    shutil.copyfile(BASE / "font.ttf", TMP / "font.ttf")
    final = BASE / f"{NAME}_final.mp4"
    os.chdir(BASE)  # subtitles 필터 경로의 드라이브 콜론 회피 — 상대 경로 사용
    run([FFMPEG, "-y", "-i", str(video), "-i", str(mixwav),
         "-vf", "subtitles=subs.ass:fontsdir=_build", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    print(f"done: {final.name} ({total:.1f}s)")


if __name__ == "__main__":
    main()
