"""
Token Refresher - exchanges the current FB Page token for a new long-lived one
using the app's client credentials. Run monthly before the 60-day token expires.

Requires: FB_APP_ID, FB_APP_SECRET, FB_ACCESS_TOKEN, FB_PAGE_ID
Updates: writes the new token to the GitHub Actions secret via the GH CLI.
"""
from __future__ import annotations
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

import requests

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)

FB_APP_ID = os.getenv("FB_APP_ID", "")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_LONG_LIVED_USER_TOKEN = os.getenv("FB_LONG_LIVED_USER_TOKEN", "")


def get_long_lived_user_token(short_token: str) -> str:
    """Exchange a short-lived user token for a 60-day long-lived one."""
    resp = requests.get(
        "https://graph.facebook.com/v21.0/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": FB_APP_ID,
            "client_secret": FB_APP_SECRET,
            "fb_exchange_token": short_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Token exchange failed: {data['error']}")
    return data["access_token"]


def get_page_token(user_token: str, page_id: str) -> str:
    """Get a never-expiring Page token from a long-lived user token."""
    resp = requests.get(
        f"https://graph.facebook.com/v21.0/{page_id}",
        params={
            "access_token": user_token,
            "fields": "access_token,name",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Page token fetch failed: {data['error']}")
    logger.info(f"Got page token for: {data.get('name')}")
    return data["access_token"]


def debug_token(token: str) -> dict:
    """Check token expiry and scopes."""
    app_token = f"{FB_APP_ID}|{FB_APP_SECRET}"
    resp = requests.get(
        "https://graph.facebook.com/v21.0/debug_token",
        params={"input_token": token, "access_token": app_token},
        timeout=30,
    )
    return resp.json().get("data", {})


def bootstrap_from_short_token(short_user_token: str) -> dict:
    """
    One-time setup: given a fresh short-lived user token from Graph Explorer,
    produces a long-lived user token and permanent page token, and saves both
    to GitHub Secrets.
    """
    logger.info("Exchanging short-lived user token for 60-day long-lived token...")
    ll_user_token = get_long_lived_user_token(short_user_token)

    logger.info("Getting permanent page token...")
    page_token = get_page_token(ll_user_token, FB_PAGE_ID)

    update_github_secret("FB_LONG_LIVED_USER_TOKEN", ll_user_token)
    update_github_secret("FB_ACCESS_TOKEN", page_token)

    debug = debug_token(page_token)
    logger.info(f"Page token type: {debug.get('type')}, expires: {debug.get('expires_at')}")
    logger.info(f"Long-lived user token stored for future refreshes (valid 60 days)")

    return {
        "status": "success",
        "page_token_type": debug.get("type"),
        "page_token_expires": debug.get("expires_at"),
        "ll_user_token_stored": True,
    }


def update_github_secret(secret_name: str, secret_value: str) -> bool:
    """Update a GitHub Actions secret using the gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "secret", "set", secret_name, "--body", secret_value],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info(f"GitHub secret {secret_name} updated successfully")
            return True
        else:
            logger.error(f"Failed to update secret: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"gh CLI error: {e}")
        return False


def run_token_refresh() -> dict:
    """
    Refresh flow: uses the stored long-lived user token to get a fresh
    permanent Page token and update the FB_ACCESS_TOKEN GitHub secret.
    Falls back to re-exchanging if the user token itself is still valid.
    """
    result = {
        "run_at": datetime.now().isoformat(),
        "status": "started",
    }

    if not all([FB_APP_ID, FB_APP_SECRET, FB_PAGE_ID]):
        missing = [k for k, v in {"FB_APP_ID": FB_APP_ID, "FB_APP_SECRET": FB_APP_SECRET,
                                   "FB_PAGE_ID": FB_PAGE_ID}.items() if not v]
        result["status"] = "error"
        result["error"] = f"Missing env vars: {missing}"
        logger.error(result["error"])
        return result

    if not FB_LONG_LIVED_USER_TOKEN:
        result["status"] = "error"
        result["error"] = (
            "FB_LONG_LIVED_USER_TOKEN secret is not set. "
            "Run bootstrap_from_short_token() once with a fresh user token from "
            "https://developers.facebook.com/tools/explorer to set it up."
        )
        logger.error(result["error"])
        return result

    try:
        # Check if long-lived user token is still valid
        debug_user = debug_token(FB_LONG_LIVED_USER_TOKEN)
        logger.info(f"Long-lived user token type: {debug_user.get('type')}, expires: {debug_user.get('expires_at')}")

        if not debug_user.get("is_valid"):
            result["status"] = "error"
            result["error"] = (
                "Long-lived user token has expired (60-day limit). "
                "Go to https://developers.facebook.com/tools/explorer, generate a new user token, "
                "and run: python main.py refresh-token --bootstrap <new_short_token>"
            )
            logger.error(result["error"])
            # Emit GH Actions error annotation
            print(f"::error::{result['error']}")
            return result

        logger.info("Getting fresh permanent Page token from long-lived user token...")
        new_page_token = get_page_token(FB_LONG_LIVED_USER_TOKEN, FB_PAGE_ID)

        debug_after = debug_token(new_page_token)
        logger.info(f"New page token type: {debug_after.get('type')}, expires: {debug_after.get('expires_at')}")

        secret_updated = update_github_secret("FB_ACCESS_TOKEN", new_page_token)

        result["status"] = "success"
        result["token_type"] = debug_after.get("type")
        result["expires_at"] = debug_after.get("expires_at")
        result["secret_updated"] = secret_updated

        log_path = OUTPUT_DIR / "final" / f"token_refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        result["status"] = "error"
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_token_refresh()
    print(json.dumps(result, indent=2))
