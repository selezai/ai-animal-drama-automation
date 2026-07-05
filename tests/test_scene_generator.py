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


if __name__ == "__main__":
    unittest.main()
