# -*- coding: utf-8 -*-
"""말리 동화 순서도 3종 → HTML 생성 → Chrome 헤드리스로 PDF·PNG 출력.

1) 제작 파이프라인 순서도 (CLAUDE.md 승인 게이트·배정 규칙 기준)
2) 강의 커리큘럼 흐름도 (수업/말리동화_커리큘럼.html 12챕터·40강 기준)
3) 영상 삽입용 7단계 흐름도 슬라이드 (강의대본_챕터3.md 03:30 장면 화면 지시 기준)
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PAPER, CARD, INK, MUTED, LINE = "#f5f9f1", "#ffffff", "#1d2a21", "#5a6b5d", "#cfdcc9"
MEADOW, MEADOW_SOFT = "#3b7a4c", "#e3f0e2"
RIBBON, RIBBON_SOFT = "#d23f36", "#fbe7e4"
SKY, SKY_INK = "#dcedf6", "#2f6f8f"
GOLD, GOLD_DARK = "#f2c14e", "#b8860b"
FONT = "'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif"


# ---------- SVG 도우미 ----------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def lines(x, y, rows, size, color, weight=400, gap=1.3):
    """여러 줄 텍스트를 (x, y) 중심에 세로 가운데 정렬로 그린다."""
    n = len(rows)
    top = y - (n - 1) * size * gap / 2
    out = []
    for i, r in enumerate(rows):
        out.append(
            f'<text x="{x}" y="{top + i * size * gap:.1f}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="middle" dominant-baseline="central">{esc(r)}</text>'
        )
    return "".join(out)


def coin(cx, cy, r=11):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GOLD}" stroke="{GOLD_DARK}" stroke-width="1.5"/>'
        f'<text x="{cx}" y="{cy + 0.5}" font-size="{r * 1.15:.1f}" fill="{GOLD_DARK}" font-weight="700" '
        f'text-anchor="middle" dominant-baseline="central">₩</text>'
    )


def box(x, y, title, sub="", kind="step", w=160, h=64):
    fill, stroke = {"step": (CARD, MEADOW), "paid": (CARD, GOLD_DARK), "free": (MEADOW_SOFT, MEADOW),
                    "fix": (RIBBON_SOFT, RIBBON), "end": (MEADOW, MEADOW)}[kind]
    rx = h / 2 if kind == "end" else 10
    s = (f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
         f'stroke="{stroke}" stroke-width="2"/>')
    tcolor = "#fff" if kind == "end" else INK
    if sub:
        s += lines(x, y - 10, [title], 15, tcolor, 700)
        s += lines(x, y + 13, sub.split("\n"), 11, MUTED)
    else:
        s += lines(x, y, [title], 15, tcolor, 700)
    if kind == "paid":
        s += coin(x + w / 2 - 4, y - h / 2 + 4, 10)
    return s


def diamond(x, y, rows, kind="gate", w=136, h=96):
    fill, stroke, color = (RIBBON_SOFT, RIBBON, RIBBON) if kind == "gate" else (SKY, SKY_INK, SKY_INK)
    pts = f"{x},{y - h / 2} {x + w / 2},{y} {x},{y + h / 2} {x - w / 2},{y}"
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2.2"/>'
            + lines(x, y, rows, 12.5, color, 700))


def arrow(pts, label="", lpos=None, color=MUTED, dash=False):
    d = " ".join(f"{px},{py}" for px, py in pts)
    marker = "arrR" if color == RIBBON else "arr"
    dasharray = 'stroke-dasharray="6 4"' if dash else ""
    s = (f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="2" '
         f'{dasharray} marker-end="url(#{marker})"/>')
    if label:
        lx, ly = lpos
        s += (f'<text x="{lx}" y="{ly}" font-size="11.5" fill="{color}" font-weight="700" '
              f'text-anchor="middle" dominant-baseline="central" paint-order="stroke" '
              f'stroke="{PAPER}" stroke-width="4">{esc(label)}</text>')
    return s


DEFS = f"""<defs>
<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>
<marker id="arrR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{RIBBON}"/></marker>
<marker id="arrB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="20" markerHeight="20" markerUnits="userSpaceOnUse" orient="auto">
<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>
</defs>"""


# ---------- 1) 제작 파이프라인 ----------
def pipeline_svg():
    s = [f'<svg viewBox="0 0 1120 650" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">', DEFS]
    R1, R2, R3 = 92, 305, 525
    # 1행: 기획 → 확인 ① → 대본 → 확인 ②
    s.append(box(90, R1, "1 동화 고르기", "후보 4개 → 1편 선택"))
    s.append(box(270, R1, "2 이야기 개요", "주인공·교훈·줄거리 3줄\n순화 방법"))
    s.append(diamond(450, R1, ["확인 ①", "개요 승인?"]))
    s.append(box(630, R1, "3 대본 · 장면 나누기", "10장면 + 목소리 연기 지시"))
    s.append(box(810, R1, "4 점수표 · 배정표", "감정·움직임·중요도"))
    s.append(diamond(990, R1, ["확인 ②", "배정표 승인?"]))
    s.append(arrow([(170, R1), (188, R1)]))
    s.append(arrow([(350, R1), (380, R1)]))
    s.append(arrow([(518, R1), (548, R1)], "예", (533, R1 - 12)))
    s.append(arrow([(710, R1), (728, R1)]))
    s.append(arrow([(890, R1), (920, R1)]))
    s.append(arrow([(450, R1 - 48), (450, 22), (270, 22), (270, R1 - 34)], "아니오 · 고쳐서 다시", (360, 11), RIBBON))
    s.append(arrow([(990, R1 - 48), (990, 22), (810, 22), (810, R1 - 34)], "아니오 · 고쳐서 다시", (900, 11), RIBBON))
    s.append(arrow([(990, R1 + 48), (990, R2 - 34)], "예 → 여기부터 크레딧 사용", (1000, 200)))
    # 2행 (오른쪽 → 왼쪽): 그림 → 나레이션 → 장면 나누기 → 배정 분기
    s.append(box(990, R2, "5 장면 그림 10장", "말리 시트 첨부 · Gemini", "paid"))
    s.append(box(790, R2, "6 나레이션 녹음", "전체 대본 1회 호출\nGemini TTS (Kore)", "paid"))
    s.append(box(590, R2, "7 장면별로 자르기", "Whisper 받아쓰기\n타임스탬프로 분할"))
    s.append(diamond(400, R2, ["움직임 7 이상", "그리고", "중요도 85 이상?"], "decide", 156, 110))
    s.append(box(190, R2 - 58, "8a 움직이는 장면", "Veo 3.1 · 편당 2개 안팎", "paid", 150))
    s.append(box(190, R2 + 58, "8b 정지 그림 + 줌", "Ken Burns · 무료", "free", 150))
    s.append(arrow([(910, R2), (872, R2)]))
    s.append(arrow([(710, R2), (672, R2)]))
    s.append(arrow([(510, R2), (480, R2)]))
    s.append(arrow([(322, R2), (295, R2), (295, R2 - 58), (267, R2 - 58)], "예", (308, R2 - 40)))
    s.append(arrow([(295, R2), (295, R2 + 58), (267, R2 + 58)], "아니오", (318, R2 + 40)))
    s.append(arrow([(115, R2 - 58), (60, R2 - 58), (60, R3 - 34)]))
    s.append(f'<polyline points="115,{R2 + 58} 60,{R2 + 58}" fill="none" stroke="{MUTED}" stroke-width="2"/>')
    # 3행: 조립 → 검증 → 마무리
    s.append(box(140, R3, "9 조립 (compose)", "줌·바닥 자막·BGM\n엔딩 구독 인사", "step", 170))
    s.append(box(350, R3, "10 프레임 검증", "ffmpeg -ss 로 장면 추출\n자막·화면 눈으로 확인"))
    s.append(diamond(545, R3, ["자막·화면", "맞나?"], "decide", 120, 90))
    s.append(box(745, R3, "11 썸네일·쇼츠·제목", "승인 없이 진행"))
    s.append(box(935, R3, "12 기록", "context-notes\nchecklist 갱신", "step", 150))
    s.append(box(1068, R3, "완성", "", "end", 84, 48))
    s.append(box(545, 618, "문제 장면만 다시 만들기", "audio/sXX.wav · scenes/sXX.mp4 삭제 후 재실행", "fix", 300, 52))
    s.append(arrow([(225, R3), (268, R3)]))
    s.append(arrow([(430, R3), (483, R3)]))
    s.append(arrow([(605, R3), (663, R3)], "예", (634, R3 - 12)))
    s.append(arrow([(825, R3), (858, R3)]))
    s.append(arrow([(1010, R3), (1024, R3)]))
    s.append(arrow([(545, R3 + 45), (545, 590)], "아니오", (572, 575), RIBBON))
    s.append(arrow([(395, 618), (140, 618), (140, R3 + 34)], "", None, RIBBON))
    s.append("</svg>")
    return "".join(s)


# ---------- 2) 커리큘럼 ----------
CURRI = [
    ("WELCOME", "말리와 동화 작가 되기", "06:00", "", ["완성작 미리보기"]),
    ("CH 1", "채널 설계: 말리는 누구?", "29:00", "", ["5~7세 영상 규칙", "말리 캐릭터 시트 만들기", "그림체 기준 그림 정하기"]),
    ("CH 2", "도구 세팅 완벽 가이드", "46:00", "", ["Claude Code 설치·로그인", "Python·ffmpeg·Git 설치",
                                          "Gemini API 키·결제 등록", "Whisper 첫 받아쓰기", "프로젝트 폴더 구조"]),
    ("CH 3", "어떤 동화를 만들까요?", "24:00", "", ["퍼블릭 도메인 동화 150편", "적합도 상·중·하 나누기",
                                         "후보 4개 받고 고르기 ✎"]),
    ("CH 4", "확인 ①: 개요와 순화", "26:00", "gate", ["왜 두 번 확인할까요?", "개요: 주인공·교훈·줄거리",
                                              "순화 사례 보기 ✎"]),
    ("CH 5", "대본과 10장면 나누기", "36:00", "", ["이야기 5단계", "따라 하는 후렴 넣기",
                                            "나레이션에 넣지 않는 것", "장면별 연기 지시 ✎"]),
    ("CH 6", "확인 ②: 점수표·배정표", "17:00", "gate", ["감정·움직임·중요도 점수", "배정표 승인: 영상 2개"]),
    ("CH 7", "그림 그리기: 10장", "37:00", "paid", ["그림 프롬프트 구조", "같은 인물로 보이는 소품",
                                           "10장 한꺼번에 만들기 ✎", "그림체 검수·다시 만들기"]),
    ("CH 8", "목소리 입히기", "39:00", "paid", ["전체를 한 번에 읽히는 이유", "Gemini TTS 동화 성우",
                                        "Whisper로 장면별 자르기", "받아쓰기 오류 고치기 ✎"]),
    ("CH 9", "움직이는 장면 만들기", "26:00", "paid", ["Veo 프롬프트 쓰는 법", "변신 장면의 함정",
                                            "실패 시: Fast→Lite→정지"]),
    ("CH 10", "한 편으로 합치기", "27:00", "", ["줌과 영상 장면 끼우기", "바닥 자막·시각 맞추기",
                                         "배경음악 잇기 ✎"]),
    ("CH 11", "썸네일·쇼츠·제목", "26:00", "", ["썸네일: 왼쪽 1/3 큰 문구", "30초 쇼츠: 궁금할 때 끊기",
                                         "제목 엔진: 후보 10여 개"]),
    ("CH 12", "업로드와 다음 편 준비", "15:00", "", ["완성본 마지막 검수", "배운 점 기록하기"]),
]


def curri_card(i, c):
    label, title, t, kind, lec = c
    badge = {"gate": '<span class="badge gate">사람 확인</span>',
             "paid": '<span class="badge paid">₩ 크레딧</span>'}.get(kind, "")
    lis = "".join(f"<li>{esc(x).replace('✎', '<b class=pr>실습</b>')}</li>" for x in lec)
    return (f'<div class="cc {kind}"><div class="ch"><span>{label}</span>{badge}<span class="tm">{t}</span></div>'
            f'<h3>{esc(title)}</h3><ol>{lis}</ol><div class="cnt">강의 {len(lec)}개</div></div>')


def curriculum_grid():
    # 9열(카드·화살표 교차) × 5행(카드행·화살표행 교차), 뱀 모양 순서
    cells = []
    order = [(1, c) for c in range(5)] + [(3, 4 - c) for c in range(5)] + [(5, c) for c in range(3)]
    for i, (row, col) in enumerate(order):
        cells.append(f'<div style="grid-row:{row};grid-column:{col * 2 + 1}">{curri_card(i, CURRI[i])}</div>')
    for col in range(4):  # 1행 →
        cells.append(f'<div class="ar" style="grid-row:1;grid-column:{col * 2 + 2}">→</div>')
    for col in range(4):  # 2행 ←
        cells.append(f'<div class="ar" style="grid-row:3;grid-column:{col * 2 + 2}">←</div>')
    for col in range(2):  # 3행 →
        cells.append(f'<div class="ar" style="grid-row:5;grid-column:{col * 2 + 2}">→</div>')
    cells.append('<div class="ar dn" style="grid-row:2;grid-column:9">↓</div>')
    cells.append('<div class="ar dn" style="grid-row:4;grid-column:1">↓</div>')
    cells.append('<div class="ar" style="grid-row:5;grid-column:6">→</div>')
    cells.append('<div style="grid-row:5;grid-column:7 / span 3" class="done">'
                 '<b>수강 완료</b><span>말리 동화 한 편 완성<br>본편 3~4분 · 쇼츠 30초 · 썸네일 · 업로드 문구</span>'
                 '<span class="sum">챕터 12개 + WELCOME · 강의 40개 · 총 5시간 54분</span></div>')
    return '<div class="cgrid">' + "".join(cells) + "</div>"


# ---------- 3) 영상 삽입용 슬라이드 ----------
def slide_svg():
    W, H = 1600, 900
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}" '
         f'preserveAspectRatio="xMidYMid meet">', DEFS]
    s.append(f'<rect width="{W}" height="{H}" fill="#fbf6ea"/>')
    s.append(f'<rect x="24" y="24" width="{W - 48}" height="{H - 48}" rx="28" fill="none" stroke="#e7dcc3" stroke-width="3"/>')
    s.append(lines(W / 2, 110, ["3번 칸 · 중간 확인 지점"], 30, MUTED, 700))
    s.append(lines(W / 2, 168, ["돈이 들기 전에, 딱 두 번만 확인해요"], 50, INK, 700))
    steps = ["동화 고르기", "이야기 개요", "대본과\n장면 나누기", "그림", "목소리", "움직이는\n장면", "조립"]
    cw, ch, y = 155, 190, 470
    gaps = [44, 110, 110, 44, 44, 44]
    xs, x = [], 60
    for i in range(7):
        xs.append(x)
        x += cw + (gaps[i] if i < 6 else 0)
    # 돈이 드는 구간 괄호
    bx0, bx1 = xs[3], xs[6] + cw
    s.append(f'<path d="M{bx0},{y - 150} L{bx0},{y - 165} L{bx1},{y - 165} L{bx1},{y - 150}" fill="none" '
             f'stroke="{GOLD_DARK}" stroke-width="3"/>')
    s.append(lines((bx0 + bx1) / 2, y - 192, ["여기부터 돈이 들어요"], 26, GOLD_DARK, 700))
    for i, (sx, name) in enumerate(zip(xs, steps)):
        paid = i >= 3
        fill = "#fffdf7" if not paid else "#fff8e3"
        stroke = MEADOW if not paid else GOLD_DARK
        s.append(f'<rect x="{sx}" y="{y - ch / 2}" width="{cw}" height="{ch}" rx="22" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="4"/>')
        s.append(f'<circle cx="{sx + cw / 2}" cy="{y - 45}" r="27" fill="{stroke}"/>')
        s.append(lines(sx + cw / 2, y - 45, [str(i + 1)], 30, "#fff", 700))
        s.append(lines(sx + cw / 2, y + 38, name.split("\n"), 24, INK, 700, 1.25))
        if paid:  # 동전: 움직이는 장면은 가장 비싸서 3개
            n = 3 if i == 5 else 1
            for k in range(n):
                s.append(coin(sx + cw / 2 + (k - (n - 1) / 2) * 40, y - ch / 2 - 34, 18))
        if i < 6:
            ax0, ax1 = sx + cw + 6, xs[i + 1] - 8
            s.append(f'<line x1="{ax0}" y1="{y}" x2="{ax1}" y2="{y}" stroke="{MUTED}" stroke-width="4" marker-end="url(#arrB)"/>')
    # 확인 깃발: 2단계 뒤, 3단계 뒤
    for gi, label in [(1, "확인 ①"), (2, "확인 ②")]:
        px = xs[gi] + cw + gaps[gi] / 2
        top, base = y + 14, y + ch / 2 + 125
        s.append(f'<line x1="{px}" y1="{top}" x2="{px}" y2="{base}" stroke="#8a5a3b" stroke-width="5" stroke-linecap="round"/>')
        s.append(f'<path d="M{px},{y + ch / 2 + 12} L{px + 70},{y + ch / 2 + 36} L{px},{y + ch / 2 + 60} z" fill="{RIBBON}"/>')
        s.append(lines(px, base + 30, [label], 28, RIBBON, 700))
    s.append(lines(xs[1] + cw + gaps[1] / 2, y + ch / 2 + 205, ["개요 보고 승인"], 21, MUTED))
    s.append(lines(xs[2] + cw + gaps[2] / 2, y + ch / 2 + 205, ["배정표 보고 승인"], 21, MUTED))
    # 마지막 줄
    s.append(f'<rect x="{W / 2 - 520}" y="790" width="1040" height="0" fill="none"/>')
    s.append(lines(W / 2 + 330, 690, ["두 번 승인한 뒤에는", "끝까지 묻지 않고 진행!"], 28, MEADOW, 700, 1.35))
    s.append("</svg>")
    return "".join(s)


CSS = f"""
@page {{ size: A4 landscape; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: {PAPER}; color: {INK}; font-family: {FONT}; }}
.page {{ width: 297mm; height: 210mm; padding: 11mm 13mm 9mm; page-break-after: always; overflow: hidden;
        display: grid; grid-template-rows: auto minmax(0, 1fr) auto; gap: 4mm; background: {PAPER}; }}
