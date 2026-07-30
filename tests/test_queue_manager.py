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
                        "scene_image_source": "provider",
                        "scene_image_fallback": False,
                        "scene_paths": ["scenes/example_scene1.png"],
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
        self.assertEqual(manifest["scene_image_source"], "provider")
        self.assertFalse(manifest["scene_image_fallback"])
        self.assertEqual(manifest["scene_paths"], ["scenes/example_scene1.png"])

    def test_mark_failed_removes_manifest_from_pending_queue(self) -> None:
        original_queue_dir = queue_manager.QUEUE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            queue_manager.QUEUE_DIR = Path(tmp)
            try:
                manifest_path = queue_manager.enqueue(
                    {
                        "pet_type": "dog",
                        "pillar": "safety",
                    },
                    video_path=Path("output/video/missing.mp4"),
                    audio_path=Path("output/audio/example.mp3"),
                    thumb_path=None,
                )
                manifest = queue_manager.pop_next()
                queue_manager.mark_failed(manifest, {"failure_reason": "video file missing"})
                data = json.loads(manifest_path.read_text())
                size = queue_manager.queue_size()
            finally:
                queue_manager.QUEUE_DIR = original_queue_dir

        self.assertEqual(data["status"], "failed")
        self.assertEqual(data["failure_reason"], "video file missing")
        self.assertEqual(size, 0)


if __name__ == "__main__":
    unittest.main()
