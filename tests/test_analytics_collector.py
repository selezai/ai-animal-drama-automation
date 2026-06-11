from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from modules.analytics_collector import run_analytics_collection


class AnalyticsCollectorTests(unittest.TestCase):
    def test_collector_updates_existing_posts_without_duplicate_snapshots(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            final_dir = tmp_path / "final"
            final_dir.mkdir()
            metrics_path = tmp_path / "post_metrics.json"
            scores_path = tmp_path / "content_scores.json"
            latest_run_path = tmp_path / "latest_run.json"
            (final_dir / "post_1.json").write_text(json.dumps({
                "status": "success",
                "run_id": "20260610_100000",
                "posted_at": (now - timedelta(hours=26)).isoformat(),
                "video_id": "fb-1",
                "ig_media_id": "ig-1",
                "pet_type": "dog",
                "pillar": "safety",
                "topic_key": "dog:safety:xylitol",
            }))

            fb_calls = []
            ig_calls = []
            first = run_analytics_collection(
                now=now,
                final_dir=final_dir,
                post_metrics_path=metrics_path,
                content_scores_path=scores_path,
                latest_run_path=latest_run_path,
                facebook_fetcher=lambda media_id: fb_calls.append(media_id) or {"views": 100, "reach": 80},
                instagram_fetcher=lambda media_id: ig_calls.append(media_id) or {"views": 90, "reach": 70},
            )
            second = run_analytics_collection(
                now=now,
                final_dir=final_dir,
                post_metrics_path=metrics_path,
                content_scores_path=scores_path,
                latest_run_path=latest_run_path,
                facebook_fetcher=lambda media_id: fb_calls.append(media_id) or {"views": 100, "reach": 80},
                instagram_fetcher=lambda media_id: ig_calls.append(media_id) or {"views": 90, "reach": 70},
            )

            metrics = json.loads(metrics_path.read_text())
            latest_run = json.loads(latest_run_path.read_text())

        self.assertEqual(first["snapshots_added"], 2)
        self.assertEqual(second["snapshots_added"], 0)
        self.assertEqual(fb_calls, ["fb-1"])
        self.assertEqual(ig_calls, ["ig-1"])
        self.assertEqual(len(metrics["posts"]), 1)
        self.assertEqual(len(metrics["posts"][0]["snapshots"]), 2)
        self.assertEqual(latest_run["status"], "success")

    def test_collector_only_fetches_missing_eligible_buckets(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            final_dir = tmp_path / "final"
            final_dir.mkdir()
            metrics_path = tmp_path / "post_metrics.json"
            scores_path = tmp_path / "content_scores.json"
            latest_run_path = tmp_path / "latest_run.json"
            (final_dir / "post_1.json").write_text(json.dumps({
                "status": "success",
                "posted_at": (now - timedelta(hours=80)).isoformat(),
                "video_id": "fb-1",
                "pet_type": "dog",
                "pillar": "safety",
            }))
            metrics_path.write_text(json.dumps({
                "posts": [{
                    "post_key": "fb-1",
                    "video_id": "fb-1",
                    "pet_type": "dog",
                    "pillar": "safety",
                    "posted_at": (now - timedelta(hours=80)).isoformat(),
                    "snapshots": [{
                        "platform": "facebook",
                        "age_bucket": "24h",
                        "views": 10,
                    }],
                }]
            }))

            calls = []
            result = run_analytics_collection(
                now=now,
                final_dir=final_dir,
                post_metrics_path=metrics_path,
                content_scores_path=scores_path,
                latest_run_path=latest_run_path,
                facebook_fetcher=lambda media_id: calls.append(media_id) or {"views": 100, "reach": 80},
                instagram_fetcher=lambda media_id: {},
            )
            metrics = json.loads(metrics_path.read_text())

        self.assertEqual(result["snapshots_added"], 1)
        self.assertEqual(calls, ["fb-1"])
        self.assertEqual(
            [s["age_bucket"] for s in metrics["posts"][0]["snapshots"]],
            ["24h", "72h"],
        )

    def test_collector_does_not_rewrite_state_when_no_snapshots_change(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
        posted_at = (now - timedelta(hours=26)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            final_dir = tmp_path / "final"
            final_dir.mkdir()
            metrics_path = tmp_path / "post_metrics.json"
            scores_path = tmp_path / "content_scores.json"
            latest_run_path = tmp_path / "latest_run.json"
            (final_dir / "post_1.json").write_text(json.dumps({
                "status": "success",
                "posted_at": posted_at,
                "video_id": "fb-1",
                "pet_type": "dog",
                "pillar": "safety",
            }))
            metrics_payload = {
                "posts": [{
                    "post_key": "fb-1",
                    "video_id": "fb-1",
                    "pet_type": "dog",
                    "pillar": "safety",
                    "posted_at": posted_at,
                    "snapshots": [{
                        "platform": "facebook",
                        "age_bucket": "24h",
                        "views": 10,
                    }],
                }]
            }
            scores_payload = {
                "last_updated": "2026-06-10T12:00:00+00:00",
                "cells": {},
            }
            metrics_path.write_text(json.dumps(metrics_payload, indent=2))
            scores_path.write_text(json.dumps(scores_payload, indent=2))

            result = run_analytics_collection(
                now=now,
                final_dir=final_dir,
                post_metrics_path=metrics_path,
                content_scores_path=scores_path,
                latest_run_path=latest_run_path,
                facebook_fetcher=lambda media_id: self.fail("No fetch expected"),
                instagram_fetcher=lambda media_id: self.fail("No fetch expected"),
            )

            self.assertFalse(result["state_changed"])
            self.assertEqual(json.loads(metrics_path.read_text()), metrics_payload)
            self.assertEqual(json.loads(scores_path.read_text()), scores_payload)


if __name__ == "__main__":
    unittest.main()
