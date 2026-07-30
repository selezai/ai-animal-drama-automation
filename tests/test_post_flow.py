from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from modules import queue_manager


class PostFlowTests(unittest.TestCase):
    def test_post_exit_code_fails_empty_queue_but_allows_test_mode(self) -> None:
        self.assertEqual(main._post_exit_code({"status": "success"}), 0)
        self.assertEqual(main._post_exit_code({"status": "skipped", "reason": "test mode"}), 0)
        self.assertEqual(main._post_exit_code({"status": "skipped", "reason": "queue empty"}), 1)
        self.assertEqual(main._post_exit_code({"status": "skipped", "reason": "no valid queued videos"}), 1)

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

    def test_run_post_marks_fallback_scene_manifest_failed_and_skips(self) -> None:
        original_output_dir = main.OUTPUT_DIR
        original_queue_dir = queue_manager.QUEUE_DIR

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video_path = tmp_path / "video" / "fallback.mp4"
            video_path.parent.mkdir(parents=True)
            video_path.write_bytes(b"video")

            main.OUTPUT_DIR = tmp_path
            queue_manager.QUEUE_DIR = tmp_path / "queue"
            queue_manager.QUEUE_DIR.mkdir(parents=True)
            manifest_path = queue_manager.QUEUE_DIR / "dog_safety.json"
            manifest_path.write_text(json.dumps({
                "queued_at": "2026-07-30T12:00:00",
                "status": "pending",
                "pet_type": "dog",
                "pillar": "safety",
                "hook": "Fallback video",
                "caption": "Caption",
                "fb_caption": "Caption",
                "first_comment": "",
                "video_path": str(video_path),
                "audio_path": str(tmp_path / "audio" / "fallback.mp3"),
                "thumb_path": "",
                "scene_image_source": "fallback",
                "scene_image_fallback": True,
            }))

            try:
                with patch.object(main, "allow_fallback_scene_images", return_value=False), \
                     patch.object(main, "post_video") as post_video:
                    result = main.run_post()
                manifest = json.loads(manifest_path.read_text())
                logs = list((tmp_path / "final").glob("post_*.json"))
            finally:
                main.OUTPUT_DIR = original_output_dir
                queue_manager.QUEUE_DIR = original_queue_dir

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "no valid queued videos")
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["failure_reason"], "fallback scene images blocked")
        self.assertEqual(result["skipped_fallback_videos"], ["fallback.mp4"])
        self.assertEqual(len(logs), 1)
        post_video.assert_not_called()


if __name__ == "__main__":
    unittest.main()
