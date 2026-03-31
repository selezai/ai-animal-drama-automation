# Manual Setup Tasks

Complete these one-time setup tasks before the automation can run.

---

## 1. OpenAI API Key (Script Generation)

**Time:** 5 minutes  
**Cost:** ~$5 minimum deposit (lasts months)

1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account or sign in
3. Go to **Settings → Billing** → Add payment method → Add $5 credit
4. Go to **API Keys** → **Create new secret key**
5. Name it "AI Animal Drama"
6. Copy the key (starts with `sk-`)
7. **Save it** — you won't see it again

**Add to GitHub Secrets as:** `OPENAI_API_KEY`

---

## 2. ElevenLabs API Key + Voices (Voice Generation)

**Time:** 15 minutes  
**Cost:** Free for testing, $5/month (Starter) for commercial use

### 2.1 Get API Key
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Create account (Free tier works for testing)
3. Go to **Developers** (left sidebar) → **API Keys** → **Create Key**
4. Give it a name, enable "Text to Speech" access
5. Copy your API key

**Free tier:** 10k credits/month (~23 videos). No commercial license.  
**Starter ($5/mo):** 30k credits/month (~46 videos). Includes commercial license.

> ⚠️ **For monetized Facebook content**, upgrade to Starter for the commercial license.

**Add to GitHub Secrets as:** `ELEVENLABS_API_KEY`

### 2.2 Create/Select Character Voices
You need 4 voice IDs — one for each character.

**Option A: Use existing voices**
1. Go to **Voice Library** → Browse voices
2. Find voices that match each character:
   - **Charlie:** Warm, friendly male voice
   - **Milo:** Dry, witty male voice  
   - **Bella:** Energetic female voice
   - **Duke:** Deep, gravelly male voice
3. Click **Add to My Voices** for each
4. Go to **My Voices** → Click each voice → Copy the **Voice ID**

**Option B: Clone custom voices**
1. Go to **My Voices** → **Add Voice** → **Instant Voice Clone**
2. Upload a 30-second audio sample of the voice style you want
3. Name it (e.g., "Charlie - Warm Dog")
4. Copy the Voice ID

**Add to GitHub Secrets:**
```
ELEVENLABS_VOICE_CHARLIE = voice_id_here
ELEVENLABS_VOICE_MILO = voice_id_here
ELEVENLABS_VOICE_BELLA = voice_id_here
ELEVENLABS_VOICE_DUKE = voice_id_here
```

---

## 3. Luma Labs API Key (Video Generation)

**Time:** 5 minutes  
**Cost:** Pay-per-use (~$14.40/month for 60 videos)

