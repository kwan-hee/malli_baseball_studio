# 하린이와 초코의 이상한 나라 (강의 샘플) — 캐릭터 탄생 과정 비교 이미지 (원본 사진 → 수채화 캐릭터 시트), 16:9 강의 슬라이드용
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent
OUT = BASE / "compare"
OUT.mkdir(exist_ok=True)
W, H = 1920, 1080
BG = (250, 246, 238)
FONT = str(BASE / "font.ttf")

PAIRS = {
    "harin": (Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "images/portraits/daughter.png")), "하린"),
    "choco": (Path(str([_p for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "AGENTS.md").is_file()][-1] / "family_test/강아지.jpg")), "초코"),
}


def fit(im, box_w, box_h):
    r = min(box_w / im.width, box_h / im.height)
    return im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)


for key, (photo_path, name) in PAIRS.items():
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    title = ImageFont.truetype(FONT, 64)
    label = ImageFont.truetype(FONT, 40)
    small = ImageFont.truetype(FONT, 26)

    d.text((W // 2, 70), f"사진 한 장에서 태어난 캐릭터, {name}", font=title, fill=(90, 70, 60), anchor="mm")

    src = Image.open(photo_path).convert("RGB")
    if key == "choco":  # 원본 오른쪽 아래 화면 캡처 잔여 글자('이') 잘라냄
        src = src.crop((0, 0, src.width, src.height - 40))
    photo = fit(src, 520, 780)
    sheet = fit(Image.open(BASE / "characters" / f"{key}_sheet.png").convert("RGB"), 1180, 780)
    py = 150 + (780 - photo.height) // 2
    canvas.paste(photo, (60 + (520 - photo.width) // 2, py))
    sy = 150 + (780 - sheet.height) // 2
    canvas.paste(sheet, (680 + (1180 - sheet.width) // 2, sy))

    # 화살표
    d.polygon([(600, 520), (650, 540), (600, 560)], fill=(220, 120, 110))
    d.rectangle([585, 534, 605, 546], fill=(220, 120, 110))

    d.text((320, 970), "원본 사진", font=label, fill=(110, 90, 80), anchor="mm")
    d.text((1270, 970), "수채화 캐릭터 시트", font=label, fill=(110, 90, 80), anchor="mm")
    d.text((W - 40, H - 30), "※ 원본은 AI로 생성한 예시 사진입니다", font=small, fill=(150, 140, 130), anchor="rm")
    canvas.save(OUT / f"{key}_compare.png")
    print(f"{key}_compare.png")
