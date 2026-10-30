# 강의 CH1-3 — 글자 카드 로컬 렌더 (무료). 템플릿 = CH1-2 render_cards.py (도구 함수 그대로, 카드만 교체). 1920x1080 RGBA 오버레이 → cards/*.png
# 제목 = 꾹꾹체(font.ttf, '·' 글리프 없음 → 'ㆍ' 치환), 본문 = 맑은 고딕 Bold. ✓·✗ 는 글리프가 없어 도형으로 그림.
# 아래 18%(y>885)는 자막 자리라 비워 둔다. 왼쪽 아래(x<300, y>560)는 말하는 사람 작은 화면 자리 (2026-10-29 CH1-2).
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).parent
OUT = BASE / "cards"
OUT.mkdir(exist_ok=True)
W, H = 1920, 1080
TITLE_FONT = str(BASE / "font.ttf")
BODY_FONT = "C:/Windows/Fonts/malgunbd.ttf"

CREAM, INK, MUTED = (255, 250, 238, 238), (45, 52, 46), (110, 118, 108)
GREEN, RED, GOLD = (59, 122, 76), (210, 63, 54), (190, 140, 30)
GREEN_SOFT, RED_SOFT = (227, 240, 226), (251, 231, 228)


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


def center(d, y, text, font, fill=INK):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


def badge(d, cx, cy, n, color=GREEN, r=44):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    f = bf(int(r * 1.15))
    w = d.textlength(str(n), font=f)
    d.text((cx - w / 2, cy - r * 0.78), str(n), font=f, fill="white")


def check(d, x, y, s=40, color=GREEN, width=9):
    d.line([(x, y + s * 0.55), (x + s * 0.38, y + s * 0.92), (x + s, y)], fill=color, width=width, joint="curve")


def cross(d, cx, cy, s=26, color=RED, width=10):
    d.line([(cx - s, cy - s), (cx + s, cy + s)], fill=color, width=width)
    d.line([(cx - s, cy + s), (cx + s, cy - s)], fill=color, width=width)


def ox(d, cx, cy, mark, r=34):
    if mark == "O":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GREEN, width=10)
    else:
        cross(d, cx, cy, r * 0.8)


def save(img, name):
    img.save(OUT / f"{name}.png")
    print(name)


def center(d, y, text, font, fill=INK, cx=1080):  # 판이 오른쪽으로 비켜 있으므로 판 가운데 기준
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)


# ---------- 그림 붙이기 ----------
ROOT = [_p for _p in BASE.resolve().parents if (_p / "AGENTS.md").is_file()][-1]
SHEET = Image.open(ROOT / "images/style_ref/malli_reference.png").convert("RGBA")
SHEET_ORIG = Image.open(ROOT / "images/style_ref/malli_reference_orig_20261029.png").convert("RGBA")
IMG = BASE / "images"
MONO = "C:/Windows/Fonts/consola.ttf"
BLUE, ORANGE = (52, 101, 164), (205, 120, 30)
BLUE_SOFT, ORANGE_SOFT, GOLD_SOFT = (225, 235, 248), (252, 236, 214), (250, 240, 205)

# 시트 칸 좌표 (malli_reference.png 1698x926)
ZONES = {
    "front": (470, 120, 900, 860), "side": (920, 120, 1640, 625), "face": (60, 480, 440, 885),
    "walk": (905, 655, 1615, 885), "room": (35, 25, 485, 430),
}
WALK_BOX = (820, 610, 1350, 760)  # V1 의 아래 걷는 그림 3개 (1376x768 기준)
FACE_RIBBON = (265, 490, 380, 590)  # 시트 얼굴 클로즈업의 머리 리본


def mono(size):
    return ImageFont.truetype(MONO, size)


def fit(im, w=None, h=None):
    k = min(w / im.width, h / im.height) if (w and h) else (w / im.width if w else h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def put(img, im, x, y, border=(225, 210, 180, 255), radius=18):
    """그림을 둥근 테두리로 붙인다. (x, y) = 왼쪽 위."""
    im = im.convert("RGBA")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius, fill=255)
    img.paste(im, (int(x), int(y)), mask)
    if border:
        ImageDraw.Draw(img).rounded_rectangle([x - 2, y - 2, x + im.width + 1, y + im.height + 1], radius,
                                              outline=border, width=4)


def ring(d, box, color=RED, width=10):
    d.ellipse(box, outline=color, width=width)


def ok_mark(d, cx, cy, ok):
    if ok:
        d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], outline=GREEN, width=10)
    else:
        cross(d, cx, cy, 28)


