# 강의 CH2-2 — 글자 카드 + 화면 카드 로컬 렌더 (무료). 1920x1080 RGBA 오버레이 → cards/*.png
# 템플릿 = CH2-1 render_cards.py (도우미 그대로, 카드 함수만 이 편 것). 화면 카드:
#   - 터미널(T): 직접 쓴 줄(이 PC 실측 + pymanager 공식 소스 + winget 실제 패키지 정보)을 칸 단위로 그림
#   - 캡처(W01·W06): 헤드리스 크롬 실제 캡처 / W02·W03·W04·W08: Windows 창 재현 그림 (2026-10-30 3안, PC 조작 없음)
#   - 번호 동그라미 + 빨간 테두리 + 아래 확대 띠. 아래 18%(y>885)는 자막, 왼쪽 아래(x<300, y>560)는 작은 화면 자리.
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).parent
OUT = BASE / "cards"
OUT.mkdir(exist_ok=True)
SCR = BASE / "screens"
SNAP = SCR / "snapshots"
W, H = 1920, 1080
TITLE_FONT = str(BASE / "font.ttf")
BODY_FONT = "C:/Windows/Fonts/malgunbd.ttf"

CREAM, INK, MUTED = (255, 250, 238, 238), (45, 52, 46), (110, 118, 108)
GREEN, RED, GOLD = (59, 122, 76), (210, 63, 54), (190, 140, 30)
GREEN_SOFT, RED_SOFT = (227, 240, 226), (251, 231, 228)
BLUE, ORANGE = (52, 101, 164), (205, 120, 30)
BLUE_SOFT, ORANGE_SOFT, GOLD_SOFT = (225, 235, 248), (252, 236, 214), (250, 240, 205)
HL = (235, 50, 50)  # 화면 강조 빨강


def tf(size):
    return ImageFont.truetype(TITLE_FONT, size)


def bf(size):
    return ImageFont.truetype(BODY_FONT, size)


def kk(text):
    return text.replace("·", "ㆍ")


def panel(box=(330, 90, 1830, 860)):
    """그림자 있는 크림색 둥근 판."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([box[0] + 8, box[1] + 14, box[2] + 8, box[3] + 14], 46, fill=(60, 50, 30, 70))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, 46, fill=CREAM, outline=(225, 210, 180, 255), width=4)
    return img, d


def badge(d, cx, cy, n, color=GREEN, r=44):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline="white", width=4)
    f = bf(int(r * 1.15))
    w = d.textlength(str(n), font=f)
    d.text((cx - w / 2, cy - r * 0.78), str(n), font=f, fill="white")


def check(d, x, y, s=40, color=GREEN, width=9):
    d.line([(x, y + s * 0.55), (x + s * 0.38, y + s * 0.92), (x + s, y)], fill=color, width=width, joint="curve")


def cross(d, cx, cy, s=26, color=RED, width=10):
    d.line([(cx - s, cy - s), (cx + s, cy + s)], fill=color, width=width)
    d.line([(cx - s, cy + s), (cx + s, cy - s)], fill=color, width=width)


def save(img, name):
    img.save(OUT / f"{name}.png")
    print(name)


def center(d, y, text, font, fill=INK, cx=1080):  # 판이 오른쪽으로 비켜 있으므로 판 가운데 기준
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)


def fit(im, w=None, h=None):
    k = min(w / im.width, h / im.height) if (w and h) else (w / im.width if w else h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


# ---------- 화면 공통 ----------
WIN = (330, 30, 1830, 790)  # 화면 창 자리 (아래 795~880 = 확대 띠)


def shadow_base():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([WIN[0] + 6, WIN[1] + 12, WIN[2] + 6, WIN[3] + 12], 18, fill=(30, 25, 15, 110))
    return Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(16)))


def hl_box(d, box, n=None, side="left", width=7):
    """빨간 둥근 테두리 + 번호 동그라미."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 - 8, y0 - 6, x1 + 8, y1 + 6], 12, outline=HL, width=width)
    if n is not None:
        cx = x0 - 8 - 34 if side == "left" else x1 + 8 + 34
        cx = max(WIN[0] + 10, min(cx, WIN[2] - 10)) if side == "inside" else cx
        badge(d, cx, (y0 + y1) / 2, n, HL, 30)


def band(d, text, font=None, label=None, color=INK, fill=(255, 250, 238, 245)):
    """아래 확대 띠 (y 800~878)."""
    font = font or bf(44)
    d.rounded_rectangle([WIN[0], 800, WIN[2], 878], 22, fill=fill, outline=HL, width=4)
    x = WIN[0] + 28
    if label:
        lf = bf(30)
        lw = d.textlength(label, font=lf)
        d.rounded_rectangle([x, 815, x + lw + 32, 863], 18, fill=HL)
        d.text((x + 16, 819), label, font=lf, fill="white")
        x += lw + 56
    d.text((x, 812), text, font=font, fill=color)


def chip(d, text, x, y, bg=(255, 214, 90, 250), fg=INK, size=36):
    f = bf(size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + w + 40, y + size + 26], (size + 26) // 2, fill=bg, outline=(120, 90, 20, 200), width=3)
    d.text((x + 20, y + 9), text, font=f, fill=fg)
    return x + w + 40


def blur_box(im, box, r=14):
    reg = im.crop(box).filter(ImageFilter.GaussianBlur(r))
    im.paste(reg, box[:2])


# ---------- 터미널 그리기 ----------
F_MONO = "C:/Windows/Fonts/consola.ttf"
F_MONO_B = "C:/Windows/Fonts/consolab.ttf"
F_SYM = "C:/Windows/Fonts/seguisym.ttf"
F_KO = "C:/Windows/Fonts/malgun.ttf"
F_EMOJI = "C:/Windows/Fonts/seguiemj.ttf"
_CMAP = {}


def has_glyph(path, ch):
    if path not in _CMAP:
        from fontTools.ttLib import TTFont
        _CMAP[path] = TTFont(path).getBestCmap()
    return ord(ch) in _CMAP[path]


