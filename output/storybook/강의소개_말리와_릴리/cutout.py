# 말리 포즈(M*.png, 흰 배경) → 투명 PNG(malli/M*.png). rembg isnet-anime (일러스트용 모델)
# 흰 배경 + 크림색 털이라 단순 colorkey 는 털이 같이 빠짐 → 배경 제거 모델 사용
import sys
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

BASE = Path(__file__).parent
OUT = BASE / "malli"
OUT.mkdir(exist_ok=True)

session = new_session("isnet-anime")
for src in sorted((BASE / "images").glob("M*.png")):
    out = OUT / src.name
    if out.exists() and "-f" not in sys.argv:
        print(f"{src.stem}: cached")
        continue
    im = remove(Image.open(src).convert("RGB"), session=session)
    a = im.getchannel("A").point(lambda v: 0 if v < 10 else v)  # 배경 잔여 alpha(1~9) 제거 — 안 하면 bbox 가 전체
    im.putalpha(a)
    im = im.crop(a.getbbox())  # 여백 제거 → 합성 시 크기 기준 통일
    im.save(out)
    print(f"{src.stem}: {im.size}")
