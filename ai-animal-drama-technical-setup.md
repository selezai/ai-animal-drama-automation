# Technical Setup Guide
## AI Animal Drama Production Stack

---

## Session Notes - 2026-06-11

### Runtime Review Fixes

- Fixed `--ig-only` behavior so Instagram-only posting skips Facebook and requires `IG_USER_ID`.
- Changed queue posting flow so pending manifests are selected without mutation and marked `posted` only after a publish succeeds.
- Changed comment reply runs to report `partial` when Facebook or Instagram reply handling records an error.

### Documentation Decisions

- Updated `README.md` to describe the current pet-tip automation pipeline: OpenAI scripts, ElevenLabs narration, Gemini images, Remotion render, queue manifests, Meta publishing, comment replies, and token refresh.
- Updated `.env.example` to match the variables read by the current code and workflows.
- This technical setup guide still contains older manual animal-drama/Kling/CapCut material below. Treat the README and code as the source of truth for the current automated pet-tip implementation until this guide is fully rewritten.

### Topic Cooldown History

- Added a GitHub-backed topic history design so weekly batch generation avoids exact topic repeats without depending on a local machine.
- Cooldown state lives in `output/history/topics.json`, which is read before generation and committed back by the batch workflow after successful queueing.
- The cooldown is exact-key based for v1: `pet_type:pillar:normalized_topic`, with a 90-day reuse block and 540-day retention pruning.
- Topic history is updated only after a video has rendered and been queued, so failed renders and rejected low-virality tips do not consume persisted cooldown slots.

### Balanced Analytics Feedback Loop

- Added a cloud-safe analytics loop that reads successful post logs, collects missing 24h, 72h, and 7d Facebook/Instagram snapshots, and commits compact state under `output/analytics/`.
- V1 scoring only adjusts `pet_type x pillar` cells. It does not score individual topics, rewrite prompts, create new pillars, or remove categories automatically.
- Generation now chooses a joint pet/pillar cell using existing static weights multiplied by a conservative analytics multiplier, then applies the existing topic cooldown inside that selected cell.
- Guardrails: multipliers require at least 5 posts per cell, clamp between `0.75` and `1.25`, decay toward `1.0` after 14 stale days, and can be disabled with `ANALYTICS_WEIGHTING_ENABLED=false`.
- Metrics collection is idempotent. Re-running the collector updates missing buckets without duplicating snapshots, and missing platform fields normalize to `0` instead of failing the workflow.
- Added analytics health tracking in `output/analytics/health.json`. A single partial analytics run is recorded but does not notify; two problem runs in a row open or update a GitHub Issue titled `Analytics feedback loop needs attention`.
- Hard analytics command failures still fail the workflow after health state is recorded. A clean recovery run resets the problem streak and closes the open analytics issue.
- Future roadmap: add weekly insight reports, then optional topic-family scoring only after an explicit taxonomy and enough data exist, then human-review strategy notes and fixed-label A/B tests. Future versions should not automatically rewrite core prompts or category strategy without approval.

### Daily Post Missing Video Guard

- Investigated a Daily Post failure where pending queue manifests remained in the repo but their referenced `output/video/*.mp4` assets had been removed.
- Root cause: stale queue manifests blocked posting because `run_post()` raised `FileNotFoundError` before it could mark or clean the bad queue item.
- Added failed-queue handling so missing-video manifests are marked `failed` and skipped. If every pending item is stale, the run exits as `skipped`, writes a post log, and lets the workflow commit the queue cleanup instead of failing repeatedly.
- Recovered only the still-pending June 10 videos from the improved thumbnail/output pipeline. The five older June 8 no-thumbnail queue items were marked `failed`, and already-posted June 10 assets were not re-added.
- Investigated duplicate posting of `dog_safety_20260610_105208.mp4`: the morning workflow posted to Facebook and Instagram, then failed while committing queue state because the workflow tried to add deleted Remotion audio/scene paths. The evening workflow saw the same manifest as pending and posted it again.
- Added Daily Post workflow concurrency with other repo-state writers and changed the queue-state commit step to commit only `output/`, then rebase/retry the push up to three times so a successful publish is much less likely to leave the remote queue stale.

### Weekly And Daily Workflow Failure Hardening

