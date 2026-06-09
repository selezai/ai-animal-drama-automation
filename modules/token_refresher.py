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


def self_refresh_page_token() -> str:
    """
    Self-refreshing: uses the current FB_ACCESS_TOKEN (Page token) to get a
    fresh Page token. Works as long as the current token is still valid.
    Call this daily — it costs nothing and keeps the token perpetually fresh.
    """
    resp = requests.get(
        f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}",
        params={"access_token": FB_ACCESS_TOKEN, "fields": "access_token,name"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Self-refresh failed: {data['error']}")
    new_token = data.get("access_token", "")
    if not new_token:
        raise RuntimeError(f"No access_token in response: {data}")
    logger.info(f"Self-refreshed Page token for: {data.get('name')}")
    return new_token


def run_token_refresh() -> dict:
    """
    Self-refreshing flow: uses the current Page token to get a fresh one
    and update the FB_ACCESS_TOKEN GitHub secret. Run this daily — as long
    as the token is used at least once every ~60 days it stays valid forever.
    """
    result = {
        "run_at": datetime.now().isoformat(),
        "status": "started",
    }

    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        result["status"] = "error"
        result["error"] = "FB_ACCESS_TOKEN and FB_PAGE_ID must be set"
        logger.error(result["error"])
        return result

    try:
        logger.info("Self-refreshing Page token...")
        new_token = self_refresh_page_token()

        secret_updated = update_github_secret("FB_ACCESS_TOKEN", new_token)
        logger.info(f"GitHub secret updated: {secret_updated}")

        result["status"] = "success"
        result["secret_updated"] = secret_updated

        log_path = OUTPUT_DIR / "final" / f"token_refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        result["status"] = "error"
        result["error"] = str(e)
        print(f"::error::FB token refresh failed: {e}. Manually update FB_ACCESS_TOKEN secret.")

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_token_refresh()
    print(json.dumps(result, indent=2))
