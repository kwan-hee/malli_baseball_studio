# 강의 CH1-2 — 글자 카드 로컬 렌더 (무료). 1920x1080 RGBA 오버레이 → cards/*.png
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


# ---------- 카드 ----------
def title_card():
    img, d = panel((420, 250, 1740, 700))
    center(d, 300, "CHAPTER 1 ㆍ 2강", bf(44), MUTED)
    center(d, 385, kk("말리 캐릭터 시트 만들기"), tf(118), GREEN)
    center(d, 590, "그림 + 글 = 한 세트", bf(48), INK)
    save(img, "title")


def sheet_full():
    img, d = panel((330, 70, 1830, 870))
    im = fit(SHEET, 1420, 760)
    put(img, im, 1080 - im.width / 2, 92)
    save(img, "sheet_full")


def set_card():
    img, d = panel()
    center(d, 120, "그림 + 글 = 한 세트", tf(92), INK)
    put(img, fit(SHEET, 640), 380, 330)
    d.text((1050, 410), "+", font=tf(120), fill=GOLD)
    d.rounded_rectangle([1130, 290, 1790, 800], 30, fill=(255, 255, 255, 255), outline=(225, 210, 180, 255), width=4)
    d.text((1170, 315), "바꾸지 않는 특징", font=bf(46), fill=GREEN)
    for i, t in enumerate(["털 = 크림색", "귀 = 길게 늘어진 곱슬 귀", "리본 = 분홍 목걸이에", "이름표 = 금색 뼈, Malli",
                           "꼬리 = 동그랗게 말림"]):
        d.ellipse([1172, 412 + i * 76, 1192, 432 + i * 76], fill=GREEN)
        d.text((1210, 395 + i * 76), t, font=bf(40), fill=INK)
    d.text((630, 700), "그림", font=bf(44), fill=MUTED)
    save(img, "set")


def zone_card(n, key, head, name):
    img, d = panel((330, 80, 1830, 870))
    badge(d, 420, 160, n, GREEN, 46)
    d.text((490, 110), kk(head), font=tf(80), fill=GREEN)
    im = fit(SHEET.crop(ZONES[key]), 1380, 600)
    put(img, im, 1080 - im.width / 2, 245)
    save(img, name)


def zone_face_walk():
    img, d = panel((330, 80, 1830, 870))
    for key, n, head, x0 in [("face", 3, "얼굴", 390), ("walk", 4, "걷는 동작", 860)]:
        badge(d, x0 + 40, 160, n, GREEN, 40)
        d.text((x0 + 100, 118), head, font=tf(70), fill=GREEN)
    put(img, fit(SHEET.crop(ZONES["face"]), 420, 590), 390, 250)
    put(img, fit(SHEET.crop(ZONES["walk"]), 920, 560), 860, 330)
    save(img, "zone34")


def zone_empty():
    img, d = panel((330, 70, 1830, 870))
    badge(d, 420, 145, 6, GREEN, 44)
    d.text((490, 98), "빈 공간도 한 칸", font=tf(78), fill=GREEN)
    im = fit(SHEET, 1400, 640)
    x0, y0 = 1080 - im.width / 2, 210
    put(img, im, x0, y0)
    k = im.width / SHEET.width
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for a, b, c, e in [(440, 40, 480, 900), (895, 40, 935, 900), (930, 625, 1680, 660), (40, 435, 470, 480)]:
        od.rounded_rectangle([x0 + a * k, y0 + b * k, x0 + c * k, y0 + e * k], 10, fill=(59, 160, 90, 110))
    save(Image.alpha_composite(img, ov), "zone6")


