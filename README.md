# AI Pet Tips Automation

Automated short-form pet-care video pipeline for Facebook and Instagram.

The current system generates educational dog and cat tips, creates narration,
generates four vertical scene images, renders a Remotion video, queues it, and
posts scheduled content through the Meta Graph API.

## Current Pipeline

```text
Weekly batch workflow
  -> GPT-4o-mini writes pet-tip scripts and captions
  -> ElevenLabs generates narration and word timestamps
  -> GPT-4o-mini creates scene prompts
  -> Gemini image generation creates 4 vertical scene images
  -> Remotion renders MP4 video and thumbnail
  -> Queue manifest is written to output/queue

Daily post workflow
  -> Read oldest pending queue manifest
  -> Upload to Facebook Page unless --ig-only is used
  -> Upload to Instagram Reels when IG_USER_ID is configured
  -> Mark queue item posted only after publish succeeds
  -> Clean up posted media assets

Engagement workflow
  -> Fetch recent Facebook and Instagram comments
  -> Generate short replies with Gemini
  -> Track replied comment IDs to avoid duplicate replies
```

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install

cp .env.example .env
# Fill in .env with your API keys and Meta IDs.

python3 main.py tip
python3 main.py batch --count=1
python3 main.py queue
python3 main.py post --test
```

For Remotion preview:

```bash
npm run studio
```

## CLI Commands

```bash
python3 main.py batch
python3 main.py batch --count=3
python3 main.py post
python3 main.py post --test
python3 main.py post --ig-only
python3 main.py tip
python3 main.py queue
python3 main.py reply
python3 main.py refresh-token
python3 main.py refresh-token --bootstrap SHORT_USER_TOKEN
```

## Required Environment Variables

Copy [.env.example](.env.example) to `.env` for local runs. Add the same values
as GitHub Actions secrets for scheduled automation.

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Script and scene prompt generation |
| `ELEVENLABS_API_KEY` | Narration generation |
| `ELEVENLABS_VOICE_ID` | Single narrator voice ID |
| `GOOGLE_API_KEY` | Gemini image generation and comment replies |
| `ALLOW_FALLBACK_SCENES` | Optional emergency flag; set `true` only to allow local placeholder scene art when Gemini image generation is quota-blocked |
| `FB_PAGE_ID` | Facebook Page target |
| `FB_ACCESS_TOKEN` | Page access token for Facebook and Instagram Graph API |
| `IG_USER_ID` | Instagram Business/Creator account ID for Reels |
| `FB_APP_ID` | Meta app ID for token debugging/bootstrap |
| `FB_APP_SECRET` | Meta app secret for token debugging/bootstrap |
| `FB_LONG_LIVED_USER_TOKEN` | Optional long-lived user token for token operations |

Never commit `.env`; it is ignored by git.

## Project Structure

```text
ai-animal-drama-automation/
├── main.py                         # Pipeline CLI
├── config.py                       # Env and content settings
├── modules/
│   ├── tip_generator.py            # OpenAI pet-tip generation
│   ├── voice_generator.py          # ElevenLabs narration + timestamps
│   ├── scene_generator.py          # Scene prompts + Gemini images
│   ├── queue_manager.py            # Pending/posted queue manifests
│   ├── facebook_poster.py          # Facebook and Instagram Graph API publishing
│   ├── comment_replier.py          # FB/IG comment reply automation
│   └── token_refresher.py          # Meta token refresh helpers
├── prompts/
│   └── tip_pillars.json            # Pet topics and hook templates
├── remotion/
│   ├── src/                        # Remotion video composition
│   └── public/                     # Generated audio and scene assets for render
├── scripts/
│   └── render_video.js             # Node Remotion renderer
├── output/
│   ├── queue/                      # Committed queue manifests
│   ├── video/                      # Rendered MP4s referenced by queue
│   └── final/                      # Run logs
└── .github/workflows/
    ├── batch-generate.yml          # Weekly content generation
    ├── daily-post.yml              # Twice-daily posting
    ├── engage-comments.yml         # Comment replies
    └── refresh-token.yml           # Meta token refresh
```

## Automation Schedule

| Workflow | Schedule | Purpose |
| --- | --- | --- |
| Weekly Batch Generate | Sunday 18:00 UTC | Generate and queue 14 videos |
| Daily Post | 05:00 and 16:00 UTC | Post queued videos |
| Engage Comments | 05:30 and 16:30 UTC | Reply to new comments |
| Refresh FB Token | Every 6 hours | Refresh/update token secret |

Times are UTC. South Africa is UTC+2, so the daily posts run at 07:00 and
18:00 SAST.

## Operational Notes

- Queue items stay `pending` until a publish operation succeeds.
- `python3 main.py post --test` does not mutate the queue.
- `python3 main.py post --ig-only` skips Facebook and requires `IG_USER_ID`.
- Instagram posting uses a GitHub raw URL for the committed MP4 and optional
  thumbnail, so queued media must be pushed before Reels publishing works.
- Generated media can be large; the posting workflow removes posted video,
  audio, and scene assets after successful publication.

## Verification

Useful checks before changing automation code:

```bash
python3 -m compileall main.py modules
npx tsc --noEmit -p remotion/tsconfig.json
git diff --check
```
