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
import os
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR, BATCH_SIZE

from modules.tip_generator import generate_tip, generate_batch
from modules.voice_generator import generate_voice_from_tip
from modules.queue_manager import enqueue, pop_next, queue_size
from modules.facebook_poster import post_video, post_reel, get_fb_video_source_url
from modules.scene_generator import generate_scenes, copy_scenes_to_remotion
from modules.comment_replier import run_comment_replies
from modules.token_refresher import run_token_refresh, bootstrap_from_short_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pipeline")


def render_video(tip: dict, audio_path: Path, scene_rel_paths: list[str], word_timestamps: list[dict] | None = None) -> tuple[Path, Path | None]:
    """Render a Remotion video for a tip. Returns (video_path, thumbnail_path)."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pet_type = tip.get("pet_type", "pet")
    pillar = tip.get("pillar", "tip")
    output_path = OUTPUT_DIR / "video" / f"{pet_type}_{pillar}_{ts}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_rel = f"audio/{audio_path.name}"

    # Derive audio duration and scene boundaries from word timestamps
    wts = word_timestamps or []
    audio_duration_secs = round(wts[-1]["end"] + 0.3, 3) if wts else 30.0  # 0.3s tail padding

    # Find where each section starts in the narration by matching first words
    narrator_script = tip.get("narrator_script", "")
    hook_text = tip.get("hook", "")
    teach_text = tip.get("teach", "")
    why_text = tip.get("why", "")
    cta_text = tip.get("cta", "Follow for daily pet tips")

    def _normalize(word: str) -> str:
        return word.lower().rstrip('.,!?:;"\'-')

    def _find_section_start(section_text: str, after_sec: float = 0.0) -> float:
        """Find the timestamp where a section starts by matching its first 3 words
        against the word timestamps. Only matches occurring after after_sec are considered."""
        if not wts or not section_text:
            return 0.0
        section_words = [_normalize(w) for w in section_text.strip().split()[:3]]
        n = len(section_words)
        for i, w in enumerate(wts):
            if w["start"] < after_sec:
                continue
            if _normalize(w["word"]) == section_words[0]:
                # Check if the next n-1 words also match
                if n == 1:
                    return w["start"]
                match = True
                for j in range(1, n):
                    if i + j >= len(wts) or _normalize(wts[i + j]["word"]) != section_words[j]:
                        match = False
                        break
                if match:
                    return w["start"]
        # Single-word fallback (after after_sec)
        first_word = section_words[0]
        for w in wts:
            if w["start"] >= after_sec and _normalize(w["word"]) == first_word:
                return w["start"]
        return 0.0

    hook_start = 0.0
    teach_start = _find_section_start(teach_text, after_sec=hook_start + 0.5)
    why_start = _find_section_start(why_text, after_sec=teach_start + 0.5)
    cta_start = _find_section_start(cta_text, after_sec=why_start + 0.5)

    # Fallback: if section detection fails, divide audio proportionally
    if teach_start <= hook_start or why_start <= teach_start or cta_start <= why_start:
        logger.warning("Section boundary detection unreliable — falling back to proportional split")
        d = audio_duration_secs
        hook_start, teach_start, why_start, cta_start = 0.0, d * 0.1, d * 0.57, d * 0.83

    scene_boundaries = [hook_start, teach_start, why_start, cta_start]
    logger.info(f"Audio duration: {audio_duration_secs:.2f}s | Scene boundaries: {[round(s,2) for s in scene_boundaries]}")

    props = {
        "petType": tip.get("pet_type", "dog"),
        "hook": hook_text,
        "teach": teach_text,
        "why": why_text,
        "cta": cta_text,
        "audioSrc": audio_rel,
        "pillar": tip.get("pillar", "safety"),
        "scenes": scene_rel_paths,
        "wordTimestamps": wts,
        "audioDurationSecs": audio_duration_secs,
        "sceneBoundaries": scene_boundaries,
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

    # Parse thumbnail path from render output
    thumb_path = None
    for line in result.stdout.splitlines():
        if line.startswith("THUMBNAIL_PATH="):
            p = Path(line.split("=", 1)[1].strip())
            if p.exists():
                thumb_path = p
                logger.info(f"Thumbnail rendered: {p.name}")
            break

    return output_path, thumb_path


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

            video_path, thumb_path = render_video(tip, audio_path, scene_rel_paths, word_timestamps)

            enqueue(tip, video_path, audio_path, thumb_path)
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

    _raw_video_path = Path(manifest["video_path"])
    # Absolute CI paths don't survive across workflow runs — fall back to filename in output/video/
    if not _raw_video_path.exists():
        _fallback = Path(__file__).parent / "output" / "video" / _raw_video_path.name
        if _fallback.exists():
            logger.info(f"Resolved video path via fallback: {_fallback}")
            _raw_video_path = _fallback
        else:
            raise FileNotFoundError(f"Video file not found: {_raw_video_path} (also tried {_fallback})")
    video_path = _raw_video_path

    ig_caption = manifest.get("caption", "")
    fb_caption = manifest.get("fb_caption", ig_caption)  # fallback to caption if no fb_caption
    first_comment = manifest.get("first_comment", "")

    logger.info(f"Posting: {manifest['pet_type']} / {manifest['pillar']}")
    logger.info(f"Hook: {manifest['hook'][:80]}")

    if test_mode:
        logger.info("TEST MODE — skipping all posts")
        logger.info(f"Would post: {video_path.name}")
        logger.info(f"Caption: {fb_caption[:100]}...")
        result["status"] = "skipped"
        result["reason"] = "test mode"
    else:
        fb_result = post_video(video_path, fb_caption)
        video_id = fb_result.get("id")
        logger.info(f"Posted to Facebook: video_id={video_id}")

        if first_comment and video_id:
            _post_first_comment(video_id, first_comment)

        result["status"] = "success"
        result["video_id"] = video_id

        if not ig_only:
            try:
                from config import IG_USER_ID
                if IG_USER_ID and video_id:
                    gh_repo = os.getenv("GITHUB_REPOSITORY", "selezai/ai-animal-drama-automation")
                    gh_branch = os.getenv("GITHUB_REF_NAME", "main")
                    try:
                        rel_path = video_path.relative_to(Path(__file__).parent)
                    except ValueError:
                        rel_path = Path("output/video") / video_path.name
                    ig_video_url = f"https://raw.githubusercontent.com/{gh_repo}/{gh_branch}/{rel_path}"
                    logger.info(f"Using GitHub raw URL for IG: {ig_video_url}")
                    # Pass thumbnail as cover if available
                    thumb_raw = manifest.get("thumb_path", "")
                    ig_cover_url = None
                    if thumb_raw:
                        thumb_p = Path(thumb_raw)
                        if not thumb_p.exists():
                            thumb_p = Path(__file__).parent / "output" / "video" / Path(thumb_raw).name
                        if thumb_p.exists():
                            try:
                                thumb_rel = thumb_p.relative_to(Path(__file__).parent)
                            except ValueError:
                                thumb_rel = Path("output/video") / thumb_p.name
                            ig_cover_url = f"https://raw.githubusercontent.com/{gh_repo}/{gh_branch}/{thumb_rel}"
                            logger.info(f"Using thumbnail for IG cover: {ig_cover_url}")
                    ig_result = post_reel(ig_video_url, ig_caption, cover_url=ig_cover_url)
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

    for key in ("video_path", "audio_path", "thumb_path"):
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
    refresh_parser = subparsers.add_parser("refresh-token", help="Refresh the Facebook Page access token")
    refresh_parser.add_argument("--bootstrap", metavar="SHORT_USER_TOKEN",
                                help="One-time setup: exchange a short-lived user token for permanent tokens")

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
        bootstrap_token = getattr(args, "bootstrap", None)
        if bootstrap_token:
            result = bootstrap_from_short_token(bootstrap_token)
        else:
            result = run_token_refresh()
        sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
