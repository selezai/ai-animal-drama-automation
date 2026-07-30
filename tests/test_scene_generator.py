from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import scene_generator


class _InlineData:
    def __init__(self, data: bytes):
        self.data = data


class _Part:
    def __init__(self, data: bytes | None):
        self.inline_data = _InlineData(data) if data is not None else None


class _Response:
    def __init__(self, data: bytes | None, text: str = ""):
        self.parts = [_Part(data)] if data is not None else []
        self.text = text


class _Models:
    def __init__(self, responses: list[_Response]):
        self.responses = responses
        self.calls = 0

    def generate_content(self, **kwargs):
        response = self.responses[self.calls]
        self.calls += 1
        return response


class _Client:
    def __init__(self, responses: list[_Response]):
        self.models = _Models(responses)


class SceneGeneratorTests(unittest.TestCase):
    def test_generate_scene_images_retries_when_response_has_no_image(self) -> None:
        original_scene_dir = scene_generator.SCENE_DIR
        client = _Client([_Response(None, "no image"), _Response(b"png bytes")])

        with tempfile.TemporaryDirectory() as tmp:
            scene_generator.SCENE_DIR = Path(tmp)
            try:
                with patch.object(scene_generator.genai, "Client", return_value=client), \
                     patch.object(scene_generator, "GOOGLE_API_KEY", "test-key"), \
                     patch.object(scene_generator.time, "sleep", return_value=None):
                    images = scene_generator.generate_scene_images(
                        ["prompt"],
                        {"pet_type": "dog", "pillar": "health"},
                    )
                    image_bytes = images[0].read_bytes()
            finally:
                scene_generator.SCENE_DIR = original_scene_dir

        self.assertEqual(client.models.calls, 2)
        self.assertEqual(len(images), 1)
        self.assertEqual(image_bytes, b"png bytes")

    def test_generate_scenes_uses_local_fallback_on_quota_error(self) -> None:
        original_scene_dir = scene_generator.SCENE_DIR
        original_quota_blocked = scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED

        with tempfile.TemporaryDirectory() as tmp:
            scene_generator.SCENE_DIR = Path(tmp)
            scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = False
            try:
                with patch.object(scene_generator, "generate_scene_prompts", return_value=["prompt"] * 4), \
                     patch.object(scene_generator, "generate_scene_images", side_effect=RuntimeError("429 RESOURCE_EXHAUSTED quota")), \
                     patch.object(scene_generator, "allow_fallback_scene_images", return_value=True):
                    images = scene_generator.generate_scenes({"pet_type": "cat", "pillar": "safety"})
                    image_bytes = [path.read_bytes() for path in images]
            finally:
                scene_generator.SCENE_DIR = original_scene_dir
                scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = original_quota_blocked

        self.assertEqual(len(images), 4)
        self.assertTrue(all(data.startswith(b"\x89PNG") for data in image_bytes))
        self.assertTrue(scene_generator.scene_images_are_fallback(images))

    def test_generate_scenes_rejects_quota_fallback_by_default(self) -> None:
        original_quota_blocked = scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED
        scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = False
        try:
            with patch.object(scene_generator, "generate_scene_prompts", return_value=["prompt"] * 4), \
                 patch.object(scene_generator, "generate_scene_images", side_effect=RuntimeError("429 RESOURCE_EXHAUSTED quota")), \
                 patch.object(scene_generator, "allow_fallback_scene_images", return_value=False):
                with self.assertRaises(scene_generator.ImageGenerationQuotaExhausted):
                    scene_generator.generate_scenes({"pet_type": "cat", "pillar": "safety"})
        finally:
            scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = original_quota_blocked

    def test_generate_scenes_does_not_fallback_for_unrelated_errors(self) -> None:
        with patch.object(scene_generator, "generate_scene_prompts", return_value=["prompt"] * 4), \
             patch.object(scene_generator, "generate_scene_images", side_effect=RuntimeError("bad prompt")):
            with self.assertRaisesRegex(RuntimeError, "bad prompt"):
                scene_generator.generate_scenes({"pet_type": "dog", "pillar": "health"})

    def test_generate_scenes_skips_provider_after_quota_is_blocked(self) -> None:
        original_scene_dir = scene_generator.SCENE_DIR
        original_quota_blocked = scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED

        with tempfile.TemporaryDirectory() as tmp:
            scene_generator.SCENE_DIR = Path(tmp)
            scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = True
            try:
                with patch.object(scene_generator, "generate_scene_prompts", return_value=["prompt"] * 4), \
                     patch.object(scene_generator, "generate_scene_images") as generate_images, \
                     patch.object(scene_generator, "allow_fallback_scene_images", return_value=True):
                    images = scene_generator.generate_scenes({"pet_type": "dog", "pillar": "training"})
            finally:
                scene_generator.SCENE_DIR = original_scene_dir
                scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = original_quota_blocked

        self.assertEqual(len(images), 4)
        generate_images.assert_not_called()

    def test_generate_scenes_rejects_cached_quota_when_fallback_disabled(self) -> None:
        original_quota_blocked = scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED
        scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = True
        try:
            with patch.object(scene_generator, "generate_scene_prompts", return_value=["prompt"] * 4), \
                 patch.object(scene_generator, "generate_scene_images") as generate_images, \
                 patch.object(scene_generator, "allow_fallback_scene_images", return_value=False):
                with self.assertRaises(scene_generator.ImageGenerationQuotaExhausted):
                    scene_generator.generate_scenes({"pet_type": "dog", "pillar": "training"})
        finally:
            scene_generator._IMAGE_PROVIDER_QUOTA_BLOCKED = original_quota_blocked

        generate_images.assert_not_called()


if __name__ == "__main__":
    unittest.main()
