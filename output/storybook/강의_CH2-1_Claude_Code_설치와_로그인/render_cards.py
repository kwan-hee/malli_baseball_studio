# 강의 CH2-1 — 글자 카드 + 화면 카드 로컬 렌더 (무료). 1920x1080 RGBA 오버레이 → cards/*.png
# 템플릿 = CH1-2 render_cards.py (판·배지·체크 도우미 그대로). 화면 카드는 이 편에서 추가:
#   - 터미널(T): screens/snapshots/NNN.json (capture_terminal.py 가 기록한 실제 글자·색) 또는 직접 쓴 줄을 칸 단위로 그림
#   - 캡처(W·B): screens/*_raw 실제 캡처를 잘라 붙이고 개인정보(이름·이메일·PC 이름·아바타)는 흐림
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


# ---------- 글자 카드 ----------
def title_card():
    img, d = panel((420, 250, 1740, 700))
    center(d, 300, "CHAPTER 2 ㆍ 1강", bf(44), MUTED)
    center(d, 385, "Claude Code", tf(112), GREEN)
    center(d, 520, kk("설치와 로그인"), tf(86), INK)
    save(img, "title")


def ch2_map(hi=1, name="K01"):
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
        if on:
            chip(d, "오늘" if hi == 1 else "다음 시간", 1450, y + 18, size=32)
    save(img, name)


def chat_vs_code(both=True, name="K02"):
    img, d = panel((330, 90, 1830, 860))
    center(d, 120, kk("Claude 두 가지"), tf(70), GREEN)
    for i, (head, sub, lines, col_, soft) in enumerate([
        ("채팅 Claude", "웹사이트에서", ["말로 대답해 줘요", "파일 저장은 내가 직접"], BLUE, BLUE_SOFT),
        ("Claude Code", "내 컴퓨터에서", ["폴더를 만들어요", "파일을 써요", "프로그램을 실행해요"], ORANGE, ORANGE_SOFT)]):
        if i == 1 and not both:
            continue
        x = 400 + i * 730
        d.rounded_rectangle([x, 240, x + 660, 820], 36, fill=soft + (255,), outline=col_, width=6)
        d.text((x + 40, 270), head, font=bf(60), fill=col_)
        d.text((x + 40, 355), sub, font=bf(40), fill=MUTED)
        if i == 0:  # 말풍선
            d.rounded_rectangle([x + 420, 270, x + 620, 380], 30, fill="white", outline=col_, width=5)
            d.polygon([(x + 460, 375), (x + 440, 420), (x + 500, 378)], fill="white", outline=col_)
            d.text((x + 470, 290), "...", font=bf(54), fill=col_)
        else:  # 폴더·파일·재생 아이콘
            d.rounded_rectangle([x + 430, 300, x + 520, 370], 8, fill=(250, 200, 80), outline=col_, width=3)
            d.rectangle([x + 430, 288, x + 470, 302], fill=(250, 200, 80), outline=col_, width=3)
            d.rectangle([x + 535, 285, x + 590, 370], fill="white", outline=col_, width=4)
            d.polygon([(x + 605, 300), (x + 645, 330), (x + 605, 360)], fill=col_)
        for j, t in enumerate(lines):
            y = 460 + j * 105
            check(d, x + 50, y + 10, 40, col_, 8)
            d.text((x + 110, y), t, font=bf(48), fill=INK)
    save(img, name)


def today_order():
    img, d = panel((360, 110, 1800, 840))
    center(d, 145, kk("오늘 순서"), tf(78), GREEN)
    for i, t in enumerate(["준비물 확인", "터미널 열기", "설치 한 줄", "로그인"], 1):
        x = 430 + (i - 1) * 340
        d.rounded_rectangle([x, 330, x + 300, 600], 36, fill=(255, 255, 255, 255), outline=GREEN, width=5)
        badge(d, x + 150, 400, i, GREEN, 46)
        w = d.textlength(t, font=bf(46))
        d.text((x + 150 - w / 2, 480), t, font=bf(46), fill=INK)
        if i < 4:
            d.polygon([(x + 308, 450), (x + 332, 465), (x + 308, 480)], fill=GOLD)
    chip(d, "Mac 은 마지막에 한 번에 정리!", 1180, 690, bg=(225, 235, 248, 250), size=36)
    save(img, "K03")