def five_card(k):
    img, d = panel()
    center(d, 115, "바꾸지 않는 특징 5가지", tf(84), INK)
    put(img, fit(SHEET.crop(ZONES["front"]), 400, 600), 400, 240)
    items = ["털 색은 크림색", "귀는 길게 늘어진 곱슬 귀", "리본은 분홍 목걸이에 빨간 리본", "이름표는 금색 뼈, 글자 Malli",
             "꼬리는 동그랗게 말린 복슬 꼬리"]
    for i, t in enumerate(items):
        on = i < k
        y = 260 + i * 118
        d.rounded_rectangle([860, y - 10, 1780, y + 90], 26, fill=GREEN_SOFT if on else (243, 240, 232, 255))
        badge(d, 915, y + 40, i + 1, GREEN if on else MUTED, 32)
        d.text((970, y + 12), t, font=bf(46), fill=INK if on else MUTED)
    save(img, f"five{k}")


def ears_card():
    img, d = panel((330, 80, 1830, 870))
    d.text((390, 100), "제일 자주 틀리는 곳: 귀", font=tf(80), fill=RED)
    w01 = Image.open(IMG / "W01.png").convert("RGBA")
    s = w01.width / 1376
    bad = fit(w01.crop((int(195 * s), int(185 * s), int(495 * s), int(545 * s))), 380, 360)
    put(img, bad, 430, 240)
    ok_mark(d, 430 + bad.width / 2, 240 + bad.height + 55, False)
    good = fit(SHEET.crop((470, 120, 900, 470)), 470, 360)
    put(img, good, 960, 240)
    ok_mark(d, 960 + good.width / 2, 240 + good.height + 55, True)
    d.rounded_rectangle([390, 720, 1780, 840], 24, fill=GREEN_SOFT)
    d.text((420, 735), "long floppy curly ears in EVERY view and expression,", font=mono(40), fill=INK)
    d.text((420, 785), "NEVER pointed or upright", font=mono(40), fill=RED)
    save(img, "ears")


def tag_card():
    img, d = panel()
    center(d, 120, "이름표 글자 확인", tf(88), INK)
    put(img, fit(SHEET.crop((560, 400, 760, 560)), 640), 420, 280)
    d.text((1150, 380), "이름표 글자는", font=bf(56), fill=INK)
    d.text((1150, 470), "처음부터 정확하게", font=bf(56), fill=GREEN)
    d.text((1150, 600), "\"Malli\" 확인", font=bf(48), fill=MUTED)
    save(img, "tag")


def input_bar(d, y, text, x0=420, x1=1740):
    d.rounded_rectangle([x0, y, x1, y + 120], 60, fill=(255, 255, 255, 255), outline=(200, 205, 215, 255), width=4)
    d.ellipse([x0 + 25, y + 25, x0 + 95, y + 95], outline=MUTED, width=5)
    d.line([(x0 + 60, y + 40), (x0 + 60, y + 80)], fill=MUTED, width=6)
    d.line([(x0 + 40, y + 60), (x0 + 80, y + 60)], fill=MUTED, width=6)
    d.ellipse([x1 - 105, y + 20, x1 - 25, y + 100], fill=BLUE)
    d.polygon([(x1 - 80, y + 40), (x1 - 80, y + 80), (x1 - 45, y + 60)], fill="white")
    d.text((x0 + 125, y + 35), text, font=mono(40), fill=INK)


def input_card():
    img, d = panel((330, 160, 1830, 800))
    center(d, 210, "입력 칸에 붙여 넣기", tf(84), INK)
    input_bar(d, 420, "Character design sheet of Malli, a ...")
    d.text((440, 600), "인터넷 창 → Gemini 앱 → 화면 아래 입력 칸", font=bf(44), fill=MUTED)
    save(img, "input")


PROMPT = (BASE / "practice_prompt.txt").read_text(encoding="utf-8").strip().splitlines()
PARTS = [(0, 2, BLUE, BLUE_SOFT, "어떤 그림"), (2, 5, GREEN, GREEN_SOFT, "외형 5가지"),
         (5, 11, ORANGE, ORANGE_SOFT, "칸 배치"), (11, 13, RED, RED_SOFT, "넣지 말 것")]


