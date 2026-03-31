# Upgrade to Premium ($40/month)

When you're ready to upgrade from Budget ($19/mo) to Premium ($40/mo), follow these steps.

## What Changes

| Component | Budget | Premium |
|-----------|--------|---------|
| **Video** | Luma Ray Flash 2 (720p, $0.24/vid) | Hailuo 02 Pro via fal.ai (1080p, $0.48/vid) |
| **Voice** | ElevenLabs Starter ($5/mo) | Fish Audio Plus ($11/mo) |
| **Quality** | Good | Fruit Love Island level |

---

## Step 1: Upgrade Voice to Fish Audio

### 1.1 Create Fish Audio Account
1. Go to [fish.audio](https://fish.audio)
2. Sign up and subscribe to **Plus** plan ($11/month)
3. Go to **Settings → API Keys** → Create new key
4. Copy the API key

### 1.2 Create Character Voices
For each character (Charlie, Milo, Bella, Duke):
1. Go to **My Voices → Create Voice**
2. Upload a 10-second audio clip of the voice style you want
3. Name it (e.g., "Charlie - Warm Golden Retriever")
4. Copy the **Voice ID**

### 1.3 Update GitHub Secrets
Replace ElevenLabs secrets with Fish Audio:

```
FISH_AUDIO_API_KEY = your_fish_audio_key
FISH_VOICE_CHARLIE = voice_id_for_charlie
FISH_VOICE_MILO = voice_id_for_milo
FISH_VOICE_BELLA = voice_id_for_bella
FISH_VOICE_DUKE = voice_id_for_duke
```

### 1.4 Update config.py
Replace the ElevenLabs section with:

```python
# ── Voice Generation (Fish Audio S1 - Premium) ─────────────────────
FISH_AUDIO_API_KEY = os.getenv("FISH_AUDIO_API_KEY", "")
FISH_AUDIO_MODEL = "s1"
FISH_VOICE_IDS = {
    "charlie": os.getenv("FISH_VOICE_CHARLIE", ""),
    "milo": os.getenv("FISH_VOICE_MILO", ""),
    "bella": os.getenv("FISH_VOICE_BELLA", ""),
    "duke": os.getenv("FISH_VOICE_DUKE", ""),
}
```

### 1.5 Replace voice_generator.py
Copy the Fish Audio version from `modules/voice_generator_premium.py` (create this file with the Fish Audio implementation).

---

## Step 2: Upgrade Video to Hailuo 02 Pro

### 2.1 Create fal.ai Account
1. Go to [fal.ai](https://fal.ai)
2. Create account and add payment method
3. Go to **Dashboard → API Keys** → Create key
4. Copy the API key

### 2.2 Update GitHub Secrets
```
FAL_KEY = your_fal_api_key
```

Add a GitHub Variable (not secret):
```
FAL_VIDEO_MODEL = fal-ai/minimax/hailuo-02/pro/image-to-video
```

### 2.3 Update config.py
Replace the Luma section with:

```python
# ── Video Generation (fal.ai - Premium) ────────────────────────────
FAL_API_KEY = os.getenv("FAL_KEY", "")
FAL_VIDEO_MODEL = os.getenv("FAL_VIDEO_MODEL", "fal-ai/minimax/hailuo-02/pro/image-to-video")
FAL_IMAGE_MODEL = "fal-ai/flux/schnell"
VIDEO_DURATION_SEC = 5
VIDEO_ASPECT_RATIO = "9:16"
```

### 2.4 Replace video_generator.py
Copy the fal.ai version from `modules/video_generator_premium.py` (create this file with the fal.ai implementation).

---

## Step 3: Update GitHub Actions Workflow

Edit `.github/workflows/generate-and-post.yml`:

```yaml
env:
  # Script generation
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  # Voice generation (Fish Audio - Premium)
  FISH_AUDIO_API_KEY: ${{ secrets.FISH_AUDIO_API_KEY }}
  FISH_VOICE_CHARLIE: ${{ secrets.FISH_VOICE_CHARLIE }}
  FISH_VOICE_MILO: ${{ secrets.FISH_VOICE_MILO }}
  FISH_VOICE_BELLA: ${{ secrets.FISH_VOICE_BELLA }}
  FISH_VOICE_DUKE: ${{ secrets.FISH_VOICE_DUKE }}
  # Video generation (fal.ai - Premium)
  FAL_KEY: ${{ secrets.FAL_KEY }}
  FAL_VIDEO_MODEL: ${{ vars.FAL_VIDEO_MODEL || 'fal-ai/minimax/hailuo-02/pro/image-to-video' }}
  # Facebook posting
  FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
  FB_ACCESS_TOKEN: ${{ secrets.FB_ACCESS_TOKEN }}
```

---

## Cost Comparison

| | Budget | Premium |
|--|--------|---------|
| Scripts (60/mo) | $0.12 | $0.12 |
| Voice | $5.00 | $11.00 |
| Video (60 × $0.24 vs $0.48) | $14.40 | $28.80 |
| **Total** | **$19.52** | **$39.92** |

---

## When to Upgrade

Upgrade when you have:
- **10,000+ followers** — Your content is resonating
- **Consistent engagement** — Comments, shares on most videos
- **Revenue** — Ads or sponsorships covering costs

The extra $20/month buys:
- 1080p instead of 720p
- Smoother character animation
- Better emotion control in voices
- More headroom for longer scripts
