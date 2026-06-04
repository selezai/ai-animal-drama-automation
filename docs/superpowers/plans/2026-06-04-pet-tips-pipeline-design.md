# Pet Tips Automation — Design Document
_Approved: 2026-06-04_

## Problem Statement
SitEasy needs to build a South African pet owner audience on Facebook from zero to drive future traffic to the pet-sitting platform. The current pipeline generates AI drama videos using Luma (expensive, inconsistent, content filters). Pivoting to educational pet tip content using Remotion (free, deterministic) with ElevenLabs voiceover, posting 2x/day. Content is purely educational — SitEasy lives in bio only.

## Solution Overview
- **Content:** Drama scripts → Pet tips (dog 70%, cat 30%)
- **Video:** Luma AI → Remotion React templates + Lottie animations
- **Voice:** ElevenLabs single narrator (warm, friendly)
- **Posting:** Facebook + Instagram Reels, 2x/day (7 AM + 6 PM SAST)
- **Schedule:** Weekly batch generation (Sunday night) + daily posting crons
- **Analytics:** Deferred to Phase 2 (week 3-4)

## Approved Decisions
1. Repo rename: `ai-animal-drama-automation` → `ai-pet-tips-automation`
2. Target: Dog owners (70%) + Cat owners (30%), South African market
3. Language: English only
4. Lottie animations (free LottieFiles) — upgrade to custom characters later
5. Batch generation: 14 videos/week (2/day)
6. No SitEasy CTA in videos — bio link only
7. Instagram Reels in Phase 2
8. Analytics feedback loop in Phase 2 (week 3-4)

## Content Model

### Hook Formula
```
HOOK  (0-3s):  "Most dog owners don't know this..."
TEACH (3-20s): Tip + animated illustration
WHY   (20-25s): Why it matters
CTA   (25-30s): "Follow for daily pet tips 🐾"
```

### Content Pillars
| Pillar | Weight |
|--------|--------|
| Safety/Danger | 35% |
| Behaviour Decoded | 25% |
| Health | 20% |
| Training | 15% |
| Fun Facts | 5% |

## Video Template
- Format: 1080x1920 (9:16 vertical)
- Duration: 25-30 seconds
- FPS: 30
- Stack: Remotion + Lottie + ElevenLabs audio

## What Gets Scrapped
| File | Action |
|------|--------|
| `characters.json` | Delete |
| `story_templates.json` | Replace |
| `video_generator.py` (Luma) | Replace |
| `script_generator.py` | Rewrite |
| `voice_generator.py` | Simplify |
| `video_editor.py` | Simplify |
| `facebook_poster.py` | Keep + add first-comment |
| `config.py` | Update |
| `main.py` | Rewrite |
| `.github/workflows/` | Rewrite |