def prompt_card(hi=None, name="prompt"):
    img, d = panel((330, 60, 1860, 880))
    x = 380
    for i, (_, _, col, soft, lab) in enumerate(PARTS):
        on = hi is None or hi == i
        tw = d.textlength(lab, font=bf(36)) + 50
        d.rounded_rectangle([x, 85, x + tw, 145], 24, fill=soft if on else (240, 238, 232, 255))
        d.text((x + 25, 90), lab, font=bf(36), fill=col if on else MUTED)
        x += tw + 20
    y = 180
    for i, (a, b, col, soft, _) in enumerate(PARTS):
        on = hi is None or hi == i
        if hi == i:
            d.rounded_rectangle([360, y - 8, 1835, y + (b - a) * 50 + 2], 16, fill=soft)
        for ln in PROMPT[a:b]:
            d.text((380, y), ln, font=mono(25), fill=col if on else (175, 175, 168))
            y += 50
        y += 12
    save(img, name)


def sheet_img_card(src, head, name, marks=()):
    img, d = panel((330, 70, 1830, 870))
    d.text((390, 88), head, font=tf(70), fill=GREEN)
    im0 = Image.open(IMG / f"{src}.png").convert("RGBA")
    im = fit(im0, 1380, 680)
    x0, y0 = 1080 - im.width / 2, 185
    put(img, im, x0, y0)
    k = im.width / im0.width
    for a, b, c, e in marks:
        ring(d, [x0 + a * k, y0 + b * k, x0 + c * k, y0 + e * k])
    save(img, name)


def fixreq_card():
    img, d = panel((330, 180, 1830, 800))
    center(d, 220, "고쳐 달라고 말하기", tf(84), INK)
    d.rounded_rectangle([420, 370, 1740, 650], 50, fill=(255, 255, 255, 255), outline=BLUE, width=6)
    d.polygon([(1560, 646), (1640, 646), (1660, 720)], fill=BLUE)
    d.text((480, 410), "아래 걷는 그림 세 개에도 분홍 목걸이와", font=bf(50), fill=INK)
    d.text((480, 485), "빨간 리본을 그려 줘.", font=bf(50), fill=INK)
    d.text((480, 560), "다른 곳은 그대로 둬.", font=bf(50), fill=RED)
    save(img, "fixreq")


def compare_card():
    img, d = panel()
    center(d, 115, "다른 곳은 그대로, 틀린 곳만", tf(80), INK)
    for i, (src, lab) in enumerate([("V1", "V1 (처음)"), ("V2", "V2 (고친 뒤)")]):
        im0 = Image.open(IMG / f"{src}.png").convert("RGBA")
        im = fit(im0, 690)
        x0, y0 = 380 + i * 730, 300
        put(img, im, x0, y0)
        k = im.width / im0.width
        a, b, c, e = WALK_BOX
        ring(d, [x0 + a * k, y0 + b * k, x0 + c * k, y0 + e * k], RED if i == 0 else GREEN, 7)
        d.text((x0 + 10, y0 + im.height + 25), lab, font=bf(46), fill=RED if i == 0 else GREEN)
    save(img, "compare")


def mychar_card():
    img, d = panel((330, 120, 1830, 840))
    center(d, 160, "내 캐릭터로 만들기", tf(84), INK)
    put(img, fit(SHEET.crop(ZONES["face"]), 170, 170), 440, 300)
    d.text((650, 345), "+ 버튼으로 내 그림, 반려동물 사진 첨부", font=bf(46), fill=MUTED)
    d.rounded_rectangle([420, 520, 1760, 630], 26, fill=GOLD_SOFT)
    d.text((450, 540), "첨부한 그림 속 아이로 캐릭터 시트를 만들어 줘.", font=bf(48), fill=INK)
    d.text((450, 680), "+ 나머지 문장은 똑같이", font=bf(46), fill=GREEN)
    save(img, "mychar")


