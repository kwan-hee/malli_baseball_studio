# 강의 CH2-2 「Python · FFmpeg · Git 설치」 — 조립 (1280x720 30fps). 템플릿 = 강의 CH2-1 compose.py
# CH2-2: 클립은 이 편 clips/ → CH2-1 clips/ → CH1-2 clips/ 순서로 찾음 (재사용 C05~C17·C22·C23)
# CH2-1 추가: 화면 카드(실제 캡처·터미널 재현)도 카드 방식 그대로 + HOLD = 따라 하기 화면에서 대사 뒤 3초 더 머묾
# 2026-10-29 사용자 피드백("1-1은 말은 잘하는데 동작이 별로 없다", "두 목소리 구분이 어렵다") 반영:
#   - 클립 장면: make_clip_inputs.CLIPS 의 재생 방식 — once = 한 번 재생 후 마지막 프레임 줌 /
#     loop = 정방향+역방향 반복으로 장면 끝까지 움직임 (1-1 은 5초 뒤 전부 정지 화면이었다)
#   - 카드 장면: 왼쪽 아래 원 안에 말하는 사람 작은 화면(릴리 C12 / 말리 C16 클립, 없으면 그림 + 살짝 흔들림)
#   - 말하는 장면마다 이름표(릴리 선생님 / 말리), 자막 색도 말리 주황으로 더 뚜렷하게
#   - 클립이 아직 없으면(clips/Cxx_1080p.mp4) 시작 그림 + 줌으로 대체 — 맥에서 클립이 오면 재실행만 하면 교체
# 소리: 나레이션 + BGM(assets/bgm/storybook b1→b2) + 클립 현장음(작게, 첫 재생 5초만) + 카드 '퐁'(합성)
# 자막: ASS, 바닥 밀착 MarginV=10. 장면 안 시간은 글자수 비례.
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
if sys.platform == "darwin":  # 맥: Homebrew ffmpeg-full (기본 ffmpeg 엔 libass 없음, 2026-10-29)
    FFDIR = "/opt/homebrew/opt/ffmpeg-full/bin"
    FFMPEG, FFPROBE = f"{FFDIR}/ffmpeg", f"{FFDIR}/ffprobe"

from storyboard import SCENES

BASE = Path(__file__).parent
ROOT = [_p for _p in BASE.resolve().parents if (_p / "AGENTS.md").is_file()][-1]
IMG, CARDS, AUD, CLIPS = BASE / "images", BASE / "cards", BASE / "audio", BASE / "clips"
TMP = BASE / "_build"
TMP.mkdir(exist_ok=True)
W, H, FPS, SR = 1280, 720, 30, 48000
PAUSE = 0.45
CLIP_LEN = 5.0
NAME = "강의_CH2-2_Python_FFmpeg_Git_설치"

from make_clip_inputs import CLIPS as CLIP_TABLE