TERM_BG, TERM_FG = (12, 12, 12), (204, 204, 204)
ANSI = {"black": (12, 12, 12), "red": (231, 72, 86), "green": (22, 198, 12), "brown": (193, 156, 0),
        "yellow": (249, 241, 165), "blue": (59, 120, 255), "magenta": (180, 0, 158), "cyan": (97, 214, 214),
        "white": (204, 204, 204), "brightblack": (118, 118, 118), "brightred": (231, 72, 86),
        "brightgreen": (22, 198, 12), "brightyellow": (249, 241, 165), "brightblue": (59, 120, 255),
        "brightmagenta": (180, 0, 158), "brightcyan": (97, 214, 214), "brightwhite": (242, 242, 242)}


def col(c, default):
    if c in (None, "default"):
        return default
    if isinstance(c, tuple):
        return c
    if c in ANSI:
        return ANSI[c]
    if len(c) == 6:
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return default


def wide(ch):
    o = ord(ch)
    return 0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or 0xAC00 <= o <= 0xD7A3 or 0xF900 <= o <= 0xFAFF \
        or 0xFF00 <= o <= 0xFF60 or 0x1F300 <= o <= 0x1FAFF or o in (0x2705,)


def snap_rows(n, rows=None, cols=None, replace=()):
    """스냅숏 → 줄 목록. 줄 = [(글자, 앞색, 뒤색, 굵게), ...] (넓은 글자 다음 빈칸은 뺌)."""
    data = json.loads((SNAP / f"{n:03d}.json").read_text(encoding="utf-8"))["rows"]
    out = []
    for y in (rows if rows is not None else range(len(data))):
        line = [tuple(c) for c in data[y][:cols]]
        cells, skip = [], False
        for ch, fg, bg, bold in line:
            if skip:
                skip = False
                continue
            cells.append((ch or " ", fg, bg, bold))
            if ch and wide(ch):
                skip = True
        txt = "".join(c[0] for c in cells)
        for a, b in replace:  # 같은 줄 안 글자 바꾸기 (색은 바뀌는 첫 칸 색을 따름)
            i = txt.find(a)
            while i >= 0:
                st = cells[i]
                cells[i:i + len(a)] = [(ch, st[1], st[2], st[3]) for ch in b]
                txt = "".join(c[0] for c in cells)
                i = txt.find(a, i + len(b))
        out.append(cells)
    return out


def text_rows(lines):
    """직접 쓴 줄: [ [(텍스트, 색), ...] 또는 "텍스트" ] → 칸 목록."""
    out = []
    for ln in lines:
        segs = [(ln, None)] if isinstance(ln, str) else ln
        cells = []
        for t, c in segs:
            for ch in t:
                cells.append((ch, c, None, False))
        out.append(cells)
    return out


def draw_cell(d, img, x, y, ch, cw, lh, fsize, fg, bold):
    if ch == " ":
        return
    w2 = wide(ch)
    if ord(ch) >= 0x1F300 or ch == "✅":
        f = ImageFont.truetype(F_EMOJI, int(fsize * 0.9))
        try:
            d.text((x + 1, y + lh * 0.12), ch, font=f, embedded_color=True)
        except Exception:
            d.text((x + 1, y + lh * 0.12), ch, font=f, fill=fg)
        return
    if 0xAC00 <= ord(ch) <= 0xD7A3 or 0x3130 <= ord(ch) <= 0x318F:
        f = ImageFont.truetype(F_KO, int(fsize * 1.0))
        d.text((x + (cw * 2 - d.textlength(ch, font=f)) / 2, y + lh * 0.08), ch, font=f, fill=fg)
        return
    path = (F_MONO_B if bold else F_MONO) if has_glyph(F_MONO, ch) else F_SYM if has_glyph(F_SYM, ch) else F_KO
    if 0x2580 <= ord(ch) <= 0x259F:  # 블록 문자는 칸을 꽉 채우도록 직접 그림
        o = ord(ch)
        if o == 0x2588:
            d.rectangle([x, y, x + cw, y + lh], fill=fg)
            return
        if o in (0x2591, 0x2592, 0x2593):
            a = {0x2591: 0.25, 0x2592: 0.5, 0x2593: 0.75}[o]
            d.rectangle([x, y, x + cw, y + lh], fill=tuple(int(TERM_BG[i] + (fg[i] - TERM_BG[i]) * a) for i in range(3)))
            return
        quads = {0x2580: "ab", 0x2584: "cd", 0x258C: "ac", 0x2590: "bd", 0x2596: "c", 0x2597: "d", 0x2598: "a",
                 0x259D: "b", 0x259B: "abc", 0x259C: "abd", 0x2599: "acd", 0x259F: "bcd", 0x259A: "ad", 0x259E: "bc"}
        if o in quads:
            hx, hy = cw / 2, lh / 2
            pos = {"a": (0, 0), "b": (hx, 0), "c": (0, hy), "d": (hx, hy)}
            for q in quads[o]:
                px, py = pos[q]
                d.rectangle([x + px, y + py, x + px + hx, y + py + hy], fill=fg)
            return
        if o == 0x258E:  # ▎
            d.rectangle([x, y, x + cw * 0.25, y + lh], fill=fg)
            return
    f = ImageFont.truetype(path, fsize)
    d.text((x, y + lh * 0.1), ch, font=f, fill=fg)