def checklist(k):
    img, d = panel((330, 90, 1830, 870))
    center(d, 115, "검수 체크리스트 5", tf(84), INK)
    qs = ["모든 그림에서 귀가 늘어진 귀인가요?", "리본이 모든 그림에서 목걸이에 있나요?", "이름표 글자가 정확한가요?",
          "서명, 로고, 다른 캐릭터가 숨어 있지 않나요?", "칸마다 말리가 한 마리씩만 있나요?"]
    for i, q in enumerate(qs):
        y = 250 + i * 122
        on = i < k
        d.rounded_rectangle([400, y - 12, 1760, y + 96], 28, fill=GREEN_SOFT if on else (243, 240, 232, 255))
        d.rounded_rectangle([430, y + 8, 500, y + 78], 14, outline=GREEN if on else MUTED, width=6, fill="white")
        if on:
            check(d, 440, y + 18, 50)
        d.text((530, y + 12), f"{i + 1}. {q}", font=bf(48), fill=INK if on else MUTED)
    save(img, f"check{k}")


def ribbon_quiz(answer=False):
    img, d = panel((330, 80, 1830, 870))
    d.rounded_rectangle([390, 110, 590, 200], 30, fill=GOLD)
    d.text((420, 115), "퀴즈", font=tf(70), fill="white")
    d.text((630, 112), "리본은 어디에 있죠?", font=tf(76), fill=INK)
    fx, fy = ZONES["face"][:2]
    crop = SHEET.crop(ZONES["face"])
    im = fit(crop, 900, 620)
    x0, y0 = 1080 - im.width / 2, 235
    put(img, im, x0, y0)
    k = im.width / crop.width
    a, b, c, e = FACE_RIBBON
    bx = [x0 + (a - fx) * k, y0 + (b - fy) * k, x0 + (c - fx) * k, y0 + (e - fy) * k]
    if answer:
        ring(d, [bx[0] - 20, bx[1] - 20, bx[2] + 20, bx[3] + 20])
    else:
        d.text((bx[2] + 30, bx[1] - 10), "?", font=tf(140), fill=GOLD)
    save(img, "quiz_a" if answer else "quiz_q")


def ribbon_cmp():
    img, d = panel()
    center(d, 115, "이 칸만 리본 위치가 달라요", tf(80), INK)
    for i, (box, ok, lab) in enumerate([((520, 130, 880, 560), True, "정면: 목걸이 리본"),
                                        (ZONES["face"], False, "얼굴: 머리 위 리본")]):
        im = fit(SHEET.crop(box), 560, 480)
        x0 = 520 + i * 640
        put(img, im, x0, 250)
        cy = 250 + im.height + 70
        ok_mark(d, x0 + 54, cy, ok)
        d.text((x0 + 110, cy - 32), lab, font=bf(46), fill=GREEN if ok else RED)
    save(img, "ribbon_cmp")


def corner_card():
    img, d = panel()
    center(d, 115, "구석까지 꼭 확인", tf(84), INK)
    box = (1530, 770, 1698, 926)
    for i, (im, ok, lab) in enumerate([(SHEET_ORIG.crop(box).filter(ImageFilter.GaussianBlur(14)), False, "원본: 낙서, 서명 (가림)"),
                                       (SHEET.crop(box), True, "정리본: 깨끗하게 지움")]):
        im = fit(im, 560, 470)
        x0 = 470 + i * 680
        put(img, im, x0, 250)
        cy = 250 + im.height + 70
        ok_mark(d, x0 + 44, cy, ok)
        d.text((x0 + 100, cy - 32), lab, font=bf(44), fill=GREEN if ok else RED)
    save(img, "corner")


def save_card():
    img, d = panel((330, 120, 1830, 840))
    center(d, 160, "저장하고, 매번 함께 첨부", tf(84), INK)
    d.rounded_rectangle([430, 300, 530, 345], 12, fill=GOLD)
    d.rounded_rectangle([430, 330, 610, 450], 16, fill=GOLD)
    d.text((640, 355), "기준그림/", font=bf(58), fill=INK)
    put(img, fit(SHEET, 230), 560, 520)
    d.text((820, 545), "malli_reference.png", font=mono(46), fill=INK)
    d.text((820, 605), "시트 그림", font=bf(38), fill=MUTED)
    d.rounded_rectangle([560, 680, 790, 770], 12, fill=(255, 255, 255, 255), outline=MUTED, width=4)
    for j in range(3):
        d.line([(585, 702 + j * 22), (765, 702 + j * 22)], fill=MUTED, width=5)
    d.text((820, 680), "malli_character.txt", font=mono(46), fill=INK)
    d.text((820, 735), "바꾸지 않는 특징 5가지", font=bf(38), fill=MUTED)
    save(img, "save")