# 장면 → (바탕, 카드). 바탕: "Cxx" = 클립(없으면 시작 그림) / "Wxx" = 그림 / "last:Cxx" = 그 클립 마지막 프레임 / "card" = 카드만
# 카드: 이름 하나 또는 [(시작, 이름), ...] — 시작 = 장면 길이 비율(숫자) 또는 대사 속 단어(그 글자 위치 비율)
VIS = {
    "S01-01": ("C30", None), "S01-02": ("last:C30", [(0.3, "title")]), "S01-03": ("C14", None),
    "S01-04": ("C05", None),
    "S01-05": ("card", [(0.0, "K02_1"), ("에프에프엠펙은 가위", "K02_2"), ("깃은 사진첩", "K02_3")]),
    "S01-06": ("card", "K01"),
    "S02-01": ("card", "K04"), "S02-02": ("C16", None), "S02-03": ("card", "T01"), "S02-04": ("card", "K03"),
    "S03-01": ("card", "W01"), "S03-02": ("C10", None), "S03-03": ("card", "W02"), "S03-04": ("card", "W03"),
    "S03-05": ("card", "T03"), "S03-06": ("C17", None), "S03-07": ("card", "T04"), "S03-08": ("card", "T05"),
    "S03-09": ("C22", None), "S03-10": ("card", "W08"),
    "S03-11": ("card", [(0.0, "T13"), ("설정의 설치된 앱", "W04")]),
    "S04-01": ("C31", None), "S04-02": ("card", "K02f"), "S04-03": ("card", "T06"), "S04-04": ("card", "T06b"),
    "S04-05": ("card", "T07"), "S04-06": ("C15", None), "S04-07": ("card", "T08"), "S04-08": ("card", "K05"),
    "S04-09": ("C05", None),
    "S05-01": ("P07", None), "S05-02": ("card", "K02g"), "S05-03": ("card", "W06"), "S05-04": ("card", "T09"),
    "S05-05": ("card", "T10"), "S05-06": ("C13", None), "S05-07": ("C11", None),
    "S06-01": ("card", "T11"), "S06-02": ("C32", None), "S06-03": ("card", "K06a"), "S06-04": ("card", "K06b"),
    "S06-05": ("C16", None), "S06-06": ("card", "K06c"), "S06-07": ("C23", None),
    "S07-01": ("C09", None),
    "S07-02": ("card", [(0.0, "K07_1"), ("둘,", "K07_2"), ("셋,", "K07_3"), ("넷,", "K07_4")]),
    "S07-03": ("card", "K08"), "S07-04": ("C07", [("다음 시간에는", "K01_next")]), "S07-05": ("C08", [("다음 시간에", "end")]),
}
SILENT_LEN = {"S01-01": 5.0}
HOLD = {k: 3.0 for k in ("S02-03", "S03-07", "S03-08", "S04-03", "S04-07", "S05-04", "S05-05", "S06-01")}  # 따라 하기 멈춤
HOLD["S07-05"] = 3.0  # 엔딩 카드가 보일 시간
# 카드 장면 작은 화면: (클립, 시작 그림, 1280x720 기준 crop w:h:x:y)
PIP = {"lily": ("C12", "J05", "300:300:490:10"), "malli": ("C16", "M05", "330:330:680:110")}
PIP_D, PIP_X, PIP_Y = 190, 22, 372


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed: {' '.join(map(str, cmd[:6]))}\n{r.stderr[-1500:]}")