def terminal(rows, title="Windows PowerShell", fsize=34, pad=(30, 22), cursor=None, box=WIN, hl=(), mono_w=0.55):
    """Windows 터미널 창 + 줄 렌더. hl = [(줄, 칸시작, 칸끝, 번호, 쪽)] → 화면 좌표 사각형 목록도 돌려줌."""
    img = shadow_base()
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 16, fill=TERM_BG + (255,), outline=(70, 70, 70, 255), width=2)
    # 제목 막대 (Windows 터미널 탭 모양)
    d.rounded_rectangle([x0, y0, x1, y0 + 58], 16, fill=(32, 32, 32, 255))
    d.rectangle([x0, y0 + 40, x1, y0 + 58], fill=(32, 32, 32, 255))
    d.rounded_rectangle([x0 + 14, y0 + 10, x0 + 420, y0 + 58], 10, fill=TERM_BG + (255,))
    d.rectangle([x0 + 14, y0 + 40, x0 + 420, y0 + 58], fill=TERM_BG + (255,))
    # 파워셸 아이콘
    d.rounded_rectangle([x0 + 30, y0 + 22, x0 + 54, y0 + 46], 5, fill=(1, 36, 86))
    d.line([(x0 + 35, y0 + 27), (x0 + 43, y0 + 34), (x0 + 35, y0 + 41)], fill="white", width=3)
    d.text((x0 + 66, y0 + 18), title, font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 24), fill=(235, 235, 235))
    d.text((x0 + 380, y0 + 16), "×", font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26), fill=(200, 200, 200))
    d.text((x0 + 440, y0 + 12), "+", font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 30), fill=(200, 200, 200))
    sf = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
    for i, s in enumerate(["—", "☐", "✕"]):
        d.text((x1 - 170 + i * 58, y0 + 14), s, font=ImageFont.truetype(F_SYM, 24), fill=(220, 220, 220))
    cw, lh = fsize * mono_w, fsize * 1.32
    tx, ty = x0 + pad[0], y0 + 58 + pad[1]
    for r, cells in enumerate(rows):
        cx = tx
        for ch, fg, bg, bold in cells:
            wch = 2 if wide(ch) else 1
            if bg not in (None, "default"):
                d.rectangle([cx, ty + r * lh, cx + cw * wch, ty + (r + 1) * lh], fill=col(bg, TERM_BG))
            draw_cell(d, img, cx, ty + r * lh, ch, cw, lh, fsize, col(fg, TERM_FG), bold)
            cx += cw * wch
    if cursor:
        r, c = cursor
        d.rectangle([tx + c * cw, ty + r * lh + lh * 0.15, tx + c * cw + cw, ty + (r + 1) * lh - lh * 0.1], fill=(204, 204, 204))
    boxes = []
    for r, c0, c1, n, side in hl:
        b = (tx + c0 * cw, ty + r * lh, tx + c1 * cw, ty + (r + 1) * lh)
        hl_box(d, b, n, side)
        boxes.append(b)
    return img, d


def capture_card(src, crop, hl=(), blur=(), title=None, box=WIN, url=None):
    """실제 캡처를 창 자리에 맞춰 붙이고 강조. hl·blur 좌표 = 원본 캡처 좌표."""
    im = Image.open(SCR / src).convert("RGB")
    for b in blur:
        blur_box(im, b)
    im = im.crop(crop)
    top = 0
    img = shadow_base()
    d = ImageDraw.Draw(img)
    bw, bh = box[2] - box[0], box[3] - box[1]
    if url:  # 크롬 주소창 모양
        top = 64
    k = min(bw / im.width, (bh - top) / im.height)
    sim = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    ox = box[0] + (bw - sim.width) // 2
    oy = box[1] + top + (bh - top - sim.height) // 2
    if url:
        d.rounded_rectangle([ox, oy - top, ox + sim.width, oy + 4], 14, fill=(223, 225, 229, 255))
        d.rounded_rectangle([ox + 150, oy - top + 12, ox + sim.width - 120, oy - 10], 18, fill=(255, 255, 255, 255))
        d.text((ox + 24, oy - top + 12), "←  →  ⟳", font=ImageFont.truetype(F_SYM, 28), fill=(90, 90, 90))
        d.text((ox + 178, oy - top + 15), url, font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26), fill=(32, 33, 36))
    mask = Image.new("L", sim.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sim.width - 1, sim.height - 1], 12, fill=255)
    img.paste(sim, (ox, oy), mask)
    d = ImageDraw.Draw(img)
    rects = []
    for item in hl:
        (bx0, by0, bx1, by1), n, side = item
        r = (ox + (bx0 - crop[0]) * k, oy + (by0 - crop[1]) * k, ox + (bx1 - crop[0]) * k, oy + (by1 - crop[1]) * k)
        hl_box(d, r, n, side)
        rects.append(r)
    return img, d, (ox, oy, k)



IMGS = BASE / "images"


def emoji(d, xy, ch, size):
    f = ImageFont.truetype(F_EMOJI, size)
    try:
        d.text(xy, ch, font=f, embedded_color=True)
    except Exception:
        d.text(xy, ch, font=f, fill=INK)


def code_box(d, x, y, text, size=44, fg=(240, 240, 240)):
    f = ImageFont.truetype(F_MONO_B, size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + w + 40, y + size + 28], 14, fill=(30, 30, 30))
    d.text((x + 20, y + 12), text, font=f, fill=fg)
    return x + w + 40


# ---------- 글자 카드 ----------
def title_card():
    img, d = panel((420, 250, 1740, 700))
    center(d, 300, "CHAPTER 2 ㆍ 2강", bf(44), MUTED)
    center(d, 385, kk("Python · FFmpeg · Git"), tf(100), GREEN)
    center(d, 525, "설치", tf(86), INK)
    save(img, "title")


def ch2_map(hi=2, name="K01"):
    img, d = panel((360, 90, 1800, 860))
    center(d, 125, kk("CHAPTER 2 ㆍ 도구 세팅 지도"), tf(72), GREEN)
    items = ["Claude Code 설치와 로그인", "Python ㆍ FFmpeg ㆍ Git 설치", "Gemini API 키 발급", "Whisper 첫 받아쓰기", "프로젝트 폴더 구조"]
    for i, t in enumerate(items, 1):
        y = 250 + (i - 1) * 118
        on = i == hi
        d.rounded_rectangle([460, y, 1700, y + 96], 30, fill=(GOLD_SOFT if on else (255, 255, 255)) + (255,),
                            outline=(GOLD if on else (220, 210, 190)), width=6 if on else 3)
        badge(d, 525, y + 48, i, GOLD if on else GREEN, 34)
        d.text((590, y + 18), t, font=bf(52 if on else 46), fill=INK if on else MUTED)
        if i < hi:
            check(d, 1600, y + 24, 46, GREEN, 10)
        if on:
            chip(d, "오늘" if hi == 2 else "다음 시간", 1450, y + 18, size=32)
    save(img, name)


