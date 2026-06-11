"""
Topic history and cooldown helpers.

The history file is committed by GitHub Actions, so cooldown state lives in the
repo instead of on a developer machine.
"""
from __future__ import annotations

import json
import logging
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)

TOPIC_HISTORY_PATH = OUTPUT_DIR / "history" / "topics.json"
TOPIC_COOLDOWN_DAYS = 90
TOPIC_RETENTION_DAYS = 540


def normalize_topic(topic: str) -> str:
    """Return a stable slug for exact topic deduplication."""
    normalized = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    return normalized or "untitled"


def make_topic_key(pet_type: str, pillar: str, topic: str) -> str:
    """Build the exact dedup key for a topic."""
    return f"{pet_type.lower()}:{pillar.lower()}:{normalize_topic(topic)}"


def load_topic_history(path: Path = TOPIC_HISTORY_PATH) -> list[dict]:
    """Load topic history. A missing file means no history yet."""
    if not path.exists():
        return []

    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"Topic history must be a list: {path}")
    return data


def save_topic_history(
    history: Iterable[dict],
    path: Path = TOPIC_HISTORY_PATH,
    now: datetime | None = None,
) -> None:
    """Prune and save topic history."""
    pruned = prune_topic_history(list(history), now=now)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pruned, indent=2) + "\n")


def recent_topic_keys(
    history: Iterable[dict],
    cooldown_days: int = TOPIC_COOLDOWN_DAYS,
    now: datetime | None = None,
) -> set[str]:
    """Return topic keys used within the cooldown window."""
    current = _coerce_datetime(now) or _utc_now()
    cutoff = current - timedelta(days=cooldown_days)

    keys = set()
    for record in history:
        used_at = _parse_used_at(record.get("used_at"))
        topic_key = record.get("topic_key")
        if used_at and topic_key and used_at >= cutoff:
            keys.add(topic_key)
    return keys


def select_topic(
    pet_type: str,
    pillar: str,
    topics: list[str],
    history: Iterable[dict] | None = None,
    attempted_topic_keys: set[str] | None = None,
    now: datetime | None = None,
) -> tuple[str, str, bool]:
    """
    Select a topic while respecting recent history and same-batch attempts.

    Returns (topic, topic_key, reused_due_to_exhaustion).
    """
    if not topics:
        raise ValueError(f"No topics configured for {pet_type}/{pillar}")

    history_list = list(history or [])
    attempted = attempted_topic_keys or set()
    blocked_keys = recent_topic_keys(history_list, now=now) | attempted

    keyed_topics = [(topic, make_topic_key(pet_type, pillar, topic)) for topic in topics]
    eligible = [(topic, key) for topic, key in keyed_topics if key not in blocked_keys]
    if eligible:
        topic, topic_key = random.choice(eligible)
        return topic, topic_key, False

    topic, topic_key = _oldest_topic(pet_type, pillar, keyed_topics, history_list)
    return topic, topic_key, True


def record_topic_use(
    tip: dict,
    video_path: Path | None = None,
    manifest_path: Path | None = None,
    path: Path = TOPIC_HISTORY_PATH,
    now: datetime | None = None,
) -> dict:
    """Append one successfully queued tip to topic history."""
    pet_type = tip.get("pet_type", "")
    pillar = tip.get("pillar", "")
    topic = tip.get("topic", "")
    if not pet_type or not pillar or not topic:
        raise ValueError("tip must include pet_type, pillar, and topic")

    topic_key = tip.get("topic_key") or make_topic_key(pet_type, pillar, topic)
    current = _coerce_datetime(now) or _utc_now()
    record = {
        "topic_key": topic_key,
        "pet_type": pet_type,
        "pillar": pillar,
        "topic": topic,
        "used_at": current.isoformat(),
        "hook": tip.get("hook", ""),
        "virality_score": tip.get("virality_score", 0),
    }
    if video_path:
        record["video_path"] = str(video_path)
    if manifest_path:
        record["manifest_path"] = str(manifest_path)

    history = load_topic_history(path)
    history.append(record)
    save_topic_history(history, path=path, now=current)
    logger.info(f"Recorded topic history: {topic_key}")
    return record


def prune_topic_history(
    history: Iterable[dict],
    retention_days: int = TOPIC_RETENTION_DAYS,
    now: datetime | None = None,
) -> list[dict]:
    """Drop records older than the retention window."""
    current = _coerce_datetime(now) or _utc_now()
    cutoff = current - timedelta(days=retention_days)

    pruned = []
    for record in history:
        used_at = _parse_used_at(record.get("used_at"))
        if used_at is None or used_at >= cutoff:
            pruned.append(record)
    return pruned


def _oldest_topic(
    pet_type: str,
    pillar: str,
    keyed_topics: list[tuple[str, str]],
    history: list[dict],
) -> tuple[str, str]:
    oldest_time = None
    oldest = keyed_topics[0]

    for topic, topic_key in keyed_topics:
        last_used = _last_used_at(topic_key, history)
        if last_used is None:
            return topic, topic_key
        if oldest_time is None or last_used < oldest_time:
            oldest_time = last_used
            oldest = (topic, topic_key)

    logger.warning(f"Topic cooldown exhausted for {pet_type}/{pillar}; reusing oldest topic")
    return oldest


def _last_used_at(topic_key: str, history: list[dict]) -> datetime | None:
    latest = None
    for record in history:
        if record.get("topic_key") != topic_key:
            continue
        used_at = _parse_used_at(record.get("used_at"))
        if used_at and (latest is None or used_at > latest):
            latest = used_at
    return latest


def _parse_used_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return _coerce_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _coerce_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