def wav_len(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


REUSE = [BASE.parent / "강의_CH2-1_Claude_Code_설치와_로그인" / "clips",  # C22·C23 (+ C05~C17 복사본)
         BASE.parent / "강의_CH1-2_말리_캐릭터_시트" / "clips"]  # C05~C17 원본


def clip_path(kid):
    for d in (CLIPS, *REUSE):
        p = d / f"{kid}_1080p.mp4"
        if p.exists() and p.stat().st_size > 100000:
            return p
    return None


def last_frame(kid):
    """클립 마지막 프레임(없으면 시작 그림)."""
    cp = clip_path(kid)
    if not cp:
        return IMG / f"{kid}.png"
    out = TMP / f"{kid}_last.png"
    if not out.exists():
        run([FFMPEG, "-y", "-sseof", "-0.1", "-i", str(cp), "-frames:v", "1", "-update", "1", str(out)])
    return out


def pingpong(kid):
    """정방향 + 역방향 이어 붙인 무음 클립 (loop 재생용, 이음새 없음)."""
    out = TMP / f"{kid}_pp.mp4"
    if not out.exists():
        run([FFMPEG, "-y", "-i", str(clip_path(kid)), "-filter_complex",
             f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},split[a][b];"
             "[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "18", str(out)])
    return out


def card_at(spec, line):
    """카드 시작: 숫자 = 비율, 문자열 = 대사 속 그 단어의 글자 위치 비율."""
    if isinstance(spec, (int, float)):
        return float(spec)
    i = line.find(spec)
    if i < 0:
        sys.exit(f"카드 전환 단어 없음: {spec!r}")
    return i / max(1, len(line))


def overlays():
    """원 마스크·원 테두리·이름표 (1280x720 RGBA, PIL)."""
    from PIL import Image, ImageDraw, ImageFont
    if sys.platform == "darwin":  # 맥: 맑은 고딕 굵게 대신 애플 SD 산돌고딕 Neo 굵게
        f = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 26, index=6)
    else:
        f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 26)
    m = Image.new("L", (PIP_D, PIP_D), 0)
    ImageDraw.Draw(m).ellipse([0, 0, PIP_D - 1, PIP_D - 1], fill=255)
    m.save(TMP / "pip_mask.png")
    for who, name, col in [("lily", "릴리 선생님", (231, 236, 255)), ("malli", "말리", (255, 226, 190))]:
        for pip in (False, True):
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            if pip:
                d.ellipse([PIP_X - 4, PIP_Y - 4, PIP_X + PIP_D + 3, PIP_Y + PIP_D + 3], outline=(255, 250, 238, 255), width=6)
            tw = d.textlength(name, font=f)
            x0, y0 = (PIP_X + PIP_D / 2 - (tw + 56) / 2, PIP_Y + PIP_D + 10) if pip else (18, 560)
            d.rounded_rectangle([x0, y0, x0 + tw + 56, y0 + 44], 22, fill=col + (240,), outline=(90, 80, 60, 200), width=2)
            d.ellipse([x0 + 14, y0 + 15, x0 + 28, y0 + 29], fill=(232, 120, 60) if who == "malli" else (80, 110, 200))
            d.text((x0 + 38, y0 + 5), name, font=f, fill=(45, 52, 46))
            im.save(TMP / f"tag_{who}{'_pip' if pip else ''}.png")


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
    hold = HOLD.get(s["id"], 0.0)  # 멈춤 시간은 대사 뒤에 붙으므로 단어 위치 비율은 대사 구간에만 적용
    cards = [(card_at(f, s["line"]) * (dur - hold) / dur, c) for f, c in cards]
    inputs, chain = [], []
    clip_dur = 0.0
    if base in CLIP_TABLE:
        kid, cp = base, clip_path(base)
        if cp and CLIP_TABLE[kid][3] == "loop":
            inputs += ["-stream_loop", "-1", "-i", str(pingpong(kid))]
            chain.append(f"[0:v]trim=duration={dur},setpts=PTS-STARTPTS[bg]")
        elif cp:
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
        t0 = max(frac * dur, clip_dur if frac == 0.0 else 0.0)
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
    spk = s["speaker"]
    if spk and base == "card":  # 말하는 사람 작은 화면
        pk, pimg, crop = PIP[spk]
        if clip_path(pk):
            inputs += ["-stream_loop", "-1", "-i", str(pingpong(pk))]
            bob = ""
        else:
            inputs += ["-loop", "1", "-i", str(IMG / f"{pimg}.png")]
            bob = "+3*sin(2*PI*t/1.4)"
        inputs += ["-loop", "1", "-i", str(TMP / "pip_mask.png")]
        chain.append(f"[{n_in}:v]scale={W}:{H},crop={crop},scale={PIP_D}:{PIP_D},fps={FPS},format=rgba[pv];"
                     f"[{n_in + 1}:v]format=gray,scale={PIP_D}:{PIP_D}[pm];[pv][pm]alphamerge[pa];"
                     f"[{cur}][pa]overlay=x={PIP_X}:y='{PIP_Y}{bob}':eval=frame[pp]")
        cur, n_in = "pp", n_in + 2
    if spk:  # 이름표
        inputs += ["-loop", "1", "-i", str(TMP / f"tag_{spk}{'_pip' if base == 'card' else ''}.png")]
        chain.append(f"[{cur}][{n_in}:v]overlay=0:0[tg]")
        cur, n_in = "tg", n_in + 1
    chain.append(f"[{cur}]format=yuv420p,trim=duration={dur}[v]")
    run([FFMPEG, "-y", *inputs, "-filter_complex", ";".join(chain), "-map", "[v]", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-t", f"{dur:.3f}", str(out)])
    return ok_cards and (base not in CLIP_TABLE or clip_dur == 0)


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
Style: malli,MemomentKkukkukk,40,&H0050C0FF,&H000000FF,&H00302020,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,40,40,10,1

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
    overlays()
    timeline, segs, t = [], [], 0.0
    for s in SCENES:
        wav = AUD / f"{s['id']}.wav"
        speech = wav_len(wav) if s["speaker"] else 0.0
        dur = speech + PAUSE if s["speaker"] else SILENT_LEN[s["id"]]
        dur += HOLD.get(s["id"], 0.0)
        if not s["speaker"] and VIS[s["id"]][0] in CLIP_TABLE and clip_path(VIS[s["id"]][0]):
            dur = max(dur, CLIP_LEN + 0.3)
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
    for k, (s, t0, dur, card_pop) in enumerate(segs):
        i0 = int(t0 * SR)
        if s["speaker"]:
            a = decode(AUD / f"{s['id']}.wav")
            voice[i0:i0 + len(a)] += a[: n - i0]
        base = VIS[s["id"]][0]
        if base in CLIP_TABLE and not (k and VIS[segs[k - 1][0]["id"]][0] == base):  # 같은 클립이 이어지면 현장음 한 번만
            cp = clip_path(base)
            if cp and has_audio(cp):
                a = decode(cp, 0, CLIP_LEN)
                fade = np.minimum(1, np.linspace(CLIP_LEN, 0, len(a)) / 0.6).astype(np.float32)
                amb[i0:i0 + len(a)] += (a * fade)[: n - i0] * 0.35
        if card_pop:
            p = pop(880)
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
