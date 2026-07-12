# malli_quality 순수 헬퍼 단위 테스트 — 전부 오프라인, mock 데이터만, 유료·네트워크 호출 0회
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import malli_quality as mq

# 8씬 mock 점수판 — s02/s04/s05/s06/s08/s09 적격(motion>=7, importance>=85), s01/s10 부적격
SCORES = {
    "s01": {"importance": 60, "motion": 2, "emotion": 5},   # 오프닝 풍경 — 부적격
    "s02": {"importance": 88, "motion": 7, "emotion": 6},
    "s04": {"importance": 90, "motion": 8, "emotion": 7},
    "s05": {"importance": 85, "motion": 7, "emotion": 5},
    "s06": {"importance": 92, "motion": 9, "emotion": 8},
    "s08": {"importance": 97, "motion": 10, "emotion": 9},  # 절정
    "s09": {"importance": 95, "motion": 9, "emotion": 9},
    "s10": {"importance": 70, "motion": 3, "emotion": 6},   # 마무리 인사 — 부적격
}

APPROVED = {k: True for k in mq.APPROVAL_KEYS}


def policy():
    return {
        "maximum_paid_video_scenes": 4,
        "recommended_paid_video_scenes": 3,
        "retry_limit_per_scene": 1,
        "fallback_after_retry": "image_motion",
        "reserve_credit_percent": 20,
        "require_image_approval": True,
        "reuse_completed_assets": True,
    }


class TestSceneSelection(unittest.TestCase):
    def test_maximum_four_paid_scenes(self):
        # 적격 6씬에서 8개를 요구해도 상한 4로 잘린다
        sel = mq.select_paid_scenes(SCORES, policy(), count=8)
        self.assertEqual(len(sel), 4)

    def test_recommended_three_by_default(self):
        sel = mq.select_paid_scenes(SCORES, policy())
        self.assertEqual(sel, ["s08", "s09", "s06"])

    def test_fewer_eligible_than_recommended(self):
        scores = {"s01": SCORES["s01"], "s08": SCORES["s08"], "s10": SCORES["s10"]}
        self.assertEqual(mq.select_paid_scenes(scores, policy()), ["s08"])

    def test_deterministic_ranking_regardless_of_input_order(self):
        reversed_scores = dict(reversed(list(SCORES.items())))
        self.assertEqual(mq.rank_scenes(SCORES), mq.rank_scenes(reversed_scores))
        self.assertEqual(
            mq.select_paid_scenes(SCORES, policy()),
            mq.select_paid_scenes(reversed_scores, policy()),
        )

    def test_stable_tie_break_by_scene_id(self):
        tied = {
            "s07": {"importance": 90, "motion": 8, "emotion": 8},
            "s03": {"importance": 90, "motion": 8, "emotion": 8},
            "s05": {"importance": 90, "motion": 8, "emotion": 8},
        }
        self.assertEqual(mq.rank_scenes(tied), ["s03", "s05", "s07"])

    def test_non_selected_scene_routes_to_image_motion(self):
        sel = mq.select_paid_scenes(SCORES, policy())
        self.assertEqual(mq.route_scene("s01", sel), "image_motion")
        self.assertEqual(mq.route_scene("s02", sel), "image_motion")
        self.assertEqual(mq.route_scene("s08", sel), "paid_video")

    def test_ineligible_scene_never_selected(self):
        sel = mq.select_paid_scenes(SCORES, policy(), count=8)
        self.assertNotIn("s01", sel)
        self.assertNotIn("s10", sel)


class TestImageApprovalGate(unittest.TestCase):
    def test_unapproved_image_rejected(self):
        record = dict(APPROVED, identity_approved=False)
        ok, missing = mq.check_image_approval(record)
        self.assertFalse(ok)
        self.assertEqual(missing, ["identity_approved"])

    def test_missing_key_rejected(self):
        record = dict(APPROVED)
        del record["hands_face_ok"]
        ok, missing = mq.check_image_approval(record)
        self.assertFalse(ok)
        self.assertEqual(missing, ["hands_face_ok"])

    def test_approved_image_accepted(self):
        ok, missing = mq.check_image_approval(dict(APPROVED))
        self.assertTrue(ok)
        self.assertEqual(missing, [])