# ---------- 카드 (CH1-3 계획서 v2) ----------
TEAL, TEAL_SOFT = (40, 120, 130), (222, 240, 240)


def src(name):
    return Image.open(IMG / f"{name}.png").convert("RGBA")


def photo_card(name, head, im_name, marks=(), head_col=GREEN, mark_col=RED):
    """제목 + 그림 한 장 (+ 원래 그림 좌표 기준 빨간 동그라미)."""
    img, d = panel((330, 70, 1830, 870))
    d.text((390, 88), kk(head), font=tf(70), fill=head_col)
    im0 = src(im_name)
    im = fit(im0, 1380, 660)
    x0, y0 = 1080 - im.width / 2, 190
    put(img, im, x0, y0)
    k = im.width / im0.width
    for a, b, c, e in marks:
        ring(d, [x0 + a * k, y0 + b * k, x0 + c * k, y0 + e * k], mark_col)
    save(img, name)


def pair_card(name, head, items, head_col=INK):
    """그림 두 장 나란히: items = [(그림, 라벨, ok/None)]."""
    img, d = panel((330, 70, 1830, 870))
    center(d, 95, kk(head), tf(76), head_col)
    for i, (nm, lab, ok) in enumerate(items):
        im = fit(src(nm), 680, 420)
        x0 = 395 + i * 720
        put(img, im, x0, 250)
        cy = 250 + im.height + 70
        if ok is None:
            d.text((x0 + 10, cy - 32), lab, font=bf(44), fill=INK)
        else:
            ok_mark(d, x0 + 44, cy, ok)
            d.text((x0 + 100, cy - 32), lab, font=bf(44), fill=GREEN if ok else RED)
    save(img, name)


def rule_card(name, code, title, lines, pics=(), col=GREEN, soft=GREEN_SOFT):
    """기준 카드: 코드 배지(A1) + 제목 + 설명 줄 + 근거 그림(작게)."""
    img, d = panel((330, 70, 1830, 870))
    d.rounded_rectangle([390, 110, 560, 200], 30, fill=col)
    w = d.textlength(code, font=bf(58))
    d.text((475 - w / 2, 118), code, font=bf(58), fill="white")
    d.text((600, 102), kk(title), font=tf(82), fill=col)
    y = 250
    for ln in lines:
        d.rounded_rectangle([400, y - 6, 1770, y + 76], 22, fill=soft)
        d.ellipse([428, y + 22, 452, y + 46], fill=col)
        d.text((475, y + 6), ln, font=bf(44), fill=INK)
        y += 100
    if pics:
        wpic = (1370 - 30 * (len(pics) - 1)) / len(pics)
        for i, (nm, lab) in enumerate(pics):
            im = fit(src(nm), int(wpic), 860 - y - 40)
            x0 = 400 + i * (wpic + 30)
            put(img, im, x0, y + 10)
            if lab:
                d.rounded_rectangle([x0 + 10, y + 20, x0 + 30 + d.textlength(lab, font=bf(32)), y + 68], 16,
                                    fill=(255, 255, 255, 230))
                d.text((x0 + 20, y + 22), lab, font=bf(32), fill=INK)
    save(img, name)


def quiz_card(name, n, q_lines, pic=None, stamp=None, pics2=None):
    img, d = panel((330, 70, 1830, 870))
    d.rounded_rectangle([390, 100, 640, 190], 30, fill=GOLD)
    d.text((420, 105), kk(f"문제 {n}"), font=tf(70), fill="white")
    for j, ln in enumerate(q_lines):
        d.text((680, 100 + j * 64), ln, font=bf(46), fill=INK)
    y0 = 100 + len(q_lines) * 64 + 40
    if pic:
        im = fit(src(pic), 1300, 860 - y0 - 20)
        x0 = 1080 - im.width / 2
        put(img, im, x0, y0)
        cx, cy = x0 + im.width / 2, y0 + im.height / 2
    if pics2:
        for i, nm in enumerate(pics2):
            im = fit(src(nm), 640, 860 - y0 - 20)
            put(img, im, 400 + i * 700, y0)
            d.text((400 + i * 700 + im.width / 2 - 30, y0 + im.height / 2 - 90), "?", font=tf(150), fill=GOLD)
        cx, cy = 1080, y0 + 200
    if stamp:
        r = 150
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 200), outline=RED, width=14)
        cross(od, cx, cy, 90, RED, 26)
        img = Image.alpha_composite(img, ov)
    save(img, name)


