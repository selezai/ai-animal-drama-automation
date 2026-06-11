from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from modules.content_scoring import (
    apply_stale_decay,
    compute_content_scores,
    content_multipliers,
    normalize_platform_metrics,
    score_snapshot,
)


class ContentScoringTests(unittest.TestCase):
    def test_normalizes_fb_and_ig_metrics_with_missing_fields(self) -> None:
        fb = normalize_platform_metrics("facebook", {
            "likes": {"summary": {"total_count": 5}},
            "comments": {"summary": {"total_count": 3}},
            "shares": {"count": 2},
            "video_insights": {
                "data": [
                    {"name": "total_video_views", "values": [{"value": 100}]},
                    {"name": "total_video_impressions", "values": [{"value": 150}]},
                ]
            },
        })
        ig = normalize_platform_metrics("instagram", {
            "data": [
                {"name": "views", "values": [{"value": 80}]},
                {"name": "reach", "values": [{"value": 70}]},
                {"name": "saved", "values": [{"value": 4}]},
            ]
        })

        self.assertEqual(fb["views"], 100)
        self.assertEqual(fb["reach"], 150)
        self.assertEqual(fb["likes"], 5)
        self.assertEqual(fb["comments"], 3)
        self.assertEqual(fb["shares"], 2)
        self.assertEqual(fb["saves"], 0)
        self.assertEqual(ig["views"], 80)
        self.assertEqual(ig["reach"], 70)
        self.assertEqual(ig["likes"], 0)
        self.assertEqual(ig["saves"], 4)

    def test_balanced_score_weights_comments_and_shares_above_likes_and_views(self) -> None:
        discussion = score_snapshot({"reach": 1000, "views": 500, "comments": 20, "shares": 20})
        passive = score_snapshot({"reach": 1000, "views": 2000, "likes": 50})

        self.assertGreater(discussion, passive)

    def test_content_score_respects_min_sample_size_and_clamps_multiplier(self) -> None:
        now = datetime(2026, 6, 11, tzinfo=timezone.utc)
        posts = []
        for i in range(5):
            posts.append({
                "post_key": f"dog-{i}",
                "pet_type": "dog",
                "pillar": "safety",
                "snapshots": [{"platform": "facebook", "age_bucket": "7d", "reach": 100, "views": 100, "shares": 50}],
            })
        posts.append({
            "post_key": "cat-1",
            "pet_type": "cat",
            "pillar": "health",
            "snapshots": [{"platform": "facebook", "age_bucket": "7d", "reach": 100, "views": 100}],
        })

        scores = compute_content_scores({"posts": posts}, now=now)

        self.assertEqual(scores["cells"]["dog:safety"]["sample_size"], 5)
        self.assertEqual(scores["cells"]["cat:health"]["sample_size"], 1)
        self.assertLessEqual(scores["cells"]["dog:safety"]["multiplier"], 1.25)
        self.assertEqual(scores["cells"]["cat:health"]["multiplier"], 1.0)

    def test_stale_scores_decay_toward_one(self) -> None:
        now = datetime(2026, 6, 30, tzinfo=timezone.utc)
        scores = {
            "last_updated": (now - timedelta(days=21)).isoformat(),
            "cells": {
                "dog:safety": {"sample_size": 5, "score": 100, "multiplier": 1.2},
                "cat:health": {"sample_size": 5, "score": 10, "multiplier": 0.8},
            },
        }

        decayed = apply_stale_decay(scores, now=now)

        self.assertEqual(decayed["cells"]["dog:safety"]["multiplier"], 1.1)
        self.assertEqual(decayed["cells"]["cat:health"]["multiplier"], 0.9)

    def test_content_multipliers_falls_back_when_disabled_missing_or_undersampled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.json"
            self.assertEqual(content_multipliers(path=path), {})

            path.write_text(json.dumps({
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "cells": {
                    "dog:safety": {"sample_size": 4, "score": 10, "multiplier": 1.25},
                    "cat:health": {"sample_size": 5, "score": 10, "multiplier": 0.9},
                },
            }))
            self.assertEqual(content_multipliers(path=path), {"cat:health": 0.9})

            with patch.dict(os.environ, {"ANALYTICS_WEIGHTING_ENABLED": "false"}):
                self.assertEqual(content_multipliers(path=path), {})


if __name__ == "__main__":
    unittest.main()
