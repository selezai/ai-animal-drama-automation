"""
Queue Manager — manages the ready-to-post video queue.
Queue is a folder of JSON manifest files, each pointing to a rendered video.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import datetime

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)

QUEUE_DIR = OUTPUT_DIR / "queue"


def enqueue(tip: dict, video_path: Path, audio_path: Path, thumb_path: Path | None = None) -> Path:
    """Add a rendered video to the posting queue."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pet_type = tip.get("pet_type", "pet")
    pillar = tip.get("pillar", "tip")

    manifest = {
        "queued_at": datetime.now().isoformat(),
        "status": "pending",
        "pet_type": pet_type,
        "pillar": pillar,
        "hook": tip.get("hook", ""),
        "caption": tip.get("caption", ""),
        "fb_caption": tip.get("fb_caption", tip.get("caption", "")),
        "first_comment": tip.get("first_comment", ""),
        "video_path": str(video_path),
        "audio_path": str(audio_path),
        "thumb_path": str(thumb_path) if thumb_path else "",
        "virality_score": tip.get("virality_score", 0),
    }

    manifest_path = QUEUE_DIR / f"{pet_type}_{pillar}_{ts}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Queued: {manifest_path.name}")
    return manifest_path


def _pending_manifests() -> list[Path]:
    return sorted(
        [f for f in QUEUE_DIR.glob("*.json") if _is_pending(f)],
        key=lambda f: f.stat().st_mtime,
    )


def _read_manifest(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    manifest["_manifest_path"] = str(manifest_path)
    return manifest


def peek_next() -> dict | None:
    """Return the oldest pending manifest without removing it."""
    pending = _pending_manifests()
    if not pending:
        return None
    return _read_manifest(pending[0])


def pop_next() -> dict | None:
    """
    Return the oldest pending manifest without marking it posted.
    Call mark_posted() only after the publish step succeeds.
    Returns None if queue is empty.
    """
    manifest = peek_next()
    if not manifest:
        logger.warning("Queue is empty — nothing to post")
        return None

    logger.info(f"Selected from queue: {Path(manifest['_manifest_path']).name}")
    return manifest


def mark_posted(manifest: dict, posted_fields: dict | None = None) -> Path:
    """Mark a pending manifest as posted after a successful publish."""
    manifest_path = _resolve_manifest_path(manifest)
    if not manifest_path:
        raise FileNotFoundError("Could not find pending queue manifest to mark posted")

    data = json.loads(manifest_path.read_text())
    data["status"] = "posted"
    data["posted_at"] = datetime.now().isoformat()
    if posted_fields:
        data.update({k: v for k, v in posted_fields.items() if v is not None})

    manifest_path.write_text(json.dumps(data, indent=2))
    logger.info(f"Marked posted: {manifest_path.name}")
    return manifest_path


def _resolve_manifest_path(manifest: dict) -> Path | None:
    raw_path = manifest.get("_manifest_path")
    if raw_path:
        path = Path(raw_path)
        if path.exists() and _is_pending(path):
            return path

    queued_at = manifest.get("queued_at")
    video_path = manifest.get("video_path")
    for candidate in _pending_manifests():
        data = json.loads(candidate.read_text())
        if data.get("queued_at") == queued_at and data.get("video_path") == video_path:
            return candidate
    return None


def queue_size() -> int:
    """Return number of pending items in the queue."""
    return len([f for f in QUEUE_DIR.glob("*.json") if _is_pending(f)])


def _is_pending(manifest_path: Path) -> bool:
    try:
        data = json.loads(manifest_path.read_text())
        return data.get("status") == "pending"
    except Exception:
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    size = queue_size()
    print(f"Queue size: {size} pending videos")
    if size > 0:
        next_item = peek_next()
        print(f"Next up: {next_item['pet_type']} / {next_item['pillar']} — {next_item['hook'][:60]}...")