def checklist(k):
    img, d = panel((360, 100, 1800, 850))
    center(d, 135, kk("준비물 세 가지"), tf(76), GREEN)
    items = [("Claude 유료 요금제", "Pro 이상 ㆍ 무료 플랜은 사용할 수 없어요"),
             ("Windows 10 이상", "Mac 은 macOS 13 이상"),
             ("인터넷 연결", "설치할 때도, 일할 때도")]
    for i, (a, b) in enumerate(items, 1):
        y = 270 + (i - 1) * 180
        on = i <= k
        d.rounded_rectangle([450, y, 1720, y + 150], 34, fill=((255, 255, 255) if on else (245, 240, 228)) + (255,),
                            outline=GREEN if on else (215, 205, 185), width=5 if on else 3)
        d.rounded_rectangle([490, y + 40, 560, y + 110], 14, fill="white", outline=GREEN, width=5)
        if on and (k == 3 or i < k):
            check(d, 500, y + 50, 50, GREEN, 10)
        d.text((600, y + 22), a, font=bf(52), fill=INK)
        d.text((600, y + 90), b, font=bf(34), fill=MUTED)
        if i == 1 and on:
            cross(d, 1620, y + 75, 22)
            d.text((1520, y + 52), "무료", font=bf(36), fill=RED)
    save(img, f"K04_{k}")


def official_only():
    img, d = panel((360, 120, 1800, 840))
    center(d, 150, kk("설치 명령어는 공식 페이지에서만"), tf(68), GREEN)
    d.rounded_rectangle([450, 300, 1060, 720], 36, fill=GREEN_SOFT + (255,), outline=GREEN, width=6)
    d.ellipse([705, 330, 805, 430], outline=GREEN, width=12)
    center(d, 470, "code.claude.com", bf(48), INK, cx=755)
    center(d, 550, "공식 안내 페이지", bf(40), MUTED, cx=755)
    d.rounded_rectangle([1100, 300, 1710, 720], 36, fill=RED_SOFT + (255,), outline=RED, width=6)
    cross(d, 1405, 380, 40, RED, 14)
    center(d, 470, "출처 모를 블로그", bf(48), INK, cx=1405)
    center(d, 550, "댓글 ㆍ 메신저 링크", bf(40), MUTED, cx=1405)
    save(img, "K08")


def next_three():
    img, d = panel((360, 110, 1800, 850))
    center(d, 140, kk("다음부터는 세 단계"), tf(76), GREEN)
    steps = [("파워셸 열기", None), ("작업실로 들어가기", "cd malli-studio"), ("일꾼 부르기", "claude")]
    for i, (a, b) in enumerate(steps, 1):
        y = 270 + (i - 1) * 165
        d.rounded_rectangle([450, y, 1720, y + 140], 34, fill=(255, 255, 255, 255), outline=GREEN, width=5)
        badge(d, 525, y + 70, i, GREEN, 40)
        d.text((600, y + 38), a, font=bf(52), fill=INK)
        if b:
            bw_ = d.textlength(b, font=ImageFont.truetype(F_MONO_B, 50))
            d.rounded_rectangle([1660 - bw_ - 40, y + 30, 1680, y + 110], 16, fill=(30, 30, 30))
            d.text((1660 - bw_ - 20, y + 42), b, font=ImageFont.truetype(F_MONO_B, 50), fill=(240, 240, 240))
    chip(d, "로그인은 처음 한 번만!", 1230, 770, size=36)
    save(img, "K05")


def stuck(k):
    img, d = panel((360, 90, 1800, 860))
    center(d, 120, kk("막혔을 때 세 가지"), tf(76), GREEN)
    rows = [("'claude' 를 인식할 수 없다", "창을 닫고 새로 열기"),
            ("인터넷 창이 안 열린다", "터미널의 긴 주소를 복사해 붙여 넣기"),
            ("로그인이 안 된다", "무료 플랜인지 요금제 확인")]
    for i, (a, b) in enumerate(rows, 1):
        y = 255 + (i - 1) * 190
        on = i == k
        alpha = 255 if i <= k else 110
        d.rounded_rectangle([430, y, 1750, y + 165], 34, fill=((255, 255, 255) if on else (250, 246, 236)) + (alpha,),
                            outline=(GOLD if on else (220, 210, 190)) + (alpha,), width=6 if on else 3)
        d.text((470, y + 20), a, font=bf(46), fill=(RED if i <= k else MUTED) + (alpha,))
        d.text((520, y + 92), "→  " + b, font=bf(44), fill=(GREEN if i <= k else MUTED) + (alpha,))
    save(img, f"K06_{k}")


