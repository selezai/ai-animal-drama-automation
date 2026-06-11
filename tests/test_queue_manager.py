from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from modules import queue_manager


class QueueManagerTests(unittest.TestCase):
    def test_enqueue_writes_topic_and_topic_key_to_manifest(self) -> None:
        original_queue_dir = queue_manager.QUEUE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            queue_manager.QUEUE_DIR = Path(tmp)
            try:
                manifest_path = queue_manager.enqueue(
                    {
                        "pet_type": "dog",
                        "pillar": "safety",
                        "topic": "grapes and raisins",
                        "topic_key": "dog:safety:grapes-and-raisins",
                        "hook": "Stop doing this",
                    },
                    video_path=Path("output/video/example.mp4"),
                    audio_path=Path("output/audio/example.mp3"),
                    thumb_path=None,
                )
                manifest = json.loads(manifest_path.read_text())
            finally:
                queue_manager.QUEUE_DIR = original_queue_dir

        self.assertEqual(manifest["topic"], "grapes and raisins")
        self.assertEqual(manifest["topic_key"], "dog:safety:grapes-and-raisins")


if __name__ == "__main__":
    unittest.main()
