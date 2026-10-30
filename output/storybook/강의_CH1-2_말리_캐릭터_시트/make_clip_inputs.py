# 강의 CH1-2 — 클립 점수판 + Wan 클립 입력 준비 (scripts/hf_web_clips.py 가 읽는 형식)
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
    "C01": ("J01", "Lily walks a few steps into the classroom holding the rolled-up paper under one arm and waves "
            "hello at the viewer with a bright smile; Malli wags her tail happily. Soft footsteps and paper rustle.",
            None, "once", "S01-01", 8, 9, 90),
    "C02": ("J02", "Lily smooths the large sheet of paper flat on the chalkboard with both hands, pressing the "
            "corners, then glances back at the viewer with a smile. Soft paper rustling.",
            "lily", "loop", "S02-01", 7, 8, 88),
    "C03": ("J03", "Lily slowly moves the magnifying glass across the paper on the board, peering through it, then "
            "looks at the viewer with a playful smile; Malli tilts her head. Quiet room tone.",
            "lily", "loop", "S03-01", 7, 7, 82),
    "C04": ("I15", "Lily writes a few lines in the notebook with the pen, then looks up at the viewer and smiles; "
            "Malli peeks at the notebook. Soft pen scribbling sound.",
            "lily", "loop", "S04-01", 5, 5, 75),
    "C05": ("I18", "Lily turns the laptop slightly toward the viewer and points at the blank bright screen with one "
            "finger, nodding with a smile; Malli looks at the screen. Soft keyboard tapping sound.",
            "lily", "loop", "S05-01", 6, 6, 80),
    "C06": ("J04", "Lily moves the small paper drawing back and forth next to Malli's face, looking from the "
            "drawing to Malli and back with a delighted smile; Malli sits still and proud. Soft paper rustle.",
            "lily", "loop", "S06-09", 8, 7, 88),
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
    "C18": ("M02", "Malli peeks out from under the small blanket, still covering her floppy ears with her front "
            "paws, then blinks with surprise. Soft fabric rustle.",
            "malli", "once", "S04-07", 6, 5, 68),
    "C19": ("M04", "Malli rolls a little on the desk with a playful mischievous grin, wiggling her paws. Soft fabric "
            "rustle.",
            "malli", "once", "S05-04", 6, 4, 65),
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
