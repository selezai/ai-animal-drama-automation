# AI Animal Drama — Fully Automated Content Pipeline

## What This Is

A set-and-forget system that generates and posts AI animal drama videos to Facebook twice daily. No server to maintain, no manual work after initial setup.

**Current Setup: Budget ($19/month)** — See [UPGRADE_TO_PREMIUM.md](UPGRADE_TO_PREMIUM.md) for $40/month option.

---

## Architecture

```
GitHub Actions (cron: twice daily at 5pm + 7pm SAST)
        │
        ▼
┌──────────────────────────────────────────────────────┐
│              PIPELINE (Python)                       │
│                                                      │
│  1. GPT-4o-mini  ──▶ Script      ($0.002)           │
│  2. ElevenLabs   ──▶ Voice       ($0.08)            │
│  3. Luma Labs    ──▶ Video       ($0.24)            │
│  4. FFmpeg       ──▶ Composite   (free)             │
│  5. Graph API    ──▶ Post to FB  (free)             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

Each run takes ~5 minutes. Two runs/day = ~10 min. GitHub free tier gives you 2,000 min/month.

---

## Cost Breakdown

### Budget Setup (Current) — $19/month

| Component | Tool | Per Video | Monthly (60 videos) |
|-----------|------|-----------|---------------------|
| Scripts | GPT-4o-mini | $0.002 | $0.12 |
| Voice | ElevenLabs (Starter) | ~$0.08 | $5.00 (flat) |
| Video | Luma Ray Flash 2 | $0.24 | $14.40 |
| Compositing | FFmpeg | $0 | $0 |
| Posting | Facebook Graph API | $0 | $0 |
| **Total** | | **~$0.32/video** | **~$19/month** |

### Premium Setup — $40/month

| Component | Tool | Per Video | Monthly (60 videos) |
|-----------|------|-----------|---------------------|
| Scripts | GPT-4o-mini | $0.002 | $0.12 |
| Voice | Fish Audio Plus | ~$0.18 | $11.00 (flat) |
| Video | Hailuo 02 Pro (1080p) | $0.48 | $28.80 |
| **Total** | | **~$0.67/video** | **~$40/month** |

See [UPGRADE_TO_PREMIUM.md](UPGRADE_TO_PREMIUM.md) when ready to upgrade.

### Why These Tools

- **GPT-4o-mini:** $0.002/script. Script quality directly determines shareability. Wrong place to save money.
- **ElevenLabs:** Natural voices with emotion. $5/month Starter plan covers ~46 videos.
- **Luma Ray Flash 2:** Real animated video at $0.24/clip. 720p is fine for mobile viewing.
- **GitHub Actions:** Zero maintenance. No server to patch or monitor.

---

## Quick Start

```bash
# 1. Clone this repo
git clone <your-repo> && cd ai-animal-drama-automation

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env with your keys (see setup guide below)

# 4. Test the pipeline locally
python main.py --test

# 5. Push to GitHub to enable automated scheduling
git push origin main
# GitHub Actions will run twice daily automatically
```

---

## Project Structure

```
ai-animal-drama-automation/
├── README.md
├── MANUAL_TASKS.md                  # Setup instructions
├── UPGRADE_TO_PREMIUM.md            # How to upgrade to $40/mo
├── requirements.txt
├── .env.example
├── .github/
│   └── workflows/
│       └── generate-and-post.yml   # Scheduled GitHub Action
├── main.py                          # Pipeline orchestrator
├── config.py                        # Configuration
├── modules/
│   ├── __init__.py
│   ├── script_generator.py          # GPT-4o-mini script gen
│   ├── voice_generator.py           # ElevenLabs TTS
│   ├── video_generator.py           # Luma Labs video gen
│   ├── video_editor.py              # FFmpeg compositing
│   └── facebook_poster.py           # Meta Graph API
├── prompts/
│   ├── characters.json              # Character bible
│   └── story_templates.json         # Story formulas
└── output/                          # Generated assets (gitignored)
```

---

## API Keys You Need

| Service | Where to Get | Cost |
|---------|-------------|------|
| OpenAI | platform.openai.com | ~$0.12/month |
| ElevenLabs | elevenlabs.io | $5/month (Starter) |
| Luma Labs | lumalabs.ai/api | ~$14/month |
| Facebook | developers.facebook.com | Free |

**See [MANUAL_TASKS.md](MANUAL_TASKS.md) for detailed setup instructions.**

---

## Honest Trade-offs

### What's Fully Automated
- Script generation, voice synthesis, video generation, compositing, posting, scheduling

### What Still Needs a Human (Weekly, ~30 min)
- **Comment engagement:** Facebook's algorithm weights comment replies heavily. Automate everything else, but reply to comments yourself. This is the one manual task worth doing.
- **Quality spot-checks:** Skim through the week's posts. AI video gen occasionally produces artifacts. If a post looks bad, delete it.
- **Token refresh:** Facebook page tokens last 60+ days but eventually expire. Re-auth when needed.

### What This System Cannot Do
- Guarantee virality (no system can)
- Replace genuine community building
- Avoid all AI content policy risk (mitigated by consistent brand, but not eliminated)
