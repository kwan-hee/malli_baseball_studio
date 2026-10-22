# make_shorts.py — 유튜브 세로 쇼츠(9:16) 2편 자동 생성
# ┌ 원칙: 기존 일반 파이프라인(compose.py)을 건드리지 않고, 그 산출 자산만 재사용한다.
# │  재사용 자산: make_narration.SCENES(대본) / audio/sXX.wav(음성) / audio/word_timestamps.json(자막 타이밍)
# │              / images/sXX.png(삽화 16:9) / clips/sXX_1080p.mp4(있으면) / bgm.mp3 / font.ttf
# │  유료 API 호출 없음(이미지·TTS 재생성 안 함).
# └ 산출: shorts/short_01_complete.mp4(완결형) + short_02_teaser.mp4(예고형) + 각 *_metadata.txt
#         + long/long_video.mp4 · long/thumbnail.png (요청 폴더구조 충족용 복사본, 원본 플랫 파일은 그대로 둠)
#
# 실행: python compose.py 로 일반 영상을 먼저 만든 뒤  ->  python make_shorts.py
# "화면 버튼" 대응(이 프로젝트엔 GUI가 없음 → CLI 모드로 매핑):
#   · 일반 영상만        : python compose.py
#   · 일반 영상 + 쇼츠 2 : python compose.py && python make_shorts.py
import json
import subprocess
import sys
import wave
from pathlib import Path

from make_narration import SCENES  # 대본 단일 출처 (compose.py 와 동일 소스)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # cp949 콘솔 print 크래시 방지

BASE = Path(__file__).parent
FFMPEG = (
    "ffmpeg"
)
FFPROBE = FFMPEG.replace("ffmpeg", "ffprobe")

# ── 세로 쇼츠 규격 ─────────────────────────────────────────────
SW, SH, FPS = 1080, 1920, 30          # 1080x1920 9:16 H.264
FG_W = 1080                            # 원본 이미지를 화면 폭에 꽉 맞춤(크롭 없이 통째로)
FG_Y = 300                            # 상단 배치 → 아래쪽에 자막 안전영역 확보
PAD = 0.12                            # 씬 경계 무음
BGM = BASE / "bgm.mp3"
BGM_VOLUME = 0.13
FINAL_FADE = 1.0
FONT = BASE / "font.ttf"              # MemomentKkukkukk (compose.py 와 동일 폰트)

# 자막: ASS 파일로 직접 생성 → PlayRes를 영상과 동일(1080x1920)로 고정해 폰트크기·위치를 픽셀 단위로 제어.
# (SRT+force_style 은 libass 기본 PlayRes 때문에 세로영상에서 MarginV 가 화면 밖으로 밀림 — 2026-07-23 검증)
SUB_FONT = "MemomentKkukkukk"        # compose.py 와 동일 폰트(font.ttf)
SUB_FONTSIZE = 62                    # 큰 글자(모바일 가독)
SUB_MARGINV = 430                    # 하단에서 위로 — 하단 UI 버튼 안전영역 확보(너무 낮지 않게)
SUB_MARGINLR = 90                    # 좌우 여백(우측 버튼 침범 방지)
LINE_MAX = 15                        # 한 줄 최대 글자수(요청 12~15자)

# 쇼츠 길이 목표(초)
COMPLETE_MIN, COMPLETE_MAX = 35, 50
TEASER_MIN, TEASER_MAX = 30, 45
ENDCARD_SEC = 2.0
END_TEXT_1 = "전체 이야기는"
END_TEXT_2 = "말리의 동화나라에서"

# 씬 자동 선정(비워두면 자동, 리스트로 지정하면 수동 오버라이드 — 편별 미세조정용)
SHORT1_SCENES = ["s07", "s09"]   # 완결형: 자정 도망·유리구두 → 구두 딱 맞음·화해(해결)
SHORT2_SCENES = ["s04", "s07"]   # 예고형: 요정 마법 변신 → 자정 종 도망(절정, 결말 직전 컷)

