# 희생플레이 — 최종 조립: 삽화 Ken Burns + 절정 클립 + Puck 나레이션 + 자막 + BGM → MP4 (1080p)
# 씬 경계 무음 최소화: PAD 0.15 / AUDIO_DELAY 0 (tts-scene-gap 규칙, 2026-07-08)
# 자막 타이밍 A안 (2026-07-15 사용자 승인, 야구 첫 적용): whisper 단어 타임스탬프 실측 SRT — 씬별 로컬 재앵커링
import json
import subprocess
from pathlib import Path

from make_narration import SCENES  # 나레이션 텍스트 단일 출처

BASE = Path(__file__).parent
FFMPEG = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.EXE"
)
FFPROBE = FFMPEG.replace("ffmpeg.EXE", "ffprobe.EXE")
W, H, FPS = 1920, 1080, 30
PAD = 0.15
AUDIO_DELAY_MS = 0
BGM = BASE / "bgm.mp3"
BGM_VOLUME = 0.15
FINAL_FADE = 2.0
SUB_STYLE = "FontName=Malgun Gothic,FontSize=18,Outline=2,MarginV=10"  # 자막 바닥 밀착 (상시 지시)

# 절정 씬 = AI 영상 클립 (없으면 Ken Burns 폴백 — 제작 중단 없음)
VIDEO_SCENES = {
    "s01": BASE / "clips" / "s01_1080p.mp4",  # 아웃인데 박수 훅
    "s07": BASE / "clips" / "s07_1080p.mp4",  # 끝내기 희생플라이
}
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


def norm_sub(text):
    return "".join(ch for ch in text if ch.isalnum())


def measure_words(spans, a, b):
    """대본 누적 글자 구간 [a,b)에 해당하는 실제 발화 (시작, 끝) 시각. 실패 시 None."""
    ws = we = None
    for s in spans:
        if ws is None and s[1] > a:
            ws = s
        if s[0] < b:
            we = s
        else:
            break
    if ws is None or we is None or we[3] <= ws[2]:
        return None
    return ws[2], we[3]


def scene_spans(words, a_start, a_end):
    """씬 오디오 구간 [a_start, a_end) 에 속한 단어들로 씬-로컬 글자 스팬 생성.
    전역 누적 매핑 금지 — whisper 오전사 글자수 차이가 뒤로 누적됨 (2026-07-15 검증)."""
    out, acc = [], 0
    for w in words:
        if w["end"] <= a_start + 0.05 or w["start"] >= a_end - 0.05:
            continue
        n = len(norm_sub(w["word"]))
        if n == 0:
            continue
        out.append((acc, acc + n, w["start"], w["end"]))
        acc += n
    return out


scene_dir = BASE / "scenes"
scene_dir.mkdir(exist_ok=True)

WORDS_JSON = BASE / "audio" / "word_timestamps.json"
all_words = None
if WORDS_JSON.exists():
    all_words = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    print(f"subtitle timing: measured ({len(all_words)} words, per-scene anchored)")
else:
    print("subtitle timing: proportional fallback (no word_timestamps.json)")

srt_lines, cue_idx, t_cursor = [], 1, 0.0
audio_cursor = 0.0    # 통짜 나레이션 기준 씬 시작 시각
prev_cue_end = 0.0    # 자막 겹침 방지용 단조 클램프
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
    spans = scene_spans(all_words, audio_cursor, audio_cursor + adur) if all_words else None
    scene_char = 0  # 씬-로컬 글자 위치 (씬별 재앵커링)
    for s in sentences:
        cdur = adur * len(s) / total_chars
        n = len(norm_sub(s))
        m = measure_words(spans, scene_char, scene_char + n) if spans else None
        scene_char += n
        if m:
            # 실측: 통짜 나레이션 시각 → 이 씬의 최종 타임라인 시각으로 변환 (씬 구간으로 클램프)
            st = t_cursor + min(max(0.0, m[0] - audio_cursor), adur)
            en = t_cursor + min(max(0.0, m[1] - audio_cursor), sdur)
            if en - st < 0.3:
                en = min(st + 0.5, t_cursor + sdur)
        else:
            # 폴백: 기존 글자수 비례 추정
            st = cue_t
            en = min(cue_t + cdur, t_cursor + sdur)
        # 단조 클램프: 오전사로 인접 문장이 한 단어씩 겹치는 것 방지
        if st < prev_cue_end:
            st = prev_cue_end
        if en < st + 0.3:
            en = min(st + 0.5, t_cursor + sdur)
        prev_cue_end = en
        srt_lines.append(f"{cue_idx}\n{ts(st)} --> {ts(en)}\n{s}\n")
        cue_idx += 1
        cue_t += cdur
    audio_cursor += adur
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
     "-vf", f"subtitles=subs.srt:force_style='{SUB_STYLE}'",
     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
     "-c:a", "copy", "-threads", "2", "_subbed.mp4"], cwd=str(BASE))

final = BASE / "희생플레이_final.mp4"
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
