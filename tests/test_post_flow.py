from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import main
from modules import queue_manager


class PostFlowTests(unittest.TestCase):
    def test_run_post_marks_missing_video_manifest_failed_and_skips(self) -> None:
        original_output_dir = main.OUTPUT_DIR
        original_queue_dir = queue_manager.QUEUE_DIR

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            main.OUTPUT_DIR = tmp_path
            queue_manager.QUEUE_DIR = tmp_path / "queue"
            queue_manager.QUEUE_DIR.mkdir(parents=True)
            manifest_path = queue_manager.QUEUE_DIR / "dog_safety.json"
            manifest_path.write_text(json.dumps({
                "queued_at": "2026-06-11T12:00:00",
                "status": "pending",
                "pet_type": "dog",
                "pillar": "safety",
                "hook": "Missing video",
                "caption": "Caption",
                "fb_caption": "Caption",
                "first_comment": "",
                "video_path": str(tmp_path / "video" / "missing.mp4"),
                "audio_path": str(tmp_path / "audio" / "missing.mp3"),
                "thumb_path": "",
            }))

            try:
                result = main.run_post()
                manifest = json.loads(manifest_path.read_text())
                logs = list((tmp_path / "final").glob("post_*.json"))
            finally:
                main.OUTPUT_DIR = original_output_dir
                queue_manager.QUEUE_DIR = original_queue_dir

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "no valid queued videos")
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["failure_reason"], "video file missing")
        self.assertEqual(len(logs), 1)


if __name__ == "__main__":
    unittest.main()
