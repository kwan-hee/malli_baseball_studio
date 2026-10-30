# 강의 CH2-1 — 클립 점수판 (템플릿 CH1-2. C05~C17 중 12개 = 1-2 클립 복사 재사용, 새 클립 = C20~C23) + Wan 클립 입력 준비 (scripts/hf_web_clips.py 가 읽는 형식)
# clip_prompts.json = {Cxx: 프롬프트}, images/Cxx.png = 시작 그림 복사본
# 테스트 버전 설정(고정): Wan 3.0 · 480p · 5초 · 16:9 · 소리 켬  →  hf_web_clips.py --test
#
# 배정 기준 비교 (gate2_plan.md 참조)
#   동화 규칙(docs/13): motion≥7 AND importance≥85            → C01·C02·C06·C08 = 4개
#   이전 2차 게이트(10-29 초안): 릴리 동작 장면만               → 8개
#   이번(강의 규칙): 캐릭터가 화면에 보이는 장면은 motion≥4 AND importance≥65 → 전부 클립
#     + 카드 장면은 말하는 릴리 작은 화면(C12)을 구석에 계속 재생
#   이유: 강의는 이야기 절정이 아니라 "정지 화면이 오래 머무는 시간"이 지루함을 만든다.
#         1-1 은 클립 15개를 배정했지만 실제 영상에는 0개가 들어갔고(정지 그림 + 줌),
#         클립이 있어도 처음 5초 뒤 정지 화면이라 15~25초 장면 대부분이 멈춰 있었다.
#   재생: once = 한 번 재생 후 마지막 프레임 유지 / loop = 정방향+역방향 반복으로 장면 끝까지 움직임
import json
import shutil
from pathlib import Path

BASE = Path(__file__).parent
IMG = BASE / "images"

COMMON = (
    "Keep the characters exactly as in the start image (same face, hair, outfit, fur, red bow on pink collar), "
    "same soft watercolor storybook art style, same classroom. Static camera, gentle natural motion, no camera shake. "
    "Audio: only soft natural ambient classroom sound effects for the action, NO music, NO speech, NO human voice, "
    "NO singing. No text appears."
)
TALK = {
    "lily": " Lily's lips move gently and naturally as if speaking warmly to the viewer.",
    "malli": " Malli's mouth opens and closes cheerfully as if she is chattering excitedly.",
    None: "",
}

# Cxx: (시작 그림, 동작, 말하는 캐릭터, 재생, 쓰는 장면, emotion, motion, importance)
CLIPS = {
    "C05": ("I18", "Lily turns the laptop slightly toward the viewer and points at the blank bright screen with one "
            "finger, nodding with a smile; Malli looks at the screen. Soft keyboard tapping sound.",
            "lily", "loop", "S05-01", 6, 6, 80),
    "C07": ("I16", "Lily gently pats Malli's head a few times; Malli closes her eyes happily and wags her tail. "
            "Quiet soft sounds.",
            "lily", "loop", "S07-03 S07-04", 8, 6, 80),
    "C08": ("I17", "Lily waves her hand at the viewer and Malli waves her front paw at the same time, both smiling "
            "warmly saying goodbye. Gentle ambient room tone.",
            "lily", "loop", "S07-05", 8, 8, 88),
    "C09": ("I06", "Lily, sitting on the chair, softly strokes Malli on her lap while talking to the viewer; Malli "
            "nuzzles into her hand contentedly. Quiet room tone.",
            "lily", "loop", "S01-06", 6, 5, 78),
    "C10": ("I04", "Lily talks to the viewer, lifts one index finger to make a gentle point, then lowers her hand "
            "back to her chest with a kind nod; Malli watches her. Quiet room tone.",
            "lily", "loop", "S04-05 S05-11", 6, 5, 80),
    "C11": ("I09", "Lily gives a cheerful thumbs-up with a playful wink and a small laugh; Malli wags her tail. "
            "Quiet room tone.",
            "lily", "loop", "S05-05", 7, 6, 78),
    "C12": ("J05", "Lily talks warmly to the viewer with small natural hand gestures, nodding gently and smiling. "
            "Quiet room tone.",
            "lily", "loop", "카드 장면 구석 작은 화면", 5, 4, 85),
    "C13": ("M08", "Malli bounces up and down joyfully, floppy ears flying, landing softly and jumping again. Soft "
            "light thumps.",
            "malli", "once", "S01-03", 9, 9, 75),
    "C14": ("M01", "Malli slowly tilts her head to one side, then the other side, with a puzzled curious look; her "
            "long floppy ears sway. Quiet room tone.",
            "malli", "once", "S01-05", 6, 5, 70),
    "C15": ("M06", "Malli's sparkling eyes widen in amazement, she leans forward a little and her tail starts to "
            "wag; her ears stay long and floppy. A tiny soft twinkle sound.",
            "malli", "once", "S02-02 S03-07 S06-07", 7, 5, 70),
    "C16": ("M05", "Malli wags her tail very fast and does a happy little hop in place with a big open-mouth smile. "
            "Soft light thumps.",
            "malli", "once", "S03-04 S05-07 S07-02", 8, 7, 72),
    "C17": ("M03", "Malli proudly raises one front paw higher, puffs out her chest and nods confidently. Quiet room "
            "tone.",
            "malli", "once", "S04-03 S06-02 S06-08c", 7, 6, 72),
    # ---- CH2-1 새 클립 (Mac hfmalli 로 생성) ----
    "C20": ("P01", "Lily walks a few steps into the classroom hugging the laptop against her chest and waves hello "
            "at the viewer with a bright smile; Malli trots behind her wagging her tail. Soft footsteps.",
            None, "once", "S01-01", 8, 9, 90),
    "C21": ("P02", "Malli flinches in surprise at the dark laptop screen, ears pulling back, and takes one small step "
            "back, eyes wide; the laptop screen stays plain dark with nothing on it. A tiny soft gasp-like room "
            "sound, no voice.",
            None, "once", "S04-04", 8, 7, 82),
    "C22": ("P03", "Malli tilts her head from side to side in confusion in front of the softly red-glowing laptop and "
            "covers her face with one front paw; the laptop screen shows only soft light, nothing on it. Quiet "
            "room tone.",
            None, "once", "S05-08", 7, 5, 80),
    "C23": ("P04", "Lily and Malli cheer together in front of the softly glowing laptop, Lily pumping both arms and "
            "Malli raising both front paws, tiny sparkles twinkling in the air. Soft cheerful room tone.",
            None, "loop", "S06-07", 9, 8, 88),
}


def mode(cid):
    return CLIPS[cid][3]


if __name__ == "__main__":
    prompts = {}
    for cid, (src, action, talker, *_rest) in CLIPS.items():
        shutil.copyfile(IMG / f"{src}.png", IMG / f"{cid}.png")
        prompts[cid] = f"{action}{TALK[talker]} {COMMON}"
    (BASE / "clip_prompts.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"clip_prompts.json: {len(prompts)}개, images/Cxx.png 복사 완료")
