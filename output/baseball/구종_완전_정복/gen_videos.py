# Higgsfield MCP 비디오 생성: s01(5종 구종 FAST) + s08(KBO 선수들 QUALITY)
# 기존 작동 방식: 이미지 → image-to-video (seedance-2.0-mini)
import os
import sys
from pathlib import Path
import logging

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

# youtube_longform_agent에서 HiggsFieldClient 가져오기
sys.path.insert(0, next(str(_p / "youtube_longform_agent") for _p in __import__("pathlib").Path(__file__).resolve().parents if (_p / "youtube_longform_agent").is_dir()))

# .env 로드
from src.quote_video import config  # noqa: F401
from src.quote_video.higgsfield_client import HiggsFieldClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
CLIPS_DIR = BASE / "clips"
IMAGES_DIR = BASE / "images"
CLIPS_DIR.mkdir(exist_ok=True)

# Higgsfield 클라이언트 초기화
client = HiggsFieldClient()

# 생성 프롬프트 (모델: seedance-2.0-mini 이미지→영상)
SCENES = {
    "s01": {
        "image": IMAGES_DIR / "s01.png",
        "prompt": (
            "5개의 서로 다른 야구 투구 종류를 보여주는 동적인 애니메이션. "
            "포심 직구(빠르고 곧은), 투심(옆으로 휘며 가라앉음), 슬라이더(급격한 횡 미끄럼), "
            "커브(위에서 아래로 뚝 떨어짐), 체인지업(느린 속도)을 각각 1초씩 순차적으로 보여줍니다. "
            "야구장 배경, 투수 관점의 공 궤적, 카툰 스타일 야구 해설 영상."
        ),
        "duration": 8,
    },
    "s08": {
        "image": IMAGES_DIR / "s08.png",
        "prompt": (
            "야구 선수들의 피칭 폼과 스트라이크 하이라이트 장면. "
            "다양한 타입의 투수들: 체인지업 마스터의 느린 폼, 고속 슬라이더의 날카로운 회전, "
            "커브의 큰 낙차, 포크볼의 급강하. 각 투수마다 다른 피칭 스타일, "
            "카툰 스타일 야구 영상, 역동적인 편집, 강렬한 순간들."
        ),
        "duration": 8,
    },
}

def generate_video(scene_id):
    """
    씬별 이미지→영상 생성.
    이미 생성되었으면 skip.
    """
    out_path = CLIPS_DIR / f"{scene_id}_seedance_1080p.mp4"
    
    if out_path.exists() and out_path.stat().st_size > 100000:
        logger.info(f"{scene_id}: cached ({out_path.stat().st_size:,} bytes)")
        return True
    
    scene_info = SCENES[scene_id]
    img_path = scene_info["image"]
    
    if not img_path.exists():
        logger.error(f"{scene_id}: 이미지 없음 — {img_path}")
        return False
    
    logger.info(f"{scene_id}: generating {scene_info['duration']}s video from image...")
    
    try:
        # image-to-video 방식 (증명된 작동 방식)
        client.image_to_video(
            image_path=img_path,
            prompt=scene_info["prompt"],
            output_path=out_path,
            model="seedance-2.0-mini",
            aspect_ratio="16:9",
            duration=scene_info["duration"],
            fallback_pan_zoom=True,  # 실패 시 FFmpeg Ken Burns로 대체
        )
        logger.info(f"{scene_id}: ✅ 완료 ({out_path.stat().st_size:,} bytes)")
        return True
    except Exception as e:
        logger.error(f"{scene_id}: ❌ 실패 — {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("구종_완전_정복 — Higgsfield MCP 비디오 생성 (Image→Video)")
    print("=" * 70)
    print()
    
    results = {}
    for scene_id in ["s01", "s08"]:
        results[scene_id] = generate_video(scene_id)
    
    print()
    print("=" * 70)
    if all(results.values()):
        print("✅ 모든 비디오 생성 완료!")
        print("다음 단계: python compose.py → 최종 MP4 생성")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"❌ 생성 실패: {', '.join(failed)}")
        print("※ 실패 시 Ken Burns (FFmpeg zoom) 로 폴백됨")
    print("=" * 70)