def mac_card():
    img, d = panel((330, 70, 1830, 870))
    center(d, 95, kk("Mac 한 장 요약"), tf(72), GREEN)
    rows = [("command + 스페이스 → '터미널' 입력 → 열기", None),
            ("빠른 시작 페이지의 macOS 칸 명령 복사 → 붙여넣기 → return", "curl -fsSL https://claude.ai/install.sh | bash"),
            ("터미널을 새로 열고 버전 확인", "claude --version"),
            ("claude 입력 → 로그인 (Windows 와 똑같아요)", "claude")]
    y = 215
    for i, (a, b) in enumerate(rows, 1):
        badge(d, 440, y + 34, i, GREEN, 32)
        d.text((495, y + 6), a, font=bf(40), fill=INK)
        y += 78
        if b:
            f = ImageFont.truetype(F_MONO_B, 40)
            d.rounded_rectangle([495, y - 4, 495 + d.textlength(b, font=f) + 40, y + 62], 14, fill=(30, 30, 30))
            d.text((515, y + 6), b, font=f, fill=(240, 240, 240))
            y += 88
        else:
            y += 20
    save(img, "K07")


def end_card():
    img, d = panel((420, 230, 1740, 720))
    center(d, 280, "CHAPTER 2 ㆍ 1강 끝", bf(46), MUTED)
    center(d, 360, kk("Claude Code 설치와 로그인"), tf(92), GREEN)
    d.line([(680, 560), (1480, 560)], fill=(225, 210, 180), width=3)
    center(d, 600, "다음 강의 ▶ Python ㆍ FFmpeg ㆍ Git 설치", bf(50), INK)
    save(img, "end")


# ---------- 실제 캡처 화면 ----------
ME = [(125, 100, 310, 170)]  # 설정 창 왼쪽 위 이름·이메일


def w01a():
    img, d, _ = capture_card("W01a_raw.jpg", (160, 0, 1300, 690),
                             hl=[((425, 140, 552, 182), 2, "left")], url="code.claude.com/docs/ko/quickstart")
    hl_box(d, (WIN[0] + 330, WIN[1] + 12, WIN[0] + 860, WIN[1] + 50), 1, "left")
    band(d, "code.claude.com/docs/ko/quickstart", ImageFont.truetype(F_MONO_B, 44), "공식 주소")
    save(img, "W01a")


def w01b():
    img, d, _ = capture_card("W01b_raw.jpg", (300, 180, 1150, 720),
                             hl=[((425, 512, 562, 535), 1, "left"), ((428, 550, 996, 592), 2, "left"),
                                 ((935, 557, 962, 584), 3, "right")])
    band(d, "irm https://claude.ai/install.ps1 | iex", ImageFont.truetype(F_MONO_B, 44), "Windows PowerShell")
    save(img, "W01b")


def w02():
    img, d, _ = capture_card("W02_raw.png", (0, 0, 1262, 791),
                             hl=[((30, 280, 444, 330), 1, "left"), ((680, 85, 768, 138), 2, "right")],
                             blur=ME + [(505, 745, 900, 791)])
    band(d, "설정  →  시스템  →  정보", label="Windows 버전 보기")
    save(img, "W02")


def w02b():
    img, d, _ = capture_card("W02b_raw.png", (0, 0, 1262, 791),
                             hl=[((575, 438, 925, 476), 3, "right")], blur=ME)
    band(d, "에디션 : Windows 11 Home  →  10 이상이면 OK!", label="확인")
    save(img, "W02b")


def w03():
    img, d, _ = capture_card("W03_raw.png", (520, 2076, 1300, 2160), hl=[((722, 2092, 768, 2156), 1, "left")])
    band(d, "화면 맨 아래 가운데, 창문 모양 버튼", label="시작 버튼")
    save(img, "W03")


def w04():
    img, d, _ = capture_card("W04_raw.png", (1290, 770, 2510, 1560),
                             hl=[((1340, 790, 2290, 852), 1, "left"), ((1334, 1012, 1826, 1100), 2, "left"),
                                 ((1894, 1248, 2076, 1302), 3, "right")],
                             blur=[(2310, 860, 2400, 935)])
    band(d, "powershell 입력  →  Windows PowerShell  →  열기", label="검색")
    save(img, "W04")