- Investigated the July 5 weekly batch failure. Root cause: Gemini image generation returned a successful API response without inline image data for scene 3 of one tip. The batch rendered and queued 13 other videos, but `python main.py batch` exited non-zero because one tip failed, so the workflow skipped the commit step and discarded the recoverable output.
- Changed the weekly batch workflow so the batch step can fail without immediately stopping the job. The workflow now commits rendered videos, queue manifests, topic history, audio, and scenes first, then fails afterward so the GitHub Issue alert still fires for partial generation problems.
- Added retry handling around Gemini scene-image generation when a response contains no image data. This keeps transient empty image responses from failing an otherwise healthy tip on the first attempt.
- Investigated the July 4 daily post failure. Root cause: the Facebook direct video upload hit the old 120-second write timeout while uploading from a GitHub runner.
- Increased Facebook direct and resumable transfer upload timeouts to a 30-second connect timeout and 300-second write/read timeout. The queue is still only marked posted after Meta returns success, so a timed-out upload does not consume or delete the manifest.
- Fixed analytics collector idempotency so it does not rewrite metrics and scores just because an already-known post log is still inside the lookback window. This prevents unnecessary analytics commits and reduces workflow churn.

### July 2026 Posting Outage Prevention

- Investigated why no real posts were published after July 6, 2026. Daily Post runs were marked successful, but their logs showed `Queue: 0 pending videos` and `Queue is empty`; the successful workflow status was misleading because `post` mode treated all skipped runs as success.
- Root cause of the empty queue: the July 12 weekly batch failed to refill it. All 14 generated tips failed at scene image generation with Gemini `429 RESOURCE_EXHAUSTED` quota errors, so the batch queued 0 videos.
- Changed post CLI exit behavior so dry-run skips still exit successfully, but real skipped posts such as `queue empty` and `no valid queued videos` exit non-zero. The Daily Post workflow now preserves cleanup/log commits first, then fails and opens/updates the existing GitHub Issue alert instead of silently closing it.
- Added local fallback scene generation for Gemini quota exhaustion. If the image provider is quota-blocked, the batch generates simple 9:16 PNG scene images locally with Pillow so videos can still render and refill the queue without extra image API calls. After the first quota error in a batch run, later tips skip Gemini immediately and use the local fallback.
- Hardened the weekly batch commit step so a zero-output failed batch no longer crashes on missing `remotion/public/audio` or `remotion/public/scenes` paths before the alert step.
- Hardened the Daily Post manifest push so cleanup deletions are temporarily stashed before `git pull --rebase && git push`. This keeps the duplicate-prevention `status=posted` commit atomic even when rendered assets were removed locally after a successful publish.
- Prevention rule: a green Daily Post workflow now means a video was actually published or the run was an intentional test dry-run; an empty production queue is a failing workflow that notifies.

---

## Tool Stack Overview

| Tool | Purpose | Cost | Setup Time |
|------|---------|------|------------|
| ChatGPT Plus | Script generation | $20/mo | 5 min |
| ElevenLabs | Voice generation | $5/mo | 15 min |
| Kling AI | Video generation | $0.10-0.30/video | 10 min |
| CapCut | Video editing | Free | 5 min |
| Meta Business Suite | Scheduling | Free | 10 min |

**Total Monthly Cost:** ~$25-35 (plus video generation costs)
**Total Setup Time:** ~45 minutes

---

## 1. ChatGPT Setup (Scripts)

