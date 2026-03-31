"""
Video Generator — Luma Labs API (Budget Setup)
Ray Flash 2: $0.24/video, 720p, 5 seconds
Two-step process: generate character image, then animate it.
"""
import json
import logging
import requests
import time
from pathlib import Path
from datetime import datetime

from config import (
    LUMA_API_KEY, LUMA_VIDEO_MODEL, LUMA_IMAGE_MODEL,
    VIDEO_DURATION_SEC, VIDEO_ASPECT_RATIO, OUTPUT_DIR, PROMPTS_DIR
)

logger = logging.getLogger(__name__)

LUMA_API = "https://api.lumalabs.ai/dream-machine/v1"


def _load_characters() -> dict:
    with open(PROMPTS_DIR / "characters.json") as f:
        return json.load(f)["characters"]


def _luma_headers() -> dict:
    return {
        "Authorization": f"Bearer {LUMA_API_KEY}",
        "Content-Type": "application/json",
    }


def _poll_generation(generation_id: str, timeout: int = 300) -> dict:
    """Poll Luma API until generation completes."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{LUMA_API}/generations/{generation_id}",
            headers=_luma_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        state = data.get("state")
        
        if state == "completed":
            return data
        if state == "failed":
            raise RuntimeError(f"Luma generation failed: {data.get('failure_reason')}")
        
        time.sleep(5)
    
    raise TimeoutError(f"Luma generation timed out after {timeout}s")


def generate_character_image(character: str, scene_visual: str,
                             emotion: str = "neutral") -> str:
    """
    Generate a character image via Luma Photon.
    Returns the image URL.
    """
    if not LUMA_API_KEY:
        raise ValueError("LUMA_API_KEY not set")

    chars = _load_characters()
    char_data = chars.get(character, {})
    base_visual = char_data.get("visual_prompt", f"{character}, 3D Pixar style")

    prompt = (
        f"{base_visual}, {emotion} expression, {scene_visual}, "
        f"vertical composition 9:16, cinematic lighting, high detail"
    )

    logger.info(f"Generating image: {character} / {emotion}")

    resp = requests.post(
        f"{LUMA_API}/generations/image",
        headers=_luma_headers(),
        json={
            "prompt": prompt,
            "model": LUMA_IMAGE_MODEL,
            "aspect_ratio": "9:16",
        },
        timeout=30,
    )
    resp.raise_for_status()
    gen_id = resp.json()["id"]

    result = _poll_generation(gen_id)
    image_url = result["assets"]["image"]
    
    logger.info(f"Image generated: {image_url[:60]}...")
    return image_url


def animate_image(image_url: str, motion_prompt: str,
                  output_path: Path = None) -> Path:
    """
    Animate a character image into a video clip via Luma Ray.
    Downloads the result to local file.
    """
    if not LUMA_API_KEY:
        raise ValueError("LUMA_API_KEY not set")

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / "video" / f"clip_{ts}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Animating image → video ({LUMA_VIDEO_MODEL})")

    resp = requests.post(
        f"{LUMA_API}/generations",
        headers=_luma_headers(),
        json={
            "prompt": motion_prompt,
            "model": LUMA_VIDEO_MODEL,
            "keyframes": {
                "frame0": {
                    "type": "image",
                    "url": image_url,
                }
            },
            "aspect_ratio": VIDEO_ASPECT_RATIO,
        },
        timeout=30,
    )
    resp.raise_for_status()
    gen_id = resp.json()["id"]

    result = _poll_generation(gen_id, timeout=300)
    video_url = result["assets"]["video"]

    video_data = requests.get(video_url, timeout=120)
    video_data.raise_for_status()
    output_path.write_bytes(video_data.content)

    logger.info(f"Video clip saved: {output_path.name} ({output_path.stat().st_size} bytes)")
    return output_path


def generate_clips_from_script(script: dict) -> list[Path]:
    """
    Generate video clips for each scene in the script.
    Returns list of video file paths in scene order.
    """
    character = script["character"]
    clips = []

    for i, scene in enumerate(script.get("scenes", [])):
        visual = scene.get("visual", "")
        emotion = scene.get("emotion", "neutral")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / "video" / f"{character}_scene{i}_{ts}.mp4"

        # Step 1: Generate character image for this scene
        image_url = generate_character_image(character, visual, emotion)

        # Step 2: Animate the image
        motion = f"{visual}, subtle emotional movement, cinematic, smooth"
        clip_path = animate_image(image_url, motion, out_path)
        clips.append(clip_path)

    return clips


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if LUMA_API_KEY:
        url = generate_character_image("charlie", "sitting by window at sunset", "sad")
        print(f"Image URL: {url}")
        path = animate_image(url, "golden retriever looking sad, subtle breathing")
        print(f"Video: {path}")
    else:
        print("Set LUMA_API_KEY to test.")