TOOLS = [("Python", "일꾼의 손", "프로그램 실행", "🧤", BLUE, BLUE_SOFT),
         ("FFmpeg", "가위와 풀", "그림 + 소리 → 영상", "✂️", ORANGE, ORANGE_SOFT),
         ("Git", "사진첩", "어제로 되돌리기", "📔", GREEN, GREEN_SOFT)]


def tools(k, name):
    """연장 3개. k = 지금 말하는 연장 (1~3), 앞 것은 보이고 뒤 것은 흐리게."""
    img, d = panel((330, 90, 1830, 860))
    center(d, 120, kk("오늘 챙길 연장 3개"), tf(70), GREEN)
    for i, (head, nick, job, em, c, soft) in enumerate(TOOLS, 1):
        x = 390 + (i - 1) * 485
        a = 255 if i <= k else 90
        on = i == k
        d.rounded_rectangle([x, 240, x + 445, 820], 36, fill=soft + (a,), outline=c + (a,), width=8 if on else 4)
        if i <= k:
            emoji(d, (x + 152, 270), em, 120)
        d.text((x + 222 - d.textlength(head, font=bf(62)) / 2, 440), head, font=bf(62), fill=c + (a,))
        d.text((x + 222 - d.textlength(nick, font=bf(54)) / 2, 545), nick, font=bf(54), fill=INK + (a,))
        d.text((x + 222 - d.textlength(job, font=bf(36)) / 2, 650), job, font=bf(36), fill=MUTED + (a,))
    save(img, name)


def ffmpeg_detail():
    img, d = panel((330, 110, 1830, 840))
    center(d, 140, kk("FFmpeg = 영상 가위와 풀"), tf(70), ORANGE)
    for x, em, t in [(470, "🖼️", "그림"), (820, "🔊", "목소리"), (1330, "🎬", "영상 한 편")]:
        emoji(d, (x, 300), em, 140)
        d.text((x + 85 - d.textlength(t, font=bf(48)) / 2, 490), t, font=bf(48), fill=INK)
    d.text((705, 330), "+", font=bf(110), fill=MUTED)
    d.text((1100, 320), "→", font=ImageFont.truetype(F_SYM, 120), fill=ORANGE)
    chip(d, "자막 ㆍ 음악도 입혀 줘요", 830, 650, bg=ORANGE_SOFT + (250,), size=44)
    save(img, "K02f")


def git_detail():
    img, d = panel((330, 110, 1830, 840))
    center(d, 140, kk("Git = 작업 사진첩"), tf(70), GREEN)
    steps = [("📷", "어제 찍어 둔 사진", GREEN), ("😵", "오늘 엉망이 됐어요", RED), ("↩️", "어제로 되돌리기", GREEN)]
    for i, (em, t, c) in enumerate(steps):
        x = 420 + i * 470
        d.rounded_rectangle([x, 270, x + 400, 700], 36, fill=(255, 255, 255, 255), outline=c, width=6)
        emoji(d, (x + 130, 320), em, 130)
        d.text((x + 200 - d.textlength(t, font=bf(42)) / 2, 540), t, font=bf(42), fill=INK)
        if i < 2:
            d.polygon([(x + 410, 470), (x + 460, 485), (x + 410, 500)], fill=GOLD)
    save(img, "K02g")


def winget_card():
    img, d = panel((330, 100, 1830, 850))
    center(d, 130, kk("심부름꾼 winget (윙겟)"), tf(70), GREEN)
    d.rounded_rectangle([400, 270, 1060, 760], 36, fill=RED_SOFT + (255,), outline=RED, width=6)
    emoji(d, (650, 300), "🚶", 130)
    center(d, 480, "가게에 직접 가서", bf(48), INK, cx=730)
    center(d, 550, "찾고 ㆍ 받고 ㆍ 설치", bf(44), MUTED, cx=730)
    cross(d, 730, 680, 34, RED, 13)
    d.rounded_rectangle([1100, 270, 1760, 760], 36, fill=GREEN_SOFT + (255,), outline=GREEN, width=6)
    emoji(d, (1360, 300), "💬", 130)
    center(d, 480, "이름 한 줄만 말하면", bf(48), INK, cx=1430)
    code_box(d, 1170, 560, "winget install ○○○", 40)
    d.ellipse([1400, 660, 1460, 720], outline=GREEN, width=10)
    save(img, "K04")


def today_order():
    img, d = panel((360, 110, 1800, 840))
    center(d, 145, kk("오늘 순서"), tf(78), GREEN)
    for i, (t, sub) in enumerate([("Python", "python.org"), ("FFmpeg", "winget"), ("Git", "winget"), ("세 줄 점검", "새 창에서")], 1):
        x = 430 + (i - 1) * 340
        d.rounded_rectangle([x, 300, x + 300, 610], 36, fill=(255, 255, 255, 255), outline=GREEN, width=5)
        badge(d, x + 150, 370, i, GREEN, 46)
        d.text((x + 150 - d.textlength(t, font=bf(46)) / 2, 450), t, font=bf(46), fill=INK)
        d.text((x + 150 - d.textlength(sub, font=bf(34)) / 2, 530), sub, font=bf(34), fill=MUTED)
        if i < 4:
            d.polygon([(x + 308, 450), (x + 332, 465), (x + 308, 480)], fill=GOLD)
    chip(d, "Mac 은 마지막에 한 번에 정리!", 1180, 690, bg=(225, 235, 248, 250), size=36)
    save(img, "K03")


