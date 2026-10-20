# 하린이와 초코의 이상한 나라 (강의 샘플) — 잠자리 그림책 전자책 생성
# 산출: ebook/ 아래
#   - 하린이와_초코의_이상한_나라_KO.epub / _EN.epub : EPUB 3 고정 레이아웃(1920x1080), 쪽마다 그림 + 나레이션 전문 + 음성 듣기
#     (Apple Books 가 주 시연본 — 스크립트 의존 없이 <audio> 로 재생, 자동 재생 없음)
#   - 하린이와_초코의_이상한_나라_그림책.html : 그림·음성·폰트를 전부 내장한 단일 파일 (iPad Safari 예비 시연본, 한/영 전환)
# 글·음성 단일 출처: make_narration.py / make_narration_en.py 의 SCENES, audio*/sXX.wav (추가 TTS 없음)
import base64
import html
import io
import subprocess
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from make_narration import SCENES as SCENES_KO
from make_narration_en import SCENES as SCENES_EN

BASE = Path(__file__).parent
OUT = BASE / "ebook"
MEDIA = OUT / "_media"
MEDIA.mkdir(parents=True, exist_ok=True)
FFMPEG = (
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.EXE"
)
PW, PH = 1920, 1080  # 페이지 크기 (16:9 가로)
IMG_W, IMG_H = 1440, 804  # 그림 영역 — 아래 276px 는 글 영역

TITLE = {"ko": "하린이와 초코의 이상한 나라", "en": "Harin and Choco in Wonderland"}
COVER_SUB = {"ko": "잠자리 그림책", "en": "A Bedtime Picture Book"}
END_TEXT = {"ko": "오늘 밤 꿈에서 또 만나요", "en": "See you again in your dreams tonight"}
LISTEN = {"ko": "읽어 주기", "en": "Read to me"}
SIDS = list(SCENES_KO.keys())


FONT_SUB = MEDIA / "font_sub.ttf"


def prepare_media():
    """그림 → JPEG(용량 절감), 씬 wav → mono 64kbps mp3, 폰트 → 실제 쓰는 글자만 서브셋(5.4MB → 수십 KB)"""
    from fontTools import subset
    used = "".join(SCENES_KO.values()) + "".join(SCENES_EN.values()) + "".join(
        "".join(d.values()) for d in (TITLE, COVER_SUB, END_TEXT, LISTEN)) + "English한국어▶■/0123456789 "
    opts = subset.Options()
    font = subset.load_font(str(BASE / "font.ttf"), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text=used)
    sub.subset(font)
    subset.save_font(font, str(FONT_SUB), opts)
    for sid in SIDS:
        jpg = MEDIA / f"{sid}.jpg"
        if not jpg.exists():
            Image.open(BASE / "images" / f"{sid}.png").convert("RGB").save(jpg, quality=85)
        for lang, folder in (("ko", "audio"), ("en", "audio_en")):
            mp3 = MEDIA / f"{sid}_{lang}.mp3"
            if not mp3.exists():
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(BASE / folder / f"{sid}.wav"),
                                "-ac", "1", "-b:a", "64k", str(mp3)], check=True)


CSS = f"""
@font-face {{ font-family: "Kkukkukk"; src: url("FONT_URL"); }}
html, body {{ margin: 0; padding: 0; }}
body {{ width: {PW}px; height: {PH}px; overflow: hidden; background: #1d2240; color: #fbf3e4;
       font-family: "Kkukkukk", sans-serif; }}
.pic {{ position: absolute; left: {(PW - IMG_W) // 2}px; top: 28px; width: {IMG_W}px; height: {IMG_H - 28}px;
        object-fit: cover; border-radius: 28px; }}
.text {{ position: absolute; left: {(PW - IMG_W) // 2}px; top: {IMG_H + 14}px; width: {IMG_W - 260}px;
         font-size: 31px; line-height: 1.45; word-break: keep-all; }}
.text.en {{ font-family: "Avenir Next", "Helvetica Neue", sans-serif; font-weight: 500; font-size: 29px; line-height: 1.4; }}
.listen {{ position: absolute; right: {(PW - IMG_W) // 2}px; top: {IMG_H + 40}px; width: 230px; text-align: center; }}
.listen span {{ display: block; font-size: 26px; color: #f6c96b; margin-bottom: 8px; }}
.listen audio {{ width: 230px; }}
.cover-img {{ position: absolute; inset: 0; width: {PW}px; height: {PH}px; object-fit: cover; opacity: .55; }}
.cover-title {{ position: absolute; top: 380px; width: {PW}px; text-align: center; font-size: 96px;
                text-shadow: 0 4px 18px rgba(0,0,0,.6); }}
.cover-sub {{ position: absolute; top: 520px; width: {PW}px; text-align: center; font-size: 44px; color: #f6c96b;
              text-shadow: 0 3px 12px rgba(0,0,0,.6); }}
"""


