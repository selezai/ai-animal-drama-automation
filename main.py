#!/usr/bin/env python3
"""
Pet Tips Automation Pipeline

Two modes:
  batch   — Generate + render 14 videos for the week (run Sunday night)
  post    — Post next video from queue to Facebook (run 2x/day)

Usage:
    python main.py batch          # Generate weekly batch of 14 videos
    python main.py batch --count=3  # Generate a smaller batch (for testing)
    python main.py post           # Post next queued video to Facebook
    python main.py post --test    # Post dry run (skip Facebook)
    python main.py tip            # Generate + render a single tip (for testing)
"""
from __future__ import annotations
import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR, BATCH_SIZE

from modules.tip_generator import generate_tip, generate_batch
from modules.voice_generator import generate_voice_from_tip
from modules.queue_manager import enqueue, pop_next, queue_size
from modules.facebook_poster import post_video, post_reel
from modules.scene_generator import generate_scenes, copy_scenes_to_remotion
from modules.comment_replier import run_comment_replies
from modules.token_refresher import run_token_refresh

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pipeline")


def render_video(tip: dict, audio_path: Path, scene_rel_paths: list[str], word_timestamps: list[dict] | None = None) -> Path:
    """Render a Remotion video for a tip. Returns path to rendered MP4."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pet_type = tip.get("pet_type", "pet")
    pillar = tip.get("pillar", "tip")
    output_path = OUTPUT_DIR / "video" / f"{pet_type}_{pillar}_{ts}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_rel = f"audio/{audio_path.name}"

    props = {
        "petType": tip.get("pet_type", "dog"),
        "hook": tip.get("hook", ""),
        "teach": tip.get("teach", ""),
        "why": tip.get("why", ""),
        "cta": tip.get("cta", "Follow for daily pet tips"),
        "audioSrc": audio_rel,
        "pillar": tip.get("pillar", "safety"),
        "scenes": scene_rel_paths,
        "wordTimestamps": word_timestamps or [],
    }

    logger.info(f"Rendering video: {output_path.name}")
    result = subprocess.run(
        ["node", "scripts/render_video.js",
         f"--props={json.dumps(props)}",
         f"--output={output_path}"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Render failed:\n{result.stderr}")

    logger.info(f"Video rendered: {output_path.name} ({output_path.stat().st_size // 1024} KB)")
    return output_path


def run_batch(count: int = BATCH_SIZE) -> dict:
    """Generate, render, and queue a batch of pet tip videos."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"run_id": run_id, "mode": "batch", "target": count, "queued": 0, "failed": 0}

    logger.info(f"Starting batch generation: {count} videos")
    tips = generate_batch(count)

    for i, tip in enumerate(tips):
        try:
            logger.info(f"Processing tip {i + 1}/{len(tips)}: {tip.get('pet_type')} / {tip.get('pillar')}")

            audio_path, word_timestamps = generate_voice_from_tip(tip)

            audio_dest = Path(__file__).parent / "remotion" / "public" / "audio" / audio_path.name
            audio_dest.parent.mkdir(parents=True, exist_ok=True)
            audio_dest.write_bytes(audio_path.read_bytes())

            scene_images = generate_scenes(tip)
            remotion_public = Path(__file__).parent / "remotion" / "public"
            scene_rel_paths = copy_scenes_to_remotion(scene_images, remotion_public)

            video_path = render_video(tip, audio_path, scene_rel_paths, word_timestamps)

            enqueue(tip, video_path, audio_path)
            result["queued"] += 1

        except Exception as e:
            logger.error(f"Failed tip {i + 1}: {e}", exc_info=True)
            result["failed"] += 1

    logger.info(f"Batch complete: {result['queued']} queued, {result['failed']} failed")
    logger.info(f"Queue size now: {queue_size()} pending videos")

    log_path = OUTPUT_DIR / "final" / f"batch_{run_id}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(result, indent=2))
    return result