def dashes():
    img, d = panel((360, 110, 1800, 840))
    center(d, 140, kk("빼기(-) 개수 확인"), tf(76), GREEN)
    for i, (c, n) in enumerate([("python --version", "빼기 2개"), ("ffmpeg -version", "빼기 1개"), ("git --version", "빼기 2개")]):
        y = 290 + i * 160
        code_box(d, 470, y, c, 58)
        chip(d, n, 1330, y + 8, bg=(GOLD_SOFT if "1" in n else (255, 255, 255)) + (250,), size=44)
    chip(d, "틀려도 빨간 글자뿐! 다시 치면 돼요", 860, 760, bg=GREEN_SOFT + (250,), size=36)
    save(img, "K05")


def judge(which):
    """심사위원 말리 O/X. which = a(Python O) / b(FFmpeg 오류 X) / c(Git O + 합격)."""
    img, d = panel((330, 90, 1830, 860))
    center(d, 115, kk("심사위원 말리의 판정"), tf(66), GREEN)
    box = (380, 230, 1180, 790)
    d.rounded_rectangle(box, 18, fill=TERM_BG + (255,), outline=(70, 70, 70, 255), width=2)
    mf = ImageFont.truetype(F_MONO, 30)
    kf = ImageFont.truetype(F_KO, 27)
    lines = {"a": [("PS> python --version", TERM_FG), ("Python 3.14.10", (242, 242, 242))],
             "b": [("PS> ffmpeg -version", TERM_FG)] + [(ln, ERR) for ln in FF_ERR[:3]],
             "c": [("PS> git --version", TERM_FG), ("git version 2.56.0.windows.3", (242, 242, 242))]}[which]
    y = 260
    for t, c in lines:
        f = kf if any(0xAC00 <= ord(ch) <= 0xD7A3 for ch in t) else mf
        while d.textlength(t, font=f) > box[2] - box[0] - 50:  # 긴 오류 줄은 판 너비에 맞춰 접기
            cut = len(t)
            while d.textlength(t[:cut], font=f) > box[2] - box[0] - 50:
                cut -= 1
            d.text((box[0] + 25, y), t[:cut], font=f, fill=c)
            t, y = t[cut:], y + 44
        d.text((box[0] + 25, y), t, font=f, fill=c)
        y += 52
    p = Image.open(IMGS / "P08.png").convert("RGB")
    p = fit(p.crop((330, 60, 1060, 768)), h=430)
    img.paste(p, (1240, 250))
    d = ImageDraw.Draw(img)
    cx, cy = 1240 + p.width // 2, 300 + p.height
    ok = which != "b"
    d.ellipse([cx - 70, cy - 40, cx + 70, cy + 100], fill="white", outline=GREEN if ok else RED, width=5)
    if ok:
        d.ellipse([cx - 45, cy - 15, cx + 45, cy + 75], outline=GREEN, width=14)
    else:
        cross(d, cx, cy + 30, 38, RED, 15)
    if which == "c":
        d.rounded_rectangle([560, 680, 1000, 760], 38, fill=RED_SOFT + (255,), outline=RED, width=6)
        center(d, 690, "세 줄 모두 합격!", bf(48), RED, cx=780)
    save(img, f"K06{which}")


def stuck(k):
    img, d = panel((330, 70, 1830, 870))
    center(d, 95, kk("막혔을 때 네 가지"), tf(70), GREEN)
    rows = [("'인식할 수 없습니다'", "창을 닫고 새로 열기"),
            ("python 을 쳤더니 Store 가 열림", "install manager 부터 설치"),
            ("'Python launcher 를 지우라'는 경고", "설정 > 앱 > 설치된 앱에서 제거"),
            ("'winget' 이 없다고 나옴", "Store 에서 '앱 설치 관리자' 업데이트")]
    for i, (a, b) in enumerate(rows, 1):
        y = 200 + (i - 1) * 162
        on = i == k
        alpha = 255 if i <= k else 110
        d.rounded_rectangle([400, y, 1760, y + 145], 30, fill=((255, 255, 255) if on else (250, 246, 236)) + (alpha,),
                            outline=(GOLD if on else (220, 210, 190)) + (alpha,), width=6 if on else 3)
        badge(d, 455, y + 72, i, (GOLD if on else GREEN), 30)
        d.text((510, y + 14), a, font=bf(42), fill=(RED if i <= k else MUTED) + (alpha,))
        d.text((540, y + 80), "→  " + b, font=bf(40), fill=(GREEN if i <= k else MUTED) + (alpha,))
    save(img, f"K07_{k}")


def mac_card():
    img, d = panel((330, 70, 1830, 870))
    center(d, 95, kk("Mac 한 장 요약"), tf(72), GREEN)
    rows = [("심부름꾼 Homebrew 설치 — brew.sh 의 설치 명령 붙여넣기", None),
            ("세 가지를 한 번에 설치", "brew install python@3.14 ffmpeg git"),
            ("터미널을 새로 열고 버전 확인", "python3.14 --version"),
            (None, "ffmpeg -version     git --version")]
    y = 215
    for i, (a, b) in enumerate(rows, 1):
        if a:
            badge(d, 440, y + 34, i, GREEN, 32)
            d.text((495, y + 6), a, font=bf(40), fill=INK)
            y += 78
        if b:
            code_box(d, 495, y - 4, b, 40)
            y += 98
        else:
            y += 20
    chip(d, "Mac 화면은 맥에서 확인 후 보완 예정", 1080, 770, bg=(225, 235, 248, 250), size=30)
    save(img, "K08")


def end_card():
    img, d = panel((420, 230, 1740, 720))
    center(d, 280, "CHAPTER 2 ㆍ 2강 끝", bf(46), MUTED)
    center(d, 360, kk("Python · FFmpeg · Git 설치"), tf(84), GREEN)
    d.line([(680, 560), (1480, 560)], fill=(225, 210, 180), width=3)
    center(d, 600, "다음 강의 ▶ Gemini API 키 발급", bf(50), INK)
    save(img, "end")


