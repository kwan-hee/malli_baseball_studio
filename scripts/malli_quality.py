# 말리 동화 선별 고품질 정책 — 프리셋 로드·결정적 씬 랭킹·이미지 승인 게이트·재시도·크레딧 예비 계산 순수 헬퍼
# 부작용 없음: 네트워크·MCP·생성 API 호출 금지, 자격증명 접근 금지, 에피소드 파일 수정 금지.
import json
from pathlib import Path

PRESET_PATH = Path(__file__).resolve().parent.parent / "presets" / "approved" / "malli_video.json"

# 유료 영상 적격 문턱 — 기존 배정 규칙(AGENTS.md 2차 게이트, docs/04)과 동일 값
MIN_MOTION = 7
MIN_IMPORTANCE = 85

# 이미지 승인 게이트 — 전부 True 여야 유료 영상 발주 가능
APPROVAL_KEYS = (
    "image_exists",
    "validation_passed",
    "identity_approved",
    "clothing_colors_approved",
    "hands_face_ok",
    "composition_approved",
    "paid_eligible",
)

# 프로바이더가 파라미터로 지원하지 않는 개념 — 프롬프트 문구로만 표현해야 함
FORBIDDEN_PROVIDER_PARAMS = frozenset({
    "negative_prompt",
    "motion_strength",
    "camera_movement",
    "quality_level",
    "character_consistency",
    "seed",
})

BALANCE_SOURCES = ("provider", "local_estimate")

LOG_PREFIX = "[Malli Quality]"


class PresetError(ValueError):
    """프리셋 파일이 없거나, JSON 이 깨졌거나, 필수 정책 필드가 잘못된 경우."""


# ---------------------------------------------------------------------------
# 프리셋 로드·검증
# ---------------------------------------------------------------------------

def load_preset(path=PRESET_PATH):
    """승인 프리셋 JSON 을 읽어 검증 후 dict 반환. 실패 시 PresetError."""
    p = Path(path)
    if not p.exists():
        raise PresetError(f"preset file not found: {p.name}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PresetError(f"preset is not valid JSON: {e}") from e
    validate_preset(data)
    return data


def validate_preset(data):
    """프리셋 dict 구조 검증. 통과 시 None, 실패 시 PresetError."""
    if not isinstance(data, dict):
        raise PresetError("preset must be a JSON object")
    if not isinstance(data.get("preset"), str) or not data["preset"]:
        raise PresetError("'preset' must be a non-empty string")
    if not isinstance(data.get("version"), int) or isinstance(data.get("version"), bool):
        raise PresetError("'version' must be an integer")
    if data.get("approved") is not True:
        raise PresetError("preset is not approved (approved must be true)")

    for section in ("higgsfield_rest", "higgsfield_mcp"):
        sec = data.get(section, {})
        if not isinstance(sec, dict):
            raise PresetError(f"'{section}' must be an object")
        bad = FORBIDDEN_PROVIDER_PARAMS.intersection(sec)
        if bad:
            raise PresetError(
                f"'{section}' contains unsupported provider params: {sorted(bad)} "
                "(express these in prompt text instead)"
            )

    qp = data.get("quality_policy")
    if not isinstance(qp, dict):
        raise PresetError("'quality_policy' must be an object")

    def _int(key, lo, hi):
        v = qp.get(key)
        if not isinstance(v, int) or isinstance(v, bool) or not (lo <= v <= hi):
            raise PresetError(f"quality_policy.{key} must be an integer in [{lo}, {hi}]")
        return v

    maximum = _int("maximum_paid_video_scenes", 1, 10)
    recommended = _int("recommended_paid_video_scenes", 1, 10)
    _int("retry_limit_per_scene", 0, 3)
    _int("reserve_credit_percent", 1, 99)
    if recommended > maximum:
        raise PresetError("recommended_paid_video_scenes must not exceed maximum_paid_video_scenes")
    if qp.get("fallback_after_retry") != "image_motion":
        raise PresetError("quality_policy.fallback_after_retry must be 'image_motion'")
    for key in ("require_image_approval", "reuse_completed_assets"):
        if not isinstance(qp.get(key), bool):
            raise PresetError(f"quality_policy.{key} must be a boolean")


# ---------------------------------------------------------------------------
# 결정적 씬 랭킹·선택
# ---------------------------------------------------------------------------

def _score(scores, sid, key):
    v = scores[sid].get(key)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"scene {sid}: score '{key}' must be a number")
    return v


def rank_scenes(scores):
    """씬 점수 dict -> 결정적 순위 리스트.

    scores: {scene_id: {"importance": n, "motion": n, "emotion": n}}
    정렬: importance 내림차순 -> motion 내림차순 -> emotion 내림차순 -> scene_id 오름차순.
    같은 입력이면 dict 삽입 순서와 무관하게 항상 같은 출력 (resume 재현성 보장).
    """
    def key(sid):
        return (
            -_score(scores, sid, "importance"),
            -_score(scores, sid, "motion"),
            -_score(scores, sid, "emotion"),
            sid,
        )
    return sorted(scores, key=key)


