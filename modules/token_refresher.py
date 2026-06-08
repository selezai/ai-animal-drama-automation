"""
Token Refresher - exchanges the current FB Page token for a new long-lived one
using the app's client credentials. Run monthly before the 60-day token expires.

Requires: FB_APP_ID, FB_APP_SECRET, FB_ACCESS_TOKEN, FB_PAGE_ID
Updates: writes the new token to the GitHub Actions secret via the GH CLI.
"""
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
    resp = requests.get(
        "https://graph.facebook.com/v21.0/debug_token",
        params={"input_token": token, "access_token": token},
        timeout=30,
    )
    return resp.json().get("data", {})


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
    """Full refresh flow: exchange token, get page token, update GitHub secret."""
    result = {
        "run_at": datetime.now().isoformat(),
        "status": "started",
    }

    if not all([FB_APP_ID, FB_APP_SECRET, FB_ACCESS_TOKEN, FB_PAGE_ID]):
        missing = [k for k, v in {"FB_APP_ID": FB_APP_ID, "FB_APP_SECRET": FB_APP_SECRET,
                                   "FB_ACCESS_TOKEN": FB_ACCESS_TOKEN, "FB_PAGE_ID": FB_PAGE_ID}.items() if not v]
        result["status"] = "error"
        result["error"] = f"Missing env vars: {missing}"
        logger.error(result["error"])
        return result

    try:
        debug_before = debug_token(FB_ACCESS_TOKEN)
        logger.info(f"Current token type: {debug_before.get('type')}, expires: {debug_before.get('expires_at')}")

        logger.info("Exchanging for long-lived user token...")
        long_lived_user_token = get_long_lived_user_token(FB_ACCESS_TOKEN)

        logger.info("Getting never-expiring page token...")
        new_page_token = get_page_token(long_lived_user_token, FB_PAGE_ID)

        debug_after = debug_token(new_page_token)
        logger.info(f"New token type: {debug_after.get('type')}, expires: {debug_after.get('expires_at')}")

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
