# 강의 CH1-1 — 글자 카드 로컬 렌더 (무료). 1920x1080 RGBA 오버레이 → cards/*.png
# 제목 = 꾹꾹체(font.ttf, '·' 글리프 없음 → 'ㆍ' 치환), 본문 = 맑은 고딕 Bold. ✓·✗ 는 글리프가 없어 도형으로 그림.
# 아래 18%(y>885)는 자막 자리라 비워 둔다.
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


def panel(box=(210, 90, 1710, 860)):
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


# ---------- 카드 ----------
def title_card():
    img, d = panel((360, 250, 1560, 700))
    center(d, 300, "CHAPTER 1 ㆍ 1강", bf(44), MUTED)
    center(d, 380, kk("5~7세 영상 규칙"), tf(150), GREEN)
    center(d, 590, "아이를 지켜 주는 약속 8가지", bf(46), INK)
    save(img, "title")


def eight_card():
    img, d = panel((310, 220, 1610, 760))
    center(d, 260, "약속은 모두 8가지", tf(92), INK)
    for x0, title, n, color, soft in [(380, "형식 약속", 3, GREEN, GREEN_SOFT), (990, "안전 약속", 5, RED, RED_SOFT)]:
        d.rounded_rectangle([x0, 420, x0 + 550, 700], 36, fill=soft)
        tw = d.textlength(title, font=bf(60))
        d.text((x0 + 275 - tw / 2, 455), title, font=bf(60), fill=color)
        nw = d.textlength(f"{n}개", font=tf(130))
        d.text((x0 + 275 - nw / 2, 535), f"{n}개", font=tf(130), fill=color)
    save(img, "eight")


def three_words(hi=None, name="three"):
    img, d = panel((260, 230, 1660, 740))
    center(d, 265, "형식 약속 3가지", tf(84), INK)
    for i, word in enumerate(["짧게", "쉽게", "하나만"]):
        x0 = 330 + i * 430
        on = hi is None or hi == i
        d.rounded_rectangle([x0, 420, x0 + 400, 680], 36, fill=GREEN_SOFT if on else (238, 236, 228, 255))
        badge(d, x0 + 200, 480, i + 1, GREEN if on else MUTED, 36)
        ww = d.textlength(word, font=tf(110))
        d.text((x0 + 200 - ww / 2, 540), word, font=tf(110), fill=GREEN if on else MUTED)
    save(img, name)


def rule_card(n, head, lines, color=GREEN, name=None, box=(260, 120, 1660, 860)):
    img, d = panel(box)
    badge(d, box[0] + 110, box[1] + 105, n, color, 52)
    d.text((box[0] + 190, box[1] + 50), kk(head), font=tf(88), fill=color)
    y = box[1] + 200
    for ln in lines:
        if isinstance(ln, tuple):  # (마크, 문장) — 비교 줄
            mark, text = ln
            if mark == "X":
                d.rounded_rectangle([box[0] + 70, y - 12, box[2] - 70, y + 92], 26, fill=RED_SOFT)
                cross(d, box[0] + 130, y + 40, 22)
            elif mark == "O":
                d.rounded_rectangle([box[0] + 70, y - 12, box[2] - 70, y + 92], 26, fill=GREEN_SOFT)
                d.ellipse([box[0] + 104, y + 14, box[0] + 156, y + 66], outline=GREEN, width=9)
            else:
                d.ellipse([box[0] + 118, y + 28, box[0] + 142, y + 52], fill=color)
            d.text((box[0] + 190, y + 6), text, font=bf(54), fill=INK)
            y += 122 if len(lines) < 4 else 112
        else:
            d.text((box[0] + 110, y + 6), ln, font=bf(50), fill=MUTED)
            y += 96
    save(img, name or f"rule{n}")