# ---------- 웹 실제 캡처 (헤드리스 크롬 1280x800) ----------
def w01():
    img, d, _ = capture_card("W01_raw.png", (0, 0, 1280, 800), url="python.org/downloads",
                             hl=[((170, 244, 672, 282), 1, "left"), ((171, 291, 424, 331), 2, "left")])
    band(d, "Download Python install manager  =  설치 도우미 받기", label="Python")
    save(img, "W01")


def w06():
    img, d, _ = capture_card("W06_raw.png", (150, 80, 1130, 800), url="git-scm.com/install/windows",
                             hl=[((446, 566, 838, 588), 1, "right")])
    band(d, "winget 칸의 빨간 글씨 한 줄을 복사", label="Git")
    save(img, "W06")


# ---------- Windows 창 재현 그림 (2026-10-30 3안: PC 조작 없음) ----------
F_UI = "C:/Windows/Fonts/malgun.ttf"
F_UIB = "C:/Windows/Fonts/malgunbd.ttf"


def ui(size, bold=False):
    return ImageFont.truetype(F_UIB if bold else F_UI, size)


def py_logo(d, x, y, s=60):
    d.rounded_rectangle([x, y, x + s * 0.62, y + s * 0.62], s * 0.14, fill=(55, 118, 171))
    d.rounded_rectangle([x + s * 0.38, y + s * 0.38, x + s, y + s], s * 0.14, fill=(255, 212, 59))
    d.ellipse([x + s * 0.12, y + s * 0.1, x + s * 0.22, y + s * 0.2], fill="white")
    d.ellipse([x + s * 0.78, y + s * 0.8, x + s * 0.88, y + s * 0.9], fill="white")


def win_frame(title, box=(430, 50, 1730, 780)):
    img = shadow_base()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, 14, fill=(243, 243, 243, 255), outline=(180, 180, 180, 255), width=2)
    d.text((box[0] + 26, box[1] + 12), title, font=ui(26), fill=(30, 30, 30))
    for i, s in enumerate(["—", "☐", "✕"]):
        d.text((box[2] - 170 + i * 58, box[1] + 12), s, font=ImageFont.truetype(F_SYM, 24), fill=(60, 60, 60))
    return img, d


def redraw_note(d):
    chip(d, "화면 모양을 다시 그린 그림", 1430, 682, bg=(235, 235, 235, 240), size=26)


def w02():
    img, d = win_frame("", (560, 150, 1600, 700))
    py_logo(d, 620, 230, 110)
    d.text((770, 230), "Python install manager", font=ui(52, True), fill=(30, 30, 30))
    d.text((772, 310), "게시자: Python Software Foundation", font=ui(30), fill=(90, 90, 90))
    b = (1330, 600, 1560, 668)
    d.rounded_rectangle(b, 8, fill=(0, 95, 184))
    d.text((b[0] + 115 - d.textlength("설치", font=ui(32, True)) / 2, b[1] + 12), "설치", font=ui(32, True), fill="white")
    hl_box(d, b, 1, "left")
    redraw_note(d)
    band(d, "받은 파일 열기  →  설치", label="Python")
    save(img, "W02")


def w03():
    img = shadow_base()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((560, 60, 1600, 780), 16, fill=(36, 36, 40, 255), outline=(90, 90, 90, 255), width=2)
    d.rounded_rectangle([600, 95, 1560, 160], 30, fill=(56, 56, 60), outline=(0, 120, 212), width=3)
    d.text((660, 105), "python install manager", font=ui(32), fill=(240, 240, 240))
    d.text((620, 200), "가장 일치하는 항목", font=ui(26, True), fill=(220, 220, 220))
    r = (610, 250, 1550, 360)
    d.rounded_rectangle(r, 10, fill=(60, 60, 66))
    py_logo(d, 640, 270, 70)
    d.text((740, 262), "Python install manager", font=ui(36, True), fill=(250, 250, 250))
    d.text((742, 312), "앱", font=ui(26), fill=(190, 190, 190))
    hl_box(d, r, 1, "left")
    redraw_note(d)
    band(d, "시작 버튼  →  python install manager 검색  →  실행", label="Python")
    save(img, "W03")