1. Go to [lumalabs.ai](https://lumalabs.ai)
2. Create account
3. Go to [lumalabs.ai/api](https://lumalabs.ai/api) → **Get Started**
4. Add payment method
5. Go to **Dashboard** → **API Keys** → Create key
6. Copy the API key

**Add to GitHub Secrets as:** `LUMA_API_KEY`

---

## 4. Facebook Page + Access Token (Posting)

**Time:** 30 minutes  
**Cost:** Free

### 4.1 Create Facebook Page
1. Go to [facebook.com/pages/create](https://facebook.com/pages/create)
2. Choose **Artist, Band or Public Figure** or **Entertainment**
3. Name it (e.g., "Animal Drama Stories")
4. Add profile picture and cover photo
5. Note your **Page ID** (in the URL or Page Settings → Page Info)

### 4.2 Create Meta Developer App
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Register as a developer (verify with credit card if SMS fails)
3. Click **My Apps** → **Create App**
4. Select use case: **Other** → **Next**
5. Select app type: **Business** → **Next**
6. Name it "Drama Paws Automation"
7. Complete setup

### 4.3 Get Access Token
1. In your app dashboard, go to **Tools** → **Graph API Explorer**
2. Select your app from the **Meta App** dropdown
3. Under **Permissions**, add:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
   - `publish_video` (for video uploads)
4. Click **Generate Access Token**
5. Authorize and select your Facebook Page when prompted

### 4.4 Exchange for Long-Lived Token
The token you just got expires in 1 hour. Exchange it:

```bash
# Run this locally (replace values)
python -c "
from modules.facebook_poster import exchange_for_long_lived_token
token = exchange_for_long_lived_token(
    'YOUR_SHORT_TOKEN',
    'YOUR_APP_ID',
    'YOUR_APP_SECRET'
)
print(f'Long-lived token: {token}')
"
```

Find your App ID and App Secret in **App Settings → Basic**.

### 4.5 Get Page Access Token
```bash
python -c "
from modules.facebook_poster import get_page_token
token = get_page_token('YOUR_LONG_LIVED_USER_TOKEN', 'YOUR_PAGE_ID')
print(f'Page token: {token}')
"
```

This page token **never expires**.

**Add to GitHub Secrets:**
```
FB_PAGE_ID = your_page_id
FB_ACCESS_TOKEN = your_page_access_token
```

---

## 5. Add All Secrets to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

| Secret Name | Value |
|-------------|-------|
| `OPENAI_API_KEY` | sk-... |
| `ELEVENLABS_API_KEY` | your_key |
| `ELEVENLABS_VOICE_CHARLIE` | voice_id |
| `ELEVENLABS_VOICE_MILO` | voice_id |
| `ELEVENLABS_VOICE_BELLA` | voice_id |
| `ELEVENLABS_VOICE_DUKE` | voice_id |
| `LUMA_API_KEY` | your_key |
| `FB_PAGE_ID` | your_page_id |
| `FB_ACCESS_TOKEN` | your_page_token |

---

## 6. Test the Pipeline

### Local Test (Recommended First)
```bash
# Clone repo and install dependencies
git clone https://github.com/YOUR_USERNAME/ai-animal-drama-automation.git
cd ai-animal-drama-automation
pip install -r requirements.txt

# Create .env file with your keys
cp .env.example .env
# Edit .env and add all your keys

# Run test (generates video but doesn't post)
python main.py --test
```

### GitHub Actions Test
1. Go to **Actions** tab in your repo
2. Click **Generate & Post AI Animal Drama**
3. Click **Run workflow** → **Run workflow**
4. Watch the logs

---

## 7. Ongoing Manual Tasks

### Daily (15-30 min)
- **Reply to comments** — This is the ONE manual task that matters. Facebook's algorithm heavily weights creator replies. Automated replies get flagged as spam.

### Weekly (10 min)
- **Spot-check video quality** — Watch 2-3 recent videos. Delete any with obvious artifacts.
- **Check engagement metrics** — Are shares increasing? Adjust pillar weights if needed.

### Every 60 Days
- **Refresh Facebook token** — If you used a user token instead of a page token, it expires. Re-run the token exchange steps.

### Monthly
- **Review costs** — Check OpenAI, ElevenLabs, and Luma dashboards. Ensure you're within budget.

---

## Troubleshooting

### "ELEVENLABS_API_KEY not set"
- Check the secret name matches exactly (case-sensitive)
- Verify the key is valid at elevenlabs.io

### "No voice ID configured for character"
- Ensure all 4 voice secrets are set
- Voice IDs look like: `21m00Tcm4TlvDq8ikWAM`

### "LUMA_API_KEY not set"
- Check the secret exists in GitHub
- Verify you have credits in your Luma account

### "Facebook credentials not configured"
- Both `FB_PAGE_ID` and `FB_ACCESS_TOKEN` must be set
- Token may have expired — regenerate it

### Video generation times out
- Luma can take 2-5 minutes per video
- If consistently timing out, check Luma status page
- Consider switching to fal.ai (see UPGRADE_TO_PREMIUM.md)

---

## Quick Reference: All Secrets

```
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_CHARLIE=...
ELEVENLABS_VOICE_MILO=...
ELEVENLABS_VOICE_BELLA=...
ELEVENLABS_VOICE_DUKE=...
LUMA_API_KEY=...
FB_PAGE_ID=...
FB_ACCESS_TOKEN=...
```
