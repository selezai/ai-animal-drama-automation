"""
Get Facebook Page Access Token — standalone helper script.

This script walks you through getting a never-expiring Page Access Token
without needing the Graph API Explorer.

Usage:
    python get_fb_token.py

You'll need:
    1. Your Facebook App ID (from developers.facebook.com → My Apps → Drama Paws)
    2. Your Facebook App Secret (from App Settings → Basic)
"""
import webbrowser
import requests
import sys

GRAPH_API = "https://graph.facebook.com/v21.0"


def main():
    print("\n=== Facebook Page Access Token Generator ===\n")

    # Step 1: Get App credentials
    app_id = input("Enter your App ID: ").strip()
    app_secret = input("Enter your App Secret: ").strip()

    if not app_id or not app_secret:
        print("Error: App ID and App Secret are required.")
        sys.exit(1)

    # Step 2: Open browser for user to authorize
    permissions = "pages_manage_posts,pages_read_engagement,pages_show_list,publish_video"
    redirect_uri = "https://localhost/"
    auth_url = (
        f"https://www.facebook.com/v21.0/dialog/oauth?"
        f"client_id={app_id}&redirect_uri={redirect_uri}"
        f"&scope={permissions}&response_type=token"
    )

    print(f"\nOpening browser for authorization...")
    print(f"If it doesn't open, visit this URL:\n{auth_url}\n")
    webbrowser.open(auth_url)

    print("After authorizing, you'll be redirected to a URL like:")
    print("  https://localhost/#access_token=EAAG...&...")
    print("\nCopy the ENTIRE redirect URL from your browser's address bar.")
    print("(The page will show an error - that's expected. Just copy the URL.)\n")

    redirect_url = input("Paste the redirect URL here: ").strip()

    # Extract token from URL fragment
    if "access_token=" not in redirect_url:
        print("Error: Could not find access_token in the URL.")
        print("Make sure you copied the full URL including the #access_token= part.")
        sys.exit(1)

    # Parse the token from the URL fragment
    fragment = redirect_url.split("access_token=")[1]
    short_token = fragment.split("&")[0]

    print(f"\nShort-lived token obtained: {short_token[:20]}...")

    # Step 3: Exchange for long-lived token
    print("\nExchanging for long-lived token...")
    resp = requests.get(f"{GRAPH_API}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })

    if resp.status_code != 200:
        print(f"Error: {resp.json()}")
        sys.exit(1)

    long_token = resp.json()["access_token"]
    print(f"Long-lived user token: {long_token[:20]}...")

    # Step 4: Get list of pages
    print("\nFetching your pages...")
    resp = requests.get(f"{GRAPH_API}/me/accounts", params={
        "access_token": long_token,
    })

    if resp.status_code != 200:
        print(f"Error: {resp.json()}")
        sys.exit(1)

    pages = resp.json().get("data", [])

    if not pages:
        print("No pages found. Make sure you granted page permissions.")
        sys.exit(1)

    # Step 5: Select page
    print("\nYour pages:")
    for i, page in enumerate(pages):
        print(f"  {i + 1}. {page['name']} (ID: {page['id']})")

    if len(pages) == 1:
        selected = pages[0]
        print(f"\nUsing: {selected['name']}")
    else:
        choice = int(input(f"\nSelect page (1-{len(pages)}): ")) - 1
        selected = pages[choice]

    page_id = selected["id"]
    page_token = selected["access_token"]

    # Page tokens derived from long-lived user tokens never expire
    print(f"\n{'='*60}")
    print(f"SUCCESS! Here are your credentials:\n")
    print(f"FB_PAGE_ID={page_id}")
    print(f"FB_ACCESS_TOKEN={page_token}")
    print(f"\n{'='*60}")
    print(f"\nThis page token NEVER EXPIRES.")
    print(f"\nTo set as GitHub Secrets, run:")
    print(f'  gh secret set FB_PAGE_ID --body "{page_id}"')
    print(f'  gh secret set FB_ACCESS_TOKEN --body "{page_token}"')


if __name__ == "__main__":
    main()
