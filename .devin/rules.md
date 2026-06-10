# Pet Tips Automation — Workspace Rules

Supplemental rules specific to this project. These extend the global rules with project-specific patterns.

---

## Architecture Patterns

### Pipeline Pattern (Mandatory)
All content generation flows through discrete, testable modules:

```
tip_generator → voice_generator → video_renderer → facebook_poster
```

Each module is independent and can be run/tested in isolation via `python main.py --step <step>`.

**Never** combine steps — each module has a single responsibility.

### API Keys (Non-Negotiable)
All API keys live in `.env` locally and GitHub Secrets in CI. Never hardcode.

```python
# Correct
api_key = os.getenv("ELEVENLABS_API_KEY")

# Never
api_key = "sk_abc123..."
```

---

## Project Structure

```
ai-animal-drama-automation/
├── .github/workflows/        # GitHub Actions automation
├── .windsurf/                # Windsurf skills, rules, workflows
├── modules/                  # Pipeline modules (one responsibility each)
│   ├── script_generator.py   # GPT-4o tip generation
│   ├── voice_generator.py    # ElevenLabs TTS
│   ├── video_generator.py    # Remotion video rendering
│   ├── video_editor.py       # FFmpeg compositing
│   └── facebook_poster.py    # Facebook Graph API posting
├── remotion/                 # Remotion React templates
│   └── src/
├── prompts/                  # JSON config for characters/tips
├── output/                   # Generated files (gitignored)
├── scripts/                  # Utility/helper scripts
├── main.py                   # Pipeline entry point
└── config.py                 # Shared config/constants
```

---

## Content Model

### Tip Structure
Generated tip JSON must always include:
```json
{
  "category": "dog|cat|bird|fish|rabbit",
  "title": "Short hook title (max 8 words)",
  "tip": "The actionable tip (1-2 sentences)",
  "explanation": "Why this works (1-2 sentences)",
  "caption": "Facebook caption with emojis + hashtags",
  "caption_es": "Spanish caption",
  "caption_pt": "Portuguese caption"
}
```

### Content Pillars
- **Health** — nutrition, vet visits, symptoms to watch
- **Training** — commands, behaviour, positive reinforcement
- **Safety** — toxic foods, hazards, emergency care
- **Enrichment** — toys, mental stimulation, exercise
- **Grooming** — brushing, bathing, nail care

---

## Video Rendering (Remotion)

### Template Rules
- All templates live in `remotion/src/`
- Templates accept typed props — never use `any`
- Always include `Audio` component with generated voiceover
- Aspect ratio: **9:16** (vertical/Reels format)
- Duration: **15-30 seconds**

### Rendering
```bash
# Local render
cd remotion && npx remotion render PetTip out/video.mp4 --props='{"tipTitle":"..."}'

# GitHub Actions render
npm run render -- --props="$(cat output/tip.json)"
```

---

## GitHub Actions

### Workflow Trigger
- **Schedule:** Daily at 9 AM UTC
- **Manual:** `workflow_dispatch` for testing
- **Never** auto-post without human review during development

### Secrets Required
```
OPENAI_API_KEY
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
FB_PAGE_ID
FB_ACCESS_TOKEN
```

---

## Common Pitfalls to Avoid

1. **Don't mix Python and Node steps** — keep them clearly separated in the workflow
2. **Don't commit output files** — `output/` is gitignored
3. **Don't hardcode voice IDs** — use env vars
4. **Don't skip the tip JSON validation** — always validate before rendering
5. **Don't use `any` type in Remotion templates** — always type props

---

## Code Review — Verify Before Fixing (MANDATORY)

**Treat working pipeline steps as "correct until proven otherwise."**

Before flagging something as a bug or proposing a fix during code review:

1. **Verify it is actually broken, not intentional design.** Read surrounding code and understand full context.
2. **Check if the "issue" is a deliberate pattern.** Consistent patterns across modules are likely intentional.
3. **Confirm the bug is reachable.** Don't report theoretical edge cases that can't occur.
4. **Do NOT report speculative or low-confidence issues.** Only report with concrete evidence.
5. **When in doubt, ASK** — don't silently change working behaviour.