def w04():
    img, d = win_frame("설정")
    d.text((480, 110), "앱 > 설치된 앱", font=ui(46, True), fill=(30, 30, 30))
    d.rounded_rectangle([480, 190, 1100, 245], 8, fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    d.text((500, 197), "python", font=ui(30), fill=(30, 30, 30))
    rows = [("Python install manager", "Python Software Foundation"), ("Python Launcher", "Python Software Foundation")]
    for i, (a, b) in enumerate(rows):
        y = 280 + i * 120
        d.rounded_rectangle([480, y, 1680, y + 105], 8, fill=(251, 251, 251), outline=(225, 225, 225), width=1)
        py_logo(d, 505, y + 25, 54)
        d.text((585, y + 14), a, font=ui(32, True), fill=(30, 30, 30))
        d.text((587, y + 60), b, font=ui(24), fill=(110, 110, 110))
        d.text((1620, y + 25), "···", font=ui(34, True), fill=(60, 60, 60))
    hl_box(d, (480, 400, 1680, 505), 1, "left")
    d.rounded_rectangle((1430, 510, 1680, 640), 10, fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    d.text((1460, 522), "수정", font=ui(30), fill=(120, 120, 120))
    d.text((1460, 578), "제거", font=ui(30, True), fill=(30, 30, 30))
    hl_box(d, (1445, 572, 1665, 625), 2, "right")
    redraw_note(d)
    band(d, "Python Launcher  →  ···  →  제거", label="오래된 런처")
    save(img, "W04")


def w08():
    img, d = win_frame("Microsoft Store")
    d.rounded_rectangle([780, 110, 1380, 160], 24, fill=(255, 255, 255), outline=(210, 210, 210), width=2)
    d.text((810, 116), "앱, 게임, 영화 등 검색", font=ui(26), fill=(140, 140, 140))
    d.rounded_rectangle([500, 210, 1660, 640], 12, fill=(255, 255, 255), outline=(225, 225, 225), width=1)
    py_logo(d, 560, 270, 150)
    d.text((760, 280), "Python", font=ui(56, True), fill=(30, 30, 30))
    d.text((762, 360), "Python Software Foundation", font=ui(28), fill=(90, 90, 90))
    d.rounded_rectangle([760, 430, 1020, 495], 8, fill=(0, 95, 184))
    d.text((850, 440), "받기", font=ui(32, True), fill="white")
    hl_box(d, (1672, 56, 1722, 98), 1, "left")
    chip(d, "install manager 먼저!", 1150, 540, size=40)
    redraw_note(d)
    band(d, "오른쪽 위 X 로 창 닫기  →  install manager 부터 설치", label="스토어가 열렸다면")
    save(img, "W08")


# ---------- 터미널 화면 (문구 = 이 PC 실측 / pymanager 공식 소스 / winget 실제 패키지) ----------
PS = "PS C:\\Users\\malli> "
BANNER = ["Windows PowerShell", "Copyright (C) Microsoft Corporation. All rights reserved.", ""]
YEL = (249, 241, 165)
ERR = (231, 72, 86)
GRN = (22, 198, 12)
BLU = (59, 120, 255)
DIM = (118, 118, 118)
STARS = "*" * 80
FF_ERR = ["ffmpeg : 'ffmpeg' 용어가 cmdlet, 함수, 스크립트 파일 또는 실행할 수 있는 프로그램",
          "이름으로 인식되지 않습니다. 이름이 정확한지 확인하고 경로가 포함된 경우 경로가",
          "올바른지 검증한 다음 다시 시도하십시오."]
FOLLOW = "잠깐 멈추고 따라 해 보세요"


def cmd(c, rest=""):
    return [(PS, None), (c, YEL), (rest, None)]


def t01():
    rows = text_rows(BANNER + [cmd("winget", " --version"), "v1.12.350", "", PS])
    img, d = terminal(rows, fsize=40, cursor=(6, len(PS)),
                      hl=[(3, len(PS), len(PS) + 16, 1, "right"), (4, 0, 9, 2, "right")])
    band(d, "숫자가 나오면 심부름꾼 준비 완료", label="winget")
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T01")


def t03():
    rows = text_rows([
        [("Welcome to the Python installation manager configuration helper.", GRN)], "", [(STARS, BLU)], "",
        [("Windows is not configured to allow paths longer than 260 characters.", YEL)],
        [("Update setting now? [y/N] ", None), ("y", (242, 242, 242))], "", [(STARS, BLU)], "",
        [("The global shortcuts directory is not configured.", YEL)],
        [("Add commands directory to your PATH now? [y/N] ", None), ("y", (242, 242, 242))], "", [(STARS, BLU)], "",
        [("You do not have any Python runtimes installed.", YEL)],
        [("Install CPython now? [Y/n] ", None), ("n", (242, 242, 242))]])
    img, d = terminal(rows, title="Python install manager", fsize=27,
                      hl=[(5, 0, 27, 1, "right"), (10, 0, 48, 2, "right"), (15, 0, 28, 3, "right")])
    chip(d, "여기만 n!", 860, 632, bg=RED_SOFT + (250,), fg=RED, size=40)
    chip(d, "관리자 확인 창이 뜨면 '예'", 860, 282, bg=(226, 238, 255, 250), size=30)
    band(d, "[y/N] 질문엔 y   ㆍ   Install CPython now? 에만 n", label="설정 도우미")
    save(img, "T03")


def t04():
    rows = text_rows(BANNER + [cmd("py", " install 3.14"),
                               "The signature for https://www.python.org/ftp/python/index-windows.json was successfully verified.",
                               "Installing Python 3.14.10.",
                               [("Python 3.14.10 will be launched by ", None), ("python.exe", GRN), (".", None)], "", PS])
    img, d = terminal(rows, fsize=27, cursor=(8, len(PS)),
                      hl=[(3, len(PS), len(PS) + 15, 1, "right"), (6, 0, 47, 2, "right")])
    band(d, "python 명령으로 3.14 가 실행된다  =  설치 끝", label="Python 3.14")
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T04")


def t05():
    rows = text_rows(BANNER + [cmd("python", " --version"), "Python 3.14.10", "", PS])
    img, d = terminal(rows, fsize=40, cursor=(6, len(PS)),
                      hl=[(3, len(PS), len(PS) + 16, 1, "right"), (4, 0, 14, 2, "right")])
    band(d, "창을 닫고 새 창에서  →  Python 3.14 가 보이면 성공", label="새 창에서")
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T05")


def t06():
    rows = text_rows(BANNER + [cmd("winget", " install Gyan.FFmpeg")])
    img, d = terminal(rows, fsize=40, cursor=(3, len(PS) + 26), hl=[(3, len(PS) + 15, len(PS) + 26, 1, "right")])
    band(d, "Gyan.FFmpeg  — 대문자 G ㆍ F ㆍ F 그대로", label="FFmpeg")
    chip(d, "설명란에서 복사하면 편해요", 1300, 600, bg=(226, 238, 255, 250), size=34)
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T06")


def t06b():
    rows = text_rows(BANNER + [cmd("winget", " install Gyan.FFmpeg"),
                               "The `msstore` source requires that you view the following agreements before using.",
                               "Terms of Transaction: https://aka.ms/microsoft-store-terms-of-transaction",
                               "The source requires the current machine's 2-letter geographic region to be sent to the",
                               "backend service to function properly (ex. \"US\").", "",
                               "Do you agree to all the source agreements terms?",
                               [("[Y] Yes  [N] No: ", None), ("Y", (242, 242, 242))]])
    img, d = terminal(rows, fsize=26, cursor=(10, 18), hl=[(10, 0, 8, 1, "left")])
    band(d, "처음 한 번만 묻는 약관  →  Y  →  Enter", label="약관 동의")
    save(img, "T06b")


def t07():
    bar = "█" * 30
    rows = text_rows([cmd("winget", " install Gyan.FFmpeg"),
                      "Found FFmpeg [Gyan.FFmpeg] Version 9.0.2",
                      "This application is licensed to you by its owner.",
                      "Microsoft is not responsible for, nor does it grant any licenses to, third-party packages.",
                      "Downloading https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-full_build.zip",
                      [("  " + bar, (59, 150, 255)), ("   245 MB /  245 MB", None)],
                      "Successfully verified installer hash",
                      "Extracting archive...",
                      "Successfully extracted archive",
                      "Starting package install...",
                      [("Path environment variable modified; restart your shell to use the new value.", YEL)],
                      "Command line alias added: \"ffmpeg\"",
                      "Command line alias added: \"ffplay\"",
                      "Command line alias added: \"ffprobe\"",
                      [("Successfully installed", GRN)], PS])
    img, d = terminal(rows, fsize=24, cursor=(15, len(PS)), hl=[(10, 0, 77, 1, "right"), (14, 0, 22, 2, "right")])
    band(d, "restart your shell  =  창을 새로 여세요", label="새 창 규칙")
    save(img, "T07")


def t08():
    rows = text_rows(BANNER + [cmd("ffmpeg", " -version"),
                               "ffmpeg version 9.0.2-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers",
                               "built with gcc 15.2.0 (Rev13, Built by MSYS2 project)",
                               "configuration: --enable-gpl --enable-version3 --enable-static --disable-w32threads --disab",
                               "le-autodetect --enable-cairo --enable-fontconfig --enable-iconv --enable-gnutls --enable-",
                               "lcms2 --enable-libxml2 --enable-gmp --enable-bzlib --enable-lzma --enable-libsnappy --ena",
                               "ble-zlib --enable-librist --enable-libsrt --enable-libssh --enable-libzmq --enable-avisyn",
                               "libavutil      60. ...", "libavcodec     62. ...", "libavformat    62. ..."])
    img, d = terminal(rows, fsize=26, hl=[(3, len(PS), len(PS) + 15, 1, "right"), (4, 0, 44, 2, "right")])
    blur_box(img, (360, 290, 1820, 770), 7)  # 아래 긴 글은 몰라도 됨 — 흐림
    d = ImageDraw.Draw(img)
    chip(d, "첫 줄만 보세요!", 1300, 520, size=44)
    band(d, "ffmpeg version 숫자  만 보이면 성공", label="빼기 하나")
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T08")


def t09():
    rows = text_rows(BANNER + [cmd("winget", " install --id Git.Git -e --source winget"),
                               "Found Git [Git.Git] Version 2.56.0.3",
                               "This application is licensed to you by its owner.",
                               "Microsoft is not responsible for, nor does it grant any licenses to, third-party packages.",
                               "Downloading https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.3/Git-2.56.0.3-64-bit.exe",
                               [("  " + "█" * 30, (59, 150, 255)), ("  63.7 MB / 63.7 MB", None)],
                               "Successfully verified installer hash",
                               "Starting package install...",
                               [("Successfully installed", GRN)], "", PS])
    img, d = terminal(rows, fsize=24, cursor=(13, len(PS)),
                      hl=[(3, len(PS), len(PS) + 46, 1, "right"), (11, 0, 22, 2, "right")])
    chip(d, "작은 설치 창이 떴다 사라져도 그대로 두기", 1000, 600, bg=(226, 238, 255, 250), size=32)
    band(d, "붙여넣기  →  Enter  →  Successfully installed", label="Git")
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T09")


def t10():
    rows = text_rows(BANNER + [cmd("git", " --version"), "git version 2.56.0.windows.3", "", PS])
    img, d = terminal(rows, fsize=40, cursor=(6, len(PS)),
                      hl=[(3, len(PS), len(PS) + 13, 1, "right"), (4, 0, 28, 2, "right")])
    band(d, "새 창에서  git version 2.○○  이 보이면 성공", label="새 창에서")
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T10")


def t11():
    rows = text_rows(BANNER + [cmd("python", " --version"), "Python 3.14.10",
                               cmd("ffmpeg", " -version"),
                               "ffmpeg version 9.0.2-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers",
                               [("   (아래 긴 글 생략)", DIM)],
                               cmd("git", " --version"), "git version 2.56.0.windows.3", "", PS])
    img, d = terminal(rows, fsize=28, cursor=(11, len(PS)),
                      hl=[(4, 0, 14, 1, "right"), (6, 0, 21, 2, "right"), (9, 0, 28, 3, "right")])
    band(d, "새 창 하나에서 세 줄  →  숫자 세 개", label="세 줄 점검")
    chip(d, FOLLOW, 1380, 690, size=34)
    save(img, "T11")


def t13():
    rows = text_rows([[("The legacy 'py' command is still installed.", YEL)], "",
                      "This may interfere with launching the new 'py' command, and may be resolved by",
                      "uninstalling 'Python launcher'.", "",
                      "Open Installed apps now? [y/N] "])
    img, d = terminal(rows, title="Python install manager", fsize=32, hl=[(0, 0, 44, 1, "right"), (3, 0, 31, 2, "right")])
    band(d, "예전 Python Launcher 를 지우라는 안내", label="경고")
    save(img, "T13")


if __name__ == "__main__":
    title_card()
    ch2_map(2, "K01")
    ch2_map(3, "K01_next")
    for k in (1, 2, 3):
        tools(k, f"K02_{k}")
    ffmpeg_detail()
    git_detail()
    winget_card()
    today_order()
    dashes()
    for w in "abc":
        judge(w)
    for k in (1, 2, 3, 4):
        stuck(k)
    mac_card()
    end_card()
    w01()
    w06()
    w02()
    w03()
    w04()
    w08()
    t01()
    t03()
    t04()
    t05()
    t06()
    t06b()
    t07()
    t08()
    t09()
    t10()
    t11()
    t13()
