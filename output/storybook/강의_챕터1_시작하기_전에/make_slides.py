# 강의 챕터1 「시작하기 전에」 — 슬라이드 렌더러 (무료, 로컬 PIL)
# 글자는 AI 이미지에 그리지 않고 여기서 렌더링 → 한글 깨짐 없음.
#  - s02~s07: 왼쪽 슬라이드 카드 + 오른쪽 말리 포즈(malli/sXX.png, gen_images 산출) 합성 → images/sXX.png
#  - s01·s08: 전체 화면 말리 그림(images/sXX.png, gen_images 산출)은 그대로 두고,
#             제목 카드만 투명 PNG(overlays/sXX.png)로 렌더 → compose 가 클립/Ken Burns 위에 얹음
# 말리 포즈가 아직 없으면 자리 표시 상자를 그려 레이아웃 미리보기용으로 쓸 수 있다.
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).parent
IMG = BASE / "images"
MALLI = BASE / "malli"
OVL = BASE / "overlays"
for d in (IMG, MALLI, OVL):
    d.mkdir(exist_ok=True)

W, H = 1920, 1080
BG = (251, 243, 228)
CARD = (255, 253, 248)
INK = (74, 52, 40)
SUB = (140, 112, 96)
PINK = (242, 120, 140)
PINK_SOFT = (253, 226, 230)
CREAM_DARK = (238, 222, 196)

TITLE_FONT = str(BASE / "font.ttf")              # 꾹꾹체 — 제목·배지
BODY_FONT = str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "fonts/malgunbd.ttf")     # 맑은 고딕 Bold — 본문 가독성


def font(path, size):
    return ImageFont.truetype(path, size)


# 표(사용자 제공 CHAPTER 1) 내용 그대로 — 시간은 강의별 분량
SLIDES = {
    "s02": {
        "no": "1-1", "min": "8분", "title": "반가워요, 말리예요",
        "items": ["말리와 크리에이터 소개", "완성작 미리보기 (한국어 · 영어)", "수강 후 손에 남는 것",
                  "강의 흐름 1분 요약: 캐릭터 → 이야기 → 목소리 → 영상"],
        "answer": "누가, 무엇을, 어떤 순서로",
    },
    "s03": {
        "no": "1-2", "min": "7분", "title": "나도 할 수 있을까요? 준비물 확인",
        "items": ["컴퓨터 사양 (운영체제 · 메모리)", "인터넷 연결", "코딩을 몰라도 되는 이유",
                  "기본 조작: 파일 저장, 폴더 만들기"],
        "answer": "내 컴퓨터로 되는지, 내가 할 수 있는지",
    },
    "s04": {
        "no": "1-3", "min": "10분", "title": "필요한 AI 도구와 요금제 고르기",
        "items": ["Claude  ·  이야기 쓰기와 작업 도우미", "VS Code  ·  우리가 작업하는 책상",
                  "Gemini  ·  그림과 목소리 만들기", "Higgsfield  ·  그림을 영상으로",
                  "무료와 유료 차이 · 가입 시점 · 한 편당 예상 비용"],
        "answer": "무엇을, 얼마에, 언제",
    },
    "s05": {
        "no": "1-4", "min": "8분", "title": "돈 걱정 없이 쓰는 법",
        "items": ["사용량 확인하기", "결제 한도 설정하기", "구독 해지 방법", "비용이 빨리 늘어나는 경우"],
        "answer": "요금 폭탄 걱정 해소",
    },
    "s06": {
        "no": "1-5", "min": "7분", "title": "이 강의 잘 듣는 법",
        "items": ["추천 수강 일정", "워크북 · 예시 파일 · 용어집 쓰는 법", "막혔을 때 Claude에게 묻는 법",
                  "코칭권 활용하기"],
        "answer": "얼마나 걸리는지, 막히면 어떻게",
    },
    "s07": {
        "no": "1-6", "min": "6분", "title": "시작 전 꼭 지킬 약속 5가지",
        "items": ["실제 아이 사진은 AI에 올리지 않기", "말리는 연습용 캐릭터", "저작권 걱정 없는 동화만",
                  "API 키는 나만 보기", "공개할 때 AI 생성 표시"],
        "answer": "무엇을 조심해야 하는지",
        "numbered": True,
    },
}