def page_xhtml(lang, body, font_url):
    css = CSS.replace("FONT_URL", font_url)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}" lang="{lang}">
<head><meta charset="UTF-8"/><meta name="viewport" content="width={PW}, height={PH}"/>
<title>{html.escape(TITLE[lang])}</title><style>{css}</style></head>
<body>{body}</body></html>"""


def build_epub(lang):
    scenes = SCENES_KO if lang == "ko" else SCENES_EN
    pages = []  # (filename, xhtml)
    font_url = "font.ttf"
    pages.append(("cover.xhtml", page_xhtml(lang, (
        f'<img class="cover-img" src="s02.jpg" alt=""/>'
        f'<div class="cover-title">{html.escape(TITLE[lang])}</div>'
        f'<div class="cover-sub">{COVER_SUB[lang]}</div>'), font_url)))
    for sid in SIDS:
        body = (f'<img class="pic" src="{sid}.jpg" alt=""/>'
                f'<div class="text {lang}">{html.escape(scenes[sid])}</div>'
                f'<div class="listen"><span>{LISTEN[lang]}</span>'
                f'<audio controls="controls" preload="none" src="{sid}_{lang}.mp3"></audio></div>')
        pages.append((f"{sid}.xhtml", page_xhtml(lang, body, font_url)))
    pages.append(("end.xhtml", page_xhtml(lang, (
        f'<img class="cover-img" src="s10.jpg" alt=""/>'
        f'<div class="cover-title" style="font-size:80px">{END_TEXT[lang]}</div>'), font_url)))

    book_id = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'harin-choco-wonderland-' + lang)}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="font" href="font.ttf" media-type="font/ttf"/>',
                '<item id="cover-image" href="s02.jpg" media-type="image/jpeg" properties="cover-image"/>']
    for sid in SIDS:
        if sid != "s02":
            manifest.append(f'<item id="img-{sid}" href="{sid}.jpg" media-type="image/jpeg"/>')
        manifest.append(f'<item id="aud-{sid}" href="{sid}_{lang}.mp3" media-type="audio/mpeg"/>')
    spine = []
    for name, _ in pages:
        pid = "p-" + name.split(".")[0]
        manifest.append(f'<item id="{pid}" href="{name}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{pid}"/>')
    opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{lang}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{book_id}</dc:identifier>
<dc:title>{html.escape(TITLE[lang])}</dc:title>
<dc:language>{lang}</dc:language>
<dc:creator>Malli Storybook</dc:creator>
<meta property="dcterms:modified">{modified}</meta>
<meta property="rendition:layout">pre-paginated</meta>
<meta property="rendition:orientation">landscape</meta>
<meta property="rendition:spread">none</meta>
</metadata>
<manifest>
{chr(10).join(manifest)}
</manifest>
<spine>
{chr(10).join(spine)}
</spine>
</package>"""
    nav_items = "".join(f'<li><a href="{n}">{n.split(".")[0]}</a></li>' for n, _ in pages)
    nav = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}" lang="{lang}">
