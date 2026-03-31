"""
Facebook Poster — Meta Graph API (FREE)
Uploads video natively to a Facebook Page (native = 478% more shares than links).
"""
import json
import logging
import requests
from pathlib import Path

from config import FB_PAGE_ID, FB_ACCESS_TOKEN

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v21.0"


def _check_creds(page_id: str, token: str) -> None:
    if not page_id or not token:
        raise ValueError(
            "FB_PAGE_ID and FB_ACCESS_TOKEN must be set. "
            "See README.md for how to get them."
        )


def post_video(video_path: Path, caption: str,
               caption_translations: dict = None,
               page_id: str = "", access_token: str = "") -> dict:
    """
    Upload and publish a video natively to a Facebook Page.
    Uses the simple direct-upload method (works for files <1 GB).
    
    Args:
        video_path: Path to video file
        caption: Primary caption (English)
        caption_translations: Optional dict like {"es": "...", "pt": "..."}
                            Facebook shows appropriate language to each user
    """
    page_id = page_id or FB_PAGE_ID
    access_token = access_token or FB_ACCESS_TOKEN
    _check_creds(page_id, access_token)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Build multi-language caption if translations provided
    # Format: English\n---\nEspañol: ...\n---\nPortuguês: ...
    # Facebook's algorithm shows the right language to each user
    full_caption = caption
    if caption_translations:
        if "es" in caption_translations:
            full_caption += f"\n\n🇪🇸 {caption_translations['es']}"
        if "pt" in caption_translations:
            full_caption += f"\n\n🇧🇷 {caption_translations['pt']}"

    size_mb = video_path.stat().st_size / (1024 * 1024)
    logger.info(f"Uploading {video_path.name} ({size_mb:.1f} MB) to page {page_id}")

    with open(video_path, "rb") as f:
        resp = requests.post(
            f"{GRAPH_API}/{page_id}/videos",
            params={"access_token": access_token},
            data={"description": full_caption},
            files={"source": f},
            timeout=120,
        )

    resp.raise_for_status()
    result = resp.json()

    logger.info(f"Posted to Facebook: video_id={result.get('id')}")
    return result


def post_video_resumable(video_path: Path, caption: str,
                         page_id: str = "", access_token: str = "") -> dict:
    """
    Resumable upload for larger videos. Three-phase protocol.
    Use this if simple upload fails on larger files.
    """
    page_id = page_id or FB_PAGE_ID
    access_token = access_token or FB_ACCESS_TOKEN
    _check_creds(page_id, access_token)

    file_size = video_path.stat().st_size
    url = f"{GRAPH_API}/{page_id}/videos"

    # Phase 1: Start
    start = requests.post(url, params={
        "access_token": access_token,
        "upload_phase": "start",
        "file_size": file_size,
    }, timeout=30)
    start.raise_for_status()
    session = start.json()

    upload_session_id = session["upload_session_id"]

    # Phase 2: Transfer
    with open(video_path, "rb") as f:
        transfer = requests.post(url, params={
            "access_token": access_token,
            "upload_phase": "transfer",
            "upload_session_id": upload_session_id,
            "start_offset": 0,
        }, files={"video_file_chunk": f}, timeout=120)
    transfer.raise_for_status()

    # Phase 3: Finish
    finish = requests.post(url, params={
        "access_token": access_token,
        "upload_phase": "finish",
        "upload_session_id": upload_session_id,
        "description": caption,
    }, timeout=30)
    finish.raise_for_status()

    result = finish.json()
    logger.info(f"Resumable upload complete: {result}")
    return result


# ── One-time setup helpers (run manually) ──────────────────────────

def exchange_for_long_lived_token(short_token: str,
                                  app_id: str, app_secret: str) -> str:
    """Exchange a short-lived user token for a 60-day long-lived token."""
    resp = requests.get(f"{GRAPH_API}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })
    resp.raise_for_status()
    token = resp.json()["access_token"]
    logger.info("Long-lived user token obtained (valid ~60 days)")
    return token


def get_page_token(user_token: str, page_id: str) -> str:
    """
    Derive a page access token from a long-lived user token.
    Page tokens derived this way never expire.
    """
    resp = requests.get(f"{GRAPH_API}/{page_id}", params={
        "fields": "access_token",
        "access_token": user_token,
    })
    resp.raise_for_status()
    token = resp.json()["access_token"]
    logger.info("Page access token obtained (never expires)")
    return token


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if FB_PAGE_ID and FB_ACCESS_TOKEN:
        resp = requests.get(f"{GRAPH_API}/{FB_PAGE_ID}", params={
            "fields": "name,fan_count",
            "access_token": FB_ACCESS_TOKEN,
        })
        resp.raise_for_status()
        print(f"Connected: {json.dumps(resp.json(), indent=2)}")
    else:
        print("Set FB_PAGE_ID and FB_ACCESS_TOKEN to test.")
