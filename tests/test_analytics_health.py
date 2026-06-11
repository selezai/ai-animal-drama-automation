from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from modules.analytics_health import (
    fallback_run_result,
    issue_body,
    load_health,
    load_latest_run,
    save_health,
    save_latest_run,
    update_health_state,
)


class AnalyticsHealthTests(unittest.TestCase):
    def test_first_partial_error_increments_streak_without_notification(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)

        health = update_health_state(
            {"status": "partial", "errors": ["facebook metrics failed"]},
            workflow_outcome="success",
            now=now,
        )

        self.assertTrue(health["last_problem"])
        self.assertEqual(health["consecutive_problem_runs"], 1)
        self.assertFalse(health["notification_required"])
        self.assertFalse(health["recovered"])

    def test_second_problem_run_requires_notification(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
        previous = {
            "last_problem": True,
            "consecutive_problem_runs": 1,
        }

        health = update_health_state(
            {"status": "workflow_failure", "errors": ["analytics workflow step ended with outcome: failure"]},
            workflow_outcome="failure",
            previous=previous,
            now=now,
        )

        self.assertEqual(health["consecutive_problem_runs"], 2)
        self.assertTrue(health["notification_required"])
        self.assertIn("analytics workflow step", health["problem_summary"])

    def test_clean_success_resets_streak_and_marks_recovery(self) -> None:
        previous = {
            "last_problem": True,
            "consecutive_problem_runs": 3,
        }

        health = update_health_state(
            {"status": "success", "errors": []},
            workflow_outcome="success",
            previous=previous,
            now=datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc),
        )

        self.assertFalse(health["last_problem"])
        self.assertEqual(health["consecutive_problem_runs"], 0)
        self.assertFalse(health["notification_required"])
        self.assertTrue(health["recovered"])

    def test_missing_latest_run_is_problem_even_when_step_succeeded(self) -> None:
        result = fallback_run_result("success")
        health = update_health_state(result, workflow_outcome="success")

        self.assertEqual(result["status"], "missing_latest_run")
        self.assertTrue(health["last_problem"])

    def test_state_files_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_path = tmp_path / "latest_run.json"
            health_path = tmp_path / "health.json"
            save_latest_run({"status": "success"}, run_path)
            save_health({"last_status": "success"}, health_path)

            self.assertEqual(load_latest_run(run_path), {"status": "success"})
            self.assertEqual(load_health(health_path), {"last_status": "success"})
            self.assertEqual(json.loads(run_path.read_text()), {"status": "success"})

    def test_issue_body_contains_run_context_and_errors(self) -> None:
        body = issue_body(
            {
                "last_status": "partial",
                "consecutive_problem_runs": 2,
                "last_checked_at": "2026-06-11T12:00:00+00:00",
            },
            {
                "posts_seen": 3,
                "snapshots_added": 0,
                "errors": ["fb failed", "ig failed"],
            },
        )

        self.assertIn("Consecutive problem runs", body)
        self.assertIn("fb failed", body)
        self.assertIn("ig failed", body)


if __name__ == "__main__":
    unittest.main()
