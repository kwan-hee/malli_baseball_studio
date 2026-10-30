# 강의 CH1-3 — 클립 점수판 + 클립 입력 준비 (scripts/hf_web_clips.py 가 읽는 형식). 템플릿 = CH1-2 make_clip_inputs.py
# clip_prompts.json = {Cxx: 프롬프트} — **새 클립(C20~C25)만** 넣는다. C07~C19 는 CH1-2 와 시작 그림·동작이 같아
# CH1-2 클립을 그대로 쓴다(compose.py 가 CH1-2 clips/ 에서 찾음, 크레딧 0).
# 테스트 = hf_web_clips.py --test (Wan 3.0 · 480p · 소리 켬 고정) / 정식 = Kling 3.0 · 720p · 5초 · 소리 켬
# 배정 기준 = 강의 규칙(캐릭터가 보이는 장면 motion≥4 AND importance≥65), 계획서_v2.md
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
    # ---- CH1-3 새 클립 ----
    "C20": ("N01", "Lily walks a few steps into the classroom holding two sheets of paper against her chest and waves "
            "hello at the viewer with a bright smile; Malli wags her tail happily. Soft footsteps and paper rustle.",
            None, "once", "S01-01", 8, 9, 90),
    "C21": ("N02", "Lily dabs the paintbrush gently on the paper on the easel a few times, then turns her head to "
            "the viewer with a warm smile; Malli watches curiously. Soft brush strokes on paper.",
            "lily", "loop", "S05-03", 6, 7, 80),
    "C22": ("N03", "Lily lifts the left sheet a little higher, then the right sheet, showing them one after the other "
            "to the viewer with a warm smile; Malli looks up at the papers. Soft paper rustle.",
            "lily", "loop", "S05-08", 7, 6, 85),
    "C23": ("N04", "Lily raises the red X paddle, then the green O paddle, alternating them playfully with a "
            "cheerful smile; Malli looks from one sign to the other. Quiet room tone.",
            "lily", "loop", "S03-01", 7, 6, 82),
    "C24": ("M09", "Malli proudly waves the open sketchbook up and down with her front paws, bouncing a little with "
            "excitement, big open-mouth smile, tail wagging. Soft paper flapping.",
            "malli", "once", "S01-03 S01-04", 9, 7, 85),
    "C25": ("M10", "Malli moves the big magnifying glass slowly left and right, peering through it like a playful "
            "detective, then holds it still with a proud smile; tail wagging. Quiet room tone.",
            "malli", "once", "S04-02", 8, 7, 80),
}

NEW = ["C20", "C21", "C22", "C23", "C24", "C25"]


def mode(cid):
    return CLIPS[cid][3]


if __name__ == "__main__":
    prompts = {}
    for cid, (src, action, talker, *_rest) in CLIPS.items():
        shutil.copyfile(IMG / f"{src}.png", IMG / f"{cid}.png")
        if cid in NEW:  # CH1-2 재사용 클립은 맥에서 다시 만들지 않음
            prompts[cid] = f"{action}{TALK[talker]} {COMMON}"
    (BASE / "clip_prompts.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"clip_prompts.json: {len(prompts)}개, images/Cxx.png 복사 완료")
