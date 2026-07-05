"""
Collect Facebook and Instagram performance snapshots for recently posted videos.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import requests

from config import FB_ACCESS_TOKEN, OUTPUT_DIR
from modules.analytics_health import LATEST_ANALYTICS_RUN_PATH, save_latest_run
from modules.content_scoring import (
    CONTENT_SCORES_PATH,
    POST_METRICS_PATH,
    compute_content_scores,
    load_post_metrics,
    normalize_platform_metrics,
    save_content_scores,
    save_post_metrics,
)
from modules.facebook_poster import GRAPH_API

logger = logging.getLogger(__name__)

SNAPSHOT_BUCKETS = {"24h": 24, "72h": 72, "7d": 168}
LOOKBACK_DAYS = 8


def run_analytics_collection(
    now: datetime | None = None,
    final_dir: Path | None = None,
    post_metrics_path: Path = POST_METRICS_PATH,
    content_scores_path: Path = CONTENT_SCORES_PATH,
    latest_run_path: Path = LATEST_ANALYTICS_RUN_PATH,
    facebook_fetcher: Callable[[str], dict] | None = None,
    instagram_fetcher: Callable[[str], dict] | None = None,
) -> dict:
    """Collect missing performance snapshots and recompute content scores."""
    current = _coerce_datetime(now) or _utc_now()
    final_dir = final_dir or OUTPUT_DIR / "final"
    facebook_fetcher = facebook_fetcher or fetch_facebook_metrics
    instagram_fetcher = instagram_fetcher or fetch_instagram_metrics
    post_metrics_existed = post_metrics_path.exists()
    content_scores_existed = content_scores_path.exists()

    metrics = load_post_metrics(post_metrics_path)
    posts_by_key = {post["post_key"]: post for post in metrics.get("posts", []) if post.get("post_key")}
    result = {
        "run_at": current.isoformat(),
        "posts_seen": 0,
        "snapshots_added": 0,
        "state_changed": False,
        "errors": [],
        "status": "started",
    }

    for post_log in _recent_post_logs(final_dir, current):
        result["posts_seen"] += 1
        post = _post_from_log(post_log)
        if not post:
            continue

        post_key = post["post_key"]
        existing = posts_by_key.get(post_key)
        if existing is None:
            existing = post
        existing.setdefault("snapshots", [])
        posts_by_key[post_key] = existing

    for existing in posts_by_key.values():
        existing.setdefault("snapshots", [])
        posted_at = _parse_datetime(existing.get("posted_at"))
        if not posted_at:
            continue

        for bucket, hours in SNAPSHOT_BUCKETS.items():
            if current < posted_at + timedelta(hours=hours):
                continue
            if existing.get("video_id") and not _has_snapshot(existing, "facebook", bucket):
                _collect_platform_snapshot(
                    existing,
                    "facebook",
                    bucket,
                    current,
                    facebook_fetcher,
                    result,
                )
            if existing.get("ig_media_id") and not _has_snapshot(existing, "instagram", bucket):
                _collect_platform_snapshot(
                    existing,
                    "instagram",
                    bucket,
                    current,
                    instagram_fetcher,
                    result,
                )

    should_write_state = result["snapshots_added"] > 0 or not post_metrics_existed or not content_scores_existed
    if should_write_state:
        metrics["posts"] = sorted(posts_by_key.values(), key=lambda p: p.get("posted_at", ""))
        save_post_metrics(metrics, post_metrics_path)

        scores = compute_content_scores(metrics, now=current)
        save_content_scores(scores, content_scores_path)
        result["state_changed"] = True

    result["status"] = "partial" if result["errors"] else "success"
    save_latest_run(result, latest_run_path)
    return result


def fetch_facebook_metrics(video_id: str, access_token: str = "") -> dict:
    token = access_token or FB_ACCESS_TOKEN
    if not token:
        raise ValueError("FB_ACCESS_TOKEN must be set to fetch Facebook metrics")

    base_fields = [
        "id",
        "length",
        "likes.summary(true)",
        "comments.summary(true)",
        "views",
    ]
    insight_metric = (
        "video_insights.metric("
        "total_video_views,total_video_impressions,"
        "total_video_avg_time_watched,total_video_view_total_time)"
    )
    # Try with watch-time insights first; fall back to basic engagement if the
    # token lacks read_insights permission (returns a 400/#10 error).
    resp = requests.get(
        f"{GRAPH_API}/{video_id}",
        params={"access_token": token, "fields": ",".join(base_fields + [insight_metric])},
        timeout=30,
    )
    if not resp.ok:
        resp = requests.get(
            f"{GRAPH_API}/{video_id}",
            params={"access_token": token, "fields": ",".join(base_fields)},
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()


def fetch_instagram_metrics(ig_media_id: str, access_token: str = "") -> dict:
    token = access_token or FB_ACCESS_TOKEN
    if not token:
        raise ValueError("FB_ACCESS_TOKEN must be set to fetch Instagram metrics")

    # Base media fields always work with instagram_basic.
    base = requests.get(
        f"{GRAPH_API}/{ig_media_id}",
        params={
            "access_token": token,
            "fields": "id,like_count,comments_count,media_type,media_product_type,timestamp",
        },
        timeout=30,
    )
    base.raise_for_status()
    data = base.json()
    merged: dict = {
        "likes": data.get("like_count", 0),
        "comments": data.get("comments_count", 0),
        "media_type": data.get("media_type", ""),
        "media_product_type": data.get("media_product_type", ""),
    }

    # Insights (reach, views, watch-time) require instagram_manage_insights.
    # If the permission is missing this 400s — degrade gracefully to base counts.
    insights = requests.get(
        f"{GRAPH_API}/{ig_media_id}/insights",
        params={
            "access_token": token,
            "metric": "reach,views,saved,shares,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time",
        },
        timeout=30,
    )
    if insights.ok:
        merged["data"] = insights.json().get("data", [])
    else:
        logger.info(f"IG insights unavailable for {ig_media_id} (likely missing instagram_manage_insights); using base counts")
    return merged


def _collect_platform_snapshot(
    post: dict,
    platform: str,
    bucket: str,
    current: datetime,
    fetcher: Callable[[str], dict],
    result: dict,
) -> None:
    media_id_key = "video_id" if platform == "facebook" else "ig_media_id"
    media_id = post.get(media_id_key)
    try:
        raw = fetcher(media_id)
        snapshot = normalize_platform_metrics(platform, raw)
        snapshot.update({
            "platform_media_id": media_id,
            "age_bucket": bucket,
            "collected_at": current.isoformat(),
        })
        post["snapshots"].append(snapshot)
        result["snapshots_added"] += 1
    except Exception as e:
        error = f"{platform} metrics failed for {media_id}: {e}"
        logger.warning(error)
        result["errors"].append(error)


def _recent_post_logs(final_dir: Path, current: datetime) -> list[Path]:
    cutoff = current - timedelta(days=LOOKBACK_DAYS)
    logs = []
    for path in sorted(final_dir.glob("post_*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        posted_at = _parse_datetime(data.get("posted_at")) or _parse_datetime(data.get("run_at"))
        if posted_at is None:
            posted_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if data.get("status") == "success" and posted_at >= cutoff:
            logs.append(path)
    return logs


def _post_from_log(path: Path) -> dict | None:
    data = json.loads(path.read_text())
    video_id = data.get("video_id")
    ig_media_id = data.get("ig_media_id")
    if not video_id and not ig_media_id:
        return None

    post_key = video_id or f"ig:{ig_media_id}" or path.stem
    posted_at = data.get("posted_at") or data.get("run_at") or _posted_at_from_run_id(data.get("run_id"))
    return {
        "post_key": post_key,
        "post_log": str(path),
        "video_id": video_id,
        "ig_media_id": ig_media_id,
        "topic_key": data.get("topic_key", ""),
        "pet_type": data.get("pet_type", ""),
        "pillar": data.get("pillar", ""),
        "topic": data.get("topic", ""),
        "hook": data.get("hook", ""),
        "posted_at": posted_at,
    }


def _has_snapshot(post: dict, platform: str, bucket: str) -> bool:
    return any(
        snapshot.get("platform") == platform and snapshot.get("age_bucket") == bucket
        for snapshot in post.get("snapshots", [])
    )


def _posted_at_from_run_id(run_id: object) -> str:
    if not isinstance(run_id, str):
        return ""
    try:
        return datetime.strptime(run_id, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return ""


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