<head><meta charset="UTF-8"/><title>{html.escape(TITLE[lang])}</title></head>
<body><nav epub:type="toc" id="toc"><ol>{nav_items}</ol></nav></body></html>"""
    container = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""

    path = OUT / f"하린이와_초코의_이상한_나라_{lang.upper()}.epub"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)  # 첫 항목·무압축 필수
        z.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        z.write(FONT_SUB, "OEBPS/font.ttf", compress_type=zipfile.ZIP_DEFLATED)
        for sid in SIDS:
            z.write(MEDIA / f"{sid}.jpg", f"OEBPS/{sid}.jpg", compress_type=zipfile.ZIP_STORED)
            z.write(MEDIA / f"{sid}_{lang}.mp3", f"OEBPS/{sid}_{lang}.mp3", compress_type=zipfile.ZIP_STORED)
        for name, x in pages:
            z.writestr(f"OEBPS/{name}", x, compress_type=zipfile.ZIP_DEFLATED)
    print(f"{path.name}: {path.stat().st_size:,} bytes")


def b64(path, mime):
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def build_html():
    """단일 파일 그림책 — 화면 크기에 맞춰 1920x1080 무대를 축소, 탭/스와이프/화살표로 넘김, 한/영 전환"""
    imgs = {sid: b64(MEDIA / f"{sid}.jpg", "image/jpeg") for sid in SIDS}
    auds = {f"{sid}_{lang}": b64(MEDIA / f"{sid}_{lang}.mp3", "audio/mpeg") for sid in SIDS for lang in ("ko", "en")}
    font = b64(FONT_SUB, "font/ttf")
    import json
    data = json.dumps({"ko": SCENES_KO, "en": SCENES_EN, "title": TITLE, "sub": COVER_SUB, "end": END_TEXT,
                       "listen": LISTEN, "sids": SIDS}, ensure_ascii=False)
    page_html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>{TITLE['ko']}</title>
<style>
@font-face {{ font-family: "Kkukkukk"; src: url("{font}"); }}
html, body {{ margin: 0; height: 100%; background: #12152b; overflow: hidden; touch-action: manipulation;
             -webkit-user-select: none; user-select: none; }}
#stage {{ position: absolute; width: {PW}px; height: {PH}px; left: 50%; top: 50%; transform-origin: center;
          background: #1d2240; color: #fbf3e4; font-family: "Kkukkukk", sans-serif; overflow: hidden; }}
.pic {{ position: absolute; left: {(PW - IMG_W) // 2}px; top: 28px; width: {IMG_W}px; height: {IMG_H - 28}px;
        object-fit: cover; border-radius: 28px; transition: opacity .5s; }}
.text {{ position: absolute; left: {(PW - IMG_W) // 2}px; top: {IMG_H + 14}px; width: {IMG_W - 280}px;
         font-size: 31px; line-height: 1.45; word-break: keep-all; }}
.text.en {{ font-family: "Avenir Next", "Helvetica Neue", sans-serif; font-weight: 500; font-size: 29px; line-height: 1.4; }}
.full {{ position: absolute; inset: 0; width: {PW}px; height: {PH}px; object-fit: cover; opacity: .55; border-radius: 0; }}
.big {{ position: absolute; top: 380px; width: {PW}px; text-align: center; font-size: 96px;
        text-shadow: 0 4px 18px rgba(0,0,0,.6); }}
.sub {{ position: absolute; top: 520px; width: {PW}px; text-align: center; font-size: 44px; color: #f6c96b;
        text-shadow: 0 3px 12px rgba(0,0,0,.6); }}
button {{ font-family: inherit; border: 0; cursor: pointer; }}
#listen {{ position: absolute; right: {(PW - IMG_W) // 2}px; top: {IMG_H + 46}px; width: 250px; height: 92px;
           border-radius: 46px; background: #f6c96b; color: #1d2240; font-size: 34px; }}
#listen.playing {{ background: #fbf3e4; }}
#lang {{ position: absolute; right: 36px; top: 36px; padding: 10px 26px; border-radius: 30px; font-size: 28px;
         background: rgba(29,34,64,.75); color: #fbf3e4; border: 2px solid #f6c96b; z-index: 2; }}
.nav {{ position: absolute; top: 0; height: {PH}px; width: 220px; background: transparent; z-index: 1; }}
#prev {{ left: 0; }} #next {{ right: 0; }}
#count {{ position: absolute; left: 36px; top: 40px; font-size: 26px; color: #b9b3c9; z-index: 2; }}
</style></head>
<body>
<div id="stage">
  <div id="page"></div>
  <button class="nav" id="prev" aria-label="이전 쪽"></button>
  <button class="nav" id="next" aria-label="다음 쪽"></button>
  <button id="lang">English</button>
  <div id="count"></div>
</div>
<audio id="player" preload="none"></audio>
<script>
const D = {data};
const IMG = {json.dumps(imgs)};
const AUD = {json.dumps(auds)};
let lang = "ko", idx = 0;
const total = D.sids.length + 2;  // 표지 + 본문 + 끝
const page = document.getElementById("page"), player = document.getElementById("player");
function esc(s) {{ const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }}
function stop() {{ player.pause(); player.removeAttribute("src"); const b = document.getElementById("listen"); if (b) b.classList.remove("playing"); }}
function render() {{
  stop();
  document.documentElement.lang = lang;
  document.getElementById("lang").textContent = lang === "ko" ? "English" : "한국어";
  document.getElementById("count").textContent = (idx + 1) + " / " + total;
  if (idx === 0) {{
    page.innerHTML = `<img class="pic full" src="${{IMG.s02}}"><div class="big">${{esc(D.title[lang])}}</div><div class="sub">${{esc(D.sub[lang])}}</div>`;
  }} else if (idx === total - 1) {{
    page.innerHTML = `<img class="pic full" src="${{IMG.s10}}"><div class="big" style="font-size:80px">${{esc(D.end[lang])}}</div>`;
  }} else {{
    const sid = D.sids[idx - 1];
    page.innerHTML = `<img class="pic" src="${{IMG[sid]}}"><div class="text ${{lang}}">${{esc(D[lang][sid])}}</div>` +
      `<button id="listen">▶ ${{esc(D.listen[lang])}}</button>`;
    document.getElementById("listen").onclick = (e) => {{
      e.stopPropagation();
      const b = e.currentTarget;
      if (!player.paused) {{ stop(); return; }}
      player.src = AUD[sid + "_" + lang];
      player.play();
      b.classList.add("playing"); b.textContent = "■ " + D.listen[lang];
    }};
  }}
}}
player.onended = () => {{ const b = document.getElementById("listen"); if (b) {{ b.classList.remove("playing"); b.textContent = "▶ " + D.listen[lang]; }} }};
function go(d) {{ idx = Math.max(0, Math.min(total - 1, idx + d)); render(); }}
document.getElementById("prev").onclick = () => go(-1);
document.getElementById("next").onclick = () => go(1);
document.getElementById("lang").onclick = () => {{ lang = lang === "ko" ? "en" : "ko"; render(); }};
document.addEventListener("keydown", (e) => {{ if (e.key === "ArrowRight") go(1); if (e.key === "ArrowLeft") go(-1); }});
let sx = null;
document.addEventListener("touchstart", (e) => {{ sx = e.touches[0].clientX; }}, {{ passive: true }});
document.addEventListener("touchend", (e) => {{ if (sx === null) return; const dx = e.changedTouches[0].clientX - sx;
  if (Math.abs(dx) > 60) go(dx < 0 ? 1 : -1); sx = null; }});
function fit() {{ const s = Math.min(innerWidth / {PW}, innerHeight / {PH});
  document.getElementById("stage").style.transform = `translate(-50%, -50%) scale(${{s}})`; }}
addEventListener("resize", fit); fit(); render();
</script>
</body></html>"""
    path = OUT / "하린이와_초코의_이상한_나라_그림책.html"
    path.write_text(page_html, encoding="utf-8")
    print(f"{path.name}: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    prepare_media()
    build_epub("ko")
    build_epub("en")
    build_html()