### Account Setup
1. Visit [chat.openai.com](https://chat.openai.com)
2. Subscribe to ChatGPT Plus ($20/month)
3. Create a new chat for "Script Generation"

### Custom Instructions (Paste in Settings)
```
You are a scriptwriter for AI animal drama content for Facebook. Your scripts are:
- 45 seconds long
- Emotionally resonant
- Feature recurring animal characters with distinct voices
- Follow a specific 4-act structure: Hook → Setup → Conflict → Resolution
- Use simple, relatable human emotions translated to animal contexts

CHARACTER VOICES:
- Charlie (Golden Retriever): Warm, earnest, naive, says "I just..." when emotional
- Milo (Tabby Cat): Dry, sarcastic, defensive, uses "whatever" as verbal tic
- Bella (Parrot): Fast-talking, dramatic, nosy, says "okay okay" when excited
- Duke (Bulldog): Gravelly, short sentences, emotional pauses

Always include stage directions in [brackets] and keep dialogue natural.
```

### Script Generation Prompt (Save as Template)
```
Write a 45-second script for [CHARACTER] following the [PILLAR] pillar.

Theme: [SPECIFIC EMOTION/SITUATION]
Target emotion for viewer: [e.g., heartbreak, hope, surprise]

Structure:
[0-3s] Hook with emotional opening line
[3-15s] Setup showing character's hope/dream
[15-30s] Conflict/twist
[30-42s] Emotional peak
[42-45s] Resolution

Include stage directions and ensure the character voice is consistent.
```

---

## 2. ElevenLabs Setup (Voice Generation)

### Account Setup
1. Visit [elevenlabs.io](https://elevenlabs.io)
2. Create account
3. Subscribe to Starter plan ($5/month - 30,000 characters)
4. Note: 45-second script ≈ 100-150 words ≈ 750-1,000 characters

### Creating Character Voices

#### Charlie (Golden Retriever)
**Settings:**
- Voice: Clone or use "Adam" as base
- Stability: 50%
- Clarity + Similarity Enhancement: 75%
- Style: 20%
- Speed: 0.95 (slightly slower, earnest)

**Sample Text for Voice Design:**
```
I just... I thought if I waited long enough, he'd remember. That spot by the window? That's my spot. That's where I watch for him. Every day. Same time. I don't ask for much. Just... don't forget about me, okay?
```

#### Milo (Tabby Cat)
**Settings:**
- Voice: Clone or use "Antoni" as base
- Stability: 60%
- Clarity + Similarity Enhancement: 60%
- Style: 35%
- Speed: 1.05 (slightly faster, dismissive)

**Sample Text for Voice Design:**
```
Look, I don't do the whole feelings thing, alright? I'm fine. This spot is fine. I'm not lonely, I'm... selective. Whatever. Move over, you're blocking my sun. And don't make it weird.
```

#### Bella (Parrot)
**Settings:**
- Voice: Clone or use "Rachel" as base
- Stability: 45%
- Clarity + Similarity Enhancement: 70%
- Style: 40%
- Speed: 1.15 (fast, energetic)

**Sample Text for Voice Design:**
```
Okay okay okay! You want to know what I saw? I'll tell you what I saw! Big tough Duke, going to the old shed every Tuesday! Secretive! Mysterious! And yesterday I followed him! You won't BELIEVE what he's hiding!
```

#### Duke (Bulldog)
**Settings:**
- Voice: Clone or use "Josh" as base, lower pitch
- Stability: 55%
- Clarity + Similarity Enhancement: 80%
- Style: 15%
- Speed: 0.85 (slow, gravelly)

**Sample Text for Voice Design:**
```
Don't need anyone. Learned that. Twice returned. "Too much," they said. Fine. I'm fine. But... that puppy was shaking. Cold. Scared. I know that feeling. So I... I just stood there. Between him and the storm. That's all.
```

### Voice Generation Workflow
1. Copy script dialogue into ElevenLabs
2. Select appropriate character voice
3. Generate audio
4. Download as MP3
5. Name file: `[Character]_[EpisodeName]_[Date].mp3`

---

## 3. Kling AI Setup (Video Generation)

### Account Setup
1. Visit [klingai.com](https://klingai.com) or use domestic alternative
2. Create account
3. Purchase credits (est. $0.10-0.30 per 5-second video clip)

### Image-to-Video Workflow
1. **Generate character images first** using:
   - Midjourney, Leonardo.ai, or Kling's image generation
   - Consistent character prompts (see below)
   - Save as reference images

2. **Upload image to Kling**
3. **Add motion prompt:**
```
Character [emotion], [action], subtle movement, emotional storytelling, cinematic lighting
```

4. **Settings:**
   - Duration: 5 seconds (extend for longer scenes)
   - Mode: Standard or Professional
   - Aspect Ratio: 9:16 (vertical for mobile)

### Character Prompts (Image Generation)

**Charlie (Golden Retriever):**
```
Golden retriever dog, friendly face, blue collar, [emotion: sad/hopeful/worried], 
sitting by window at sunset, soft warm lighting, 3D Pixar animation style, 
high quality, detailed fur, emotional expression --ar 9:16
```

**Milo (Tabby Cat):**
```
Orange tabby cat with green eyes, striped fur, [emotion: annoyed/defensive/softening], 
sitting on windowsill at dusk, soft lighting, 3D Pixar animation style, 
high quality, detailed fur, emotional expression --ar 9:16
```

**Bella (African Grey Parrot):**
```
African Grey Parrot, distinctive red tail feathers, intelligent eyes, 
[emotion: excited/dramatic/guilty], perched indoors, warm lighting, 
3D Pixar animation style, high quality, detailed feathers, expressive --ar 9:16
```

**Duke (Bulldog):**
```
Bulldog with wrinkled face, stocky build, small scar above eye, 
[emotion: gruff/vulnerable/protective], outdoor or cozy indoor setting, 
3D Pixar animation style, high quality, detailed texture, emotional expression --ar 9:16
```

### Video Generation Tips
- **Batch generate:** Create 10-15 clips at once
- **Consistent lighting:** Specify "warm sunset lighting" or "soft indoor lighting"
- **Camera movement:** Keep minimal for dialogue-heavy scenes
- **Emotion first:** Always specify exact emotion in prompt

---

## 4. CapCut Setup (Editing)

### Download & Install
1. Download CapCut desktop or mobile app (free)
2. Sign in with Google/Apple account

### Project Settings
- **Aspect Ratio:** 9:16 (1080x1920)
- **Frame Rate:** 30fps
- **Resolution:** 1080p

### Editing Workflow (Per Episode)

#### Step 1: Import Assets
1. Import video clips from Kling
2. Import audio from ElevenLabs
3. Import music (copyright-free from YouTube Audio Library or Epidemic Sound)

#### Step 2: Arrange Timeline
```
Track 1: Video clips (cut to 45 seconds total)
Track 2: Voiceover audio
Track 3: Background music (low volume, -20dB)
Track 4: Sound effects (optional)
```

#### Step 3: Add Captions
1. Use CapCut's "Auto Captions" feature
2. OR manually add text for key lines
3. Style: White text with black outline, centered bottom
4. Font: Bold, readable (Montserrat Bold or similar)
5. Duration: Show for full line delivery, fade in/out

#### Step 4: Transitions
- Use simple cuts (avoid fancy transitions)
- Add slight zoom for emotional moments
- Keep pacing: match cuts to dialogue beats

#### Step 5: Color Grade
- Use "Warm" filter for emotional scenes
- Use "Cool" filter for sad/reflective moments
- Keep consistent across all episodes

#### Step 6: Export
- Format: MP4
- Resolution: 1080x1920
- Quality: High
- File naming: `[Character]_[Pillar]_[Date].mp4`

### Quick Edit Checklist
- [ ] Hook in first 3 seconds is clear
- [ ] Voiceover synced with character on screen
- [ ] Captions readable on mobile
- [ ] Background music not drowning dialogue
- [ ] Total duration 45 seconds
- [ ] Character recognizable throughout

---

## 5. Meta Business Suite Setup (Scheduling)

### Page Setup
1. Create Facebook Page:
   - Name: [Your Brand Name, e.g., "The Creek Stories"]
   - Category: Video Creator
   - Profile: Character image
   - Cover: Banner with all 4 characters

2. Add to Meta Business Suite:
   - Go to business.facebook.com
   - Add your page
   - Download mobile app for management

### Scheduling Workflow

#### Batch Schedule (Sunday Setup)
1. Open Meta Business Suite
2. Click "Create Post" → "Schedule"
3. Upload video
4. Write caption using template
5. Set time: 7:00 PM or 9:00 PM SAST
6. Repeat for all 14 weekly posts

#### Optimal Posting Times (South Africa)
- **Primary:** 7:00-9:00 PM SAST (evening wind-down)
- **Secondary:** 12:00-1:00 PM SAST (lunch break)
- **Test:** Try both, track performance

### Post Structure
1. **Video:** Native upload (never link)
2. **Caption:** Hook + story summary + engagement question + tags
3. **Cover Image:** Select most emotional frame
4. **Polls/Questions:** Add engagement sticker if available

---

## 6. Production Schedule (Weekly)

### Sunday: Planning (2 hours)
- [ ] Review last week's analytics
- [ ] Generate 14 scripts using ChatGPT
- [ ] Refine scripts for emotional beats
- [ ] Create shot list for each episode

### Monday: Generation (3 hours)
- [ ] Generate character images (if needed)
- [ ] Create video clips in Kling AI (batch process)
- [ ] Generate all voiceovers in ElevenLabs
- [ ] Download all assets

### Tuesday: Editing (2 hours)
- [ ] Rough cut all 14 videos in CapCut
- [ ] Add captions and music
- [ ] Final review and export
- [ ] Create thumbnails

### Tuesday Evening: Scheduling (30 min)
- [ ] Write captions for all 14 posts
- [ ] Schedule in Meta Business Suite
- [ ] Set notifications for engagement

### Wednesday-Saturday: Monitoring (30 min/day)
- [ ] Respond to comments (first hour critical)
- [ ] Check analytics
- [ ] Pin engaging comments
- [ ] Note top-performing content type

---

## 7. File Organization System

### Folder Structure
```
/TheCreek/
  /01_Scripts/
    /Week1/
    /Week2/
    ...
  /02_Audio/
    /Charlie/
    /Milo/
    /Bella/
    /Duke/
  /03_VideoClips/
    /Week1/
    /Week2/
    ...
  /04_FinalVideos/
    /Published/
    /Scheduled/
  /05_Assets/
    /CharacterImages/
    /Music/
    /SFX/
  /06_Analytics/
    /WeeklyReports/
```

### Naming Conventions
- **Scripts:** `W1_Mon_AM_Charlie_Betrayal_v1.txt`
- **Audio:** `Charlie_ReplacementFear_20250330.mp3`
- **Video Clips:** `Charlie_Sad_Window_5sec.mp4`
- **Final Videos:** `Charlie_Betrayal_20250330_1080p.mp4`
- **Thumbnails:** `Thumb_Charlie_Betrayal_20250330.jpg`

---

## 8. Troubleshooting Common Issues

### Voice Issues
| Problem | Solution |
|---------|----------|
| Voice sounds robotic | Increase stability to 60%, reduce speed to 0.95 |
| Emotion not coming through | Adjust style setting higher (30-40%) |
| Audio quality poor | Check internet connection, regenerate |
| Wrong character voice | Clear cache, select correct voice profile |

### Video Issues
| Problem | Solution |
|---------|----------|
| Character inconsistent | Use same seed/reference image |
| Motion unnatural | Simplify motion prompt, reduce movement |
| Quality low | Use Professional mode, increase credits |
| Wrong emotion | Be very specific in prompt, add "emotional expression" |

### Engagement Issues
| Problem | Solution |
|---------|----------|
| Low views | Check posting time, test new hook |
| Low shares | Increase emotional peak intensity |
| Low comments | Adjust caption question to be more specific |
| Algorithm suppression | Ensure native upload, check for policy violations |

---

## 9. Monthly Review Checklist

### Analytics Review
- [ ] Top 5 performing videos (what do they have in common?)
- [ ] Worst 5 performing videos (what went wrong?)
- [ ] Best posting times (refine schedule)
- [ ] Character performance (which character gets most engagement?)
- [ ] Pillar performance (which story type performs best?)

### Content Review
- [ ] Character consistency (do they feel like the same characters?)
- [ ] Story variety (avoiding repetition)
- [ ] Visual quality (improving over time?)
- [ ] Audio quality (voices still distinct?)

### Technical Review
- [ ] Tool costs (staying within budget?)
- [ ] Workflow efficiency (can we batch better?)
- [ ] New tool evaluation (anything new worth trying?)
- [ ] Backup system (files backed up?)

---

## 10. Quick Reference Card

### Daily Tasks (15 min)
- Respond to all new comments
- Check notification for viral potential
- Share top performer to story

### Weekly Tasks (5.5 hours)
- Script generation: 2 hours
- Video/audio generation: 3 hours
- Editing: 2 hours
- Scheduling: 30 min

### Monthly Tasks (2 hours)
- Analytics review: 1 hour
- Strategy refinement: 30 min
- Tool subscription review: 30 min

### Emergency Contacts/Issues
- Facebook support: business.facebook.com/help
- ElevenLabs support: help.elevenlabs.io
- Kling AI support: Check Discord/forum

---

**Remember:** Consistency > Perfection. Get content out, learn from data, iterate.