class TestRetryAndFallback(unittest.TestCase):
    def test_retry_allowed_only_once(self):
        self.assertEqual(mq.next_step_after_failure(1, policy()), "retry")

    def test_second_failure_falls_back_to_image_motion(self):
        self.assertEqual(mq.next_step_after_failure(2, policy()), "image_motion")
        self.assertEqual(mq.next_step_after_failure(3, policy()), "image_motion")

    def test_completed_asset_is_reused(self):
        self.assertTrue(mq.should_skip_generation(True))
        self.assertFalse(mq.should_skip_generation(False))


class TestReservePolicy(unittest.TestCase):
    def test_reserve_reports_twenty_percent(self):
        rep = mq.reserve_report(1000, policy(), source="provider")
        self.assertEqual(rep["reserve_percent"], 20)
        self.assertEqual(rep["reserve_floor"], 200.0)
        self.assertEqual(rep["usable"], 800.0)
        self.assertEqual(rep["source"], "provider")

    def test_local_estimate_source_is_distinguished(self):
        rep = mq.reserve_report(500, policy(), source="local_estimate")
        self.assertEqual(rep["source"], "local_estimate")
        with self.assertRaises(ValueError):
            mq.reserve_report(500, policy(), source="guess")


class TestPresetFile(unittest.TestCase):
    def test_real_preset_loads_and_matches_spec(self):
        preset = mq.load_preset()
        self.assertTrue(preset["approved"])
        qp = preset["quality_policy"]
        self.assertEqual(qp["maximum_paid_video_scenes"], 4)
        self.assertEqual(qp["recommended_paid_video_scenes"], 3)
        self.assertEqual(qp["retry_limit_per_scene"], 1)
        self.assertEqual(qp["fallback_after_retry"], "image_motion")
        self.assertEqual(qp["reserve_credit_percent"], 20)
        self.assertTrue(qp["require_image_approval"])
        self.assertTrue(qp["reuse_completed_assets"])

    def test_real_preset_has_no_unsupported_provider_params(self):
        preset = mq.load_preset()
        for section in ("higgsfield_rest", "higgsfield_mcp"):
            bad = mq.FORBIDDEN_PROVIDER_PARAMS.intersection(preset[section])
            self.assertEqual(bad, set())

    def test_malformed_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "broken.json"
            p.write_text("{not json", encoding="utf-8")
            with self.assertRaises(mq.PresetError):
                mq.load_preset(p)

    def test_missing_file_rejected(self):
        with self.assertRaises(mq.PresetError):
            mq.load_preset(Path("no_such_dir") / "no_such_preset.json")

    def test_unapproved_or_broken_policy_rejected(self):
        good = mq.load_preset()
        cases = [
            dict(good, approved=False),
            dict(good, quality_policy=dict(good["quality_policy"], recommended_paid_video_scenes=9)),
            dict(good, quality_policy=dict(good["quality_policy"], fallback_after_retry="retry_forever")),
            dict(good, higgsfield_mcp=dict(good["higgsfield_mcp"], negative_prompt="blurry")),
        ]
        for bad in cases:
            with self.assertRaises(mq.PresetError):
                mq.validate_preset(bad)


class TestSafeLogging(unittest.TestCase):
    FORBIDDEN_SUBSTRINGS = (
        "AIza", "sk-", "AQ.", "Bearer", "Authorization",
        "api_key", "apikey", "secret", "token", "password",
        "HF_API", "@gmail", "@", "cookie",
    )

    def test_no_credentials_or_account_ids_in_logs(self):
        preset = mq.load_preset()
        sel = mq.select_paid_scenes(SCORES, preset["quality_policy"])
        lines = mq.quality_summary_lines(preset, selected=sel)
        for line in lines:
            self.assertTrue(line.startswith("[Malli Quality]"), line)
            low = line.lower()
            for bad in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(bad.lower(), low, f"forbidden substring '{bad}' in log: {line}")

    def test_summary_reports_policy_numbers(self):
        preset = mq.load_preset()
        lines = mq.quality_summary_lines(preset, selected=["s08", "s09", "s06"])
        joined = "\n".join(lines)
        self.assertIn("Paid-scene limit: 4", joined)
        self.assertIn("Recommended paid scenes: 3", joined)
        self.assertIn("Retry limit: 1", joined)
        self.assertIn("Reserve target: 20%", joined)
        self.assertIn("Selected scenes: s08, s09, s06", joined)
        self.assertIn("Remaining scenes use FFmpeg image motion", joined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
