"""
Balanced performance scoring for pet-tip content.

The score file is intentionally small and conservative: V1 only adjusts
pet_type x pillar cells, never individual topics or prompts.
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from config import CONTENT_PILLARS, OUTPUT_DIR, PET_TYPES

ANALYTICS_DIR = OUTPUT_DIR / "analytics"
POST_METRICS_PATH = ANALYTICS_DIR / "post_metrics.json"
CONTENT_SCORES_PATH = ANALYTICS_DIR / "content_scores.json"

MIN_SAMPLE_SIZE = 5
MIN_MULTIPLIER = 0.75
MAX_MULTIPLIER = 1.25
STALE_AFTER_DAYS = 14
FULL_DECAY_DAYS = 28

# All videos are ~30s; used as the retention denominator when the platform
# API doesn't expose a clip length (e.g. Instagram media fields).
DEFAULT_VIDEO_LENGTH_SECS = 30.0


def cell_key(pet_type: str, pillar: str) -> str:
    return f"{pet_type}:{pillar}"


def default_content_scores(now: datetime | None = None) -> dict:
    current = _coerce_datetime(now) or _utc_now()
    return {
        "last_updated": current.isoformat(),
        "min_sample_size": MIN_SAMPLE_SIZE,
        "multiplier_bounds": {"min": MIN_MULTIPLIER, "max": MAX_MULTIPLIER},
        "cells": {
            cell_key(pet_type, pillar): {
                "sample_size": 0,
                "score": 0.0,
                "multiplier": 1.0,
            }
            for pet_type in PET_TYPES
            for pillar in CONTENT_PILLARS.keys()
        },
    }


def load_post_metrics(path: Path = POST_METRICS_PATH) -> dict:
    if not path.exists():
        return {"posts": []}
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return {"posts": data}
    if not isinstance(data, dict):
        raise ValueError(f"Post metrics must be an object or list: {path}")
    data.setdefault("posts", [])
    return data


def save_post_metrics(data: dict, path: Path = POST_METRICS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_content_scores(path: Path = CONTENT_SCORES_PATH) -> dict:
    if not path.exists():
        return default_content_scores()
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Content scores must be an object: {path}")
    data.setdefault("cells", {})
    return data


def save_content_scores(data: dict, path: Path = CONTENT_SCORES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def normalize_platform_metrics(platform: str, raw_metrics: dict | None) -> dict:
    """Normalize FB/IG metric shapes into the common analytics schema."""
    raw = raw_metrics or {}
    # Watch-time fields are reported in milliseconds by the Graph API.
    avg_watch_ms = _metric_value(raw, [
        "ig_reels_avg_watch_time",
        "total_video_avg_time_watched",
    ])
    total_watch_ms = _metric_value(raw, [
        "ig_reels_video_view_total_time",
        "total_video_view_total_time",
    ])
    video_length_secs = float(_metric_value(raw, ["video_length_secs", "length"]) or 0.0)
    length_for_retention = video_length_secs or DEFAULT_VIDEO_LENGTH_SECS
    avg_watch_secs = round(avg_watch_ms / 1000.0, 3) if avg_watch_ms else 0.0
    retention = 0.0
    if length_for_retention > 0 and avg_watch_secs > 0:
        retention = round(min(avg_watch_secs / length_for_retention, 1.0), 4)
    return {
        "platform": platform,
        "views": int(_metric_value(raw, ["views", "plays", "video_views", "total_video_views"])),
        "reach": int(_metric_value(raw, ["reach", "impressions", "total_video_impressions"])),
        "likes": int(_metric_value(raw, [
            "likes",
            "like_count",
            "reactions",
            "total_reactions",
            "total_video_reactions_by_type_total",
        ])),
        "comments": int(_metric_value(raw, ["comments", "comment_count"])),
        "shares": int(_metric_value(raw, ["shares", "share_count"])),
        "saves": int(_metric_value(raw, ["saves", "saved"])),
        "avg_watch_secs": avg_watch_secs,
        "total_watch_secs": round(total_watch_ms / 1000.0, 3) if total_watch_ms else 0.0,
        "video_length_secs": round(video_length_secs, 3),
        "retention": retention,
        "raw_metrics": raw,
    }


def score_snapshot(metrics: dict) -> float:
    """Balanced score using rates where possible."""
    views = max(0, float(metrics.get("views") or 0))
    reach = max(0, float(metrics.get("reach") or 0))
    denominator = max(reach, views, 1.0)

    view_rate = min(views / denominator, 3.0)
    share_rate = min(max(0, float(metrics.get("shares") or 0)) / denominator, 1.0)
    comment_rate = min(max(0, float(metrics.get("comments") or 0)) / denominator, 1.0)
    save_rate = min(max(0, float(metrics.get("saves") or 0)) / denominator, 1.0)
    like_rate = min(max(0, float(metrics.get("likes") or 0)) / denominator, 1.0)
    retention = min(max(0.0, float(metrics.get("retention") or 0.0)), 1.0)

    return round(
        (retention * 400.0)
        + (view_rate * 20.0)
        + (share_rate * 320.0)
        + (comment_rate * 300.0)
        + (save_rate * 220.0)
        + (like_rate * 90.0),
        4,
    )


def compute_content_scores(post_metrics: dict, now: datetime | None = None) -> dict:
    current = _coerce_datetime(now) or _utc_now()
    cell_scores: dict[str, list[float]] = {
        cell_key(pet_type, pillar): []
        for pet_type in PET_TYPES
        for pillar in CONTENT_PILLARS.keys()
    }

    for post in post_metrics.get("posts", []):
        key = cell_key(str(post.get("pet_type", "")), str(post.get("pillar", "")))
        if key not in cell_scores:
            continue
        post_score = _score_post(post)
        if post_score is not None:
            cell_scores[key].append(post_score)

    all_scores = [score for scores in cell_scores.values() for score in scores]
    global_average = sum(all_scores) / len(all_scores) if all_scores else 0.0
    result = default_content_scores(now=current)
    result["global_average_score"] = round(global_average, 4)

    for key, scores in cell_scores.items():
        sample_size = len(scores)
        average = sum(scores) / sample_size if scores else 0.0
        multiplier = 1.0
        if sample_size >= MIN_SAMPLE_SIZE and global_average > 0:
            multiplier = math.sqrt(max(average, 0.0) / global_average)
            multiplier = min(MAX_MULTIPLIER, max(MIN_MULTIPLIER, multiplier))

        result["cells"][key] = {
            "sample_size": sample_size,
            "score": round(average, 4),
            "multiplier": round(multiplier, 4),
        }

    return result


def content_multipliers(
    path: Path = CONTENT_SCORES_PATH,
    now: datetime | None = None,
) -> dict[str, float]:
    """Return conservative cell multipliers, respecting flag and staleness."""
    if not _analytics_weighting_enabled(path):
        return {}

    scores = apply_stale_decay(load_content_scores(path), now=now)
    return {
        key: float(cell.get("multiplier", 1.0))
        for key, cell in scores.get("cells", {}).items()
        if int(cell.get("sample_size", 0)) >= MIN_SAMPLE_SIZE
    }


def apply_stale_decay(scores: dict, now: datetime | None = None) -> dict:
    current = _coerce_datetime(now) or _utc_now()
    last_updated = _parse_datetime(scores.get("last_updated"))
    if not last_updated:
        return scores

    age_days = (current - last_updated).total_seconds() / 86400
    if age_days <= STALE_AFTER_DAYS:
        return scores

    decay = max(0.0, 1.0 - ((age_days - STALE_AFTER_DAYS) / (FULL_DECAY_DAYS - STALE_AFTER_DAYS)))
    decayed = json.loads(json.dumps(scores))
    for cell in decayed.get("cells", {}).values():
        multiplier = float(cell.get("multiplier", 1.0))
        cell["multiplier"] = round(1.0 + ((multiplier - 1.0) * decay), 4)
    return decayed


def _score_post(post: dict) -> float | None:
    snapshots = post.get("snapshots", [])
    if not snapshots:
        return None

    latest_by_platform: dict[str, dict] = {}
    for snapshot in snapshots:
        platform = str(snapshot.get("platform", "unknown"))
        existing = latest_by_platform.get(platform)
        if not existing or _bucket_rank(snapshot.get("age_bucket")) > _bucket_rank(existing.get("age_bucket")):
            latest_by_platform[platform] = snapshot

    scores = [score_snapshot(snapshot) for snapshot in latest_by_platform.values()]
    return sum(scores) / len(scores) if scores else None


def _metric_value(raw: dict, keys: list[str]) -> float:
    for key in keys:
        value = _direct_value(raw, key)
        if value is not None:
            return float(value)
    insights = []
    if isinstance(raw.get("data"), list):
        insights = raw.get("data", [])
    elif isinstance(raw.get("insights"), dict):
        insights = raw.get("insights", {}).get("data", [])
    elif isinstance(raw.get("video_insights"), dict):
        insights = raw.get("video_insights", {}).get("data", [])
    for item in insights or []:
        name = item.get("name")
        if name not in keys:
            continue
        values = item.get("values") or []
        if values:
            value = values[-1].get("value", 0)
            if isinstance(value, dict):
                return float(sum(v for v in value.values() if isinstance(v, (int, float))))
            return float(value or 0)
    return 0.0


def _direct_value(raw: dict, key: str) -> int | float | None:
    value = raw.get(key)
    if isinstance(value, dict):
        if "count" in value:
            return value["count"]
        summary = value.get("summary")
        if isinstance(summary, dict) and "total_count" in summary:
            return summary["total_count"]
    if isinstance(value, (int, float)):
        return value
    return None


def _bucket_rank(bucket: object) -> int:
    return {"24h": 1, "72h": 2, "7d": 3}.get(str(bucket), 0)


def _analytics_weighting_enabled(path: Path) -> bool:
    raw = os.getenv("ANALYTICS_WEIGHTING_ENABLED", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    return path.exists()


def _parse_datetime(value: object) -> datetime | None:
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