def w05():
    """탐색기: 창 틀은 실제 캡처, 오른쪽 목록만 새 PC 의 사용자 폴더처럼 다시 그림 (129개 숨김 폴더 대신)."""
    im = Image.open(SCR / "W05_raw.png").convert("RGB")
    dd = ImageDraw.Draw(im)
    icon = im.crop((636, 262, 664, 286))
    dd.rectangle([611, 238, 1052, 640], fill=(255, 255, 255))  # 목록 영역 지우기
    dd.rectangle([0, 645, 600, 690], fill=(243, 243, 243))
    f = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 17)
    names = ["malli-studio", "다운로드", "문서", "바탕 화면", "사진", "음악", "동영상"]
    for i, n in enumerate(names):
        y = 255 + i * 43
        if n == "malli-studio":
            dd.rectangle([631, y - 6, 1052, y + 32], fill=(204, 232, 255))
        im.paste(icon, (637, y))
        dd.text((668, y + 1), n, font=f, fill=(25, 25, 25))
    dd.text((24, 660), f"{len(names)}개 항목      1개 항목 선택함", font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 16), fill=(30, 30, 30))
    blur_box(im, (40, 315, 200, 352))  # OneDrive 이름
    im.save(SCR / "W05_clean.png")
    img, d, _ = capture_card("W05_clean.png", (0, 0, 1082, 691),
                             hl=[((625, 247, 860, 289), 1, "right"), ((455, 75, 640, 120), 2, "right")])
    band(d, "내 사용자 폴더 안에  malli-studio  폴더가 생겼어요", label="작업실")
    save(img, "W05")


def b01():
    img, d, _ = capture_card("B01a_login_raw.png", (420, 130, 1940, 1130),
                             hl=[((905, 690, 1445, 750), 1, "left"), ((905, 970, 1445, 1035), 2, "left")],
                             blur=[(1750, 1040, 2352, 1412)], url="claude.ai/login")
    band(d, "평소 Claude 를 쓰던 계정으로 로그인 → 안내에 따라 승인", label="로그인")
    save(img, "B01")


# ---------- 터미널 화면 ----------
PS = "PS C:\\Users\\malli> "
PS2 = "PS C:\\Users\\malli\\malli-studio> "
BANNER = ["Windows PowerShell", "Copyright (C) Microsoft Corporation. All rights reserved.", ""]
YEL = (249, 241, 165)
ERR = (231, 72, 86)


def t01():
    img, d = terminal(text_rows(BANNER + [PS]), fsize=40, cursor=(3, len(PS)), hl=[(3, 0, 2, 1, "left")])
    band(d, "PS  로 시작하면 파워셸이 맞아요!", label="확인")
    save(img, "T01")


def t02(wait=False):
    cmd = [(PS, None), ("irm", YEL), (" https://claude.ai/install.ps1 | ", None), ("iex", YEL)]
    img, d = terminal(text_rows(BANNER + [cmd]), fsize=40, cursor=(4, 0) if wait else (3, len(PS) + 39),
                      hl=[] if wait else [(3, len(PS), len(PS) + 39, 1, "right")])
    if wait:
        band(d, "멈춘 게 아니에요. 열심히 내려받는 중!", label="조용해도 기다리기")
    else:
        band(d, "마우스 오른쪽 클릭 = 붙여넣기  →  Enter", label="붙여넣기")
        chip(d, "잠깐 멈추고 따라 해 보세요", 1380, 690, size=34)
    save(img, "T02w" if wait else "T02")


def t03():
    cmd = [(PS, None), ("irm", YEL), (" https://claude.ai/install.ps1 | ", None), ("iex", YEL)]
    G = (22, 198, 12)
    rows = text_rows(BANNER + [cmd, "Setting up Claude Code...", "",
                               [("✔ Claude Code successfully installed!", G)], "",
                               "  Version: 2.1.312", "", "  Location: C:\\Users\\malli\\.local\\bin\\claude.exe", "", "",
                               "  Next: Run claude --help to get started", "", "✅ Installation complete!", "", PS])
    img, d = terminal(rows, fsize=32, cursor=(17, len(PS)), hl=[(15, 0, 26, 1, "left")])
    band(d, "Installation complete!  =  설치 완료", label="성공")
    save(img, "T03")


