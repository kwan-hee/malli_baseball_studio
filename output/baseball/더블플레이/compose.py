# 더블플레이 — 최종 조립: 화이트보드 삽화 + Puck 나레이션 + 자막 + BGM → MP4 (720p)
# 화이트보드 파일럿: fade-in 등장 + 지우개 wipe 퇴장
# 최종 출력 1280x720. 완성본 파일명 앞 ✅.
import json
import subprocess
from pathlib import Path

from make_narration import SCENES  # 나레이션 텍스트 단일 출처

BASE = Path(__file__).parent
FFMPEG = (
    "ffmpeg"
)
FFPROBE = FFMPEG.replace("ffmpeg", "ffprobe")
W, H, FPS = 1280, 720, 30
PAD = 0.15
BGM = BASE / "bgm.mp3"
BGM_VOLUME = 0.15
FINAL_FADE = 2.0
SUB_STYLE = "FontName=Malgun Gothic,FontSize=18,Outline=2,MarginV=10"


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


def norm_sub(text):
    return "".join(ch for ch in text if ch.isalnum())


def build_scene_video(sid, dur, is_last=False):
    """화이트보드 효과: fade-in 등장 → 정지 → 지우개 wipe(왼→오) 퇴장."""
    img = BASE / "images" / f"{sid}.png"
    out = BASE / "scenes" / f"{sid}.mp4"
    if out.exists() and out.stat().st_size > 1000:
        return out

    if not img.exists():
        print(f"  WARNING: {sid}.png missing, generating white frame")
        run([
            FFMPEG, "-y", "-f", "lavfi", "-i", f"color=c=white:s={W}x{H}:d={dur:.3f}:r={FPS}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
        ])
        return out

    FADE_IN = 1.5
    ERASE_DUR = 1.2
    erase_start = max(dur - ERASE_DUR, FADE_IN + 0.5) if not is_last else dur + 10

    filter_complex = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:white,"
        f"fade=t=in:st=0:d={FADE_IN}:color=white[img];"
        f"color=c=white:s={W}x{H}:d={dur:.3f}:r={FPS}[eraser];"
        f"[img][eraser]overlay="
        f"x='if(lt(t,{erase_start}),-{W},-{W}+{W}*min(1,(t-{erase_start})/{ERASE_DUR}))'"
        f":y=0:shortest=1[out]"
    )

    run([
        FFMPEG, "-y",
        "-loop", "1", "-i", str(img),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(out),
    ])
    return out


def main():
    scenes_dir = BASE / "scenes"
    scenes_dir.mkdir(exist_ok=True)

    audio_dir = BASE / "audio"
    full_wav = audio_dir / "narration_full.wav"
    word_ts_path = audio_dir / "word_timestamps.json"

    if not full_wav.exists():
        raise FileNotFoundError("narration_full.wav not found — run make_narration.py first")
    if not word_ts_path.exists():
        raise FileNotFoundError("word_timestamps.json not found — run make_narration.py first")

    words = json.loads(word_ts_path.read_text(encoding="utf-8"))

    # 씬 경계 계산 (whisper 타임스탬프 기반)
    full_text = "\n\n".join(SCENES.values())
    normed_words_cum = []
    cum = 0
    for w in words:
        normed_words_cum.append(cum)
        cum += len(norm_sub(w["word"]))

    scene_times = []
    pos = 0
    for sid, text in SCENES.items():
        ns = len(norm_sub(full_text[:pos]))
        ne = len(norm_sub(full_text[:pos + len(text)]))
        ws_idx = next((i for i, c in enumerate(normed_words_cum) if c >= ns), 0)
        we_idx = next((i for i, c in enumerate(normed_words_cum) if c >= ne), len(words)) - 1
        t_start = max(0, words[ws_idx]["start"] - PAD)
        t_end = words[min(we_idx, len(words) - 1)]["end"] + PAD
        scene_times.append((sid, t_start, t_end))
        pos += len(text) + 2

    # 씬별 오디오 슬라이스 + 비디오 생성
    concat_entries = []
    total_scenes = len(scene_times)
    for scene_idx, (sid, t_start, t_end) in enumerate(scene_times):
        dur = t_end - t_start
        audio_out = audio_dir / f"{sid}.wav"
        if not audio_out.exists() or audio_out.stat().st_size < 1000:
            run([
                FFMPEG, "-y", "-i", str(full_wav),
                "-ss", f"{t_start:.3f}", "-to", f"{t_end:.3f}",
                "-c:a", "pcm_s16le", str(audio_out),
            ])
        is_last = (scene_idx == total_scenes - 1)
        vid = build_scene_video(sid, dur, is_last=is_last)
        merged = scenes_dir / f"{sid}_merged.mp4"
        if not merged.exists() or merged.stat().st_size < 1000:
            run([
                FFMPEG, "-y", "-i", str(vid), "-i", str(audio_out),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", str(merged),
            ])
        concat_entries.append(f"file '{merged.name}'")
        print(f"  {sid}: {dur:.1f}s")

    # Concat
    concat_file = scenes_dir / "concat.txt"
    concat_file.write_text("\n".join(concat_entries), encoding="utf-8")
    joined = BASE / "_joined.mp4"
    run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", str(joined),
    ])
    print(f"joined: {duration_of(joined):.1f}s")

    # 자막 생성
    srt_path = BASE / "subs.srt"
    srt_lines = []
    idx = 1
    cumulative_offset = 0.0
    for sid, t_start, t_end in scene_times:
        text = SCENES[sid]
        sents = split_sentences(text)
        scene_dur = t_end - t_start
        if sents:
            per_sent = scene_dur / len(sents)
            for i, sent in enumerate(sents):
                s_start = cumulative_offset + i * per_sent
                s_end = cumulative_offset + (i + 1) * per_sent
                srt_lines.append(f"{idx}\n{ts(s_start)} --> {ts(s_end)}\n{sent}\n")
                idx += 1
        cumulative_offset += scene_dur
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    print(f"subtitles: {idx - 1} entries")

    # 자막 합성
    subbed = BASE / "_subbed.mp4"
    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
    sub_filter = f"subtitles='{srt_escaped}':force_style='{SUB_STYLE}'"
    run([
        FFMPEG, "-y", "-i", str(joined),
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy", str(subbed),
    ])

    # BGM 믹스 + 페이드아웃
    final_dur = duration_of(subbed)
    fade_start = final_dur - FINAL_FADE
    final = BASE / "\u2705\ub354\ube14\ud50c\ub808\uc774_final.mp4"

    if BGM.exists():
        run([
            FFMPEG, "-y", "-i", str(subbed), "-stream_loop", "-1", "-i", str(BGM),
            "-filter_complex",
            f"[1:a]volume={BGM_VOLUME},afade=t=out:st={fade_start}:d={FINAL_FADE}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{final_dur:.3f}", str(final),
        ])
    else:
        run([
            FFMPEG, "-y", "-i", str(subbed),
            "-c:v", "copy", "-c:a", "copy", str(final),
        ])

    print(f"\n{'=' * 50}")
    print(f"FINAL: {final}")
    print(f"Duration: {duration_of(final):.1f}s")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
