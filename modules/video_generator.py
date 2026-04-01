"""
Video Generator — Luma Labs API
Ray Flash 2: text-to-video, $0.24/clip, 720p, 5 seconds

Generates fully animated video scenes directly from text prompts.
Each scene gets a unique animated video — characters move, interact, emote.
No static images. Pure text-to-video generation.
"""
import json
import logging
import requests
import time
from pathlib import Path
from datetime import datetime

from config import (
    LUMA_API_KEY, LUMA_VIDEO_MODEL,
    VIDEO_ASPECT_RATIO, OUTPUT_DIR, PROMPTS_DIR,
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


def _sanitize_prompt(prompt: str) -> str:
    """Remove trademarked/IP terms that Luma blocks."""
    ip_replacements = {
        "pixar": "stylized 3D",
        "disney": "animated",
        "dreamworks": "3D animated",
        "nintendo": "colorful 3D",
        "marvel": "",
        "anime": "Japanese animation",
    }
    cleaned = prompt
    for ip_term, replacement in ip_replacements.items():
        cleaned = cleaned.lower().replace(ip_term, replacement)
    return cleaned


def generate_video_scene(prompt: str, output_path: Path = None) -> Path:
    """
    Generate a fully animated video scene from a text prompt.
    Pure text-to-video — characters move, interact, emote.

    Args:
        prompt: Detailed scene description with action, characters, mood
        output_path: Where to save the video

    Returns:
        Path to the generated video file
    """
    if not LUMA_API_KEY:
        raise ValueError("LUMA_API_KEY not set")

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / "video" / f"scene_{ts}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clean_prompt = _sanitize_prompt(prompt)
    logger.info(f"Generating animated scene: {clean_prompt[:80]}...")

    resp = requests.post(
        f"{LUMA_API}/generations",
        headers=_luma_headers(),
        json={
            "prompt": clean_prompt,
            "model": LUMA_VIDEO_MODEL,
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

    logger.info(f"Video scene saved: {output_path.name} ({output_path.stat().st_size} bytes)")
    return output_path


def generate_clips_from_script(script: dict) -> list[Path]:
    """
    Generate fully animated video clips for each scene in the script.
    Each scene gets a unique text-to-video clip based on its visual description.

    Returns list of video file paths in scene order.
    """
    character = script["character"]
    clips = []

    chars = _load_characters()
    char_data = chars.get(character, {})
    char_visual = char_data.get("visual_prompt", character)

    for i, scene in enumerate(script.get("scenes", [])):
        visual = scene.get("visual", "")
        emotion = scene.get("emotion", "neutral")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / "video" / f"{character}_scene{i}_{ts}.mp4"

        prompt = (
            f"{char_visual}, {visual}, "
            f"{emotion} mood, stylized 3D animated, "
            f"cinematic lighting, smooth character animation, "
            f"expressive, dynamic camera movement, vertical 9:16"
        )

        logger.info(f"Scene {i+1}/{len(script.get('scenes', []))}: {visual[:60]}...")
        clip_path = generate_video_scene(prompt, out_path)
        clips.append(clip_path)

    return clips


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if LUMA_API_KEY:
        test_prompt = (
            "A golden retriever sitting by a window at sunset, owner walks "
            "in the door with a new puppy, the golden retriever looks surprised, "
            "3D Pixar animation style, cinematic lighting, smooth animation, "
            "dynamic camera, vertical 9:16"
        )
        path = generate_video_scene(test_prompt)
        print(f"Video: {path}")
    else:
        print("Set LUMA_API_KEY to test.")