# 카드 영역 (자막이 바닥 MarginV=10 에 깔리므로 아래쪽은 비워 둔다)
CX0, CY0, CX1, CY1 = 70, 70, 1230, 900


def rounded_card(base, box, radius, fill, shadow=True):
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([box[0] + 8, box[1] + 14, box[2] + 8, box[3] + 14], radius,
                                             fill=(120, 90, 60, 60))
        base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(base).rounded_rectangle(box, radius, fill=fill)


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def header_chip(d):
    f = font(TITLE_FONT, 34)
    # 꾹꾹체에 가운뎃점 글리프가 없어 점은 직접 그린다
    a, b = "CHAPTER 1", "시작하기 전에"
    wa, wb = d.textlength(a, font=f), d.textlength(b, font=f)
    d.rounded_rectangle([CX0 + 50, CY0 + 40, CX0 + 50 + wa + wb + 92, CY0 + 96], 28, fill=PINK_SOFT)
    d.text((CX0 + 74, CY0 + 68), a, font=f, fill=PINK, anchor="lm")
    dx = CX0 + 74 + wa + 22
    d.ellipse([dx - 5, CY0 + 63, dx + 5, CY0 + 73], fill=PINK)
    d.text((dx + 22, CY0 + 68), b, font=f, fill=PINK, anchor="lm")


