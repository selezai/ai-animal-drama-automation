#!/usr/bin/env python3
"""
AI Animal Drama — Automated Content Pipeline

Generates one video per run:
  Script (GPT-4o-mini) → Voice (Fish Audio) → Video (fal.ai) → Composite (FFmpeg) → Post (Facebook)

Usage:
    python main.py              # Generate and post one video
    python main.py --test       # Full pipeline, skip Facebook posting
    python main.py --step script  # Run only the script step (for debugging)
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR

from modules.script_generator import generate_script
from modules.voice_generator import generate_voice_from_script
from modules.video_generator import generate_clips_from_script
from modules.video_editor import composite
from modules.facebook_poster import post_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pipeline")


def run_pipeline(test_mode: bool = False) -> dict:
    """
    Execute the full content pipeline once.
    Returns a result dict with status and metadata.
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"run_id": run_id, "status": "started", "steps": {}}

    try:
        # ── 1. Script ──────────────────────────────────────────────
        logger.info("Step 1/5: Generating script...")
        script = generate_script()
        result["steps"]["script"] = {
            "status": "ok",
            "character": script["character"],
            "pillar": script["pillar"],
            "title": script.get("title", ""),
        }

        # ── 2. Voice ──────────────────────────────────────────────
        logger.info("Step 2/5: Generating voiceover (Fish Audio)...")
        audio_path = generate_voice_from_script(script)
        result["steps"]["voice"] = {"status": "ok", "file": audio_path.name}

        # ── 3. Video Clips ────────────────────────────────────────
        logger.info("Step 3/5: Generating video clips (fal.ai)...")
        clip_paths = generate_clips_from_script(script)
        result["steps"]["video"] = {
            "status": "ok",
            "clips": len(clip_paths),
        }

        # ── 4. Composite ─────────────────────────────────────────
        logger.info("Step 4/5: Compositing final video (FFmpeg)...")
        final_video = composite(clip_paths, audio_path, script)
        result["steps"]["composite"] = {
            "status": "ok",
            "file": final_video.name,
            "size_mb": round(final_video.stat().st_size / (1024 * 1024), 2),
        }

        # ── 5. Post ──────────────────────────────────────────────
        if test_mode:
            logger.info("Step 5/5: SKIPPED (test mode)")
            result["steps"]["post"] = {"status": "skipped"}
        else:
            logger.info("Step 5/5: Posting to Facebook (multi-language)...")
            caption = script.get("caption", "")
            translations = {
                "es": script.get("caption_es", ""),
                "pt": script.get("caption_pt", ""),
            }
            fb_result = post_video(final_video, caption, translations)
            result["steps"]["post"] = {
                "status": "ok",
                "video_id": fb_result.get("id"),
                "shareability_score": script.get("shareability_score", "N/A"),
            }

        result["status"] = "success"
        result["final_video"] = str(final_video)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        result["status"] = "failed"
        result["error"] = str(e)

    # Save run log
    log_path = OUTPUT_DIR / "final" / f"run_{run_id}.json"
    log_path.write_text(json.dumps(result, indent=2))
    logger.info(f"Run complete: {result['status']} → {log_path.name}")

    return result


def main():
    parser = argparse.ArgumentParser(description="AI Animal Drama Pipeline")
    parser.add_argument("--test", action="store_true",
                        help="Run full pipeline but skip Facebook posting")
    parser.add_argument("--step", choices=["script", "voice", "video"],
                        help="Run a single step for debugging")
    args = parser.parse_args()

    if args.step == "script":
        script = generate_script()
        print(json.dumps(script, indent=2))
    elif args.step == "voice":
        script = generate_script()
        path = generate_voice_from_script(script)
        print(f"Audio: {path}")
    elif args.step == "video":
        script = generate_script()
        clips = generate_clips_from_script(script)
        print(f"Clips: {[str(c) for c in clips]}")
    else:
        result = run_pipeline(test_mode=args.test)
        sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
