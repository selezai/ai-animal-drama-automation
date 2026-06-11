from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from modules.topic_history import (
    load_topic_history,
    make_topic_key,
    prune_topic_history,
    recent_topic_keys,
    record_topic_use,
    save_topic_history,
    select_topic,
)


class TopicHistoryTests(unittest.TestCase):
    def test_normalizes_equivalent_topic_strings_to_same_key(self) -> None:
        key_a = make_topic_key(
            "Dog",
            "Safety",
            " Grapes & raisins cause acute kidney failure!!! ",
        )
        key_b = make_topic_key(
            "dog",
            "safety",
            "grapes raisins cause acute kidney failure",
        )

        self.assertEqual(key_a, key_b)
        self.assertEqual(key_a, "dog:safety:grapes-raisins-cause-acute-kidney-failure")

    def test_recent_topic_keys_excludes_only_records_inside_cooldown(self) -> None:
        now = datetime(2026, 6, 11, tzinfo=timezone.utc)
        recent_key = make_topic_key("dog", "safety", "recent topic")
        old_key = make_topic_key("dog", "safety", "old topic")
        history = [
            {"topic_key": recent_key, "used_at": (now - timedelta(days=10)).isoformat()},
            {"topic_key": old_key, "used_at": (now - timedelta(days=100)).isoformat()},
        ]

        self.assertEqual(recent_topic_keys(history, now=now), {recent_key})

    def test_select_topic_allows_old_records_outside_cooldown(self) -> None:
        now = datetime(2026, 6, 11, tzinfo=timezone.utc)
        old_topic = "old topic"
        history = [
            {
                "topic_key": make_topic_key("dog", "safety", old_topic),
                "used_at": (now - timedelta(days=100)).isoformat(),
            }
        ]

        topic, topic_key, reused = select_topic(
            "dog",
            "safety",
            [old_topic],
            history=history,
            now=now,
        )

        self.assertEqual(topic, old_topic)
        self.assertEqual(topic_key, make_topic_key("dog", "safety", old_topic))
        self.assertFalse(reused)

    def test_prunes_records_older_than_retention_window(self) -> None:
        now = datetime(2026, 6, 11, tzinfo=timezone.utc)
        kept = {"topic_key": "kept", "used_at": (now - timedelta(days=100)).isoformat()}
        pruned = {"topic_key": "pruned", "used_at": (now - timedelta(days=600)).isoformat()}

        self.assertEqual(prune_topic_history([kept, pruned], now=now), [kept])

    def test_missing_history_file_returns_empty_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "topics.json"

            self.assertEqual(load_topic_history(path), [])

    def test_save_topic_history_prunes_before_writing(self) -> None:
        now = datetime(2026, 6, 11, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "topics.json"
            save_topic_history(
                [
                    {"topic_key": "kept", "used_at": (now - timedelta(days=100)).isoformat()},
                    {"topic_key": "pruned", "used_at": (now - timedelta(days=600)).isoformat()},
                ],
                path=path,
                now=now,
            )

            self.assertEqual(json.loads(path.read_text()), [
                {"topic_key": "kept", "used_at": (now - timedelta(days=100)).isoformat()}
            ])

    def test_record_topic_use_appends_successful_queue_item(self) -> None:
        now = datetime(2026, 6, 11, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "topics.json"
            tip = {
                "pet_type": "dog",
                "pillar": "safety",
                "topic": "grapes raisins cause kidney failure",
                "topic_key": make_topic_key("dog", "safety", "grapes raisins cause kidney failure"),
                "hook": "Stop doing this",
                "virality_score": 8,
            }

            record = record_topic_use(
                tip,
                video_path=Path("output/video/example.mp4"),
                manifest_path=Path("output/queue/example.json"),
                path=path,
                now=now,
            )

            saved = json.loads(path.read_text())
            self.assertEqual(saved, [record])
            self.assertEqual(record["video_path"], "output/video/example.mp4")
            self.assertEqual(record["manifest_path"], "output/queue/example.json")


if __name__ == "__main__":
    unittest.main()