def eligible_scenes(scores):
    """유료 영상 적격 씬 (motion >= 7 그리고 importance >= 85), 순위 순."""
    return [
        sid for sid in rank_scenes(scores)
        if _score(scores, sid, "motion") >= MIN_MOTION
        and _score(scores, sid, "importance") >= MIN_IMPORTANCE
    ]


def select_paid_scenes(scores, policy, count=None):
    """유료 영상 씬 선택. 기본 = 권장 개수(3), 상한 = 최대 개수(4) 강제.

    count 를 더 크게 요구해도 maximum_paid_video_scenes 로 잘린다.
    """
    maximum = policy["maximum_paid_video_scenes"]
    wanted = policy["recommended_paid_video_scenes"] if count is None else count
    wanted = max(0, min(wanted, maximum))
    return eligible_scenes(scores)[:wanted]


def route_scene(scene_id, selected_paid):
    """선택된 씬 -> 'paid_video', 나머지 전부 -> 'image_motion' (FFmpeg Ken Burns)."""
    return "paid_video" if scene_id in selected_paid else "image_motion"


# ---------------------------------------------------------------------------
# 이미지 승인 게이트
# ---------------------------------------------------------------------------

def check_image_approval(record):
    """승인 레코드 검사 -> (통과 여부, 미충족 항목 리스트).

    APPROVAL_KEYS 전 항목이 정확히 True 여야 통과. 누락·False·비불리언 = 미충족.
    미통과 씬은 유료 영상 발주 금지 — 이미지 모션 사용 또는 수동 검토.
    """
    missing = [k for k in APPROVAL_KEYS if record.get(k) is not True]
    return (not missing, missing)


# ---------------------------------------------------------------------------
# 재시도·폴백 결정
# ---------------------------------------------------------------------------

def next_step_after_failure(failed_attempts, policy):
    """유료 생성 실패 후 다음 행동. 1회 실패 -> 'retry', 그 이상 -> 'image_motion'."""
    if not isinstance(failed_attempts, int) or isinstance(failed_attempts, bool) or failed_attempts < 1:
        raise ValueError("failed_attempts must be an integer >= 1")
    if failed_attempts <= policy["retry_limit_per_scene"]:
        return "retry"
    return policy["fallback_after_retry"]


def should_skip_generation(asset_complete):
    """완성 산출물 존재 -> 재생성 금지 (resume 시 재사용)."""
    return bool(asset_complete)


# ---------------------------------------------------------------------------
# 크레딧 예비 정책
# ---------------------------------------------------------------------------

def reserve_report(balance, policy, source="provider"):
    """예비 크레딧 계산. source 로 provider 실측 잔액 vs 로컬 추정을 구분해 기록.

    가격(씬당 크레딧 단가)은 변동 가능하므로 여기 하드코딩하지 않는다.
    """
    if source not in BALANCE_SOURCES:
        raise ValueError(f"source must be one of {BALANCE_SOURCES}")
    if isinstance(balance, bool) or not isinstance(balance, (int, float)) or balance < 0:
        raise ValueError("balance must be a non-negative number")
    pct = policy["reserve_credit_percent"]
    floor = balance * pct / 100.0
    return {
        "source": source,
        "balance": float(balance),
        "reserve_percent": pct,
        "reserve_floor": floor,
        "usable": max(0.0, float(balance) - floor),
    }


# ---------------------------------------------------------------------------
# 안전 로그 (자격증명·계정 식별자 절대 미포함)
# ---------------------------------------------------------------------------

def quality_summary_lines(preset, selected=None):
    """정책 요약 로그 라인. 프리셋 이름·버전·정책 숫자·씬 ID 만 사용 — 비밀값 유입 경로 없음."""
    qp = preset["quality_policy"]
    lines = [
        f"{LOG_PREFIX} Approved preset loaded: {preset['preset']} v{preset['version']}",
        f"{LOG_PREFIX} Paid-scene limit: {qp['maximum_paid_video_scenes']}",
        f"{LOG_PREFIX} Recommended paid scenes: {qp['recommended_paid_video_scenes']}",
        f"{LOG_PREFIX} Retry limit: {qp['retry_limit_per_scene']}",
        f"{LOG_PREFIX} Reserve target: {qp['reserve_credit_percent']}%",
    ]
    if selected is not None:
        shown = ", ".join(selected) if selected else "(none)"
        lines.append(f"{LOG_PREFIX} Selected scenes: {shown}")
    lines.append(f"{LOG_PREFIX} Remaining scenes use FFmpeg image motion")
    return lines