def title_card():
    img, d = panel((420, 250, 1740, 700))
    center(d, 300, "CHAPTER 1 ㆍ 3강", bf(44), MUTED)
    center(d, 385, kk("그림체 기준 정하기"), tf(118), GREEN)
    center(d, 590, "아무도 다치지 않는 이야기를, 늘 같은 말리 나라 그림으로", bf(40), INK)
    save(img, "title")


def sketchbook(img, d, nm, box):
    """스케치북 한 장(스프링 + 흰 종이) 안에 그림."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 20, fill=(255, 255, 252, 255), outline=(190, 180, 160, 255), width=5)
    for k in range(14):
        cx = x0 + 60 + k * (x1 - x0 - 120) / 13
        d.ellipse([cx - 14, y0 - 22, cx + 14, y0 + 14], outline=(120, 120, 120, 255), width=6)
    im = fit(src(nm), x1 - x0 - 60, y1 - y0 - 70)
    put(img, im, x0 + (x1 - x0 - im.width) / 2, y0 + 40, border=None)


def tiger_sketch(nm, name, head):
    img, d = panel((330, 70, 1830, 870))
    d.text((390, 88), kk(head), font=tf(70), fill=ORANGE)
    sketchbook(img, d, nm, (480, 220, 1680, 840))
    save(img, name)


def forty_card():
    img, d = panel((330, 70, 1830, 870))
    center(d, 90, kk("말리 동화 마흔 편 가까이"), tf(80), GREEN)
    names = ["R01", "R03", "R04", "R05", "R06", "R07", "R08", "old_ghibli", "R02"]
    for i, nm in enumerate(names):
        im = fit(src(nm), 440, 248)
        put(img, im, 405 + (i % 3) * 460, 215 + (i // 3) * 210, radius=12)
    save(img, "forty")


def three_card(k):
    img, d = panel((330, 70, 1830, 870))
    center(d, 100, kk("그림체 기준 세 묶음"), tf(84), INK)
    groups = [("A", "잔인하지 않게", "이야기 장면 5가지", RED, RED_SOFT),
              ("B", "예쁘고 한결같게", "그림 4가지", BLUE, BLUE_SOFT),
              ("C", "그림체는 하나로", "기준 그림 1장", GREEN, GREEN_SOFT)]
    for i, (code, t, sub, col, soft) in enumerate(groups):
        on = i < k
        y = 250 + i * 190
        d.rounded_rectangle([420, y, 1760, y + 160], 34, fill=soft if on else (243, 240, 232, 255))
        badge(d, 510, y + 80, code, col if on else MUTED, 52)
        d.text((600, y + 22), kk(t), font=tf(76), fill=col if on else MUTED)
        d.text((1300, y + 52), sub, font=bf(42), fill=INK if on else MUTED)
    save(img, f"three{k}")


def w4_card(answer=False):
    img, d = panel((330, 70, 1830, 870))
    center(d, 90, kk("누가 진짜 말리일까요?"), tf(80), INK)
    cells = [src("W01a").crop((430, 40, 960, 740)), src("W01b").crop((430, 40, 960, 740)),
             src("W01c").crop((420, 30, 960, 768)), SHEET.crop((470, 120, 900, 860))]
    labs = ["3D 장난감", "TV 만화", "어두운 그림", "수채화"]
    for i, (im, lab) in enumerate(zip(cells, labs)):
        im = fit(im, 320, 520)
        x0 = 400 + i * 350 + (320 - im.width) / 2
        put(img, im, x0, 230)
        d.text((400 + i * 350 + 160 - d.textlength(lab, font=bf(40)) / 2, 775), lab, font=bf(40),
               fill=GREEN if (answer and i == 3) else INK)
        if answer:
            cx, cy = x0 + im.width / 2, 230 + im.height / 2
            if i == 3:
                d.ellipse([cx - 190, cy - 290, cx + 190, cy + 290], outline=GREEN, width=12)
            else:
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ov).rounded_rectangle([x0, 230, x0 + im.width, 230 + im.height], 18,
                                                     fill=(255, 250, 238, 150))
                img = Image.alpha_composite(img, ov)
                d = ImageDraw.Draw(img)
    save(img, "w4_answer" if answer else "w4")


def zero_card():
    img, d = panel((420, 200, 1740, 760))
    center(d, 250, kk("기준 그림을 함께 첨부했더니"), tf(80), INK)
    center(d, 400, "그림 10장 중 다시 만들기", bf(60), MUTED)
    center(d, 490, kk("0장"), tf(170), GREEN)
    center(d, 690, "2026년 7월 「미운 오리 새끼」 편, 채널 처음", bf(36), MUTED)
    save(img, "zero")


def v1_mark():
    img, d = panel((330, 70, 1830, 870))
    d.text((390, 88), kk("가운데만 작게, 둘레는 빈 종이"), font=tf(70), fill=RED)
    im0 = src("V1")
    im = fit(im0, 1380, 660)
    x0, y0 = 1080 - im.width / 2, 190
    put(img, im, x0, y0)
    k = im.width / im0.width
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([x0, y0, x0 + im.width, y0 + im.height], fill=(210, 63, 54, 70))
    od.rectangle([x0 + 270 * k, y0 + 60 * k, x0 + 1120 * k, y0 + 700 * k], fill=(0, 0, 0, 0))
    img = Image.alpha_composite(img, ov)
    d = ImageDraw.Draw(img)
    d.rectangle([x0 + 270 * k, y0 + 60 * k, x0 + 1120 * k, y0 + 700 * k], outline=GREEN, width=6)
    save(img, "v1_mark")


def use_card(k):
    img, d = panel((330, 70, 1830, 870))
    center(d, 100, kk("기준을 쓰는 세 번"), tf(84), INK)
    steps = [("대본", "이야기부터 순하게 바꾸기", "A 다섯 가지"),
             ("요청 문장", "그림을 부탁할 때 기준을 적기", "no blood, grumpy but cute ..."),
             ("검수", "체크리스트로 한 장씩, 걸린 장만 다시", "A·B·C 열 가지")]
    for i, (t, sub, ex) in enumerate(steps):
        on = i < k
        y = 250 + i * 190
        d.rounded_rectangle([420, y, 1760, y + 160], 34, fill=GREEN_SOFT if on else (243, 240, 232, 255))
        badge(d, 500, y + 80, i + 1, GREEN if on else MUTED, 46)
        d.text((580, y + 20), kk(t), font=tf(70), fill=GREEN if on else MUTED)
        d.text((580, y + 100), sub, font=bf(38), fill=INK if on else MUTED)
        d.text((1220, y + 55), ex, font=mono(32) if i == 1 else bf(36), fill=MUTED)
    save(img, f"use{k}")


def summary():
    img, d = panel((330, 70, 1830, 870))
    center(d, 92, kk("아무도 다치지 않는 이야기를, 늘 같은 말리 나라 그림으로"), tf(54), GREEN)
    cols = [("A 잔인하지 않게", RED, ["아무도 죽거나 다치지 않아요", "때리기 대신 웃긴 소동", "악역은 심술꾸러기 얼굴",
                                    "무서운 것은 부드럽게", "마지막은 화해와 나눔"]),
            ("B 예쁘고 한결같게", BLUE, ["표정은 대사를 따라가요", "이야기 나라에 맞는 배경", "캐릭터는 매번 같게",
                                      "그림 속엔 글자 없이"]),
            ("C 그림체는 하나로", GREEN, ["기준 그림 한 장", "시트와 늘 함께 첨부"])]
    x = 380
    for title, col, items in cols:
        wcol = 520 if title[0] != "C" else 420
        d.text((x, 200), kk(title), font=tf(50), fill=col)
        for j, it in enumerate(items):
            y = 290 + j * 104
            d.rounded_rectangle([x, y, x + wcol - 30, y + 84], 20, fill=(255, 255, 255, 255), outline=col, width=3)
            d.text((x + 20, y + 20), it, font=bf(32), fill=INK)
        x += wcol
    save(img, "summary")


def end_card():
    img, d = panel((420, 230, 1740, 720))
    center(d, 280, "CHAPTER 1 ㆍ 3강 끝", bf(46), MUTED)
    center(d, 360, kk("그림체 기준 정하기"), tf(104), GREEN)
    d.line([(680, 560), (1480, 560)], fill=(225, 210, 180), width=3)
    center(d, 600, "다음 ▶ CHAPTER 2 도구 세팅", bf(52), INK)
    save(img, "end")


if __name__ == "__main__":
    title_card()
    tiger_sketch("T01", "tiger_sketch", "말리가 골라 온 그림")
    tiger_sketch("T01", "redraw_a", "말리의 호랑이, 다시 그리기")
    tiger_sketch("T02", "redraw_b", "볼은 통통, 이빨은 쏙!")
    pair_card("two_ways", "같은 호랑이, 두 갈래", [("T01", "무섭게 그리면", False), ("T02", "따뜻하게 그리면", True)])
    forty_card()
    for k in range(0, 4):
        three_card(k)
    # A — 심사위원 말리 O·X
    quiz_card("q1", 1, ["청개구리 이야기에서 엄마 개구리가", "세상을 떠나는 장면, 그대로 그릴까요?"], pic="R01")
    quiz_card("q1_x", 1, ["청개구리 이야기에서 엄마 개구리가", "세상을 떠나는 장면, 그대로 그릴까요?"], pic="R01", stamp="X")
    quiz_card("q2", 2, ["흥부와 놀부에서 놀부가", "제비 다리를 부러뜨리는 장면은요?"], pic="R07")
    quiz_card("q2_x", 2, ["흥부와 놀부에서 놀부가", "제비 다리를 부러뜨리는 장면은요?"], pic="R07", stamp="X")
    quiz_card("q3", 3, ["팥죽 할머니 이야기의 호랑이는", "어떤 얼굴일까요?"], pics2=["T01", "T02"])
    photo_card("a1", "청개구리: 꽃이 핀 작은 풀 언덕", "R02", head_col=GREEN)
    rule_card("rule_a1", "A1", "아무도 죽거나 다치지 않아요",
              ["피, 상처, 쓰러진 몸은 그리지 않아요", "죽음은 \"먼 여행\"처럼 말로만"], [("R02", "청개구리")],
              RED, RED_SOFT)
    photo_card("a2", "흥부와 놀부: 멀쩡한 제비에 억지 붕대", "R03")
    rule_card("rule_a2", "A2", "때리는 장면 대신 웃긴 소동",
              ["매질, 찌르기, 부러뜨리기 없음", "놀라서 도망, 풍덩, 엉덩방아"], [("R03", "흥부와 놀부"), ("R08", "팥죽 할머니")],
              RED, RED_SOFT)
    rule_card("rule_a3", "A3", "악역은 심술꾸러기 얼굴",
              ["동글동글한 얼굴, 이빨과 발톱은 쏙", "혼쭐나고 도망가면 끝"], [("T02", ""), ("R04", "팥죽 할머니")],
              RED, RED_SOFT)
    photo_card("a3_tiger", "팥죽 할머니: 헤엄쳐 도망간 호랑이", "R04")
    photo_card("a3_wolf", "아기 돼지 삼형제: 눈이 빙글빙글 늑대", "old_ghibli")
    rule_card("rule_a4", "A4", "무서운 것은 부드럽게",
              ["밤 = 남색 하늘 + 큰 달, 등불", "무덤 = 꽃이 핀 작은 풀 언덕"], [("R06", "의좋은 형제"), ("R02", "청개구리")],
              RED, RED_SOFT)
    rule_card("rule_a5", "A5", "마지막 그림은 화해와 나눔",
              ["벌 받는 장면 대신 사과, 용서, 함께 먹기"], [("R05", "팥죽 할머니"), ("R07", "흥부와 놀부")],
              RED, RED_SOFT)
    # B — 탐정 말리
    photo_card("d1_mark", "\"미안해\" 장면인데…", "D01", [(380, 180, 580, 360), (580, 290, 720, 420)])
    rule_card("rule_b1", "B1", "표정은 대사를 따라가요",
              ["사과 장면엔 미안한 얼굴, 화해 장면엔 웃는 얼굴", "요청 문장에 감정을 직접 적기"],
              [("D01", "다시 그린 예시")], BLUE, BLUE_SOFT)
    photo_card("d2_mark", "한국 옛날이야기 마을인데…", "D02", [(530, 110, 1240, 470)])
    rule_card("rule_b2", "B2", "이야기 나라에 맞는 배경",
              ["한국 옛날이야기 = 초가집과 한옥", "실제로 세 편에서 서양식 집이 나왔어요"],
              [("R06", "초가 마을"), ("D02", "다시 그린 예시")], BLUE, BLUE_SOFT)
    rule_card("rule_b3", "B3", "캐릭터는 매번 같게",
              ["시트를 늘 첨부하기", "품종, 나이, 소품이 바뀌지 않았는지 확인", "예: 진돗개 귀가 늘어진 귀로 바뀐 적"],
              (), BLUE, BLUE_SOFT)
    rule_card("rule_b4", "B4", "그림 속엔 글자가 없어요",
              ["간판, 배너, 책 표지 글자 없음 (말리 이름표만 예외)", "예: 결승선에 \"WINNER!\" 배너가 들어간 적"],
              (), BLUE, BLUE_SOFT)
    # C — 진짜 말리 찾기 + 기준 그림
    w4_card(False)
    w4_card(True)
    zero_card()
    photo_card("v1", "오늘 만든 기준 그림 (V1)", "V1")
    v1_mark()
    photo_card("v2", "화면을 꽉 채운 기준 그림 (V2)", "V2")
    for k in range(0, 4):
        use_card(k)
    summary()
    end_card()
