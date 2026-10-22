# 강의 소개 영상 — 자막 큐 (대사 원문 그대로, 장면 wav 의 발화 구간 안에서 문장별 글자수 비례)
# 맥 Homebrew ffmpeg 에 libass(subtitles 필터)가 없어 render.py 가 직접 굽는다. subs.srt 도 함께 저장(참고용).
import wave
from pathlib import Path

import numpy as np

from timeline import TIMELINE

BASE = Path(__file__).parent


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def ts(sec):
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_sentences(text):
    parts, cur = [], ""
    for i, ch in enumerate(text):
        cur += ch
        nxt = text[i + 1] if i + 1 < len(text) else " "
        if ch in ".?!" and nxt in " \"”":
            parts.append(cur.strip())
            cur = ""
    if cur.strip():
        parts.append(cur.strip())
    out = []
    for p in parts:
        if out and p in ('"', "”"):
            out[-1] += p
        else:
            out.append(p)
    return out


def speech_span(wav_path):
    """장면 wav 안의 실제 발화 시작·끝 (앞뒤 무음 제외)."""
    x, sr = read_wav(wav_path)
    fr = int(0.02 * sr)
    e = np.sqrt(np.mean(x[: len(x) // fr * fr].reshape(-1, fr) ** 2, axis=1))
    on = np.where(e > 10 ** (-40 / 20))[0]
    if len(on) == 0:
        return 0.0, len(x) / sr
    return on[0] * 0.02, (on[-1] + 1) * 0.02


EMPHASIS = {"S01-08": "충분해요!"}  # 콘티: 자막에서 "충분해요!" 강조


def build():
    cues = []
    for s in TIMELINE:
        if not s["wav"]:
            continue
        a, b = speech_span(s["wav"])
        sents = split_sentences(s["line"])
        total = sum(len(x) for x in sents)
        cur = s["start"] + a
        for sent in sents:
            dur = (b - a) * len(sent) / total
            cues.append({"start": cur, "end": cur + dur, "text": sent, "emph": EMPHASIS.get(s["id"])})
            cur += dur
    return cues


CUES = build()

if __name__ == "__main__":
    srt = [f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n" for i, c in enumerate(CUES, 1)]
    (BASE / "subs.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"SRT: {len(CUES)} cues")