def draw_slide(canvas, s):
    rounded_card(canvas, (CX0, CY0, CX1, CY1), 40, CARD)
    d = ImageDraw.Draw(canvas)
    header_chip(d)

    # 강의 번호 배지 + 시간
    fb = font(TITLE_FONT, 44)
    d.rounded_rectangle([CX0 + 50, CY0 + 130, CX0 + 170, CY0 + 200], 20, fill=PINK)
    d.text((CX0 + 110, CY0 + 165), s["no"], font=fb, fill="white", anchor="mm")
    fm = font(BODY_FONT, 30)
    mw = d.textlength(s["min"], font=fm)
    d.rounded_rectangle([CX1 - 90 - mw, CY0 + 44, CX1 - 50, CY0 + 92], 24, outline=SUB, width=3)
    d.text((CX1 - 70 - mw / 2, CY0 + 68), s["min"], font=fm, fill=SUB, anchor="mm")

    # 제목 (길면 줄바꿈)
    ft = font(TITLE_FONT, 64)
    y = CY0 + 165
    for i, line in enumerate(wrap(d, s["title"], ft, CX1 - CX0 - 290)):
        d.text((CX0 + 200, y + i * 76), line, font=ft, fill=INK, anchor="lm")
    y += 76 * (len(wrap(d, s["title"], ft, CX1 - CX0 - 290)) - 1) + 80
    d.line([CX0 + 50, y, CX1 - 50, y], fill=CREAM_DARK, width=3)

    # 항목
    fi = font(BODY_FONT, 38 if len(s["items"]) <= 4 else 35)
    gap = 92 if len(s["items"]) <= 4 else 80
    y += 70
    for i, item in enumerate(s["items"]):
        cx, cy = CX0 + 92, y
        if s.get("numbered"):
            d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=PINK)
            d.text((cx, cy), str(i + 1), font=font(TITLE_FONT, 34), fill="white", anchor="mm")
        else:
            d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=PINK)
        d.text((CX0 + 140, cy), item, font=fi, fill=INK, anchor="lm")
        y += gap

    # 수강생이 얻는 답
    ay0 = CY1 - 130
    d.rounded_rectangle([CX0 + 40, ay0, CX1 - 40, CY1 - 40], 26, fill=PINK_SOFT)
    d.text((CX0 + 80, (ay0 + CY1 - 40) // 2), "수강생이 얻는 답", font=font(TITLE_FONT, 36), fill=PINK, anchor="lm")
    d.text((CX0 + 360, (ay0 + CY1 - 40) // 2), s["answer"], font=font(BODY_FONT, 36), fill=INK, anchor="lm")


def paste_malli(canvas, sid):
    """오른쪽 영역에 말리 포즈. 배경이 캔버스와 섞이도록 가장자리를 부드럽게 페더링."""
    box = (1210, 150, 1900, 1040)  # x0, y0, x1, y1
    bw, bh = box[2] - box[0], box[3] - box[1]
    src = MALLI / f"{sid}.png"
    if not src.exists():
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle(box, 30, outline=SUB, width=4)
        d.text(((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), f"말리 포즈\n({sid})", font=font(TITLE_FONT, 48),
               fill=SUB, anchor="mm", align="center")
        return
    im = Image.open(src).convert("RGBA")
    scale = min(bw / im.width, bh / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    m = 40
    ImageDraw.Draw(mask).rounded_rectangle([m, m, im.width - m, im.height - m], 60, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(28))
    im.putalpha(mask)
    canvas.alpha_composite(im, (box[0] + (bw - im.width) // 2, box[3] - im.height))


def title_overlay(sid):
    """s01·s08 전체 화면 그림 위에 얹는 반투명 제목 카드 (투명 PNG)."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    box = (80, 170, 960, 760)
    rounded_card(ov, box, 44, CARD + (236,))
    d = ImageDraw.Draw(ov)
    if sid == "s01":
        d.text((140, 260), "CHAPTER 1", font=font(TITLE_FONT, 56), fill=PINK, anchor="lm")
        d.text((140, 380), "시작하기 전에", font=font(TITLE_FONT, 110), fill=INK, anchor="lm")
        d.line([140, 470, 900, 470], fill=CREAM_DARK, width=3)
        lines = ["1-1  반가워요, 말리예요", "1-2  준비물 확인", "1-3  AI 도구와 요금제",
                 "1-4  돈 걱정 없이 쓰는 법", "1-5  이 강의 잘 듣는 법", "1-6  꼭 지킬 약속 5가지"]
        f = font(BODY_FONT, 30)
        for i, ln in enumerate(lines):
            d.text((150 + (i // 3) * 400, 530 + (i % 3) * 64), ln, font=f, fill=INK, anchor="lm")
    else:
        d.text((140, 270), "준비 끝!", font=font(TITLE_FONT, 120), fill=PINK, anchor="lm")
        checks = ["무엇을 만드는지", "무엇이 필요한지", "무엇을 조심할지"]
        f = font(BODY_FONT, 40)
        for i, c in enumerate(checks):
            y = 410 + i * 80
            d.rounded_rectangle([150, y - 22, 194, y + 22], 10, fill=PINK)
            # 맑은 고딕에 ✓ 글리프가 없어 선으로 그린다
            d.line([(160, y + 1), (169, y + 10), (185, y - 9)], fill="white", width=6, joint="curve")
            d.text((222, y), c, font=f, fill=INK, anchor="lm")
        d.text((140, 680), "다음 챕터에서 만나요", font=font(TITLE_FONT, 56), fill=INK, anchor="lm")
    ov.save(OVL / f"{sid}.png")
    print(f"{sid}: overlay")


if __name__ == "__main__":
    for sid, s in SLIDES.items():
        # 말리 포즈 배경색(모서리 평균)을 캔버스 배경으로 → 합성 경계 사각형이 안 보이게
        mp = MALLI / f"{sid}.png"
        bg = BG
        if mp.exists():
            px = Image.open(mp).convert("RGB")
            pts = [px.getpixel((x, y)) for x in (5, px.width - 6) for y in (5, px.height - 6)]
            bg = tuple(sum(c[i] for c in pts) // len(pts) for i in range(3))
        canvas = Image.new("RGBA", (W, H), bg + (255,))
        draw_slide(canvas, s)
        paste_malli(canvas, sid)
        canvas.convert("RGB").save(IMG / f"{sid}.png")
        print(f"{sid}: slide {'(malli)' if (MALLI / f'{sid}.png').exists() else '(placeholder)'}")
    for sid in ("s01", "s08"):
        title_overlay(sid)
