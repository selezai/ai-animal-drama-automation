"""
Comment Replier - fetches new comments on the latest posted video and
replies to the first batch using Google Gemini Flash (free tier).

Strategy: reply to up to MAX_REPLIES comments per post to signal engagement
to the Facebook algorithm within the first 30 minutes.
"""
from __future__ import annotations
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests
import google.genai as genai

from config import FB_PAGE_ID, FB_ACCESS_TOKEN, GOOGLE_API_KEY, OUTPUT_DIR
try:
    from config import IG_USER_ID
except ImportError:
    IG_USER_ID = ""

logger = logging.getLogger(__name__)

MAX_REPLIES = 5
REPLIED_DIR = OUTPUT_DIR / "replied"
REPLIED_DIR.mkdir(parents=True, exist_ok=True)

REPLY_SYSTEM_PROMPT = """You write short, friendly replies to comments on a pet care social media page.

Rules:
- Warm, conversational South African English
- 1-2 sentences max
- Acknowledge what they said, add a small helpful nudge or fun fact
- End with an invitation to follow or share if natural
- Never sound robotic or copy-paste
- No hashtags in replies
- Use 1 emoji max per reply"""


def get_latest_post_ids() -> tuple[str | None, str | None]:
    """Read the most recent post log (last 24h) and return (fb_video_id, ig_media_id)."""
    from datetime import timezone, timedelta
    final_dir = OUTPUT_DIR / "final"
    post_logs = sorted(final_dir.glob("post_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    for log_file in post_logs:
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            data = json.loads(log_file.read_text())
            if data.get("status") != "success":
                continue
            video_id = data.get("video_id")
            ig_media_id = data.get("ig_media_id")
            if video_id:
                logger.info(f"Found post ids from {log_file.name}: fb={video_id} ig={ig_media_id}")
                return video_id, ig_media_id
        except Exception:
            continue

    logger.info("No successful post log found in the last 24h — skipping comment replies")
    return None, None


def get_latest_video_id() -> str | None:
    """Backwards-compat wrapper — returns FB video_id only."""
    video_id, _ = get_latest_post_ids()
    return video_id


def fetch_unanswered_comments(video_id: str) -> list[dict]:
    """Fetch top-level comments on the video that have not been replied to yet."""
    if not FB_ACCESS_TOKEN:
        raise ValueError("FB_ACCESS_TOKEN not set")

    url = f"https://graph.facebook.com/v21.0/{video_id}/comments"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "id,message,from,created_time,can_reply_privately",
        "limit": 25,
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    comments = resp.json().get("data", [])

    replied_ids = _load_replied_ids(video_id)
    unanswered = [c for c in comments if c["id"] not in replied_ids]

    logger.info(f"Found {len(comments)} comments, {len(unanswered)} unanswered")
    return unanswered[:MAX_REPLIES]


def generate_reply(comment_text: str, hook: str) -> str:
    """Use Gemini Flash to generate a contextual reply."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set")

    client = genai.Client(api_key=GOOGLE_API_KEY)

    prompt = f"""{REPLY_SYSTEM_PROMPT}

Video topic hint: {hook}
Comment to reply to: "{comment_text}"

Write the reply:"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    reply = response.text.strip().strip('"').strip("'")
    return reply


def post_reply(comment_id: str, message: str) -> bool:
    """Post a reply to a specific Facebook comment."""
    if not FB_ACCESS_TOKEN:
        raise ValueError("FB_ACCESS_TOKEN not set")

    url = f"https://graph.facebook.com/v21.0/{comment_id}/comments"
    resp = requests.post(
        url,
        params={"access_token": FB_ACCESS_TOKEN},
        data={"message": message},
        timeout=30,
    )

    if resp.status_code == 200:
        logger.info(f"Replied to FB comment {comment_id}: {message[:60]}...")
        return True
    else:
        logger.warning(f"Failed to reply to FB {comment_id}: {resp.status_code} {resp.text[:100]}")
        return False


def fetch_unanswered_ig_comments(ig_media_id: str) -> list[dict]:
    """Fetch top-level IG comments that haven't been replied to yet."""
    if not FB_ACCESS_TOKEN:
        raise ValueError("FB_ACCESS_TOKEN not set")

    url = f"https://graph.facebook.com/v21.0/{ig_media_id}/comments"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "id,text,username,timestamp",
        "limit": 25,
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    comments = resp.json().get("data", [])

    replied_ids = _load_replied_ids(f"ig_{ig_media_id}")
    unanswered = [c for c in comments if c["id"] not in replied_ids]

    logger.info(f"IG: found {len(comments)} comments, {len(unanswered)} unanswered")
    return unanswered[:MAX_REPLIES]


def post_ig_reply(comment_id: str, message: str) -> bool:
    """Post a reply to a specific Instagram comment."""
    if not FB_ACCESS_TOKEN:
        raise ValueError("FB_ACCESS_TOKEN not set")

    url = f"https://graph.facebook.com/v21.0/{comment_id}/replies"
    resp = requests.post(
        url,
        params={"access_token": FB_ACCESS_TOKEN},
        data={"message": message},
        timeout=30,
    )

    if resp.status_code == 200:
        logger.info(f"Replied to IG comment {comment_id}: {message[:60]}...")
        return True
    else:
        logger.warning(f"Failed to reply to IG {comment_id}: {resp.status_code} {resp.text[:100]}")
        return False


def run_comment_replies(video_id: str | None = None, ig_media_id: str | None = None, hook: str = "") -> dict:
    """Main function: fetch unanswered comments on FB and IG and reply to them."""
    result = {
        "run_at": datetime.now().isoformat(),
        "video_id": None,
        "ig_media_id": None,
        "fb_comments_found": 0,
        "ig_comments_found": 0,
        "replies_sent": 0,
        "status": "started",
    }

    if not video_id:
        video_id, ig_media_id = get_latest_post_ids()

    if not video_id:
        logger.warning("No video_id found, skipping comment replies")
        result["status"] = "skipped"
        result["reason"] = "no video_id"
        return result

    result["video_id"] = video_id
    result["ig_media_id"] = ig_media_id

    if not hook:
        hook = _get_hook_for_video(video_id)

    # --- Facebook replies ---
    try:
        comments = fetch_unanswered_comments(video_id)
        result["fb_comments_found"] = len(comments)
        replied_ids = _load_replied_ids(video_id)

        for comment in comments:
            comment_id = comment["id"]
            comment_text = comment.get("message", "")
            if not comment_text.strip():
                continue
            reply = generate_reply(comment_text, hook)
            success = post_reply(comment_id, reply)
            if success:
                replied_ids.add(comment_id)
                result["replies_sent"] += 1
                time.sleep(2)

        _save_replied_ids(video_id, replied_ids)

    except Exception as e:
        logger.error(f"FB comment reply failed: {e}", exc_info=True)
        result["fb_error"] = str(e)

    # --- Instagram replies ---
    if ig_media_id:
        try:
            ig_comments = fetch_unanswered_ig_comments(ig_media_id)
            result["ig_comments_found"] = len(ig_comments)
            ig_replied_ids = _load_replied_ids(f"ig_{ig_media_id}")

            for comment in ig_comments:
                comment_id = comment["id"]
                comment_text = comment.get("text", "")
                if not comment_text.strip():
                    continue
                reply = generate_reply(comment_text, hook)
                success = post_ig_reply(comment_id, reply)
                if success:
                    ig_replied_ids.add(comment_id)
                    result["replies_sent"] += 1
                    time.sleep(2)

            _save_replied_ids(f"ig_{ig_media_id}", ig_replied_ids)

        except Exception as e:
            logger.error(f"IG comment reply failed: {e}", exc_info=True)
            result["ig_error"] = str(e)
    else:
        logger.info("No ig_media_id available — skipping IG comment replies")

    result["status"] = "success"
    log_path = OUTPUT_DIR / "final" / f"replies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(result, indent=2))
    logger.info(f"Reply run complete: {result['replies_sent']} replies sent (FB + IG)")
    return result


def _load_replied_ids(video_id: str) -> set:
    path = REPLIED_DIR / f"{video_id}.json"
    if path.exists():
        return set(json.loads(path.read_text()))
    return set()


def _save_replied_ids(video_id: str, ids: set) -> None:
    path = REPLIED_DIR / f"{video_id}.json"
    path.write_text(json.dumps(list(ids)))


def _get_hook_for_video(video_id: str) -> str:
    """Try to find the hook text for this video from post logs."""
    final_dir = OUTPUT_DIR / "final"
    for log_file in sorted(final_dir.glob("post_*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            data = json.loads(log_file.read_text())
            if data.get("video_id") == video_id:
                return data.get("hook", "")
        except Exception:
            continue
    return ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_comment_replies()
    print(json.dumps(result, indent=2))