def quiz_card(q, answer=None, name="quiz"):
    img, d = panel((210, 150, 1710, 840))
    d.rounded_rectangle([270, 200, 470, 290], 30, fill=GOLD)
    d.text((300, 205), "퀴즈", font=tf(70), fill="white")
    y = 330
    for ln in q:
        center(d, y, ln, bf(62), INK)
        y += 92
    for cx, mark in [(760, "O"), (1160, "X")]:
        hit = answer == mark
        d.rounded_rectangle([cx - 120, 560, cx + 120, 760], 40,
                            fill=(RED_SOFT if mark == "X" else GREEN_SOFT) if hit or answer is None else (240, 238, 232, 255),
                            outline=(RED if mark == "X" else GREEN) if hit else (225, 215, 195, 255), width=8 if hit else 3)
        ox(d, cx, 660, mark, 62)
    save(img, name)


def quiz_answer(head, lines, name):
    img, d = panel((210, 170, 1710, 820))
    cross(d, 360, 300, 46)
    d.text((440, 235), head, font=tf(92), fill=RED)
    y = 420
    for mark, text in lines:
        d.rounded_rectangle([290, y - 12, 1630, y + 96], 26, fill=GREEN_SOFT if mark == "O" else RED_SOFT)
        if mark == "O":
            d.ellipse([320, y + 14, 376, y + 70], outline=GREEN, width=9)
        else:
            cross(d, 348, y + 42, 24)
        d.text((410, y + 8), text, font=bf(54), fill=INK)
        y += 140
    save(img, name)


def rulebook():
    img, d = panel((260, 150, 1660, 830))
    d.rounded_rectangle([320, 210, 1600, 770], 22, fill=(36, 40, 48, 255))
    d.rounded_rectangle([320, 210, 1600, 280], 22, fill=(58, 63, 74, 255))
    d.rectangle([320, 250, 1600, 280], fill=(58, 63, 74, 255))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([350 + i * 40, 232, 374 + i * 40, 256], fill=c)
    d.text((500, 222), "CLAUDE.md  (규칙서)", font=bf(34), fill=(200, 205, 214))
    rows = [("# 꼭 지킬 것", (120, 200, 255), False), ("- 5~7세 아이용 영상", (230, 232, 236), True),
            ("- 죽음·폭력은 바꿔 말하기", (230, 232, 236), True), ("- 결말은 언제나 밝게", (230, 232, 236), True),
            ("- 따라 하면 위험한 행동은 멋있게 그리지 않기", (150, 156, 166), False)]
    y = 320
    for text, color, hi in rows:
        if hi:
            d.rounded_rectangle([360, y - 8, 1560, y + 70], 12, fill=(80, 70, 30, 255))
        d.text((390, y), text, font=bf(48), fill=(255, 226, 120) if hi else color)
        y += 88
    save(img, "rulebook")


def checklist(k, passed=False):
    img, d = panel((210, 150, 1710, 840))
    center(d, 185, "완성 후 점검 질문 3개", tf(84), INK)
    qs = ["아이 옆에 앉아 같이 끝까지 볼 수 있나요?", "오늘 밤 이 장면 때문에 무서운 꿈을 꾸지 않을까요?",
          "아이가 따라 해도 괜찮은 행동인가요?"]
    for i, q in enumerate(qs):
        y = 350 + i * 140
        on = i < k
        d.rounded_rectangle([290, y - 14, 1630, y + 100], 28, fill=GREEN_SOFT if on else (243, 240, 232, 255))
        d.rounded_rectangle([320, y + 8, 390, y + 78], 14, outline=GREEN if on else MUTED, width=6, fill="white")
        if on:
            check(d, 330, y + 18, 50)
        d.text((420, y + 12), f"{i + 1}. {q}", font=bf(50), fill=INK if on else MUTED)
    if passed:
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.ellipse([1440, 150, 1700, 360], outline=RED + (230,), width=12)
        sd.text((1485, 200), "통과", font=tf(100), fill=RED + (230,))
        img = Image.alpha_composite(img, st.rotate(-12, center=(1570, 255)))
    save(img, f"check{k}{'_pass' if passed else ''}")


