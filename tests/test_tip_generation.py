from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from modules import tip_generator
from modules.topic_history import make_topic_key, select_topic


class TipGenerationSelectionTests(unittest.TestCase):
    def test_pick_content_excludes_recent_history_topics(self) -> None:
        now = datetime.now(timezone.utc)
        pillars = {
            "pillars": {
                "safety": {
                    "dog_topics": ["recent topic", "fresh topic"],
                }
            }
        }
        history = [
            {
                "topic_key": make_topic_key("dog", "safety", "recent topic"),
                "used_at": (now - timedelta(days=10)).isoformat(),
            }
        ]

        with patch.object(tip_generator.random, "choices", return_value=[("dog", "safety")]):
            pillar, pet_type, topic, topic_key = tip_generator._pick_content(
                pillars,
                history=history,
                attempted_topic_keys=set(),
            )

        self.assertEqual((pillar, pet_type, topic), ("safety", "dog", "fresh topic"))
        self.assertEqual(topic_key, make_topic_key("dog", "safety", "fresh topic"))

    def test_pick_content_excludes_same_batch_attempted_topics(self) -> None:
        pillars = {
            "pillars": {
                "safety": {
                    "dog_topics": ["already attempted", "fresh topic"],
                }
            }
        }
        attempted = {make_topic_key("dog", "safety", "already attempted")}

        with patch.object(tip_generator.random, "choices", return_value=[("dog", "safety")]):
            _, _, topic, topic_key = tip_generator._pick_content(
                pillars,
                history=[],
                attempted_topic_keys=attempted,
            )

        self.assertEqual(topic, "fresh topic")
        self.assertEqual(topic_key, make_topic_key("dog", "safety", "fresh topic"))

    def test_exhausted_topic_pool_falls_back_to_oldest_topic(self) -> None:
        now = datetime(2026, 6, 11, tzinfo=timezone.utc)
        oldest_topic = "oldest recent topic"
        newest_topic = "newest recent topic"
        history = [
            {
                "topic_key": make_topic_key("dog", "safety", oldest_topic),
                "used_at": (now - timedelta(days=80)).isoformat(),
            },
            {
                "topic_key": make_topic_key("dog", "safety", newest_topic),
                "used_at": (now - timedelta(days=5)).isoformat(),
            },
        ]

        topic, topic_key, reused = select_topic(
            "dog",
            "safety",
            [oldest_topic, newest_topic],
            history=history,
            now=now,
        )

        self.assertEqual(topic, oldest_topic)
        self.assertEqual(topic_key, make_topic_key("dog", "safety", oldest_topic))
        self.assertTrue(reused)

    def test_pick_content_uses_joint_pet_pillar_weights_with_multiplier(self) -> None:
        pillars = {
            "pillars": {
                "safety": {"dog_topics": ["dog safety"], "cat_topics": ["cat safety"]},
                "behaviour": {"dog_topics": ["dog behaviour"], "cat_topics": ["cat behaviour"]},
            }
        }

        with patch.object(tip_generator, "PET_TYPES", ["dog", "cat"]), \
                patch.object(tip_generator, "PET_WEIGHTS", [0.7, 0.3]), \
                patch.object(tip_generator, "CONTENT_PILLARS", {
                    "safety": {"weight": 0.6},
                    "behaviour": {"weight": 0.4},
                }), \
                patch.object(tip_generator.random, "choices", return_value=[("cat", "behaviour")]) as choices:
            pillar, pet_type, topic, topic_key = tip_generator._pick_content(
                pillars,
                history=[],
                attempted_topic_keys=set(),
                multipliers={"cat:behaviour": 1.25},
            )

        self.assertEqual((pillar, pet_type, topic), ("behaviour", "cat", "cat behaviour"))
        self.assertEqual(topic_key, make_topic_key("cat", "behaviour", "cat behaviour"))
        self.assertEqual(choices.call_args.kwargs["weights"], [0.42, 0.27999999999999997, 0.18, 0.15])


if __name__ == "__main__":
    unittest.main()
