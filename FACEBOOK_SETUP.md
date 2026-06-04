# Facebook Page Setup Guide

This guide gets you a `FB_PAGE_ID` and a **never-expiring** `FB_ACCESS_TOKEN` for your pet tips page.

---

## Step 1: Create a Facebook App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **My Apps → Create App**
3. Select **Other → Business**
4. Name it `Pet Tips Automation` (or anything)
5. After creation, note your **App ID** and **App Secret** (Settings → Basic)

---

## Step 2: Add the Pages API Product

1. In your app dashboard, click **Add Product**
2. Find **Facebook Login** → click **Set Up**
3. Also add **Pages API** if listed

---

## Step 3: Get a Short-Lived User Token

1. Go to [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. Select your app from the dropdown
3. Click **Generate Access Token**
4. Add these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
5. Click **Generate Access Token** and log in when prompted
6. Copy the token (valid for ~1 hour only — we'll exchange it next)

---

## Step 4: Exchange for a 60-Day Long-Lived Token

Run this in your terminal (replace values):

```bash
curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
```

Copy the `access_token` from the response. It's valid for 60 days.

---

## Step 5: Get a Never-Expiring Page Token

Run the helper script (uses your long-lived user token):

```bash
python3 get_fb_token.py
```

Or run manually (replace values):

```bash
curl "https://graph.facebook.com/v21.0/YOUR_PAGE_ID?fields=access_token&access_token=YOUR_60DAY_USER_TOKEN"
```

The `access_token` in the response is your **Page Token** — it **never expires** as long as your app remains active.

---

## Step 6: Get Your Page ID

1. Go to your Facebook Page
2. Click **About** (or scroll down on the page)
3. Scroll to the bottom — **Page ID** is listed there

Or run:
```bash
curl "https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_USER_TOKEN"
```

This lists all pages you manage with their IDs.

---

## Step 7: Add to .env and GitHub Secrets

**.env** (for local testing):
```
FB_PAGE_ID=123456789012345
FB_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**GitHub Secrets** (for automated posting):
1. Go to your repo → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `FB_PAGE_ID` — your page ID
   - `FB_ACCESS_TOKEN` — the never-expiring page token
   - `OPENAI_API_KEY` — from openai.com
   - `ELEVENLABS_API_KEY` — from elevenlabs.io
   - `ELEVENLABS_VOICE_ID` — `TX3LPaxmHKxFdv7VOQHJ` (or your preferred voice)

---

## Token Maintenance

- **Page tokens derived from long-lived user tokens never expire** — you set it once
- If the token ever stops working, repeat Steps 3–5
- Check token validity anytime: [developers.facebook.com/tools/debug/accesstoken](https://developers.facebook.com/tools/debug/accesstoken)

---

## Test Your Setup

```bash
python3 -c "
from modules.facebook_poster import FB_PAGE_ID, FB_ACCESS_TOKEN
import requests
resp = requests.get(f'https://graph.facebook.com/v21.0/{FB_PAGE_ID}', params={'fields': 'name,fan_count', 'access_token': FB_ACCESS_TOKEN})
print(resp.json())
"
```

Expected: `{'name': 'Your Page Name', 'fan_count': 0, 'id': '...'}`
