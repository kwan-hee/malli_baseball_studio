# 강의 소개 영상 — 화면 렌더러 (콘티 '화면 지시' 78장면 → 무음 영상 _video.mp4)
# 배경·말리 포즈·예시 그림은 Gemini 이미지, 카드·아이콘·흐름도·이름표·말풍선은 여기서 로컬 렌더(무료)
# 테스트 버전 임시 화면: 조이님 프로필·유튜브/블로그 캡처·하린 완성작 클립 (자료 받으면 교체)
# 사용: python render.py            → 전체 렌더
#       python render.py S02-05 2.0 → 해당 장면 2.0초 시점 프레임만 png 로 (미리보기)
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from subs import CUES
from timeline import TIMELINE, TOTAL

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
ROOT = [_p for _p in BASE.resolve().parents if (_p / "AGENTS.md").is_file()][-1]
IMG, MALLI_DIR, CLIPS = BASE / "images", BASE / "malli", BASE / "clips"
W, H, FPS = 1280, 720, 25
FONT = str(BASE / "font.ttf")
GOTHIC = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"

INK = (92, 66, 52)
SOFT = (150, 128, 112)
GRAY = (150, 150, 150)
CREAM = (250, 244, 232)
ACCENT = (232, 120, 110)
GOLD = (236, 176, 64)

# 클립 장면: (클립, 클립 내 시작, 끝) — 장면 길이에 맞춰 배속
CLIP_SCENES = {"S01-02": ("open", 0.0, 6.0), "S01-03": ("open", 6.0, 8.0), "S06-13": ("close", 0.0, 8.0)}


# ---------------------------------------------------------------------------
# 그리기 도구
# ---------------------------------------------------------------------------

def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, x):
    return a + (b - a) * x


@lru_cache(None)
def font(size, kind="kk"):
    return ImageFont.truetype(FONT if kind == "kk" else GOTHIC, size)


@lru_cache(None)
def text_sprite(txt, size, color=INK, kind="kk", stroke=0, stroke_color=(255, 255, 255)):
    f = font(size, kind)
    if kind == "kk":
        txt = txt.replace("·", "ㆍ")  # 꾹꾹체에 U+00B7 글리프 없음 → 한글 가운뎃점
    lines = txt.split("\n")
    boxes = [f.getbbox(l or " ", stroke_width=stroke) for l in lines]
    lh = int(size * 1.3)
    w = max(b[2] - b[0] for b in boxes) + 12
    h = lh * len(lines) + 12
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for i, (l, b) in enumerate(zip(lines, boxes)):
        x = (w - (b[2] - b[0])) // 2 - b[0]
        d.text((x, 6 + i * lh), l, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_color)
    return im


@lru_cache(None)
def emoji_sprite(e, size):
    e = e.replace("️", "")
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new("RGBA", (220 * max(1, len(e)), 220))
    ImageDraw.Draw(im).text((10, 10), e, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return fit(im, size, size)


def fit(im, w, h):
    r = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)


@lru_cache(None)
def load(path):
    return Image.open(path).convert("RGBA")


@lru_cache(None)
def image_sprite(path, w, h, gray=False, rounded=0):
    im = fit(load(path), w, h)
    if gray:
        im = ImageOps.grayscale(im.convert("RGB")).convert("RGBA")
        im = ImageEnhance.Brightness(im).enhance(1.15)
    if rounded:
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), rounded, fill=255)
        im.putalpha(m)
    return im


@lru_cache(None)
def silhouette(path, w, h):
    im = fit(load(path), w, h)
    a = im.getchannel("A")
    # 크림 종이 배경 그림 → 밝기로 대략적인 형태만 남겨 회색 실루엣
    lum = ImageOps.grayscale(im.convert("RGB")).point(lambda v: 255 if v < 215 else 0)
    lum = lum.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1))
    out = Image.new("RGBA", im.size, (120, 120, 130, 0))
    out.putalpha(Image.fromarray(__import__("numpy").minimum(__import__("numpy").array(lum), __import__("numpy").array(a))))
    return out


@lru_cache(None)
def card_sprite(w, h, fill=(255, 255, 255), radius=28, border=None, shadow=True):
    pad = 24
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2))
    if shadow:
        sh = Image.new("RGBA", im.size)
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 8, pad + w, pad + h + 8), radius, fill=(90, 60, 40, 70))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius, fill=fill,
                        outline=border, width=4 if border else 0)
    return im


def paste(canvas, sprite, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    sp = sprite
    if abs(scale - 1) > 0.005:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.1:
        sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.99:
        sp = sp.copy()
        sp.putalpha(sp.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - sp.width / 2), int(cy - sp.height / 2)
    if x >= canvas.width or y >= canvas.height or x + sp.width <= 0 or y + sp.height <= 0:
        return  # 화면 밖 (슬라이드 인/아웃 중)
    sx, sy = max(-x, 0), max(-y, 0)
    sp = sp.crop((sx, sy, min(sp.width, canvas.width - x), min(sp.height, canvas.height - y)))
    canvas.alpha_composite(sp, (max(x, 0), max(y, 0)))


@lru_cache(None)
def background(name):
    if name == "black":
        return Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if name in ("cover", "field", "book"):
        src = {"cover": "B1", "field": "B2", "book": "B3"}[name]
        return ImageOps.fit(load(IMG / f"{src}.png"), (W, H), Image.LANCZOS)
    if name == "field_blur":
        return background("field").filter(ImageFilter.GaussianBlur(6))
    if name == "paper":
        import numpy as np

        rng = np.random.default_rng(3)
        n = rng.normal(0, 1, (H // 4, W // 4))
        n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype("uint8"))
                     .resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))) / 255.0
        base = np.array(CREAM, dtype=float)[None, None, :] * (0.97 + 0.04 * n[..., None])
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - 0.07 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        img = np.clip(base * vig[..., None], 0, 255).astype("uint8")
        return Image.fromarray(img).convert("RGBA")
    if name == "cinema":
        return Image.new("RGBA", (W, H), (28, 24, 30, 255))
    raise KeyError(name)


@lru_cache(None)
def malli_sprite(pose, h, flip=False):
    im = load(MALLI_DIR / f"{pose}.png")
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    return ImageOps.mirror(im) if flip else im


# 말리 위치: 가운데 큰 말리 / 오른쪽 아래 구석 작은 말리
CENTER = (640, 610, 360)   # x, 발 y, 키
CORNER = (1170, 632, 165)


class Ctx:
    def __init__(self, canvas, t, d):
        self.c, self.t, self.d = canvas, t, d

    def f(self, frac):
        return frac * self.d

    def appear(self, at, dur=0.35, out=None, out_dur=0.3):
        """at/out = 장면 길이 대비 비율. (scale, alpha) 반환."""
        t0 = self.f(at)
        if self.t < t0:
            return 0.0, 0.0
        x = (self.t - t0) / dur
        s, a = 0.6 + 0.4 * ease_back(x), ease_out(x * 1.5)
        if out is not None:
            t1 = self.f(out)
            if self.t >= t1:
                y = ease_out((self.t - t1) / out_dur)
                s, a = s * (1 - 0.4 * y), a * (1 - y)
        return s, a

    def pop(self, sprite, x, y, at=0.0, out=None, scale=1.0, dur=0.35, rot=0.0):
        s, a = self.appear(at, dur, out)
        paste(self.c, sprite, x, y, s * scale, a, rot)

    def text(self, txt, x, y, size=40, at=0.0, out=None, color=INK, kind="kk", stroke=0):
        self.pop(text_sprite(txt, size, color, kind, stroke), x, y, at, out)

    def emoji(self, e, x, y, size=120, at=0.0, out=None, scale=1.0):
        self.pop(emoji_sprite(e, size), x, y, at, out, scale)

    def card(self, x, y, w, h, at=0.0, out=None, fill=(255, 255, 255), border=None, scale=1.0):
        self.pop(card_sprite(w, h, fill, 28, border), x, y, at, out, scale)

    def malli(self, pose, pos=CENTER, anim=None, flip=False, at=0.0, out=None, alpha=1.0):
        x, foot, h = pos
        dx = dy = rot = 0.0
        t = self.t
        if anim == "wag":
            rot = 2.0 * math.sin(t * 2 * math.pi * 1.6)
        elif anim == "fastwag":
            rot = 3.5 * math.sin(t * 2 * math.pi * 6)
            dx = 3 * math.sin(t * 2 * math.pi * 6)
        elif anim == "bounce":
            dy = -abs(math.sin(t * 2 * math.pi * 1.2)) * h * 0.04
        elif anim == "nod":
            dy = max(0.0, math.sin(t * 2 * math.pi * 1.4)) * h * 0.035
        elif anim == "breathe":
            dy = math.sin(t * 2 * math.pi * 0.5) * h * 0.01
        sp = malli_sprite(pose, int(h), flip)
        s, a = self.appear(at, 0.3, out) if (at or out is not None) else (1.0, 1.0)
        paste(self.c, sp, x + dx, foot - h / 2 + dy, s, a * alpha, rot)

    def malli_move(self, pose, p0, p1, start=0.0, dur=0.5, flip=False, hop=True):
        """p0 → p1 이동 (start: 비율, dur: 초). 이동 중 깡충."""
        x = ease_out((self.t - self.f(start)) / dur)
        pos = tuple(lerp(a, b, x) for a, b in zip(p0, p1))
        sp = malli_sprite(pose, int(pos[2]), flip)
        dy = -math.sin(math.pi * x) * 40 if hop and 0 < x < 1 else 0
        paste(self.c, sp, pos[0], pos[1] - pos[2] / 2 + dy)

    def particles(self, e, x, y, at=0.3, n=3, size=44, rise=120, life=1.6):
        t0 = self.f(at)
        for i in range(n):
            k = (self.t - t0 - i * 0.18) / life
            if 0 <= k <= 1:
                px = x + (i - (n - 1) / 2) * 70 + 12 * math.sin(k * 6 + i)
                paste(self.c, emoji_sprite(e, size), px, y - rise * k, 0.7 + 0.5 * k, 1 - k ** 2)

    def sparkle(self, x, y, at=0.0, n=4, r=90, size=34):
        t0 = self.f(at)
        for i in range(n):
            k = ((self.t - t0) * 1.2 + i / n) % 1.0
            if self.t >= t0:
                ang = i * 2 * math.pi / n + 0.5
                paste(self.c, emoji_sprite("✨", size), x + r * math.cos(ang), y + r * math.sin(ang),
                      0.6 + 0.6 * math.sin(math.pi * k), math.sin(math.pi * k))