ERR_LINES = ["claude : 'claude' 용어가 cmdlet, 함수, 스크립트 파일 또는 실행할 수 있는 프로그램",
             "이름으로 인식되지 않습니다. 이름이 정확한지 확인하고 경로가 포함된 경우 경로가",
             "올바른지 검증한 다음 다시 시도하십시오.",
             "위치 줄:1 문자:1", "+ claude --version", "+ ~~~~~~",
             "    + CategoryInfo          : ObjectNotFound: (claude:String) [], CommandNotFoundEx",
             "   ception", "    + FullyQualifiedErrorId : CommandNotFoundException"]


def t04():
    rows = text_rows(["✅ Installation complete!", "", [(PS, None), ("claude", YEL), (" --version", (118, 118, 118))]]
                     + [[(ln, ERR)] for ln in ERR_LINES] + ["", PS])
    img, d = terminal(rows, fsize=30, cursor=(13, len(PS)), hl=[(3, 0, 80, 1, "left")])
    band(d, "설치 전에 열어 둔 창은 새 프로그램을 아직 몰라요", label="흔한 일")
    save(img, "T04")


def t05():
    rows = text_rows(BANNER + [[(PS, None), ("claude", YEL), (" --version", (118, 118, 118))], "2.1.312 (Claude Code)", "", PS])
    img, d = terminal(rows, fsize=40, cursor=(6, len(PS)), hl=[(3, len(PS), len(PS) + 16, 1, "right"), (4, 0, 21, 2, "right")])
    band(d, "숫자가 나오면 설치 성공  (숫자는 달라도 괜찮아요)", label="새 창에서")
    chip(d, "잠깐 멈추고 따라 해 보세요", 1380, 690, size=34)
    save(img, "T05")


def t06(step):
    rows = [[(PS, None), ("mkdir", YEL), (" malli-studio", None)]]
    if step >= 1:
        rows += ["", "", "    디렉터리: C:\\Users\\malli", "", "",
                 "Mode                 LastWriteTime         Length Name",
                 "----                 -------------         ------ ----",
                 "d-----        2026-10-29  오후 10:12                malli-studio", "", ""]
        rows += [[(PS, None), ("cd", YEL), (" malli-studio", None)]]
    if step >= 2:
        rows += [PS2]
    rows = text_rows(BANNER + rows)
    hl = [(3, len(PS), len(PS) + 18, 1, "right")]
    if step >= 1:
        hl.append((14, len(PS), len(PS) + 15, 2, "right"))
    if step >= 2:
        hl.append((15, 0, len(PS2) - 1, 3, "right"))
    img, d = terminal(rows, fsize=30, cursor=(len(rows) - 1, len(PS2)) if step >= 2 else None, hl=hl)
    band(d, "mkdir = 폴더 만들기    cd = 폴더로 들어가기", label="작업실")
    chip(d, "잠깐 멈추고 따라 해 보세요", 1380, 690, size=34)
    save(img, f"T06_{step}")


def t07a():
    rows = text_rows(BANNER + [PS, [(PS2, None), ("claude", YEL)]])
    img, d = terminal(rows, fsize=40, cursor=(4, len(PS2) + 6), hl=[(4, len(PS2), len(PS2) + 6, 1, "right")])
    band(d, "claude  입력  →  Enter", label="일꾼 부르기")
    save(img, "T07a")


# 스냅숏 번호 (screens/snapshots, capture_terminal.py 2026-10-29 기록): 001 테마 · 002 로그인 방법 · 003 주소 · 004 성공
# 005 보안 안내 · 006 터미널 설정 · 007 폴더 신뢰(No) · 008 (Yes) · 009 시작 화면 · 013 첫 답장
def snap_card(n, rows, name, hl, band_text, label, chip_=False, cursor=None, cols=96, fsize=29, replace=(), extra=None,
              note=None):
    r = snap_rows(n, rows, cols, replace)
    if extra:
        r = extra(r)
    img, d = terminal(r, fsize=fsize, hl=hl, cursor=cursor)
    band(d, band_text, label=label)
    if chip_:
        chip(d, "잠깐 멈추고 따라 해 보세요", 1380, 690, size=34)
    if note:  # 머리글 옆 메모 (요금제마다 달라지는 글자 안내)
        chip(d, note, 1010, 105, bg=(226, 238, 255, 250), size=30)
    save(img, name)


