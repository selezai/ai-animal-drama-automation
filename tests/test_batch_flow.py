from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from modules import queue_manager


class BatchFlowTests(unittest.TestCase):
    def test_run_batch_stops_on_image_quota_before_voice_generation(self) -> None:
        original_output_dir = main.OUTPUT_DIR
        original_queue_dir = queue_manager.QUEUE_DIR

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            main.OUTPUT_DIR = tmp_path
            queue_manager.QUEUE_DIR = tmp_path / "queue"
            queue_manager.QUEUE_DIR.mkdir(parents=True)

            try:
                with patch.object(main, "generate_batch", return_value=[
                    {"pet_type": "dog", "pillar": "health"},
                    {"pet_type": "cat", "pillar": "safety"},
                ]), \
                    patch.object(
                        main,
                        "generate_scenes",
                        side_effect=main.ImageGenerationQuotaExhausted("quota blocked"),
                    ), \
                    patch.object(main, "generate_voice_from_tip") as generate_voice:
                    result = main.run_batch(count=2)
            finally:
                main.OUTPUT_DIR = original_output_dir
                queue_manager.QUEUE_DIR = original_queue_dir

        self.assertEqual(result["queued"], 0)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(result["failure_reason"], "image_generation_quota_exhausted")
        generate_voice.assert_not_called()


if __name__ == "__main__":
    unittest.main()
