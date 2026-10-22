# make_shorts.py — 유튜브 세로 쇼츠(9:16) 25~30초 자동 생성
import json, subprocess, sys, wave
from pathlib import Path
from make_narration import SCENES

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
FFMPEG = ("ffmpeg")
FFPROBE = FFMPEG.replace("ffmpeg", "ffprobe")

SW, SH, FPS = 1080, 1920, 30; FG_W = 1080; FG_Y = 300; PAD = 0.12
BGM = BASE / "bgm.mp3"; BGM_VOLUME = 0.13; FINAL_FADE = 1.0; FONT = BASE / "font.ttf"
SUB_FONT = "MemomentKkukkukk"; SUB_FONTSIZE = 62; SUB_MARGINV = 430; SUB_MARGINLR = 90; LINE_MAX = 15
TARGET_MIN, TARGET_MAX = 25, 30
SHORT_SCENES = ["s06", "s08"]  # 치즈 떨어짐 + 화해·나눔

def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    if r.returncode != 0: raise RuntimeError(f"ffmpeg failed:\n{r.stderr[-1500:]}")

def wav_dur(path):
    with wave.open(str(path), "rb") as w: return w.getnframes() / w.getframerate()

def img_dims(path):
    r = subprocess.run([FFPROBE, "-v", "quiet", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split(","); return int(w), int(h)

def ass_ts(sec):
    cs = int(round(sec * 100)); h, rem = divmod(cs, 360000); m, rem = divmod(rem, 6000); s, cs = divmod(rem, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"

def norm_sub(text): return "".join(ch for ch in text if ch.isalnum())

def split_sentences(text):
    parts, cur = [], ""
    for ch in text:
        cur += ch
        if ch in ".?!":
            if cur.strip(): parts.append(cur.strip())
            cur = ""
    if cur.strip(): parts.append(cur.strip())
    return parts

SIDS = list(SCENES.keys())
ADUR = {s: wav_dur(BASE / "audio" / f"{s}.wav") for s in SIDS}
ABS0 = {}; _acc = 0.0
for s in SIDS: ABS0[s] = _acc; _acc += ADUR[s]

WORDS_JSON = BASE / "audio" / "word_timestamps.json"
ALL_WORDS = json.loads(WORDS_JSON.read_text(encoding="utf-8")) if WORDS_JSON.exists() else None

def scene_spans(a_start, a_end):
    out, acc = [], 0
    if not ALL_WORDS: return out
    for w in ALL_WORDS:
        if w["end"] <= a_start + 0.05 or w["start"] >= a_end - 0.05: continue
        n = len(norm_sub(w["word"]));
        if n == 0: continue
        out.append((acc, acc + n, w["start"], w["end"])); acc += n
    return out

def measure_words(spans, a, b):
    ws = we = None
    for s in spans:
        if ws is None and s[1] > a: ws = s
        if s[0] < b: we = s
        else: break
    if ws is None or we is None or we[3] <= ws[2]: return None
    return ws[2], we[3]

def wrap_lines(sentence):
    words, lines, cur = sentence.split(), [], ""
    for w in words:
        if not cur: cur = w
        elif len(cur) + 1 + len(w) <= LINE_MAX: cur += " " + w
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines or [sentence]

def cues_from_sentence(sentence, st, en):
    lines = wrap_lines(sentence)
    pages = [lines[i:i + 2] for i in range(0, len(lines), 2)]
    total = sum(sum(len(l) for l in pg) for pg in pages) or 1
    out, cur = [], st
    for pg in pages:
        dur = (en - st) * (sum(len(l) for l in pg) / total)
        cst, cen = cur, min(en, cur + dur) if dur > 0 else en
        if cen - cst < 0.3: cen = min(en, cst + 0.5)
        out.append(("\\N".join(pg), cst, cen)); cur = cen
    return out

def build_scene_9x16(sid, play_dur, out):
    audio = BASE / "audio" / f"{sid}.wav"; sdur = play_dur + PAD
    frames = max(1, int(round(sdur * FPS)))
    clip = BASE / "clips" / f"{sid}_1080p.mp4"; use_clip = clip.exists() and clip.stat().st_size > 0
    if use_clip:
        vf = (f"[0:v]split=2[b][f];[b]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},"
              f"boxblur=26:2,eq=brightness=-0.18,fps={FPS},setsar=1[bg];[f]scale={FG_W}:-2,fps={FPS},setsar=1[fg];"
              f"[bg][fg]overlay=0:{FG_Y}:shortest=1,trim=duration={sdur:.3f},setpts=PTS-STARTPTS[v];"
              f"[1:a]apad,atrim=duration={sdur:.3f}[a]")
        inp = ["-stream_loop", "-1", "-i", str(clip), "-i", str(audio)]
    else:
        img = BASE / "images" / f"{sid}.png"; w, h = img_dims(img)
        fgh = int(round(FG_W * h / w)) // 2 * 2
        vf = (f"[0:v]split=2[b][f];[b]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},"
              f"boxblur=28:2,eq=brightness=-0.20,zoompan=z=1:d={frames}:s={SW}x{SH}:fps={FPS},setsar=1[bg];"
              f"[f]scale={FG_W*2}:{fgh*2},zoompan=z='min(1+0.06*on/{frames},1.06)':x='(iw-iw/zoom)/2'"
              f":y='(ih-ih/zoom)/2':d={frames}:s={FG_W}x{fgh}:fps={FPS},setsar=1[fg];"
              f"[bg][fg]overlay=0:{FG_Y}[vv];[vv]trim=duration={sdur:.3f},setpts=PTS-STARTPTS[v];"
              f"[1:a]apad,atrim=duration={sdur:.3f}[a]")
        inp = ["-i", str(img), "-i", str(audio)]
    run([FFMPEG, "-y", *inp, "-filter_complex", vf, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1", "-threads", "2", str(out)])
    return sdur

ASS_HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {SW}
PlayResY: {SH}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{SUB_FONT},{SUB_FONTSIZE},&H0000FFFF,&H000000FF,&H00202020,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,{SUB_MARGINLR},{SUB_MARGINLR},{SUB_MARGINV},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def build_ass(scene_ids, play_durs, ass_path):
    events, ncues, cursor, prev_end = [], 0, 0.0, 0.0
    for sid in scene_ids:
        pd = play_durs[sid]; a0 = ABS0[sid]; spans = scene_spans(a0, a0 + pd); scene_char = 0
        for s in split_sentences(SCENES[sid]):
            n = len(norm_sub(s)); m = measure_words(spans, scene_char, scene_char + n); scene_char += n
            if m: lst = min(max(0.0, m[0] - a0), pd); len_ = min(max(0.0, m[1] - a0), pd)
            else: lst, len_ = 0.0, pd
            st, en = cursor + lst, cursor + len_
            for txt, cst, cen in cues_from_sentence(s, st, en):
                if cst < prev_end: cst = prev_end
                if cen < cst + 0.3: cen = cst + 0.5
                prev_end = cen; events.append(f"Dialogue: 0,{ass_ts(cst)},{ass_ts(cen)},Default,,0,0,0,,{txt}"); ncues += 1
        cursor += pd + PAD
    ass_path.write_text(ASS_HEADER + "\n".join(events) + "\n", encoding="utf-8"); return ncues

if __name__ == "__main__":
    (BASE / "shorts").mkdir(exist_ok=True); work = BASE / "shorts" / "_work"; work.mkdir(parents=True, exist_ok=True)
    if not FONT.exists(): sys.exit("font.ttf 없음")
    scene_ids = SHORT_SCENES; play_durs = {s: ADUR[s] for s in scene_ids}
    total = sum(play_durs[s] + PAD for s in scene_ids)
    print(f"[선정] scenes = {scene_ids}  ({total:.1f}s 원본)")
    if total > TARGET_MAX:
        last = scene_ids[-1]; play_durs[last] = max(4.0, play_durs[last] - (total - TARGET_MAX))
        total = sum(play_durs[s] + PAD for s in scene_ids); print(f"[트림] -> {total:.1f}s")
    scene_files = []
    for sid in scene_ids:
        f = work / f"short_{sid}.mp4"; build_scene_9x16(sid, play_durs[sid], f); scene_files.append(f)
    ass = work / "short.ass"; ncues = build_ass(scene_ids, play_durs, ass)
    concat = work / "short_concat.txt"
    concat.write_text("\n".join(f"file '{p.as_posix()}'" for p in scene_files), encoding="utf-8")
    joined = work / "short_joined.mp4"
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", str(joined)])
    subbed = work / "short_subbed.mp4"
    run([FFMPEG, "-y", "-i", joined.relative_to(BASE).as_posix(),
         "-vf", f"subtitles={ass.relative_to(BASE).as_posix()}:fontsdir=.",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "copy", "-threads", "2",
         str(subbed)], cwd=str(BASE))
    out = BASE / "shorts" / "short_여우와_까마귀.mp4"
    dur = float(subprocess.run([FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(subbed)], capture_output=True, text=True).stdout.strip())
    fade_st = max(0.0, dur - FINAL_FADE)
    run([FFMPEG, "-y", "-i", str(subbed), "-stream_loop", "-1", "-i", str(BGM), "-filter_complex",
         f"[1:a]volume={BGM_VOLUME}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[mix];"
         f"[mix]afade=t=out:st={fade_st:.2f}:d={FINAL_FADE}[aout];"
         f"[0:v]fade=t=out:st={fade_st:.2f}:d={FINAL_FADE}[vout]",
         "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-threads", "2", str(out)])
    print(f"[완료] {out.name}  {dur:.1f}s  자막 {ncues}큐  9:16 세로")
    print("SHORTS DONE")
