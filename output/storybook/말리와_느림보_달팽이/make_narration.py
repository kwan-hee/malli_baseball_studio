# 말리와 느림보 달팽이 — edge-tts로 씬별 나레이션 생성 (SunHiNeural -5%)
import asyncio
from pathlib import Path

import edge_tts

BASE = Path(__file__).parent
OUT = BASE / "audio"
OUT.mkdir(exist_ok=True)

VOICE = "ko-KR-SunHiNeural"
RATE = "-5%"

SCENES = {
    "s01": "안녕, 친구들! 나는 말리야, 멍멍! 오늘은 꽃밭으로 소풍 가는 날이에요. 우와, 생각만 해도 신난다!",
    "s02": "말리는 신나서 달렸어요. 폴짝폴짝! 꼬리가 살랑살랑. 꽃밭아, 기다려! 내가 제일 먼저 갈 거야!",
    "s03": "그때, 길 위에 작은 달팽이가 있었어요. 안녕? 나는 토토야. 토토는 아주아주 느렸어요. 엉금엉금, 엉금엉금.",
    "s04": "토토야, 너무 느려! 말리는 답답했어요. 나 먼저 갈게! 말리는 혼자 폴짝폴짝 뛰어갔어요.",
    "s05": "그런데 이런! 길이 두 갈래로 갈라져 있었어요. 어느 쪽이지? 여기가 어디지? 말리는 그만 길을 잃고 말았어요. 눈물이 핑 돌았어요.",
    "s06": "그때, 토토가 엉금엉금 다가왔어요. 울지 마, 말리야. 나는 길을 다 기억해. 빨간 꽃 옆을 지나서, 둥근 돌 옆으로! 토토는 천천히 왔기 때문에, 다 보았던 거예요.",
    "s07": "말리는 토토 옆에서 천천히 걸었어요. 천천히, 천천히, 하나씩 보면서! 반짝반짝 이슬도 보였어요. 팔랑팔랑 노란 나비도 보였어요.",
    "s08": "우와! 도착했다! 알록달록 꽃들이 활짝 피어 있었어요. 말리와 토토는 함께 웃었어요.",
    "s09": "말리는 알았어요. 빠른 것만 좋은 게 아니라는 걸요. 천천히 가면, 예쁜 것들이 더 많이 보인다는 걸요.",
    "s10": "오늘 이야기 어땠어요? 우리도 같이 외쳐볼까요? 천천히, 천천히, 하나씩 보면서! 다음에 또 만나요. 안녕!",
}


async def main():
    for sid, text in SCENES.items():
        out = OUT / f"{sid}.mp3"
        if out.exists() and out.stat().st_size > 1000:
            print(f"{sid}: cached")
            continue
        tts = edge_tts.Communicate(text, VOICE, rate=RATE)
        await tts.save(str(out))
        print(f"{sid}: {out.stat().st_size:,} bytes")
    print("TTS DONE")


asyncio.run(main())