.page:last-child {{ page-break-after: auto; }}
header {{ display: flex; justify-content: space-between; align-items: end; border-bottom: 2px solid {MEADOW}; padding-bottom: 2.5mm; }}
header .eb {{ font-size: 9pt; color: {MUTED}; letter-spacing: .05em; }}
header h1 {{ margin: 1mm 0 0; font-size: 19pt; }}
header .no {{ font-size: 28pt; color: {MEADOW}; font-weight: 700; line-height: 1; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 2mm 6mm; font-size: 8.5pt; color: {MUTED}; align-items: center; }}
.legend i {{ display: inline-block; width: 12px; height: 12px; margin-right: 4px; vertical-align: -2px; border: 2px solid; border-radius: 3px; }}
.legend .g {{ background: {RIBBON_SOFT}; border-color: {RIBBON}; transform: rotate(45deg) scale(.85); }}
.legend .d {{ background: {SKY}; border-color: {SKY_INK}; transform: rotate(45deg) scale(.85); }}
.legend .p {{ background: {GOLD}; border-color: {GOLD_DARK}; border-radius: 50%; }}
.legend .f {{ background: {MEADOW_SOFT}; border-color: {MEADOW}; }}
.legend .s {{ background: #fff; border-color: {MEADOW}; }}
.fig {{ min-height: 0; display: grid; place-items: center; }}
.fig svg {{ width: 100%; height: 100%; }}
footer {{ font-size: 7.8pt; color: {MUTED}; line-height: 1.5; }}
.cgrid {{ display: grid; width: 100%; height: 100%;
         grid-template-columns: repeat(4, minmax(0,1fr) 5mm) minmax(0,1fr);
         grid-template-rows: minmax(0,1fr) 4.5mm minmax(0,1fr) 4.5mm minmax(0,1fr); }}
.cgrid > div {{ min-width: 0; min-height: 0; }}
.ar {{ display: grid; place-items: center; color: {MUTED}; font-size: 12pt; font-weight: 700; }}
.cc {{ height: 100%; background: {CARD}; border: 1.5px solid {LINE}; border-left: 4px solid {MEADOW}; border-radius: 6px;
      padding: 2mm 2.5mm; display: grid; grid-template-rows: auto auto 1fr auto; gap: .8mm; }}
.cc.gate {{ border-left-color: {RIBBON}; background: #fff8f7; }}
.cc.paid {{ border-left-color: {GOLD_DARK}; background: #fffcf2; }}
.cc .ch {{ display: flex; gap: 1.5mm; align-items: center; font-size: 7.5pt; color: {MUTED}; font-weight: 700; }}
.cc .tm {{ margin-left: auto; font-weight: 400; }}
.cc h3 {{ margin: 0; font-size: 11pt; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.25; }}
.cc ol {{ margin: 0; padding-left: 4.2mm; font-size: 8.4pt; line-height: 1.5; color: #2d3a30; }}
.cc .cnt {{ font-size: 7pt; color: {MUTED}; text-align: right; }}
.pr {{ white-space: nowrap; font-size: 6.5pt; background: {RIBBON_SOFT}; color: {RIBBON}; padding: 0 3px; border-radius: 3px; font-weight: 700; }}
.badge {{ font-size: 6.5pt; padding: 0 4px; border-radius: 3px; }}
.badge.gate {{ background: {RIBBON_SOFT}; color: {RIBBON}; }}
.badge.paid {{ background: #fdf0c8; color: {GOLD_DARK}; }}
.done {{ background: {MEADOW}; color: #fff; border-radius: 10px; display: grid; align-content: center; gap: 1.2mm; padding: 3mm 5mm; }}
.done b {{ font-size: 15pt; }}
.done span {{ font-size: 8.5pt; line-height: 1.5; }}
.done .sum {{ opacity: .85; font-size: 7.8pt; }}
.slide {{ width: 100%; aspect-ratio: 16/9; max-height: 100%; border-radius: 6px; overflow: hidden; box-shadow: 0 0 0 1px {LINE}; }}
.slide svg {{ display: block; width: 100%; height: 100%; }}
"""


def page(no, eyebrow, title, body, legend="", foot=""):
    return (f'<section class="page"><div><header><div><div class="eb">{eyebrow}</div><h1>{title}</h1></div>'
            f'<div class="no">{no}</div></header>{f"<div class=legend style=margin-top:2mm>{legend}</div>" if legend else ""}</div>'
            f'<div class="fig">{body}</div><footer>{foot}</footer></section>')


def build():
    p1 = page("1", "말리 동화 · 제작 파이프라인", "한 편이 만들어지는 순서",
              pipeline_svg(),
              '<span><i class="g"></i>사람 확인(승인 게이트)</span><span><i class="d"></i>자동 판단</span>'
              '<span><i class="p"></i>크레딧이 드는 단계</span><span><i class="f"></i>무료(로컬)</span>'
              '<span><i class="s"></i>일반 단계</span>',
              "기준: CLAUDE.md 2단계 승인 게이트 · 씬 배정 규칙(움직임 7~10 그리고 중요도 85+ 장면만 영상, 편당 2개 안팎 → 크레딧 약 88% 절감). "
              "TTS·조립·썸네일은 승인 불필요. 편별 스크립트: gen_images.py → make_narration.py → compose.py "
              "(output/storybook/{편명}/). 2차 게이트 승인 전에는 이미지·영상을 생성하지 않습니다.")
    p2 = page("2", "말리 동화 제작 클래스 · 커리큘럼", "챕터 12개 · 강의 40개 흐름",
              curriculum_grid(),
              '<span><i class="g" style="transform:none"></i>사람 확인 챕터</span>'
              '<span><i class="p" style="border-radius:3px"></i>크레딧이 드는 실습 챕터</span>'
              '<span><b class="pr">실습</b> 따라 하는 강의</span><span>오른쪽 위 숫자 = 챕터 강의 시간 합계</span>',
              "기준: 수업/말리동화_커리큘럼.html (12챕터·40강, 제작 예정 버전). 강의 제목은 지면에 맞게 줄였습니다. "
              "※ 이 html 이 최신 기준입니다(2026-10-28 확정). 수업/챕터3_규칙서와_시험실행/ 등 기존 강의 자료는 이전 커리큘럼 구성입니다.")
    p3 = page("3", "영상 삽입용 슬라이드 · 강의 챕터 3 [03:30–05:00]", "7단계 흐름도: 돈이 들기 전 두 번만 확인",
              f'<div class="slide">{slide_svg()}</div>', "",
              "기준: 수업/챕터3_규칙서와_시험실행/강의대본_챕터3.md 화면 지시(7단계 가로 흐름도, 2·3단계 뒤 빨간 깃발, 4~7단계 위 동전). "
              "움직이는 장면은 '가장 비싸요' 대사에 맞춰 동전 3개. 아래쪽 12%는 자막 자리로 비워 두었습니다. "
              "영상용 1920×1080 PNG: 순서도/슬라이드_7단계_흐름도.png")
    html = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>말리 동화 순서도</title>'
            f'<style>{CSS}</style></head><body>{p1}{p2}{p3}</body></html>')
    (HERE / "말리동화_순서도.html").write_text(html, encoding="utf-8")
    slide_html = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;width:100vw;height:100vh;'
                  f'overflow:hidden;background:#fbf6ea}}svg{{display:block;width:100vw;height:100vh}}</style></head>'
                  f'<body>{slide_svg()}</body></html>')
    (HERE / "_slide.html").write_text(slide_html, encoding="utf-8")


def render():
    pdf = HERE / "말리동화_순서도.pdf"
    png = HERE / "슬라이드_7단계_흐름도.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", (HERE / "말리동화_순서도.html").as_uri()], check=True)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1920,1080",
                    f"--screenshot={png}", (HERE / "_slide.html").as_uri()], check=True)
    print("done:", pdf.name, png.name)


if __name__ == "__main__":
    build()
    render()
