# 말리와 개와 고양이와 구슬 — 최종 조립: 이미지 Ken Burns + 절정 클립 + 나레이션 + 자막 + BGM → MP4
import subprocess
from pathlib import Path

from make_narration import SCENES  # 나레이션 텍스트 단일 출처 (자막 SRT도 여기서 생성)

BASE = Path(__file__).parent
FFMPEG = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.EXE"
)
FFPROBE = FFMPEG.replace("ffmpeg.EXE", "ffprobe.EXE")
W, H, FPS = 1920, 1080, 30
PAD = 0.15          # 씬 경계 무음 (2026-07-08 규칙: 0.8→0.15)
AUDIO_DELAY_MS = 0  # 씬 경계 무음 (2026-07-08 규칙: 400→0)
BGM = BASE / "bgm.mp3"
BGM_VOLUME = 0.15
FINAL_FADE = 2.0
SUB_STYLE = "FontName=MemomentKkukkukk,FontSize=20,Outline=2,MarginV=10"  # 자막 바닥 밀착 (상시 지시)

# 절정 씬 = AI 영상 클립 (나머지는 정지 이미지 + Ken Burns)
VIDEO_SCENES = {
    "s04": BASE / "clips" / "s04_1080p.mp4",  # 누렁이 등에 나비, 강 헤엄
    "s07": BASE / "clips" / "s07_1080p.mp4",  # 구슬 퐁당 절정
}
# 클립이 없으면 해당 씬도 Ken Burns 로 폴백 (제작 중단 없음)
VIDEO_SCENES = {k: v for k, v in VIDEO_SCENES.items() if v.exists() and v.stat().st_size > 0}


def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (rc={r.returncode}):\n{r.stderr[-1500:]}")


def duration_of(path):
    r = subprocess.run(
        [FFPROBE, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def ts(sec):
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_sentences(text):
    parts, cur = [], ""
    for ch in text:
        cur += ch
        if ch in ".?!":
            if cur.strip():
                parts.append(cur.strip())
            cur = ""
    if cur.strip():
        parts.append(cur.strip())
    return parts


scene_dir = BASE / "scenes"
scene_dir.mkdir(exist_ok=True)

srt_lines, cue_idx, t_cursor = [], 1, 0.0
scene_files = []

for i, (sid, text) in enumerate(SCENES.items()):
    audio = BASE / "audio" / f"{sid}.wav"
    adur = duration_of(audio)
    sdur = adur + PAD
    out = scene_dir / f"{sid}.mp4"

    if not (out.exists() and out.stat().st_size > 0):
        if sid in VIDEO_SCENES:
            run([FFMPEG, "-y", "-stream_loop", "-1", "-i", str(VIDEO_SCENES[sid]), "-i", str(audio),
                 "-filter_complex",
                 f"[0:v]scale={W}:{H},fps={FPS},trim=duration={sdur:.3f},setpts=PTS-STARTPTS[v];"
                 f"[1:a]adelay={AUDIO_DELAY_MS}|{AUDIO_DELAY_MS},apad,atrim=duration={sdur:.3f}[a]",
                 "-map", "[v]", "-map", "[a]",
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-threads", "2", str(out)])
        else:
            frames = int(sdur * FPS)
            if i % 2 == 0:
                zexpr = f"min(1+0.10*on/{frames},1.10)"
            else:
                zexpr = f"max(1.10-0.10*on/{frames},1.0)"
            img = BASE / "images" / f"{sid}.png"
            vf = (
                f"scale=2400:1350,zoompan=z='{zexpr}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
                f":d={frames}:s={W}x{H}:fps={FPS}"
            )
            run([FFMPEG, "-y", "-i", str(img), "-i", str(audio),
                 "-filter_complex",
                 f"[0:v]{vf}[v];[1:a]adelay={AUDIO_DELAY_MS}|{AUDIO_DELAY_MS},apad,atrim=duration={sdur:.3f}[a]",
                 "-map", "[v]", "-map", "[a]",
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-threads", "2", str(out)])
        print(f"{sid}: {sdur:.1f}s {'(clip)' if sid in VIDEO_SCENES else '(kenburns)'}")
    else:
        print(f"{sid}: cached ({sdur:.1f}s)")
    scene_files.append(out)

    sentences = split_sentences(text)
    total_chars = sum(len(s) for s in sentences)
    cue_t = t_cursor + AUDIO_DELAY_MS / 1000
    for s in sentences:
        cdur = adur * len(s) / total_chars
        srt_lines.append(f"{cue_idx}\n{ts(cue_t)} --> {ts(min(cue_t + cdur, t_cursor + sdur))}\n{s}\n")
        cue_idx += 1
        cue_t += cdur
    t_cursor += sdur

srt_path = BASE / "subs.srt"
srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
print(f"SRT: {cue_idx - 1} cues, total {t_cursor:.1f}s")

concat_txt = BASE / "concat.txt"
concat_txt.write_text("\n".join(f"file '{p.as_posix()}'" for p in scene_files), encoding="utf-8")
joined = BASE / "_joined.mp4"
run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", str(joined)])

sub = BASE / "_subbed.mp4"
run([FFMPEG, "-y", "-i", "_joined.mp4",
     "-vf", f"subtitles=subs.srt:fontsdir=.:force_style='{SUB_STYLE}'",
     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
     "-c:a", "copy", "-threads", "2", "_subbed.mp4"], cwd=str(BASE))

final = BASE / "말리와_개와_고양이와_구슬_final.mp4"
fade_st = max(0.0, t_cursor - FINAL_FADE)
run([FFMPEG, "-y", "-i", str(sub), "-stream_loop", "-1", "-i", str(BGM),
     "-filter_complex",
     f"[1:a]volume={BGM_VOLUME}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[mix];"
     f"[mix]afade=t=out:st={fade_st:.2f}:d={FINAL_FADE}[aout];"
     f"[0:v]fade=t=out:st={fade_st:.2f}:d={FINAL_FADE}[vout]",
     "-map", "[vout]", "-map", "[aout]",
     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
     "-c:a", "aac", "-b:a", "192k", "-threads", "2", str(final)])
print(f"FINAL: {final.name} ({final.stat().st_size:,} bytes, {t_cursor:.1f}s)")  # cp949 콘솔 — 파일명만 출력