def summary():
    img, d = panel((160, 110, 1760, 870))
    center(d, 140, "오늘 배운 약속 8가지", tf(84), INK)
    items = ["짧게: 3~4분, 10장면", "쉽게: 한 문장 15자, 아는 단어", "하나만: 교훈 하나, 마지막 한 줄",
             "죽음 → 잠들기·떠나기·돌아오기", "폭력 → 혼내 주기·사과·화해", "무서움은 깜짝까지만",
             "위험한 행동은 멋있게 X", "놀림·따돌림·종교·정치 X"]
    for i, t in enumerate(items):
        col, row = divmod(i, 4) if False else (i // 4, i % 4)
        x, y = 210 + col * 800, 300 + row * 135
        color = GREEN if i < 3 else RED
        badge(d, x + 40, y + 45, i + 1, color, 36)
        d.text((x + 100, y + 12), t, font=bf(46), fill=INK)
    save(img, "summary")


def end_card():
    img, d = panel((360, 230, 1560, 720))
    center(d, 280, "CHAPTER 1 ㆍ 1강 끝", bf(46), MUTED)
    center(d, 360, kk("5~7세 영상 규칙"), tf(120), GREEN)
    d.line([(560, 560), (1360, 560)], fill=(225, 210, 180), width=3)
    center(d, 600, "다음 강의 ▶ 말리 캐릭터 시트 만들기", bf(52), INK)
    save(img, "end")


if __name__ == "__main__":
    title_card()
    eight_card()
    three_words()
    rule_card(1, "짧게", [("•", "한 편은 3~4분"), ("•", "장면은 10개 정도"), "아이가 한 번에 집중하는 길이예요"])
    rule_card(2, "쉽게", [("•", "한 문장은 15자 안팎"), ("X", "그는 매우 나태했습니다"), ("O", "돌쇠는 일하기가 싫었어요")])
    rule_card(3, "하나만", [("•", "교훈은 한 편에 하나"), ("•", "설교 대신 이야기로 보여 주기"), ("•", "마지막에 딱 한 줄로 정리")])
    rule_card(4, "죽음은 보여 주지 않아요", [("•", "잠들기 · 멀리 떠나기 · 원래대로 돌아오기"),
              ("X", "무를 먹으면 죽는다"), ("O", "일하는 기쁨을 알면 사람으로 돌아온다"), ("O", "독사과 → 한숨 푹 잠드는 사과")], RED)
    rule_card(5, "때리고 벌주지 않아요", [("•", "혼내 주기 · 사과하기 · 화해하기"),
              ("X", "욕심쟁이가 매를 맞는다"), ("O", "깜짝 놀라 도망가고 스스로 반성한다")], RED)
    rule_card(6, "무서움은 깜짝까지만", [("•", "놀란 다음엔 바로 안심시키기"), ("X", "캄캄한 어둠 · 괴물 얼굴 크게 · 큰 소리"),
              ("O", "결말은 언제나 밝게")], RED)
    rule_card(7, "위험한 행동은 멋있게 그리지 않아요", [("X", "높은 곳에서 뛰어내리기"), ("X", "불장난"),
              ("X", "모르는 사람 따라가기"), ("O", "꼭 나오면 \"그러면 안 돼요\"로 마무리")], RED)
    rule_card(8, "놀리거나 편 가르지 않아요", [("X", "생김새 놀리기 · 따돌리기"), ("X", "특정 종교 · 정치 이야기"),
              ("O", "놀림은 짧게, 사과하고 함께 노는 장면은 길게")], RED)
    quiz_card(["늑대가 아기 염소를 꿀꺽 삼키는 장면,", "그대로 보여 줘도 될까요?"], None, "quiz1")
    quiz_card(["늑대가 아기 염소를 꿀꺽 삼키는 장면,", "그대로 보여 줘도 될까요?"], "X", "quiz1_x")
    quiz_answer("정답은 X", [("X", "늑대가 아기 염소를 삼킨다"), ("O", "벽장에 가두고, 엄마 염소가 금방 구해 줘요")], "quiz1_ans")
    quiz_card(["주인공이 우산을 펴고", "높은 나무에서 뛰어내리는 장면은요?"], None, "quiz2")
    quiz_card(["주인공이 우산을 펴고", "높은 나무에서 뛰어내리는 장면은요?"], "X", "quiz2_x")
    quiz_answer("정답은 X", [("X", "우산 펴고 높은 나무에서 뛰어내리기"), ("O", "사다리로 천천히 내려오기")], "quiz2_ans")
    rulebook()
    for k in (1, 2, 3):
        checklist(k)
    checklist(3, passed=True)
    summary()
    end_card()