# 대본 자동 선정용 후킹 키워드(요청 사양: 사라짐/이상한 소리/비밀/위험/달·별·밤·숲/도움·화해/반전)
CUE_WEIGHTS = {
    "사라": 3, "갑자기": 3, "비밀": 3, "위험": 3, "구해": 3, "살려": 3, "몰래": 3,
    "이상한": 3, "소리": 2, "그런데": 2, "깜짝": 2, "놀라": 2, "어째": 2, "도깨비": 2,
    "달": 2, "별": 2, "밤": 2, "숲": 2, "도와": 2, "도움": 2, "화해": 2, "사과": 2,
}
RESOLUTION_KEYWORDS = ["화해", "사과", "받아", "함께", "행복", "나눠", "나누", "친구가 되",
                       "오래오래", "고맙", "다정", "따뜻"]
INTRO_MARKERS = ["안녕", "나는 말리", "오늘은"]                 # 도입 인사(쇼츠 훅 부적합)
OUTRO_MARKERS = ["구독", "좋아요", "다음 편", "오늘 이야기", "또 만나"]  # 채널 아웃트로


def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (rc={r.returncode}):\n{' '.join(map(str, cmd))[:400]}\n{r.stderr[-1500:]}")


def wav_dur(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def img_dims(path):
    r = subprocess.run([FFPROBE, "-v", "quiet", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")
    return int(w), int(h)


def ass_ts(sec):
    cs = int(round(sec * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def norm_sub(text):
    return "".join(ch for ch in text if ch.isalnum())


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


# ── 씬 절대 오프셋(전체 나레이션 기준) & 자막 단어 타이밍 (compose.py 로직 재사용) ──
SIDS = list(SCENES.keys())
ADUR = {s: wav_dur(BASE / "audio" / f"{s}.wav") for s in SIDS}
ABS0 = {}
_acc = 0.0
for s in SIDS:
    ABS0[s] = _acc
    _acc += ADUR[s]

WORDS_JSON = BASE / "audio" / "word_timestamps.json"
ALL_WORDS = json.loads(WORDS_JSON.read_text(encoding="utf-8")) if WORDS_JSON.exists() else None


def scene_spans(a_start, a_end):
    """씬 오디오 구간 단어들의 (로컬글자시작, 로컬글자끝, 절대start, 절대end)."""
    out, acc = [], 0
    if not ALL_WORDS:
        return out
    for w in ALL_WORDS:
        if w["end"] <= a_start + 0.05 or w["start"] >= a_end - 0.05:
            continue
        n = len(norm_sub(w["word"]))
        if n == 0:
            continue
        out.append((acc, acc + n, w["start"], w["end"]))
        acc += n
    return out


def measure_words(spans, a, b):
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


def wrap_lines(sentence):
    words, lines, cur = sentence.split(), [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= LINE_MAX:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [sentence]


def cues_from_sentence(sentence, st, en):
    """문장을 ≤2줄(줄당 ~12~15자) 페이지들로 나누고, 시간을 글자수 비례로 배분."""
    lines = wrap_lines(sentence)
    pages = [lines[i:i + 2] for i in range(0, len(lines), 2)]
    total = sum(sum(len(l) for l in pg) for pg in pages) or 1
    out, cur = [], st
    for pg in pages:
        dur = (en - st) * (sum(len(l) for l in pg) / total)
        cst, cen = cur, min(en, cur + dur) if dur > 0 else en
        if cen - cst < 0.3:
            cen = min(en, cst + 0.5)
        out.append(("\\N".join(pg), cst, cen))
        cur = cen
    return out


# ── 씬 자동 선정 ───────────────────────────────────────────────
def has_any(text, markers):
    return any(m in text for m in markers)


def cue_score(sid):
    text = SCENES[sid]
    sc = sum(wt * text.count(k) for k, wt in CUE_WEIGHTS.items())
    sc += min(text.count("?"), 2) * 1.0            # 궁금증(물음표)
    sc += min(text.count("!"), 2) * 0.5            # 감정 고조(느낌표)
    if (BASE / "clips" / f"{sid}_1080p.mp4").exists():
        sc += 2                                    # 영상 클립 보유 = 절정/모션 씬
    return sc


def is_intro(sid):
    return has_any(SCENES[sid], INTRO_MARKERS) and SIDS.index(sid) <= 1


def is_outro(sid):
    return has_any(SCENES[sid], OUTRO_MARKERS) and SIDS.index(sid) >= len(SIDS) - 2


def pick_complete():
    core = [s for s in SIDS if not is_intro(s) and not is_outro(s)]
    # 해결 씬 = 화해/사과 키워드를 가진 가장 뒤쪽 씬 (없으면 core 마지막)
    res = next((s for s in reversed(core) if has_any(SCENES[s], RESOLUTION_KEYWORDS)), core[-1])
    before = [s for s in core if SIDS.index(s) < SIDS.index(res)]
    if not before:
        return [res]
    # 문제/훅 = 상위권 점수 중 '가장 이른' 씬(설정→해결 흐름을 위해 앞쪽 우선)
    top = max(cue_score(s) for s in before)
    problem = min([s for s in before if cue_score(s) >= top - 2], key=SIDS.index)
    chosen = sorted({problem, res}, key=SIDS.index)

    def total(ss):
        return sum(ADUR[s] + PAD for s in ss)
    # 부족하면 고득점 씬 삽입, 초과면 중간 씬 제거(해결 씬은 유지)
    for cand in sorted(before, key=cue_score, reverse=True):
        if total(chosen) >= COMPLETE_MIN:
            break
        chosen = sorted(set(chosen) | {cand}, key=SIDS.index)
    while total(chosen) > COMPLETE_MAX and len(chosen) > 2:
        chosen.pop(-2)
    return chosen


def pick_teaser():
    # 결말 직전에서 종료 → '첫' 해결 씬(후반부) 이전까지만 후보. 도입 인사 제외.
    core = [s for s in SIDS if not is_intro(s) and not is_outro(s)]
    res_start = next((s for s in core
                      if has_any(SCENES[s], RESOLUTION_KEYWORDS) and SIDS.index(s) >= len(SIDS) // 2),
                     core[-1])
    pre = [s for s in core if SIDS.index(s) < SIDS.index(res_start)] or [core[0]]
    # 절정 = 영상 클립 보유 씬 우선(파이프라인이 motion/importance 로 고른 씬), 없으면 최고 점수
    clip_scenes = [s for s in pre if (BASE / "clips" / f"{s}_1080p.mp4").exists()]
    climax = max(clip_scenes or pre, key=lambda s: (cue_score(s), SIDS.index(s)))
    ci = SIDS.index(climax)
    hook = next((s for s in pre if SIDS.index(s) == ci - 1 and not is_intro(s)), None)
    if hook is None:
        others = [s for s in pre if s != climax]
        hook = max(others, key=cue_score) if others else climax
    return sorted({hook, climax}, key=SIDS.index)


# ── 9:16 씬 클립 빌드 (블러 배경 + 원본 통째 오버레이, 크롭 없음) ──
def build_scene_9x16(sid, play_dur, out):
    audio = BASE / "audio" / f"{sid}.wav"
    sdur = play_dur + PAD
    frames = max(1, int(round(sdur * FPS)))
    clip = BASE / "clips" / f"{sid}_1080p.mp4"
    use_clip = clip.exists() and clip.stat().st_size > 0

    if use_clip:
        vf = (
            f"[0:v]split=2[b][f];"
            f"[b]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},"
            f"boxblur=26:2,eq=brightness=-0.18,fps={FPS},setsar=1[bg];"
            f"[f]scale={FG_W}:-2,fps={FPS},setsar=1[fg];"
            f"[bg][fg]overlay=0:{FG_Y}:shortest=1,trim=duration={sdur:.3f},setpts=PTS-STARTPTS[v];"
            f"[1:a]apad,atrim=duration={sdur:.3f}[a]"
        )
        inp = ["-stream_loop", "-1", "-i", str(clip), "-i", str(audio)]
    else:
        img = BASE / "images" / f"{sid}.png"
        w, h = img_dims(img)
        fgh = int(round(FG_W * h / w)) // 2 * 2
        vf = (
            f"[0:v]split=2[b][f];"
            f"[b]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},"
            f"boxblur=28:2,eq=brightness=-0.20,zoompan=z=1:d={frames}:s={SW}x{SH}:fps={FPS},setsar=1[bg];"
            f"[f]scale={FG_W*2}:{fgh*2},"
            f"zoompan=z='min(1+0.06*on/{frames},1.06)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
            f":d={frames}:s={FG_W}x{fgh}:fps={FPS},setsar=1[fg];"
            f"[bg][fg]overlay=0:{FG_Y}[vv];"
            f"[vv]trim=duration={sdur:.3f},setpts=PTS-STARTPTS[v];"
            f"[1:a]apad,atrim=duration={sdur:.3f}[a]"
        )
        inp = ["-i", str(img), "-i", str(audio)]

    run([FFMPEG, "-y", *inp, "-filter_complex", vf, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
         "-threads", "2", str(out)])
    return sdur


def build_endcard(bg_sid, out):
    img = BASE / "images" / f"{bg_sid}.png"
    frames = int(ENDCARD_SEC * FPS)
    vf = (
        f"[0:v]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},"
        f"boxblur=32:3,eq=brightness=-0.38,zoompan=z=1:d={frames}:s={SW}x{SH}:fps={FPS},setsar=1,"
        f"drawtext=fontfile='font.ttf':text='{END_TEXT_1}':fontcolor=white:fontsize=66:"
        f"x=(w-tw)/2:y=h*0.40:borderw=5:bordercolor=black,"
        f"drawtext=fontfile='font.ttf':text='{END_TEXT_2}':fontcolor=yellow:fontsize=76:"
        f"x=(w-tw)/2:y=h*0.40+110:borderw=6:bordercolor=black[v]"
    )
    run([FFMPEG, "-y", "-i", str(img), "-f", "lavfi", "-t", f"{ENDCARD_SEC}",
         "-i", "anullsrc=r=24000:cl=mono", "-filter_complex", vf,
         "-map", "[v]", "-map", "1:a", "-t", f"{ENDCARD_SEC}",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
         str(out)], cwd=str(BASE))


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
        pd = play_durs[sid]
        a0 = ABS0[sid]
        spans = scene_spans(a0, a0 + pd)
        scene_char = 0
        for s in split_sentences(SCENES[sid]):
            n = len(norm_sub(s))
            m = measure_words(spans, scene_char, scene_char + n)
            scene_char += n
            if m:
                lst = min(max(0.0, m[0] - a0), pd)
                len_ = min(max(0.0, m[1] - a0), pd)
            else:
                lst, len_ = 0.0, pd  # 폴백(타이밍 없으면 씬 전체)
            st, en = cursor + lst, cursor + len_
            for txt, cst, cen in cues_from_sentence(s, st, en):
                if cst < prev_end:
                    cst = prev_end
                if cen < cst + 0.3:
                    cen = cst + 0.5
                prev_end = cen
                events.append(f"Dialogue: 0,{ass_ts(cst)},{ass_ts(cen)},Default,,0,0,0,,{txt}")
                ncues += 1
        cursor += pd + PAD
    ass_path.write_text(ASS_HEADER + "\n".join(events) + "\n", encoding="utf-8")
    return ncues


def build_short(short_id, scene_ids, is_teaser):
    work = BASE / "shorts" / "_work"
    work.mkdir(parents=True, exist_ok=True)

    # 길이 맞추기(마지막 씬 트림). 예고형은 끝카드 시간을 빼고 계산.
    budget = (TEASER_MAX - ENDCARD_SEC) if is_teaser else COMPLETE_MAX
    play_durs = {s: ADUR[s] for s in scene_ids}
    total = sum(play_durs.values()) + PAD * len(scene_ids)
    if total > budget:
        last = scene_ids[-1]
        play_durs[last] = max(4.0, play_durs[last] - (total - budget))

    scene_files = []
    for sid in scene_ids:
        f = work / f"{short_id}_{sid}.mp4"
        build_scene_9x16(sid, play_durs[sid], f)
        scene_files.append(f)
    if is_teaser:
        ec = work / f"{short_id}_endcard.mp4"
        build_endcard(scene_ids[-1], ec)
        scene_files.append(ec)

    ass = work / f"{short_id}.ass"
    ncues = build_ass(scene_ids, play_durs, ass)

    concat = work / f"{short_id}_concat.txt"
    concat.write_text("\n".join(f"file '{p.as_posix()}'" for p in scene_files), encoding="utf-8")
    joined = work / f"{short_id}_joined.mp4"
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", str(joined)])

    subbed = work / f"{short_id}_subbed.mp4"
    run([FFMPEG, "-y", "-i", joined.relative_to(BASE).as_posix(),
         "-vf", f"subtitles={ass.relative_to(BASE).as_posix()}:fontsdir=.",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "copy", "-threads", "2",
         str(subbed)], cwd=str(BASE))

    out = BASE / "shorts" / f"{short_id}.mp4"
    dur = float(subprocess.run([FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(subbed)], capture_output=True, text=True).stdout.strip())
    fade_st = max(0.0, dur - FINAL_FADE)
    run([FFMPEG, "-y", "-i", str(subbed), "-stream_loop", "-1", "-i", str(BGM),
         "-filter_complex",
         f"[1:a]volume={BGM_VOLUME}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[mix];"
         f"[mix]afade=t=out:st={fade_st:.2f}:d={FINAL_FADE}[aout];"
         f"[0:v]fade=t=out:st={fade_st:.2f}:d={FINAL_FADE}[vout]",
         "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-threads", "2", str(out)])
    return out, dur, ncues


def tale_name():
    # 폴더명 "말리와_여우와_학" → 본편 제목 "말리와 여우와 학"
    return BASE.name.replace("_", " ")


def short_name():
    return tale_name().replace("말리와 ", "")


def write_metadata(short_id, kind, scene_ids, dur, path):
    tale, name = tale_name(), short_name()
    if kind == "complete":
        titles = [f"{name}, 이 장면만 봐도 돼요 💛", f"1분 순삭! {name} 이야기", f"말리가 들려주는 {name} 🐾"]
        desc = f"'{tale}' 이야기의 핵심 장면을 짧게 담았어요. 따뜻한 동화 한 편, 지금 바로 만나보세요!"
    else:
        titles = [f"{name}, 결말이 궁금하다면? 👀", f"{name}… 과연 어떻게 됐을까?", f"이다음이 진짜예요! {name}"]
        desc = f"'{tale}'에서 가장 궁금한 순간! 전체 이야기는 말리의 동화나라 채널에서 확인하세요."
    tags = ["#말리동화", "#전래동화", "#동화", "#shorts", f"#{name.replace(' ', '')}"]
    lines = [
        f"[쇼츠 유형] {kind}",
        f"[사용된 본편 제목] {tale}",
        f"[영상 길이] {dur:.1f}초",
        f"[사용한 장면] {', '.join(scene_ids)}",
        "",
        "[추천 제목 3개]",
        *[f"  {i+1}. {t}" for i, t in enumerate(titles)],
        "",
        "[영상 설명]",
        f"  {desc}",
        "",
        f"[해시태그] {' '.join(tags)}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_long():
    """요청 폴더구조(long/) 충족용: 기존 완성본·썸네일을 복사(원본 플랫 파일은 그대로 둠)."""
    import shutil
    longd = BASE / "long"
    longd.mkdir(exist_ok=True)
    finals = sorted(BASE.glob("✅*_final.mp4"))
    if finals:
        shutil.copy(finals[0], longd / "long_video.mp4")
    thumb = BASE / "thumbnail.png"
    if thumb.exists():
        shutil.copy(thumb, longd / "thumbnail.png")


if __name__ == "__main__":
    (BASE / "shorts").mkdir(exist_ok=True)
    if not FONT.exists():
        sys.exit("font.ttf 없음 — compose.py 와 같은 폰트가 폴더에 있어야 함")

    s1 = SHORT1_SCENES or pick_complete()
    s2 = SHORT2_SCENES or pick_teaser()
    print(f"[선정] complete = {s1}  ({sum(ADUR[s] for s in s1):.1f}s 원본)")
    print(f"[선정] teaser   = {s2}  ({sum(ADUR[s] for s in s2):.1f}s 원본)")

    o1, d1, c1 = build_short("short_01_complete", s1, is_teaser=False)
    write_metadata("short_01_complete", "complete", s1, d1, BASE / "shorts" / "short_01_metadata.txt")
    print(f"[완료] {o1.name}  {d1:.1f}s  자막 {c1}큐")

    o2, d2, c2 = build_short("short_02_teaser", s2, is_teaser=True)
    write_metadata("short_02_teaser", "teaser", s2, d2, BASE / "shorts" / "short_02_metadata.txt")
    print(f"[완료] {o2.name}  {d2:.1f}s  자막 {c2}큐")

    copy_long()
    print("SHORTS DONE")
