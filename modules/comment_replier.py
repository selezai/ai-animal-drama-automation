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

logger = logging.getLogger(__name__)

MAX_REPLIES = 5
REPLIED_DIR = OUTPUT_DIR / "replied"
REPLIED_DIR.mkdir(parents=True, exist_ok=True)

REPLY_SYSTEM_PROMPT = """You write short, friendly replies to Facebook comments on a pet care page.

Rules:
- Warm, conversational South African English
- 1-2 sentences max
- Acknowledge what they said, add a small helpful nudge or fun fact
- End with an invitation to follow or share if natural
- Never sound robotic or copy-paste
- No hashtags in replies
- Use 1 emoji max per reply"""


def get_latest_video_id() -> str | None:
    """Read the most recent post log to get the Facebook video_id."""
    final_dir = OUTPUT_DIR / "final"
    post_logs = sorted(final_dir.glob("post_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

    for log_file in post_logs:
        try:
            data = json.loads(log_file.read_text())
            video_id = data.get("video_id")
            if video_id and data.get("status") == "success":
                logger.info(f"Found latest video_id: {video_id} from {log_file.name}")
                return video_id
        except Exception:
            continue

    return None


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
    """Post a reply to a specific comment."""
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
        logger.info(f"Replied to comment {comment_id}: {message[:60]}...")
        return True
    else:
        logger.warning(f"Failed to reply to {comment_id}: {resp.status_code} {resp.text[:100]}")
        return False


def run_comment_replies(video_id: str | None = None, hook: str = "") -> dict:
    """Main function: fetch unanswered comments and reply to them."""
    result = {
        "run_at": datetime.now().isoformat(),
        "video_id": None,
        "comments_found": 0,
        "replies_sent": 0,
        "status": "started",
    }

    if not video_id:
        video_id = get_latest_video_id()

    if not video_id:
        logger.warning("No video_id found, skipping comment replies")
        result["status"] = "skipped"
        result["reason"] = "no video_id"
        return result

    result["video_id"] = video_id

    if not hook:
        hook = _get_hook_for_video(video_id)

    try:
        comments = fetch_unanswered_comments(video_id)
        result["comments_found"] = len(comments)

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
        result["status"] = "success"

    except Exception as e:
        logger.error(f"Comment reply run failed: {e}", exc_info=True)
        result["status"] = "error"
        result["error"] = str(e)

    log_path = OUTPUT_DIR / "final" / f"replies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(result, indent=2))
    logger.info(f"Reply run complete: {result['replies_sent']} replies sent")
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