def mask_url(rows):
    out = []
    for cells in rows:
        txt = "".join(c[0] for c in cells)
        if txt.startswith(("https://claude.com/cai", "code&", "3Apro", "code_ch", "uGAA")):
            cells = [(("•" if ch.strip() else " "), (90, 90, 90), bg, b) for ch, fg, bg, b in cells]
        out.append(cells)
    return out


def drop_warn(rows):
    return [c for c in rows if "Transcript saving" not in "".join(x[0] for x in c)]


def keep_reply(rows):
    """첫 답장 중 이 PC 개인 환경이 드러나는 줄(콘텐츠 하네스·연결 서비스)은 뺌."""
    bad = ("콘텐츠 제작", "검수 순서로", "연결된 서비스", "Transcript saving")
    return [c for c in rows if not any(b in "".join(x[0] for x in c) for b in bad)]


U2M = [("\\Users\\user\\", "\\Users\\malli\\")]


def terminals():
    t01()
    t02()
    t02(True)
    t03()
    t04()
    t05()
    for s in (0, 1, 2):
        t06(s)
    t07a()
    snap_card(1, range(12, 25), "T07", [(7, 1, 14, 1, "left")], "이미 선택된 Dark mode 그대로  →  Enter", "화면 색", chip_=True, cols=62, fsize=36)
    snap_card(2, range(16, 25), "T08", [(6, 1, 77, 1, "right")],
              "1번 = 구독 중인 Claude 계정으로 로그인  →  Enter", "로그인 방법", chip_=True, cols=110, fsize=24)
    snap_card(3, range(16, 27), "T08b", [(1, 1, 61, 1, "inside")],
              "브라우저가 안 열리면  c  를 눌러 주소 복사 → 붙여넣기", "창이 안 열릴 때", extra=mask_url, cols=110, fsize=24)
    snap_card(4, range(16, 20), "T09", [(2, 1, 43, 1, "left")], "Login successful  =  로그인 성공  →  Enter", "성공", cols=60, fsize=36,
              replace=[("yrats1234@gmail.com", "●●●●●●@gmail.com")])
    snap_card(5, range(16, 28), "T09b", [(3, 1, 30, 1, "left"), (7, 1, 66, 2, "left")],
              "① Claude 도 실수할 수 있어요  ② 믿을 수 있는 파일에서만", "안전 안내", cols=72, fsize=32)
    snap_card(6, range(16, 27), "T09c", [(6, 1, 39, 1, "left")], "1번 선택된 그대로  →  Enter", "터미널 설정", cols=72, fsize=32)
    snap_card(7, range(1, 17), "T10a", [(12, 1, 12, 1, "left")], "처음엔  No, exit (나가기)  가 선택돼 있어요!", "조심",
              replace=U2M, cols=110, fsize=24)
    snap_card(8, range(1, 17), "T10b", [(13, 1, 27, 2, "left")],
              "키보드  ↓  한 번  →  Yes, I trust this folder  →  Enter", "아래 화살표", replace=U2M, cols=110, fsize=24)
    snap_card(9, range(0, 16), "T11a", [(11, 0, 40, 1, "right")], "아래 입력 칸에 한국어로 말을 걸어요", "첫 인사",
              extra=drop_warn, chip_=True, cols=110, fsize=24, note="위쪽 글자는 요금제에 따라 달라도 괜찮아요")
    snap_card(13, range(10, 34), "T11b", [(0, 0, 18, 1, "left"), (2, 0, 108, 2, "left")],
              "안녕하세요! 저는 Claude Code예요.", "대답했어요", extra=keep_reply, cols=110, fsize=24)



if __name__ == "__main__":
    title_card()
    ch2_map(1, "K01")
    ch2_map(2, "K01_next")
    chat_vs_code(False, "K02a")
    chat_vs_code(True, "K02")
    today_order()
    for k in (1, 3):
        checklist(k)
    official_only()
    next_three()
    for k in (1, 2, 3):
        stuck(k)
    mac_card()
    end_card()
    w01a()
    w01b()
    w02()
    w02b()
    w03()
    w04()
    w05()
    b01()
    terminals()