def attach_card():
    img, d = panel((330, 80, 1830, 870))
    center(d, 105, "시트를 첨부할 때 한 줄", tf(80), INK)
    im0 = Image.open(IMG / "W02.png").convert("RGBA")
    im = fit(im0, 600)
    put(img, im, 400, 240)
    k = im.width / im0.width
    ring(d, [400 + 1020 * k, 240 + 30 * k, 400 + 1290 * k, 240 + 300 * k], RED, 8)
    ok_mark(d, 440, 240 + im.height + 55, False)
    d.text((490, 240 + im.height + 25), "구석에 작은 말리가 또", font=bf(42), fill=RED)
    d.rounded_rectangle([1050, 240, 1790, 760], 26, fill=GREEN_SOFT)
    for j, ln in enumerate(["Use the attached sheet", "ONLY for appearance and", "art style. Do NOT copy",
                            "its layout or small", "figures. Malli appears", "only ONCE."]):
        d.text((1090, 275 + j * 52), ln, font=mono(33), fill=INK)
    d.text((1090, 615), "생김새, 그림체만 참고", font=bf(40), fill=GREEN)
    d.text((1090, 670), "말리는 딱 한 번만", font=bf(40), fill=GREEN)
    save(img, "attach")


def summary():
    img, d = panel((330, 90, 1830, 870))
    center(d, 115, "오늘 정리", tf(84), INK)
    items = ["캐릭터 시트 = 그림 + 글 한 세트", "그림은 여섯 칸 (정면, 옆뒤, 얼굴, 동작, 방, 빈 공간)",
             "글은 바꾸지 않는 특징 다섯 가지", "만들면 검수 5개 → 저장", "그림 만들 때마다 첨부, 말리는 딱 한 번만"]
    for i, t in enumerate(items):
        y = 260 + i * 118
        badge(d, 450, y + 40, i + 1, GREEN, 34)
        d.text((510, y + 10), t, font=bf(46), fill=INK)
    save(img, "summary")


def end_card():
    img, d = panel((420, 230, 1740, 720))
    center(d, 280, "CHAPTER 1 ㆍ 2강 끝", bf(46), MUTED)
    center(d, 360, kk("말리 캐릭터 시트 만들기"), tf(104), GREEN)
    d.line([(680, 560), (1480, 560)], fill=(225, 210, 180), width=3)
    center(d, 600, "다음 강의 ▶ 그림체 기준 정하기", bf(52), INK)
    save(img, "end")


if __name__ == "__main__":
    title_card()
    sheet_full()
    set_card()
    zone_card(1, "front", "가운데 큰 정면 그림", "zone1")
    zone_card(2, "side", "옆모습과 뒷모습", "zone2")
    zone_face_walk()
    zone_card(5, "room", "작은 방 그림", "zone5")
    zone_empty()
    for n in range(1, 6):
        five_card(n)
    ears_card()
    tag_card()
    input_card()
    prompt_card()
    for i, n in enumerate(["prompt_a", "prompt_b", "prompt_c", "prompt_d"]):
        prompt_card(i, n)
    sheet_img_card("V1", "실제로 만든 첫 번째 시트 (V1)", "v1")
    sheet_img_card("V1", "고칠 곳 찾기", "v1_mark", [WALK_BOX])
    fixreq_card()
    sheet_img_card("V2", "고친 시트 (V2)", "v2")
    compare_card()
    mychar_card()
    for n in range(1, 6):
        checklist(n)
    ribbon_quiz(False)
    ribbon_quiz(True)
    ribbon_cmp()
    corner_card()
    save_card()
    attach_card()
    summary()
    end_card()


