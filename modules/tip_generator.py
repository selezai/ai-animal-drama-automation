"""
Tip Generator — GPT-4o-mini
Generates pet care tip scripts for video production. ~$0.001 per tip.
"""
from __future__ import annotations
import json
import random
import logging
from datetime import datetime
from openai import OpenAI

from config import (
    OPENAI_API_KEY, OPENAI_MODEL, PROMPTS_DIR, OUTPUT_DIR,
    CONTENT_PILLARS, PET_TYPES, PET_WEIGHTS, VIRALITY_THRESHOLD, BATCH_SIZE,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a pet care expert and viral content creator making short educational video scripts for South African pet owners on Instagram Reels and Facebook.

Your scripts follow this exact 30-second format:
- HOOK (0-2s): One punchy sentence that stops the scroll. Use one of these proven formulas:
  * Curiosity gap: "I just found out [shocking thing] about my [pet]"
  * Relatable: "POV: your [pet] does [thing every owner knows]"
  * Controversial: "Unpopular opinion: [spicy but lighthearted take]"
  * Unexpected: "My [pet] just did something I can't explain"
  * Danger: "Stop doing this to your [pet] right now"
  * Narrative: "So this just happened..."
  The hook MUST feel personal and emotional, not clinical or generic.
- TEACH (2-18s): The actual tip, explained clearly with one specific example. 2-3 sentences max.
- WHY (18-25s): Why this matters — real consequence or benefit. 1-2 sentences.
- CTA (25-30s): Always exactly "Follow for daily pet tips"

Rules:
- Write in South African English (warm, friendly, not American slang)
- Simple language — no medical jargon
- Be specific — not vague ("some foods" → "grapes, raisins, and xylitol")
- The hook must create urgency or curiosity in ONE SHORT sentence
- Hooks should feel like a friend telling you something, not a textbook
- Output structured JSON only — no markdown, no extra text"""


def _load_pillars() -> dict:
    with open(PROMPTS_DIR / "tip_pillars.json") as f:
        return json.load(f)


def _pick_content(pillars: dict) -> tuple[str, str, str]:
    pillar_keys = list(CONTENT_PILLARS.keys())
    pillar_weights = [CONTENT_PILLARS[p]["weight"] for p in pillar_keys]
    pillar = random.choices(pillar_keys, weights=pillar_weights, k=1)[0]
    pet_type = random.choices(PET_TYPES, weights=PET_WEIGHTS, k=1)[0]
    topics_key = f"{pet_type}_topics"
    topic = random.choice(pillars["pillars"][pillar][topics_key])
    return pillar, pet_type, topic


def _build_prompt(pillar: str, pet_type: str, topic: str, pillars: dict) -> str:
    pillar_data = pillars["pillars"][pillar]
    hook_template = random.choice(pillar_data["hook_templates"])
    hook_example = (
        hook_template
        .replace("{pet}", pet_type)
        .replace("{pet_cap}", pet_type.capitalize())
    )

    return f"""Write a 30-second educational pet tip video script.

PET TYPE: {pet_type}
PILLAR: {pillar_data['label']}
TOPIC: {topic}
HOOK STYLE EXAMPLE: "{hook_example}"

Return ONLY this JSON (no markdown, no extra text):
{{
  "pet_type": "{pet_type}",
  "pillar": "{pillar}",
  "topic": "{topic}",
  "hook": "one-sentence hook (0-3s) — creates urgency or curiosity immediately",
  "teach": "the tip explained clearly (3-20s) — specific, practical, 2-3 sentences",
  "why": "why this matters (20-25s) — real consequence or benefit, 1-2 sentences",
  "cta": "Follow for daily pet tips",
  "narrator_script": "full narration as one flowing paragraph: hook → teach → why → cta",
  "caption": "Instagram-optimized caption: hook as first line (with line break after) + 1-sentence value summary + engagement question that begs a comment (e.g. 'Tag someone who needs to see this' or 'Drop a [emoji] if your [pet] does this') + 8-10 relevant hashtags mixing big (#DogsOfInstagram) with niche (#SAPetOwner #PetTipsSA)",
  "fb_caption": "Facebook caption: same hook + summary + engagement question but only 3-4 hashtags (FB penalises hashtag stuffing)",
  "first_comment": "a relatable follow-up question or controversial take to post as first comment to spark debate and boost engagement",
  "virality_score": 8,
  "virality_reason": "one sentence explaining the score"
}}"""


def generate_tip() -> dict:
    """Generate one complete pet tip script via GPT-4o-mini."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=OPENAI_API_KEY)
    pillars = _load_pillars()
    pillar, pet_type, topic = _pick_content(pillars)

    logger.info(f"Generating tip: {pet_type} / {pillar} / {topic}")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(pillar, pet_type, topic, pillars)},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )

    tip = json.loads(response.choices[0].message.content)
    tip["generated_at"] = datetime.now().isoformat()

    raw_score = tip.get("virality_score", 5)
    try:
        score = int(str(raw_score).split("/")[0].strip().split(".")[0])
    except (ValueError, AttributeError):
        score = 5
    tip["virality_score"] = score

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_DIR / "scripts" / f"{pet_type}_{pillar}_{ts}.json"
    out.write_text(json.dumps(tip, indent=2))
    logger.info(f"Tip saved: {out.name} (score: {score}/10)")
    return tip


def generate_batch(count: int = BATCH_SIZE) -> list[dict]:
    """
    Generate a batch of tips, discarding any scoring below VIRALITY_THRESHOLD.
    Attempts up to 2x count to fill the batch.
    """
    tips = []
    attempts = 0
    max_attempts = count * 2

    logger.info(f"Starting batch: target {count} tips (threshold: {VIRALITY_THRESHOLD}/10)")

    while len(tips) < count and attempts < max_attempts:
        attempts += 1
        try:
            tip = generate_tip()
            score = tip.get("virality_score", 0)
            if score >= VIRALITY_THRESHOLD:
                tips.append(tip)
                logger.info(f"Kept tip {len(tips)}/{count} — score {score}/10")
            else:
                logger.info(f"Discarded tip — score {score}/10 (below threshold)")
        except Exception as e:
            logger.warning(f"Tip generation failed (attempt {attempts}): {e}")

    logger.info(f"Batch complete: {len(tips)} tips in {attempts} attempts")
    return tips


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tip = generate_tip()
    print(json.dumps(tip, indent=2))
