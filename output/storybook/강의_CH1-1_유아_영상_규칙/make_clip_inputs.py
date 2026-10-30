# 강의 CH1-1 — Kling 3.0 클립 입력 준비 (scripts/hf_web_clips.py 가 읽는 형식)
# clip_prompts.json = {Kxx: 프롬프트}, images/Kxx.png = 콘티의 시작 이미지(Ixx) 복사본
# 2차 게이트 A안 15개 (2026-10-29 승인). 설정: 480p · 5초 · 16:9 · 소리 켬(현장음만, 목소리는 Gemini TTS)
import json
import shutil
from pathlib import Path

from storyboard import SCENES

BASE = Path(__file__).parent
IMG = BASE / "images"

COMMON = (
    "Keep both characters exactly as in the start image (same face, hair, outfit, fur, red bow on pink collar), "
    "same soft watercolor storybook art style, same classroom. Static camera, gentle natural motion, no camera shake. "
    "Audio: only soft natural ambient classroom sound effects for the action, NO music, NO speech, NO human voice, "
    "NO singing. No text appears."
)
TALK = " Lily's lips move gently and naturally as if speaking softly to the viewer."

# Kxx: (동작, 릴리가 말하는 장면인가)
ACTIONS = {
    "K01": ("Lily opens the door wider, steps into the classroom and waves hello at the viewer with a bright smile; "
            "Malli wags her tail happily. Sound of a wooden door opening and soft footsteps.", False),
    "K02": ("Malli hops up onto the teacher's desk in one light cute jump, sits down and wags her tail; Lily laughs "
            "softly beside the desk. Sound of a small soft landing thump.", False),
    "K03": ("Lily walks two steps toward the blank chalkboard, turns back to the viewer and gestures at the board "
            "with an open palm, smiling. Soft footsteps.", True),
    "K04": ("Lily, kneeling, slowly opens the picture book and turns it toward the viewer, smiling gently; Malli "
            "looks at the book. Soft page-turning sound.", True),
    "K05": ("Lily turns the wooden hourglass upside down and sets it on the desk, sand starts to flow, she smiles at "
            "the viewer; Malli watches the sand. A soft wooden tap on the desk.", True),
    "K06": ("Lily draws a few loose wavy chalk lines on the board (not readable letters), then turns her head back "
            "to the viewer with a smile. Soft chalk scratching sound.", True),
    "K07": ("Lily takes one shiny red apple out of the basket and holds it up next to her face, smiling; Malli's "
            "eyes follow the apple. Soft rustle of the wicker basket.", True),
    "K08": ("Lily opens her pressed-together hands wide in a cheerful little magic gesture, tiny gentle sparkles "
            "appear around her hands; Malli looks up amazed. A soft twinkling sound.", True),
    "K09": ("Lily gently picks up the startled Malli in both arms, hugs her close and pats her back softly; Malli "
            "relaxes and smiles. Soft rustle of clothes.", True),
    "K10": ("Lily playfully raises the left round sign, then the right round sign, alternating, with a teasing "
            "quiz smile; Malli tilts her head thinking. Soft swish sounds.", True),
    "K11": ("Malli taps her front paw against Lily's open palm in a high-five, both burst into happy smiles, Malli "
            "wags her tail. A soft light clap sound.", False),
    "K12": ("Lily writes a few lines in the notebook with the pen, then looks up at the viewer and smiles; Malli "
            "peeks at the notebook. Soft pen scribbling sound.", True),
    "K13": ("Lily gently pats Malli's head a few times; Malli closes her eyes happily and wags her tail. Quiet "
            "soft sounds.", True),
    "K14": ("Lily waves her hand at the viewer and Malli waves her front paw at the same time, both smiling "
            "warmly saying goodbye. Gentle ambient room tone.", True),
    "K15": ("Lily turns the laptop slightly toward the viewer and points at the blank bright screen with one "
            "finger, nodding with a smile; Malli looks at the screen. Soft keyboard tapping sound.", True),
}

if __name__ == "__main__":
    prompts = {}
    for s in SCENES:
        if not s["clip"]:
            continue
        kid, src = s["clip"], IMG / f"{s['clip_img']}.png"
        action, talk = ACTIONS[kid]
        prompts[kid] = f"{action}{TALK if talk else ''} {COMMON}"
        if src.exists():
            shutil.copyfile(src, IMG / f"{kid}.png")
        else:
            print(f"{kid}: start image {src.name} missing")
    (BASE / "clip_prompts.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"clip_prompts.json: {len(prompts)} clips")