def run_post(test_mode: bool = False, ig_only: bool = False) -> dict:
    """Post the next queued video to Facebook and/or Instagram."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"run_id": run_id, "mode": "post", "status": "started"}

    manifest = pop_next()
    if not manifest:
        logger.warning("Queue is empty — nothing to post")
        result["status"] = "skipped"
        result["reason"] = "queue empty"
        return result

    video_path = Path(manifest["video_path"])
    caption = manifest.get("caption", "")
    first_comment = manifest.get("first_comment", "")

    logger.info(f"Posting: {manifest['pet_type']} / {manifest['pillar']}")
    logger.info(f"Hook: {manifest['hook'][:80]}")

    if test_mode:
        logger.info("TEST MODE — skipping all posts")
        logger.info(f"Would post: {video_path.name}")
        logger.info(f"Caption: {caption[:100]}...")
        result["status"] = "skipped"
        result["reason"] = "test mode"
    elif ig_only:
        logger.info("IG-ONLY MODE — skipping Facebook post")
        try:
            from config import IG_USER_ID
            if not IG_USER_ID:
                raise ValueError("IG_USER_ID not set")
            ig_result = post_reel(video_path, caption)
            result["ig_media_id"] = ig_result.get("id")
            result["status"] = "success"
            logger.info(f"Posted to Instagram Reels only: {ig_result.get('id')}")
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Instagram post failed: {e}")
    else:
        fb_result = post_video(video_path, caption)
        video_id = fb_result.get("id")
        logger.info(f"Posted to Facebook: video_id={video_id}")

        if first_comment and video_id:
            _post_first_comment(video_id, first_comment)

        result["status"] = "success"
        result["video_id"] = video_id

        try:
            from config import IG_USER_ID
            if IG_USER_ID:
                ig_result = post_reel(video_path, caption)
                result["ig_media_id"] = ig_result.get("id")
                logger.info(f"Posted to Instagram Reels: {ig_result.get('id')}")
        except Exception as e:
            logger.warning(f"Instagram post failed (FB post succeeded): {e}")
            print(f"::warning::Instagram Reel post failed: {e}. FB post succeeded. Check IG token/permissions.")

    if result["status"] == "success":
        _cleanup_posted_files(manifest)

    result["remaining_queue"] = queue_size()
    log_path = OUTPUT_DIR / "final" / f"post_{run_id}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(result, indent=2))
    return result


def _cleanup_posted_files(manifest: dict) -> None:
    """Delete video, audio, and scene files after successful posting to keep repo lean."""
    base = Path(__file__).parent
    deleted = []

    for key in ("video_path", "audio_path"):
        raw = manifest.get(key, "")
        if not raw:
            continue
        p = Path(raw)
        if not p.is_absolute():
            p = base / p
        local = base / "output" / p.name if "output" in str(p) else p
        for candidate in [p, local]:
            if candidate.exists():
                candidate.unlink()
                deleted.append(str(candidate))
                break

    audio_name = Path(manifest.get("audio_path", "")).name
    if audio_name:
        remotion_audio = base / "remotion" / "public" / "audio" / audio_name
        if remotion_audio.exists():
            remotion_audio.unlink()
            deleted.append(str(remotion_audio))

    stem = Path(manifest.get("audio_path", "")).stem
    if stem:
        scenes_dir = base / "remotion" / "public" / "scenes"
        if scenes_dir.exists():
            for f in scenes_dir.glob(f"{stem.rsplit('_', 1)[0]}*"):
                f.unlink()
                deleted.append(str(f))
        out_scenes = base / "output" / "scenes"
        if out_scenes.exists():
            for f in out_scenes.glob(f"{stem.rsplit('_', 1)[0]}*"):
                f.unlink()
                deleted.append(str(f))

    if deleted:
        logger.info(f"Cleaned up {len(deleted)} files after posting")
    else:
        logger.info("No files to clean up")


def _post_first_comment(video_id: str, comment: str) -> None:
    """Post a comment on a published Facebook video to boost engagement."""
    import requests
    from config import FB_PAGE_ID, FB_ACCESS_TOKEN
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v21.0/{video_id}/comments",
            params={"access_token": FB_ACCESS_TOKEN},
            data={"message": comment},
            timeout=30,
        )
        resp.raise_for_status()
        logger.info(f"First comment posted: {comment[:60]}...")
    except Exception as e:
        logger.warning(f"First comment failed (non-critical): {e}")


def main():
    parser = argparse.ArgumentParser(description="Pet Tips Automation Pipeline")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    batch_parser = subparsers.add_parser("batch", help="Generate weekly batch of videos")
    batch_parser.add_argument("--count", type=int, default=BATCH_SIZE,
                              help=f"Number of videos to generate (default: {BATCH_SIZE})")

    post_parser = subparsers.add_parser("post", help="Post next queued video to Facebook and Instagram")
    post_parser.add_argument("--test", action="store_true",
                             help="Dry run — skip all posting")
    post_parser.add_argument("--ig-only", action="store_true",
                             help="Post to Instagram only, skip Facebook")

    subparsers.add_parser("tip", help="Generate + render a single tip (for testing)")
    subparsers.add_parser("queue", help="Show queue status")
    subparsers.add_parser("reply", help="Reply to comments on latest posted video")
    subparsers.add_parser("refresh-token", help="Refresh the Facebook Page access token")

    args = parser.parse_args()

    if args.mode == "batch":
        result = run_batch(count=args.count)
        sys.exit(0 if result["failed"] == 0 else 1)

    elif args.mode == "post":
        result = run_post(test_mode=args.test, ig_only=getattr(args, "ig_only", False))
        sys.exit(0 if result["status"] in ("success", "skipped") else 1)

    elif args.mode == "tip":
        logger.info("Generating single tip for testing...")
        tip = generate_tip()
        print(json.dumps(tip, indent=2))

    elif args.mode == "queue":
        size = queue_size()
        print(f"Queue: {size} pending videos")

    elif args.mode == "reply":
        result = run_comment_replies()
        sys.exit(0 if result["status"] in ("success", "skipped") else 1)

    elif args.mode == "refresh-token":
        result = run_token_refresh()
        sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