# 이름표 (🐶 말리 / 🎙️ 릴리) — 왼쪽 아래, 자막 위
@lru_cache(None)
def nametag_sprite(who):
    em, name, col = {"malli": ("🐶", "말리", (255, 236, 214)), "lily": ("🎙️", "릴리", (231, 236, 255))}[who]
    tx = text_sprite(name, 34, INK)
    w = 70 + tx.width + 20
    im = card_sprite(w, 62, col, 31, None, True).copy()
    im.alpha_composite(emoji_sprite(em, 40), (24 + 16, 24 + 11))
    im.alpha_composite(tx, (24 + 64, 24 + (62 - tx.height) // 2))
    return im


def draw_nametag(ctx, who, slide_in=False, slide_out=False):
    sp = nametag_sprite(who)
    x = 30 + sp.width / 2
    y = 520  # 두 줄 자막(위끝 ~y565)과 겹치지 않게
    if slide_in:
        k = ease_out(ctx.t / 0.6)
        x = lerp(-sp.width, x, k)
    if slide_out:
        k = ease_out(ctx.t / 0.5)
        x = lerp(x, -sp.width, k)
    paste(ctx.c, sp, x, y)


# ---------------------------------------------------------------------------
# 공통 소품
# ---------------------------------------------------------------------------

def joy_card(ctx, x, y, at=0.0, out=None, scale=1.0):
    """[테스트 임시] 조이 선생님 프로필 — 이름만 있는 카드."""
    s, a = ctx.appear(at, 0.35, out)
    sp = joy_card_sprite()
    paste(ctx.c, sp, x, y, s * scale, a)


@lru_cache(None)
def joy_card_sprite():
    im = card_sprite(300, 360, (255, 255, 255)).copy()
    d = ImageDraw.Draw(im)
    d.ellipse((24 + 75, 24 + 40, 24 + 225, 24 + 190), fill=(255, 226, 205))
    im.alpha_composite(text_sprite("J", 96, (210, 140, 110)), (24 + 120, 24 + 52))
    tx = text_sprite("조이 선생님", 40, INK)
    im.alpha_composite(tx, (24 + (300 - tx.width) // 2, 24 + 220))
    tx2 = text_sprite("(프로필 사진 자리)", 22, GRAY, "gothic")
    im.alpha_composite(tx2, (24 + (300 - tx2.width) // 2, 24 + 290))
    return im


@lru_cache(None)
def lily_card_sprite(caption=None):
    sheet = load(ROOT / "images/style_ref/lily.png")
    fig = sheet.crop((690, 20, 970, 900))  # 정면 전신
    fig = fit(fig, 230, 330)
    h = 360 + (60 if caption else 0)
    im = card_sprite(300, h, (255, 255, 255)).copy()
    im.alpha_composite(fig, (24 + (300 - fig.width) // 2, 24 + 15))
    if caption:
        tx = text_sprite(caption, 30, INK)
        im.alpha_composite(tx, (24 + (300 - tx.width) // 2, 24 + 352))
    return im


@lru_cache(None)
def malli_card_sprite():
    im = card_sprite(300, 360, (255, 255, 255)).copy()
    m = malli_sprite("M1", 300)
    im.alpha_composite(m, (24 + (300 - m.width) // 2, 24 + 30))
    return im


@lru_cache(None)
def labeled_card(path, w, h, label, gray=False):
    pic = image_sprite(path, w, h, gray, 18)
    tx = text_sprite(label, 28, INK) if label else None
    ch = pic.height + (50 if tx else 0) + 20
    im = card_sprite(pic.width + 20, ch).copy()
    im.alpha_composite(pic, (24 + 10, 24 + 10))
    if tx:
        im.alpha_composite(tx, (24 + (pic.width + 20 - tx.width) // 2, 24 + pic.height + 18))
    return im


@lru_cache(None)
def icon_tile(e, label, size=110, w=230):
    em = emoji_sprite(e, size)
    tx = text_sprite(label, 30, INK)
    im = Image.new("RGBA", (max(w, tx.width + 10), size + 60))
    im.alpha_composite(em, ((im.width - em.width) // 2, 0))
    im.alpha_composite(tx, ((im.width - tx.width) // 2, size + 10))
    return im


def icon_row(ctx, items, y=330, ats=None, size=110):
    n = len(items)
    gap = min(330, 1000 // max(n, 1))
    for i, (e, label) in enumerate(items):
        x = 640 + (i - (n - 1) / 2) * gap
        at = ats[i] if ats else 0.1 + i * 0.8 / n
        ctx.pop(icon_tile(e, label, size), x, y, at)


@lru_cache(None)
def bubble_sprite(txt, size=44):
    tx = text_sprite(txt, size, INK)
    w, h = tx.width + 50, tx.height + 30
    im = Image.new("RGBA", (w + 8, h + 34))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, w + 4, h + 4), 30, fill=(255, 255, 255), outline=(220, 200, 185), width=3)
    d.polygon([(w * 0.25, h + 2), (w * 0.2, h + 30), (w * 0.38, h + 2)], fill=(255, 255, 255))
    im.alpha_composite(tx, (29, 19))
    return im


@lru_cache(None)
def title_card(txt, size=56, w=None, fill=(255, 250, 240)):
    tx = text_sprite(txt, size, INK)
    cw = w or tx.width + 90
    im = card_sprite(cw, tx.height + 50, fill).copy()
    im.alpha_composite(tx, (24 + (cw - tx.width) // 2, 24 + 25))
    return im


@lru_cache(None)
def arrow_sprite(length, color=SOFT, width=8):
    im = Image.new("RGBA", (int(length) + 30, 40))
    d = ImageDraw.Draw(im)
    d.line((0, 20, length, 20), fill=color, width=width)
    d.polygon([(length + 25, 20), (length - 5, 4), (length - 5, 36)], fill=color)
    return im


def arrow(ctx, x0, x1, y, at=0.0, dur=0.6):
    k = ease_out((ctx.t - ctx.f(at)) / dur)
    if k <= 0:
        return
    L = (x1 - x0) * k
    paste(ctx.c, arrow_sprite(max(L, 6)), x0 + (L + 30) / 2, y)


@lru_cache(None)
def placeholder_panel(title, sub, color, w=520, h=300):
    im = card_sprite(w, h, (255, 255, 255)).copy()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 24, 24 + w, 24 + 64), 28, fill=color)
    d.rectangle((24, 24 + 34, 24 + w, 24 + 64), fill=color)
    tx = text_sprite(title, 34, (255, 255, 255))
    im.alpha_composite(tx, (24 + 24, 24 + 8))
    for i in range(3):
        d.rounded_rectangle((24 + 30 + i * 160, 24 + 100, 24 + 170 + i * 160, 24 + 190), 12, fill=(238, 232, 224))
    s2 = text_sprite(sub, 22, GRAY, "gothic")
    im.alpha_composite(s2, (24 + (w - s2.width) // 2, 24 + 225))
    return im


@lru_cache(None)
def code_panel():
    w, h = 620, 380
    im = card_sprite(w, h, (30, 32, 40), 18).copy()
    d = ImageDraw.Draw(im)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((24 + 18 + i * 24, 24 + 14, 24 + 32 + i * 24, 24 + 28), fill=c)
    d.text((24 + 110, 24 + 10), "make_narration.py — VS Code", font=font(16, "g"), fill=(170, 170, 180))
    lines = [
        ("# 말리 동화 나레이션 만들기", (110, 160, 110)),
        ('VOICE = "Kore"', (156, 220, 254)),
        ('MODEL = "gemini-3.8-flash-tts"', (156, 220, 254)),
        ('API_KEY = "AIzaSyD0-xxxxxxxxxxxxxxx"', (206, 145, 120)),
        ("", None),
        ("def generate_full():", (220, 220, 170)),
        ("    for sid, text in SCENES.items():", (212, 212, 212)),
        ('        style = BASE_STYLE + SCENE_STYLES[sid]', (212, 212, 212)),
        ("        speak(text, style)", (212, 212, 212)),
        ("", None),
        ("split_scenes()  # Whisper 로 장면 나누기", (212, 212, 212)),
    ]
    for i, (l, c) in enumerate(lines):
        if not l:
            continue
        y = 24 + 50 + i * 28
        d.text((24 + 16, y), f"{i + 1:>2}", font=font(17, "g"), fill=(110, 110, 120))
        d.text((24 + 56, y), l, font=font(18, "g"), fill=c)
    # API 키 줄 흐리게 (콘티: API 키와 개인 파일은 흐리게)
    box = (24 + 56, 24 + 50 + 3 * 28 - 2, 24 + w - 20, 24 + 50 + 3 * 28 + 26)
    region = im.crop(box).filter(ImageFilter.GaussianBlur(7))
    im.paste(region, box[:2])
    return im


# 선물 상자
BOX_CONTENT = {1: ("🎬", "동화 영상 1편"), 2: ("🌍", "영어 버전"), 3: ("🛠️", "제작 프로그램"),
               4: ("🧸", "주인공 얼굴"), 5: ("📚", "규칙서 묶음"), 6: ("📱", "동화 앱"), 7: ("💡", "AI에게 맡기는 법")}
NUM = {1: "1", 2: "2", 3: "3", 4: "④", 5: "⑤", 6: "⑥", 7: "⑦"}


@lru_cache(None)
def box_sprite(n, opened, size=150, glow=False):
    if opened:
        e, label = BOX_CONTENT[n]
        im = Image.new("RGBA", (int(size * 1.6), int(size * 1.45)))
        d = ImageDraw.Draw(im)
        cx = im.width // 2
        d.ellipse((cx - size * 0.55, 0, cx + size * 0.55, size * 1.1), fill=(255, 255, 255),
                  outline=GOLD if glow else (235, 215, 190), width=10 if glow else 4)
        em = emoji_sprite(e, int(size * 0.62))
        im.alpha_composite(em, (cx - em.width // 2, int(size * 0.55 - em.height / 2)))
        tx = text_sprite(label, max(20, int(size * 0.2)), INK)
        im.alpha_composite(tx, (cx - tx.width // 2, int(size * 1.12)))
        return im
    em = emoji_sprite("🎁", size)
    im = Image.new("RGBA", (em.width + 20, em.height + 20))
    im.alpha_composite(em, (10, 20))
    d = ImageDraw.Draw(im)
    r = size * 0.2
    d.ellipse((0, 0, 2 * r, 2 * r), fill=(255, 255, 255), outline=ACCENT, width=4)
    tx = text_sprite(NUM[n] if n <= 3 else str(n), int(r * 1.1), ACCENT, "gothic")
    im.alpha_composite(tx, (int(r - tx.width / 2), int(r - tx.height / 2)))
    return im


BIG_POS = {1: (340, 300), 2: (640, 300), 3: (940, 300)}
SMALL_TOP = {1: (400, 120), 2: (640, 120), 3: (880, 120)}
SMALL_ROW = {4: (250, 420), 5: (520, 420), 6: (790, 420), 7: (1060, 420)}


def boxes(ctx, opened, big=True, small=False, opening=None, small_opening=None, drop_at=None):
    """opened: 이미 열린 상자 번호 set. opening: 이 장면에서 열리는 상자(0.15에 열림)."""
    for n in (1, 2, 3):
        is_open = n in opened or (n == opening and ctx.t >= ctx.f(0.12))
        if big:
            x, y = BIG_POS[n]
            sp = box_sprite(n, is_open, 170)
            if drop_at is not None:
                k = ease_back((ctx.t - ctx.f(drop_at + 0.12 * (n - 1))) / 0.5)
                if ctx.t < ctx.f(drop_at + 0.12 * (n - 1)):
                    continue
                paste(ctx.c, sp, x, lerp(-150, y, min(k, 1.05)))
            else:
                bump = 1 + 0.12 * math.sin(math.pi * min(1, max(0, (ctx.t - ctx.f(0.12)) / 0.4))) if n == opening else 1
                paste(ctx.c, sp, x, y, bump)
        else:
            x, y = SMALL_TOP[n]
            paste(ctx.c, box_sprite(n, is_open, 80), x, y)
    if small:
        for n in (4, 5, 6, 7):
            is_open = n in opened or (n == small_opening and ctx.t >= ctx.f(0.08))
            x, y = SMALL_ROW[n]
            if small_opening and n == small_opening:
                continue  # 여는 상자는 장면에서 크게 따로 그림
            paste(ctx.c, box_sprite(n, is_open, 110), x, y)


# 흐름도 (STAGE 5, 11칸 — 콘티 기준)
FLOW = ["시작하기 전에", "내 작업실", "말리로 연습", "소재·주인공", "대본", "장면 점수",
        "🖼️ 그림", "🎤 목소리", "🎞️ 움직이는 장면", "합치기", "🚩 완성과 확장"]


def flow_pos(i):
    if i < 6:
        return 140 + i * 200, 215
    return 1140 - (i - 6) * 200, 395


@lru_cache(None)
def flow_cell(i, filled):
    label = FLOW[i]
    e = None
    if label[0] in "🖼🎤🎞🚩":
        e, label = label.split(" ", 1)
    w, h = 176, 96
    im = Image.new("RGBA", (w + 8, h + 8))
    d = ImageDraw.Draw(im)
    if filled:
        d.rounded_rectangle((4, 4, w + 4, h + 4), 20, fill=(255, 238, 214), outline=(232, 170, 120), width=4)
    else:
        d.rounded_rectangle((4, 4, w + 4, h + 4), 20, fill=(255, 255, 255, 120), outline=(205, 195, 185), width=3)
    num = text_sprite(str(i + 1), 22, (232, 140, 100) if filled else GRAY, "gothic")
    im.alpha_composite(num, (12, 6))
    if filled:
        y0 = 14
        if e:
            em = emoji_sprite(e, 34)
            im.alpha_composite(em, ((w + 8 - em.width) // 2, 10))
            y0 = 44
        size = 24 if len(label) <= 6 else 21
        tx = text_sprite(label, size, INK)
        im.alpha_composite(tx, ((w + 8 - tx.width) // 2, y0 + (h - y0 - tx.height) // 2 + 4))
    return im


def flow(ctx, filled_before, fill_now=(), path_draw=False):
    # 길(경로)
    pts = [flow_pos(i) for i in range(11)]
    k = ease_out(ctx.t / (ctx.d * 0.8)) if path_draw else 1.0
    d = ImageDraw.Draw(ctx.c)
    total = len(pts) - 1
    upto = k * total
    for i in range(total):
        if i >= upto:
            break
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        part = min(1.0, upto - i)
        d.line((x0, y0, lerp(x0, x1, part), lerp(y0, y1, part)), fill=(222, 200, 170), width=14)
    for i in range(11):
        if path_draw and i > upto:
            continue
        x, y = pts[i]
        if i in filled_before:
            paste(ctx.c, flow_cell(i, True), x, y)
        elif i in fill_now:
            j = list(fill_now).index(i)
            at = 0.08 + j * 0.85 / len(fill_now)
            if ctx.t >= ctx.f(at):
                s, a = ctx.appear(at)
                paste(ctx.c, flow_cell(i, False), x, y)
                paste(ctx.c, flow_cell(i, True), x, y, s, a)
                if i >= 6:
                    k2 = (ctx.t - ctx.f(at)) / 0.8
                    if k2 < 1:
                        paste(ctx.c, emoji_sprite("✨", 40), x + 70, y - 45, 1, 1 - k2)
            else:
                paste(ctx.c, flow_cell(i, False), x, y)
        else:
            paste(ctx.c, flow_cell(i, False), x, y)


def flow_malli(ctx, i0, i1=None, start=0.1, dur=1.0):
    x0, y0 = flow_pos(i0)
    if i1 is None:
        x, y = x0, y0
    else:
        x1, y1 = flow_pos(i1)
        k = ease_out((ctx.t - ctx.f(start)) / dur)
        x, y = lerp(x0, x1, k), lerp(y0, y1, k)
    paste(ctx.c, malli_sprite("M9", 70), x, y - 80 - abs(math.sin(ctx.t * 6)) * 6)


RESULTS = ["📋", "🗂️", "🐶", "🧸", "📝", "📊", "🖼️", "🎤", "🎞️", "🎬", "🌍"]


def result_icon_pos(i):
    return 270 + i * 80, 560  # 이름표(왼쪽 아래)·구석 말리 피해서


# ---------------------------------------------------------------------------
# 장면별 화면 (콘티 '화면 지시')
# ---------------------------------------------------------------------------

def corner(ctx, pose="M7", anim="breathe"):
    ctx.malli(pose, CORNER, anim)


def S(ctx, sid):  # noqa: C901 — 장면 표
    c, t, d = ctx.c, ctx.t, ctx.d
    # ---------------- STAGE 1 ----------------
    if sid == "S01-01":
        c.alpha_composite(background("cover"))
        k = ease_out(t / 2.0)
        ctx.c = c
        title = text_sprite("말리의 동화나라", 78, (110, 80, 60), "kk", 3, (255, 252, 240))
        paste(c, title, 640, 215, 1.0, 1 - ease_out((t - (d - 0.5)) / 0.5))
        black = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - k))))
        c.alpha_composite(black)
    elif sid == "S01-04":
        c.alpha_composite(background("field"))
        ctx.malli("M1", anim="wag")
    elif sid == "S01-05":
        c.alpha_composite(background("field"))
        jt = ctx.f(0.62)
        if t < jt or t > jt + 0.8:
            ctx.malli("M1", anim="wag")
        else:
            k = (t - jt) / 0.8
            ctx.malli("M2", (640, 610 - math.sin(math.pi * k) * 110, 360))
        ctx.particles("💗", 640, 260, at=0.62, n=3)
    elif sid == "S01-06":
        c.alpha_composite(background("field"))
        ctx.malli("M3", anim="wag")
        ctx.pop(bubble_sprite("Hello!", 54), 860, 250, at=0.05)
    elif sid == "S01-07":
        c.alpha_composite(background("field_blur"))
        ctx.malli("M4", (400, 620, 330), "breathe")
        cloud = cloud_sprite()
        ctx.pop(cloud, 860, 270, at=0.12, dur=0.5)
    elif sid == "S01-08":
        c.alpha_composite(background("field"))
        if t < 0.35:
            paste(c, cloud_sprite(), 860, 270, 1 + t, 1 - t / 0.35)
        ctx.malli("M5", anim="nod")
    elif sid == "S01-09":
        c.alpha_composite(background("field"))
        ctx.malli("M6", anim="breathe")
    elif sid == "S01-10":
        c.alpha_composite(background("field"))
        ctx.malli_move("M7", CENTER, CORNER, 0.0, 0.5)
    # ---------------- STAGE 2 ----------------
    elif sid == "S02-01":
        c.alpha_composite(background("paper"))
        ctx.c.alpha_composite(Image.new("RGBA", (W, H)))
        paste(c, title_card("말리의 동화나라", 60), 640, 300, 1, 0.35)
        corner(ctx, "M3", "wag")
    elif sid == "S02-02":
        c.alpha_composite(background("paper"))
        ctx.pop(title_card("함께 만든 사람들", 64), 640, 300, at=0.05)
        corner(ctx)
    elif sid == "S02-03":
        c.alpha_composite(background("paper"))
        k = ease_out(t / 0.6)
        paste(c, title_card("함께 만든 사람들", 64), 640, lerp(300, 90, k), lerp(1, 0.6, k))
        joy_card(ctx, 640, 380, at=0.2)
        corner(ctx)
    elif sid == "S02-04":
        c.alpha_composite(background("paper"))
        paste(c, title_card("함께 만든 사람들", 64), 640, 90, 0.6)
        k = ease_out(t / 0.6)
        joy_card(ctx, lerp(640, 250, k), lerp(380, 370, k), scale=lerp(1, 0.75, k))
        half = d / 2
        if t < half:
            z = 1 + 0.06 * t / half
            ctx.pop(placeholder_panel("▶ 유튜브 채널", "유튜브 채널 메인 캡처 자리", (226, 74, 62)), 790, 370, at=0.08, scale=z)
        else:
            z = 1 + 0.06 * (t - half) / half
            paste(c, placeholder_panel("블로그", "블로그 메인 캡처 자리", (60, 170, 110)), 790, 370, z)
        corner(ctx)
    elif sid == "S02-05":
        c.alpha_composite(background("paper"))
        icon_row(ctx, [("🎬", "콘텐츠 만들기"), ("📰", "최신 트렌드"), ("🌱", "쉽게 시작하기")], 330, [0.05, 0.35, 0.65])
        corner(ctx)
    elif sid == "S02-06":
        c.alpha_composite(background("book"))
        k = ease_out((t - ctx.f(0.3)) / 0.6)
        if k > 0:
            paste(c, code_panel(), lerp(1600, 860, k), 330)
        corner(ctx)
    elif sid == "S02-07":
        c.alpha_composite(background("paper"))
        steps = [("📖", "이야기"), ("🖼️", "그림"), ("🎤", "목소리"), ("🎞️", "영상")]
        for i, (e, lb) in enumerate(steps):
            x = 220 + i * 280
            at = 0.05 + i * 0.22
            on = t >= ctx.f(at)
            sp = icon_tile(e, lb, 100, 200)
            if not on:
                g = ImageOps.grayscale(sp.convert("RGB")).convert("RGBA")
                g.putalpha(sp.getchannel("A").point(lambda v: v // 3))
                paste(c, g, x, 330)
            else:
                s, a = ctx.appear(at, 0.3)
                paste(c, sp, x, 330, max(s, 0.9))
            if i < 3:
                arrow(ctx, x + 85, x + 170, 300, at=at + 0.1, dur=0.4)
        corner(ctx)
    elif sid == "S02-08":
        c.alpha_composite(background("paper"))
        ctx.pop(lily_card_sprite("릴리 / 강의 기획·목소리"), 640, 330, at=0.1)
        corner(ctx)
    elif sid == "S02-09":
        c.alpha_composite(background("paper"))
        s, a = ctx.appear(0.02, 0.4)
        pulse = 1 + 0.25 * math.sin(math.pi * min(1, t / 1.0))
        paste(c, text_sprite("17년", 120, (232, 120, 90)), 640, 200, s * pulse, a)
        icon_row(ctx, [("🏭", "의약품 생산 시설"), ("🔬", "연구")], 420, [0.35, 0.65])
        corner(ctx)
    elif sid == "S02-10":
        c.alpha_composite(background("paper"))
        paste(c, icon_tile("🏭", "의약품 생산", 90, 200), 230, 330)
        paste(c, icon_tile("🔬", "연구", 90, 200), 450, 330)
        arrow(ctx, 560, 830, 300, at=0.15, dur=1.2)
        ctx.pop(icon_tile("🤖", "AI 교육", 130, 220), 990, 320, at=0.5)
        corner(ctx)
    elif sid == "S02-11":
        c.alpha_composite(background("paper"))
        s, a = ctx.appear(0.05, 0.5)
        shrink = 1 - 0.25 * ease_out((t - ctx.f(0.55)) / 0.8)
        paste(c, bubble_sprite("아, 이게 이런 거구나!", 64), 640, 320, s * shrink, a)
        corner(ctx)
    elif sid == "S02-12":
        c.alpha_composite(background("paper"))
        paste(c, lily_card_sprite("릴리 / 강의 기획·목소리"), 520, 330)
        ctx.malli("M5", CORNER, "nod")
    elif sid == "S02-13":
        c.alpha_composite(background("paper"))
        k = ease_out(t / 0.5)
        paste(c, lily_card_sprite("릴리 / 강의 기획·목소리"), 520, 330, 1 - k, 1 - k)
        if t < ctx.f(0.55):
            corner(ctx)
        else:
            ctx.malli("M8", CORNER, "bounce")
    elif sid == "S02-14":
        c.alpha_composite(background("paper"))
        ctx.malli_move("M9", CORNER, CENTER, 0.0, 0.7)
    # ---------------- STAGE 3 ----------------
    elif sid == "S03-01":
        c.alpha_composite(background("paper"))
        sheet = load(ROOT / "images/style_ref/malli_reference.png")
        cuts = [((470, 120, 900, 860), "앞모습"), ((925, 120, 1345, 640), "옆모습"), ((1345, 120, 1660, 640), "뒷모습")]
        for i, (box, lb) in enumerate(cuts):
            sp = labeled_card_crop(box, lb)
            ctx.pop(sp, 600 + i * 230, 320, at=0.05 + i * min(0.3, 1.0 / d))
        ctx.malli("M1", (230, 640, 330), "wag")
    elif sid == "S03-02":
        c.alpha_composite(background("paper"))
        ctx.malli("M10", anim="breathe")
        ctx.sparkle(600, 230, at=0.1)
    elif sid == "S03-03":
        c.alpha_composite(background("paper"))
        ctx.malli("M1", (190, 640, 300), "wag")
        for i, (e, lb) in enumerate([("E5", "전래동화"), ("E6", "서양동화"), ("E7", "창작동화")]):
            ctx.pop(labeled_card(IMG / f"{e}.png", 210, 280, lb), 520 + i * 260, 330, at=0.04 + i * 0.3)
    elif sid == "S03-04":
        c.alpha_composite(background("paper"))
        ctx.malli("M1", (330, 640, 340), "wag")
        k = (t - ctx.f(0.45)) / 0.6
        if k < 0:
            paste(c, silhouette_card(), 860, 320)
            paste(c, text_sprite("?", 120, (140, 140, 150)), 860, 300)
        else:
            paste(c, labeled_card(IMG / "E2.png", 280, 280, "여러분의 주인공"), 860, 330)
            if k < 1:
                paste(c, silhouette_card(), 860, 320, 1, 1 - k)
            ctx.sparkle(860, 300, at=0.45, r=150)
    elif sid == "S03-05":
        c.alpha_composite(background("paper"))
        paste(c, frame_sprite(520, 320), 520, 320)
        ctx.malli("M6", (1010, 640, 340), "breathe")
    elif sid == "S03-06":
        c.alpha_composite(background("paper"))
        k = ease_out(t / 0.9)
        c.alpha_composite(Image.new("RGBA", (W, H), (20, 16, 24, int(200 * k))))
        paste(c, frame_sprite(520, 320), lerp(520, 640, k), lerp(320, 330, k), lerp(1, 2.0, k))
        ctx.malli_move("M7", (1010, 640, 340), CORNER, 0.0, 0.5)
    elif sid in ("S03-07", "S03-09"):
        c.alpha_composite(background("cinema"))
        lang = "한국어" if sid == "S03-07" else "English"
        paste(c, still_placeholder(lang, W / 900), 640, 360)
        corner(ctx) if sid == "S03-07" else None
    elif sid in ("S03-08", "S03-10"):
        c.alpha_composite(background("cinema"))
        lang = "한국어" if sid == "S03-08" else "English"
        name = "harin_ko" if sid == "S03-08" else "harin_en"
        if (CLIPS / f"{name}.mp4").exists():
            ctx.c = harin_frame(name, int(t * FPS))
            return
        paste(c, clip_placeholder(lang), 640, 360)
        # 진행 바 (임시 화면이 멈춘 화면처럼 보이지 않게)
        ImageDraw.Draw(c).rounded_rectangle((340, 620, 352 + 588 * t / d, 630), 5, fill=(230, 160, 120))
    elif sid == "S03-11":
        c.alpha_composite(background("cinema"))
        paste(c, still_placeholder("한국어", 0.55), 360, 320)
        paste(c, still_placeholder("English", 0.55), 920, 320)
        ctx.malli("M10", CORNER, "breathe", at=0.05)
        ctx.sparkle(CORNER[0], CORNER[1] - 120, at=0.2, r=60, size=26)
    elif sid == "S03-12":
        c.alpha_composite(background("cinema"))
        blur = Image.new("RGBA", (W, H))
        paste(blur, still_placeholder("한국어", 0.55), 360, 320)
        paste(blur, still_placeholder("English", 0.55), 920, 320)
        c.alpha_composite(blur.filter(ImageFilter.GaussianBlur(6 * ease_out(t / 0.6))))
        ctx.malli_move("M9", CORNER, CENTER, 0.0, 0.7)
    # ---------------- STAGE 4 ----------------
    elif sid == "S04-01":
        c.alpha_composite(background("paper"))
        ctx.malli("M1", anim="breathe")
    elif sid == "S04-02":
        c.alpha_composite(background("paper"))
        ctx.malli("M11", anim="breathe")
        ctx.particles("💗", 640, 250, at=0.15, n=4, life=2.4, rise=160)
    elif sid == "S04-03":
        c.alpha_composite(background("paper"))
        ctx.malli("M1", anim="fastwag")
    elif sid == "S04-04":
        c.alpha_composite(background("paper"))
        ctx.pop(joy_card_sprite(), 330, 330, at=0.05, scale=0.85)
        ctx.pop(lily_card_sprite(), 640, 330, at=0.3, scale=0.85)
        ctx.pop(malli_card_sprite(), 950, 330, at=0.6, scale=0.85)
    elif sid == "S04-05":
        c.alpha_composite(background("paper"))
        ctx.malli("M7", anim="wag")
    elif sid == "S04-06":
        c.alpha_composite(background("paper"))
        ctx.malli_move("M7", CENTER, CORNER, 0.0, 0.5)
    elif sid == "S04-07":
        c.alpha_composite(background("paper"))
        boxes(ctx, set(), drop_at=0.1)
        corner(ctx)
    elif sid == "S04-08":
        c.alpha_composite(background("paper"))
        boxes(ctx, set(), opening=1)
        corner(ctx)
    elif sid == "S04-09":
        c.alpha_composite(background("paper"))
        seg = [("E2", 0.0, 0.3), ("E3", 0.3, 0.6), ("E4", 0.6, 0.86)]
        if t < ctx.f(0.86):
            for e, a0, a1 in seg:
                if ctx.f(a0) <= t < ctx.f(a1):
                    ctx.pop(labeled_card(IMG / f"{e}.png", 330, 330, None), 640, 330, at=a0, dur=0.3)
        else:
            for i, e in enumerate(["E2", "E3", "E4"]):
                ctx.pop(labeled_card(IMG / f"{e}.png", 260, 260, None), 330 + i * 310, 330, at=0.86, dur=0.25)
        corner(ctx)
    elif sid == "S04-10":
        c.alpha_composite(background("paper"))
        boxes(ctx, {1}, opening=2)
        for i, lb in enumerate(["대본", "목소리", "자막"]):
            ctx.pop(tag_sprite(lb), 560 + i * 85, 470, at=0.35 + i * 0.18)
        corner(ctx)
    elif sid == "S04-11":
        c.alpha_composite(background("paper"))
        boxes(ctx, {1, 2}, opening=3)
        ctx.pop(mini_app_sprite(False), 860, 510, at=0.25, scale=0.6)
        for i in range(3):  # 자막 영역(y>620) 피해서 쌓기
            ctx.pop(book_stack_sprite(i + 1), 1100, 560 - i * 46, at=0.45 + i * 0.15)
        corner_off = True  # 책 쌓기와 겹쳐 구석 말리 생략
    elif sid == "S04-12":
        c.alpha_composite(background("paper"))
        k = ease_out(t / 0.7)
        for n in (1, 2, 3):
            x0, y0 = BIG_POS[n]
            x1, y1 = SMALL_TOP[n]
            paste(c, box_sprite(n, True, 170), lerp(x0, x1, k), lerp(y0, y1, k), lerp(1, 0.47, k))
        for i, n in enumerate((4, 5, 6, 7)):
            x, y = SMALL_ROW[n]
            ctx.pop(box_sprite(n, False, 110), x, y, at=0.3 + i * 0.12)
        corner(ctx)
    elif sid in ("S04-13", "S04-14", "S04-15", "S04-16"):
        c.alpha_composite(background("paper"))
        n = {"S04-13": 4, "S04-14": 5, "S04-15": 6, "S04-16": 7}[sid]
        opened = {1, 2, 3} | set(range(4, n))
        boxes(ctx, opened, big=False)
        for m in (4, 5, 6, 7):
            if m == n:
                continue
            x, y = SMALL_ROW[m]
            paste(c, box_sprite(m, m in opened, 70), x, 245)
        ctx.pop(box_sprite(n, True, 120), 640, 300, at=0.03)
        detail_scene(ctx, n)
        corner(ctx)
    elif sid == "S04-17":
        c.alpha_composite(background("paper"))
        for n in (1, 2, 3):
            paste(c, box_sprite(n, True, 150), BIG_POS[n][0], 230)
        for n in (4, 5, 6, 7):
            paste(c, box_sprite(n, True, 110), SMALL_ROW[n][0], 470)
        corner(ctx)
    elif sid == "S04-18":
        c.alpha_composite(background("paper"))
        k = ease_out(t / 0.6)
        allbox = Image.new("RGBA", (W, H))
        for n in (1, 2, 3):
            paste(allbox, box_sprite(n, True, 150), BIG_POS[n][0], 230)
        for n in (4, 5, 6, 7):
            paste(allbox, box_sprite(n, True, 110), SMALL_ROW[n][0], 470)
        paste(c, allbox, 640, lerp(360, 110, k), lerp(1, 0.3, k))
        ctx.pop(gray_card(0), 640, 400, at=0.3)
        corner(ctx)
    elif sid == "S04-19":
        c.alpha_composite(background("paper"))
        small_all(c)
        items = ["유튜브 업로드", "썸네일과 쇼츠 만들기", "수익 내는 방법", "영상 편집"]
        shown = sum(1 for i in range(4) if t >= ctx.f(0.05 + i * 0.22))
        paste(c, gray_card(shown), 640, 400)
        corner(ctx)
    elif sid == "S04-20":
        c.alpha_composite(background("paper"))
        k = ease_out(t / 0.6)
        if k < 1:
            small_all(c, 1 - k)
            paste(c, gray_card(4), 640, 400, 1, 1 - k)
        g = 0.5 + 0.5 * math.sin(t * 4)
        ctx.pop(box_sprite(1, True, 200, glow=True), 430, 330, at=0.2)
        ctx.pop(box_sprite(3, True, 200, glow=True), 850, 330, at=0.3)
        ctx.sparkle(430, 300, at=0.4, r=140)
        ctx.sparkle(850, 300, at=0.4, r=140)
        corner(ctx)
    # ---------------- STAGE 5 ----------------
    elif sid == "S05-01":
        c.alpha_composite(background("paper"))
        flow(ctx, set(), path_draw=True)
        flow_malli(ctx, 0)
        corner(ctx)
    elif sid == "S05-02":
        c.alpha_composite(background("paper"))
        flow(ctx, set(), (0, 1))
        flow_malli(ctx, 0, 1, start=0.45)
        corner(ctx)
    elif sid == "S05-03":
        c.alpha_composite(background("paper"))
        flow(ctx, {0, 1}, (2,))
        flow_malli(ctx, 1, 2, start=0.05)
        x, y = flow_pos(2)
        ctx.pop(malli_sprite("M1", 120), x - 40, y + 140, at=0.25)
        ctx.emoji("🔊", x + 50, y + 140, 60, at=0.4)
        corner(ctx)
    elif sid == "S05-04":
        c.alpha_composite(background("paper"))
        flow(ctx, {0, 1, 2}, (3, 4, 5))
        flow_malli(ctx, 2, 5, start=0.1, dur=ctx.d * 0.8)
        corner(ctx)
    elif sid == "S05-05":
        c.alpha_composite(background("paper"))
        flow(ctx, set(range(6)), (6, 7, 8, 9))
        k = min(1.0, max(0.0, (t - ctx.f(0.05)) / (ctx.d * 0.85)))
        seg = 5 + k * 4
        i0 = int(min(seg, 8.999))
        x0, y0 = flow_pos(i0)
        x1, y1 = flow_pos(i0 + 1)
        f = seg - i0
        paste(c, malli_sprite("M9", 70), lerp(x0, x1, f), lerp(y0, y1, f) - 80)
        corner(ctx)
    elif sid == "S05-06":
        c.alpha_composite(background("paper"))
        flow(ctx, set(range(10)), (10,))
        flow_malli(ctx, 9, 10, start=0.3)
        corner(ctx)
    elif sid == "S05-07":
        c.alpha_composite(background("paper"))
        flow(ctx, set(range(11)))
        flow_malli(ctx, 10)
        for i, e in enumerate(RESULTS):
            x, y = result_icon_pos(i)
            ctx.emoji(e, x, y, 64, at=0.05 + i * 0.075)
        corner(ctx)
    elif sid == "S05-08":
        c.alpha_composite(background("paper"))
        fade = 1 - ease_out(t / 0.8)
        if fade > 0:
            lay = Image.new("RGBA", (W, H))
            sub = Ctx(lay, 99, ctx.d)
            flow(sub, set(range(11)))
            paste(c, lay, 640, 360, 1, fade)
        k = ease_out((t - ctx.f(0.05)) / 1.2)
        for i, e in enumerate(RESULTS):
            x, y = result_icon_pos(i)
            if k < 1:
                paste(c, emoji_sprite(e, 64), lerp(x, 640, k), lerp(y, 330, k), 1 - 0.6 * k, 1 - k * 0.8)
        if k > 0.6:
            s, a = ctx.appear(0.05 + 1.2 / ctx.d * 0.6)
            paste(c, emoji_sprite("📖", 220), 640, 330, s, a)
            ctx.sparkle(640, 330, at=0.4, r=150, n=5, size=40)
        corner(ctx)
    # ---------------- STAGE 6 ----------------
    elif sid in ("S06-01", "S06-02", "S06-03", "S06-04"):
        c.alpha_composite(background("paper"))
        card = title_card("1-2. 나도 할 수 있을까요? 준비물 확인", 50)
        if sid == "S06-01":
            k = ease_out(t / 0.7)
            paste(c, card, lerp(1700, 640, k), 150)
        else:
            paste(c, card, 640, 150)
        if sid == "S06-02":
            icon_row(ctx, [("💻", "컴퓨터"), ("📶", "인터넷")], 390, [0.1, 0.5])
        elif sid == "S06-03":
            ctx.pop(code_symbol_sprite(), 560, 380, at=0.05)
            ctx.emoji("✅", 680, 330, 90, at=0.35)
            ctx.text("몰라도 괜찮아요", 640, 520, 46, at=0.5, color=(70, 150, 90))
        elif sid == "S06-04":
            icon_row(ctx, [("💾", "파일 저장"), ("📁", "폴더 만들기")], 390, [0.1, 0.5])
        corner(ctx)
    elif sid in ("S06-05", "S06-06", "S06-07"):
        c.alpha_composite(background("paper"))
        card13 = title_card("1-3. 필요한 AI 도구와 요금", 50)
        if sid == "S06-05":
            k = ease_out(t / 0.7)
            paste(c, title_card("1-2. 나도 할 수 있을까요? 준비물 확인", 50), lerp(640, -500, k), 150)
            paste(c, card13, lerp(1700, 640, k), 150)
            tools = [badge_sprite("Claude", (204, 120, 92)), badge_sprite("VS Code", (40, 120, 200)),
                     icon_tile("🎨", "그림·목소리 도구", 90, 230), icon_tile("🎞️", "영상 도구", 90, 200)]
            for i, sp in enumerate(tools):
                ctx.pop(sp, 220 + i * 280, 400, at=0.15 + i * min(0.2, 1.0 / d))
        else:
            paste(c, card13, 640, 150)
        if sid == "S06-06":
            ctx.pop(scale_sprite(), 520, 400, at=0.05)
            ctx.emoji("📅", 900, 400, 120, at=0.55)
        elif sid == "S06-07":
            ctx.emoji("👛", 640, 420, 170, at=0.05)
            k = ease_back((t - ctx.f(0.35)) / 0.5)
            if t >= ctx.f(0.35):
                paste(c, emoji_sprite("🔒", 90), 700, lerp(150, 380, min(k, 1.05)))
        corner(ctx)
    elif sid == "S06-08":
        c.alpha_composite(background("paper"))
        k = ease_out(t / 0.5)
        paste(c, title_card("1-3. 필요한 AI 도구와 요금", 50), 640, 150, 1 - 0.5 * k, 1 - k)
        if t < ctx.f(0.4):
            corner(ctx)
        else:
            ctx.malli("M8", CORNER, "bounce")
    elif sid == "S06-09":
        k = ease_out(t / 0.8)
        c.alpha_composite(background("paper"))
        fb = background("field").copy()
        fb.putalpha(int(255 * k))
        c.alpha_composite(fb)
        ctx.malli_move("M9", CORNER, CENTER, 0.0, 0.7)
    elif sid == "S06-10":
        c.alpha_composite(background("field"))
        ctx.malli("M12", anim="bounce")
        ctx.sparkle(640, 360, at=0.05, r=200, n=6, size=40)
    elif sid == "S06-11":
        c.alpha_composite(background("field"))
        ctx.malli("M1", (300, 640, 330), "wag")
        ctx.pop(mission_card(), 830, 230, at=0.05)
        for i, e in enumerate(["E2", "E3", "E4"]):
            at = 0.5 + i * 0.15
            sp = silhouette(IMG / f"{e}.png", 170, 170)
            paste(c, sp, 640 + i * 190, 470, 1, 0.55)
            if t >= ctx.f(at):
                k = (t - ctx.f(at)) / 0.9
                if k < 1:
                    paste(c, emoji_sprite("✨", 50), 640 + i * 190 + 60, 400, 1, math.sin(math.pi * k))
                    paste(c, sp, 640 + i * 190, 470, 1.06, 0.4 * math.sin(math.pi * k))
    elif sid == "S06-12":
        c.alpha_composite(background("field"))
        k = ease_out(t / 0.6)
        paste(c, mission_card(), lerp(830, 640, k), lerp(230, 70, k), lerp(1, 0.5, k))
        ctx.malli("M3", anim="wag")
        ctx.pop(bubble_sprite("Bye bye!", 54), 870, 260, at=0.55)
    elif sid == "S06-14":
        c.alpha_composite(background("paper"))
        ctx.pop(next_button(), 640, 230, at=0.05)
        ctx.text("🐾 미션: 내 주인공 한 명 떠올리기".replace("🐾 ", ""), 670, 520, 34, at=0.2, color=SOFT)
        ctx.emoji("🐾", 430, 520, 40, at=0.2)
    else:
        raise KeyError(sid)


# 장면 전용 소품 ----------------------------------------------------------------

@lru_cache(None)
def cloud_sprite():
    w, h = 520, 360
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for (x, y, r) in [(260, 170, 150), (130, 190, 105), (390, 190, 105), (200, 100, 95), (330, 95, 100)]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 245))
    for (x, y, r) in [(90, 320, 18), (50, 350, 10)]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 245))
    pic = image_sprite(IMG / "E1.png", 270, 270, False, 130)
    im.alpha_composite(pic, ((w - pic.width) // 2, 165 - pic.height // 2 + 10))
    return im


@lru_cache(None)
def labeled_card_crop(box, label):
    sheet = load(ROOT / "images/style_ref/malli_reference.png").crop(box)
    pic = fit(sheet, 200, 300)
    tx = text_sprite(label, 26, INK)
    im = card_sprite(220, 360, (255, 252, 246)).copy()
    im.alpha_composite(pic, (24 + (220 - pic.width) // 2, 24 + 10 + (300 - pic.height) // 2))
    im.alpha_composite(tx, (24 + (220 - tx.width) // 2, 24 + 318))
    return im


@lru_cache(None)
def silhouette_card():
    im = card_sprite(300, 350, (238, 238, 240)).copy()
    sil = silhouette(IMG / "E2.png", 260, 260)
    im.alpha_composite(sil, (24 + 20, 24 + 20))
    return im


@lru_cache(None)
def frame_sprite(w, h):
    im = Image.new("RGBA", (w + 60, h + 60))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w + 59, h + 59), 18, fill=(196, 150, 100))
    d.rounded_rectangle((18, 18, w + 41, h + 41), 10, fill=(255, 250, 240), outline=(160, 115, 75), width=4)
    return im


# 정지 화면 프레임 시점: 원본 영상에 구운 자막이 없는 틈 (하린 subs.srt / subs_en.srt 기준)
# — 클립 첫 프레임은 원본 자막("초코야, 기다려!")이 남아 이 영상 자막과 겹침 (2026-10-22 프레임 검수)
STILL_T = {"한국어": 8.2, "English": 7.5}


@lru_cache(None)
def harin_first_frame(lang):
    name = "harin_ko" if lang == "한국어" else "harin_en"
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", str(STILL_T[lang]), "-i", str(CLIPS / f"{name}.mp4"), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout
    return Image.frombytes("RGBA", (W, H), raw)


@lru_cache(None)
def still_placeholder(lang, scale=1.0):
    """완성작(하린) 클립 장면 정지 화면(원본 자막 없는 프레임) + 왼쪽 위 언어 라벨. 클립이 없으면 들판 배경으로 대체."""
    w, h = int(900 * scale), int(506 * scale)
    if (CLIPS / ("harin_ko.mp4" if lang == "한국어" else "harin_en.mp4")).exists():
        pic = harin_first_frame(lang).resize((w, h), Image.LANCZOS)
    else:
        pic = ImageOps.fit(load(IMG / "B2.png"), (w, h), Image.LANCZOS).copy()
    k = max(scale, 0.7)
    lab = card_sprite(int(150 * k), int(54 * k), (255, 255, 255), 16, None, False)
    pic.alpha_composite(lab, (-4, -4))
    tx = text_sprite(lang, int(30 * k), INK)
    pic.alpha_composite(tx, (20 + (int(150 * k) - tx.width) // 2, 20 + (int(54 * k) - tx.height) // 2))
    return pic


@lru_cache(None)
def clip_placeholder(lang):
    im = Image.new("RGBA", (960, 540), (48, 42, 52, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 959, 539), 20, outline=(120, 110, 120), width=3)
    em = emoji_sprite("🎬", 110)
    im.alpha_composite(em, ((960 - em.width) // 2, 120))
    t1 = text_sprite(f"완성작 {lang} 버전 · 20초", 50, (255, 240, 225))
    im.alpha_composite(t1, ((960 - t1.width) // 2, 270))
    t2 = text_sprite("(테스트 버전 — 클립 자리)", 28, (190, 180, 185), "gothic")
    im.alpha_composite(t2, ((960 - t2.width) // 2, 350))
    return im


@lru_cache(None)
def tag_sprite(label):
    tx = text_sprite(label, 26, (255, 255, 255))
    im = Image.new("RGBA", (tx.width + 26, tx.height + 10))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 18, fill=(90, 150, 220))
    im.alpha_composite(tx, (13, 5))
    return im


@lru_cache(None)
def mini_app_sprite(pressed):
    w, h = 300, 220
    im = card_sprite(w, h, (255, 255, 255), 24).copy()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 24, 24 + w, 24 + 44), 24, fill=(255, 214, 180))
    d.rectangle((24, 24 + 24, 24 + w, 24 + 44), fill=(255, 214, 180))
    tx = text_sprite("나만의 동화 앱", 24, INK)
    im.alpha_composite(tx, (24 + (w - tx.width) // 2, 24 + 6))
    col = (220, 110, 90) if pressed else (240, 140, 110)
    off = 4 if pressed else 0
    d.rounded_rectangle((24 + 70, 24 + 100 + off, 24 + 230, 24 + 170 + off), 30, fill=col)
    bt = text_sprite("▶ 만들기", 30, (255, 255, 255), "gothic")
    im.alpha_composite(bt, (24 + 150 - bt.width // 2, 24 + 135 + off - bt.height // 2))
    return im


@lru_cache(None)
def book_stack_sprite(n):
    w, h = 200, 40
    im = Image.new("RGBA", (w + 4, h + 4))
    col = [(240, 160, 140), (150, 190, 230), (170, 210, 150)][n - 1]
    ImageDraw.Draw(im).rounded_rectangle((2, 2, w, h), 8, fill=col, outline=(120, 90, 70), width=2)
    tx = text_sprite(f"{n}편", 24, (255, 255, 255))
    im.alpha_composite(tx, ((w - tx.width) // 2, (h - tx.height) // 2 + 2))
    return im


@lru_cache(None)
def shelf_book(label, col):
    w, h = 64, 140
    im = Image.new("RGBA", (w + 4, h + 4))
    ImageDraw.Draw(im).rounded_rectangle((2, 2, w, h), 8, fill=col, outline=(120, 90, 70), width=2)
    for i, ch in enumerate(label):
        tx = text_sprite(ch, 26, (255, 255, 255))
        im.alpha_composite(tx, ((w - tx.width) // 2 + 2, 12 + i * 34))
    return im


@lru_cache(None)
def rule_flow_sprite():
    im = Image.new("RGBA", (900, 200))
    b = bubble_sprite("규칙", 40)
    im.alpha_composite(b, (40, 40))
    ai = emoji_sprite("🤖", 120)
    im.alpha_composite(ai, (450 - ai.width // 2, 40))
    r = bubble_sprite("결과", 40)
    im.alpha_composite(r, (900 - r.width - 40, 40))
    a = arrow_sprite(120)
    im.alpha_composite(a, (230, 85))
    im.alpha_composite(a, (560, 85))
    return im


def detail_scene(ctx, n):
    c, t = ctx.c, ctx.t
    if n == 4:
        for i in range(3):
            ctx.pop(image_sprite(IMG / "E2.png", 150, 150, False, 75), 330 + i * 230, 475, at=0.15 + i * 0.1)
            if i < 2:
                ctx.text("=", 445 + i * 230, 475, 60, at=0.2 + i * 0.1, color=SOFT)
        ctx.emoji("📘", 1000, 475, 90, at=0.5)
        ctx.text("캐릭터 규칙서 = 주인공 설명서", 640, 590, 32, at=0.55)
    elif n == 5:
        cols = [(240, 160, 140), (240, 200, 120), (170, 210, 150), (150, 190, 230), (190, 160, 220), (230, 150, 190)]
        ImageDraw.Draw(c).rectangle((300, 572, 980, 587), fill=(170, 120, 80))  # 자막 영역 위
        for i, lb in enumerate(["소재", "대본", "그림", "목소리", "영상", "조립"]):
            at = 0.12 + i * 0.1
            if t >= ctx.f(at):
                k = ease_out((t - ctx.f(at)) / 0.35)
                paste(c, shelf_book(lb, cols[i]), 360 + i * 110, lerp(360, 501, k))
        ctx.text("규칙서 = 레시피", 990, 380, 34, at=0.8, color=(200, 110, 80))
    elif n == 6:
        pressed = t >= ctx.f(0.6) and t < ctx.f(0.6) + 0.35
        ctx.pop(mini_app_sprite(pressed), 640, 510, at=0.12)
        if t >= ctx.f(0.6):
            k = (t - ctx.f(0.6)) / 0.6
            if k < 1:
                paste(c, emoji_sprite("👆", 60), 690, 560 - 20 * math.sin(math.pi * k))
    elif n == 7:
        ctx.pop(rule_flow_sprite(), 640, 510, at=0.15)


def small_all(c, alpha=1.0):
    lay = Image.new("RGBA", (W, H))
    for n in (1, 2, 3):
        paste(lay, box_sprite(n, True, 150), BIG_POS[n][0], 230)
    for n in (4, 5, 6, 7):
        paste(lay, box_sprite(n, True, 110), SMALL_ROW[n][0], 470)
    paste(c, lay, 640, 110, 0.3, alpha)


@lru_cache(None)
def gray_card(shown):
    w, h = 760, 360
    im = card_sprite(w, h, (236, 236, 238)).copy()
    tx = text_sprite("이 강의에서 다루지 않아요", 42, (120, 120, 125))
    im.alpha_composite(tx, (24 + (w - tx.width) // 2, 24 + 30))
    items = ["유튜브 업로드", "썸네일과 쇼츠 만들기", "수익 내는 방법", "영상 편집"]
    for i in range(shown):
        it = text_sprite("· " + items[i], 34, (140, 140, 145))
        im.alpha_composite(it, (24 + 150, 24 + 110 + i * 56))
    return im


@lru_cache(None)
def code_symbol_sprite():
    im = card_sprite(200, 160, (40, 44, 56), 24).copy()
    tx = text_sprite("</>", 80, (156, 220, 254), "gothic")
    im.alpha_composite(tx, (24 + (200 - tx.width) // 2, 24 + (160 - tx.height) // 2))
    return im


@lru_cache(None)
def badge_sprite(label, col):
    tx = text_sprite(label, 44, (255, 255, 255), "gothic")
    w, h = max(200, tx.width + 50), 130
    im = card_sprite(w, h, col, 26).copy()
    im.alpha_composite(tx, (24 + (w - tx.width) // 2, 24 + (h - tx.height) // 2))
    return im


@lru_cache(None)
def scale_sprite():
    im = Image.new("RGBA", (520, 300))
    d = ImageDraw.Draw(im)
    d.line((260, 60, 260, 260), fill=(150, 120, 90), width=10)
    d.rectangle((200, 255, 320, 275), fill=(150, 120, 90))
    d.line((60, 90, 460, 70), fill=(150, 120, 90), width=8)
    for x, y, lb, col in [(60, 90, "무료", (120, 190, 130)), (460, 70, "유료", (230, 150, 110))]:
        d.line((x, y, x - 50, y + 90), fill=(170, 150, 130), width=3)
        d.line((x, y, x + 50, y + 90), fill=(170, 150, 130), width=3)
        d.pieslice((x - 75, y + 50, x + 75, y + 150), 0, 180, fill=col)
        tx = text_sprite(lb, 34, (255, 255, 255))
        im.alpha_composite(tx, (x - tx.width // 2, y + 95))
    return im


@lru_cache(None)
def mission_card():
    w, h = 560, 160
    im = card_sprite(w, h, (255, 248, 220), 22, (230, 190, 120)).copy()
    em = emoji_sprite("🐾", 50)
    im.alpha_composite(em, (24 + 26, 24 + 22))
    t1 = text_sprite("말리 미션", 34, (200, 120, 70))
    im.alpha_composite(t1, (24 + 90, 24 + 20))
    t2 = text_sprite("내 주인공 한 명 떠올리기", 40, INK)
    im.alpha_composite(t2, (24 + (w - t2.width) // 2, 24 + 82))
    return im


@lru_cache(None)
def next_button():
    w, h = 760, 130
    im = card_sprite(w, h, (240, 140, 110), 65).copy()
    tx = text_sprite("다음 강의 ▶ 1-2. 나도 할 수 있을까요?", 42, (255, 255, 255))
    im.alpha_composite(tx, (24 + (w - tx.width) // 2, 24 + (h - tx.height) // 2))
    return im


# ---------------------------------------------------------------------------
# 이름표 상태 + 렌더 루프
# ---------------------------------------------------------------------------

NO_TAG = {"S01-01", "S01-02", "S01-03", "S03-08", "S03-10", "S06-13", "S06-14"}
TAG_IN = {"S01-04": "malli", "S01-10": "lily", "S03-06": "lily", "S04-06": "lily"}
TAG_OUT = {"S02-14": "lily"}


def tag_state(i):
    """(누구, 들어오는 중, 나가는 중)."""
    s = TIMELINE[i]
    sid = s["id"]
    if sid in NO_TAG:
        return None, False, False
    if sid in TAG_IN:
        return TAG_IN[sid], True, False
    if sid in TAG_OUT:
        return TAG_OUT[sid], False, True
    if s["speaker"]:
        return s["speaker"], False, False
    # 화자 전환(말리 쪽으로)·쉼: 다음 대사 화자 이름표를 그대로
    for nxt in TIMELINE[i + 1:]:
        if nxt["speaker"]:
            return (nxt["speaker"], False, False) if sid not in ("S03-12", "S06-09") else ("malli", True, False)
    return None, False, False


_clip_cache = {}
_harin = {}


def harin_frame(name, idx):
    """하린 클립(20초) 프레임을 순차 디코딩 — 전부 메모리에 올리면 1.8GB 라 스트리밍."""
    st = _harin.get(name)
    if st is None or idx < st["idx"] or idx > st["idx"] + 50:
        if st:
            st["proc"].kill()
        proc = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{idx / FPS:.3f}", "-i", str(CLIPS / f"{name}.mp4"),
                                 "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
        st = _harin[name] = {"proc": proc, "idx": idx, "img": None}
        st["img"] = _read_rgba(proc) or st["img"]
    while st["idx"] < idx:
        nxt = _read_rgba(st["proc"])
        st["idx"] += 1
        if nxt is not None:
            st["img"] = nxt
    return st["img"].copy() if st["img"] else Image.new("RGBA", (W, H), (0, 0, 0, 255))


def _read_rgba(proc):
    buf = proc.stdout.read(W * H * 4)
    return Image.frombytes("RGBA", (W, H), buf) if len(buf) == W * H * 4 else None



def clip_frames(name):
    if name not in _clip_cache:
        import numpy as np

        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(CLIPS / f"{name}.mp4"), "-vf", f"scale={W}:{H}",
                              "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout
        _clip_cache[name] = np.frombuffer(raw, dtype="uint8").reshape(-1, H, W, 4)
    return _clip_cache[name]


# 자막 (ASS FontSize=20·Outline=2·MarginV=10 @ PlayResY 288 을 720p 로 환산: 50px·외곽 5px·바닥 25px)
SUB_SIZE, SUB_STROKE, SUB_MARGIN, SUB_MAXW = 50, 5, 25, 1180


@lru_cache(None)
def sub_sprite(text, emph):
    f = font(SUB_SIZE)
    text = text.replace("·", "ㆍ")  # 꾹꾹체에 U+00B7 글리프 없음
    # 너비 초과 시 공백 기준으로 두 줄
    lines = [text]
    if f.getlength(text) > SUB_MAXW:
        words = text.split(" ")
        best = min(range(1, len(words)), key=lambda k: abs(f.getlength(" ".join(words[:k])) - f.getlength(text) / 2))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    lh = int(SUB_SIZE * 1.25)
    w = int(max(f.getlength(l) for l in lines)) + SUB_STROKE * 2 + 8
    im = Image.new("RGBA", (w, lh * len(lines) + SUB_STROKE * 2 + 8))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = (w - f.getlength(l)) / 2
        y = SUB_STROKE + 4 + i * lh
        if emph and emph in l:
            pre, post = l.split(emph, 1)
            for part, col in ((pre, (255, 255, 255)), (emph, (255, 180, 60)), (post, (255, 255, 255))):
                d.text((x, y), part, font=f, fill=col, stroke_width=SUB_STROKE, stroke_fill=(0, 0, 0))
                x += f.getlength(part)
        else:
            d.text((x, y), l, font=f, fill=(255, 255, 255), stroke_width=SUB_STROKE, stroke_fill=(0, 0, 0))
    return im


def draw_sub(canvas, gt):
    for c in CUES:
        if c["start"] <= gt < c["end"]:
            sp = sub_sprite(c["text"], c["emph"])
            canvas.alpha_composite(sp, ((W - sp.width) // 2, H - SUB_MARGIN - sp.height + SUB_STROKE + 4))
            return


def frame_at(i, t):
    s = TIMELINE[i]
    sid, d = s["id"], s["length"]
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if sid in CLIP_SCENES and (CLIPS / f"{CLIP_SCENES[sid][0]}.mp4").exists():
        name, a, b = CLIP_SCENES[sid]
        fr = clip_frames(name)
        src_t = a + (b - a) * t / d
        idx = min(len(fr) - 1, int(src_t / 8.0 * len(fr)))
        canvas = Image.fromarray(fr[idx].copy())
    elif sid in CLIP_SCENES:  # 클립 실패 폴백: 정지 화면
        canvas.alpha_composite(background("book" if sid == "S06-13" else "cover"))
    else:
        ctx = Ctx(canvas, t, d)
        S(ctx, sid)
        canvas = ctx.c
    who, tin, tout = tag_state(i)
    if who:
        draw_nametag(Ctx(canvas, t, d), who, tin, tout)
    draw_sub(canvas, s["start"] + t)
    return canvas


def main():
    if len(sys.argv) >= 3:
        sid, tt = sys.argv[1], float(sys.argv[2])
        i = next(k for k, s in enumerate(TIMELINE) if s["id"] == sid)
        out = BASE / "_preview" / f"{sid}_{tt:.1f}.png"
        out.parent.mkdir(exist_ok=True)
        frame_at(i, tt).convert("RGB").save(out)
        print(out.name)
        return
    out = BASE / "_video.mp4"
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                             str(out)], stdin=subprocess.PIPE)
    n_total = 0
    for i, s in enumerate(TIMELINE):
        start_f = round(s["start"] * FPS)
        end_f = round((s["start"] + s["length"]) * FPS)
        for f in range(start_f, end_f):
            t = f / FPS - s["start"]
            proc.stdin.write(frame_at(i, t).convert("RGB").tobytes())
            n_total += 1
        print(f"{s['id']}: {end_f - start_f} frames")
    proc.stdin.close()
    proc.wait()
    print(f"VIDEO: {n_total} frames ({n_total / FPS:.1f}s, timeline {TOTAL:.1f}s)")


if __name__ == "__main__":
    main()
