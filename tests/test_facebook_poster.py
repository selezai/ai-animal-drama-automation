from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import facebook_poster


class _Response:
    ok = True
    text = "{}"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"id": "video_123"}


class FacebookPosterTests(unittest.TestCase):
    def test_post_video_uses_long_upload_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "video.mp4"
            video.write_bytes(b"x")

            with patch.object(facebook_poster.requests, "post", return_value=_Response()) as post:
                result = facebook_poster.post_video(
                    video,
                    "caption",
                    page_id="page",
                    access_token="token",
                )

        self.assertEqual(result["id"], "video_123")
        self.assertEqual(post.call_args.kwargs["timeout"], facebook_poster.DIRECT_UPLOAD_TIMEOUT)
        self.assertEqual(facebook_poster.DIRECT_UPLOAD_TIMEOUT, (30, 300))


if __name__ == "__main__":
    unittest.main()
