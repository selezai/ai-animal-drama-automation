"""
Script Generator — GPT-4o-mini via OpenAI API
~$0.002 per script. Better quality than any local model.
"""
import json
import random
import logging
from datetime import datetime
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, PROMPTS_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a scriptwriter for viral emotional AI animal drama content on Facebook.
Your scripts are 45 seconds long, emotionally resonant, and feature recurring animal characters.
Each script has one clear emotional thread. Dialogue is natural and uses the character's specific voice.

VIRALITY RULES:
- First 3 seconds must create pattern interrupt (shock, extreme emotion, or unanswered question)
- Universal emotions only (no cultural/geographic references)
- Visual storytelling > dialogue (works across languages)
- Peak emotion at 30-35 seconds (the "share moment")

You output structured JSON only."""


def load_prompts() -> tuple[dict, dict]:
    with open(PROMPTS_DIR / "characters.json") as f:
        characters = json.load(f)
    with open(PROMPTS_DIR / "story_templates.json") as f:
        templates = json.load(f)
    return characters, templates


def pick_content(characters: dict, templates: dict) -> tuple[str, str]:
    character = random.choice(list(characters["characters"].keys()))
    pillars = list(templates["pillars"].keys())
    weights = [templates["pillars"][p]["weight"] for p in pillars]
    pillar = random.choices(pillars, weights=weights, k=1)[0]
    return character, pillar


def build_user_prompt(character: str, pillar: str,
                      characters: dict, templates: dict) -> str:
    c = characters["characters"][character]
    p = templates["pillars"][pillar]
    theme = random.choice(p["themes"])
    hook = random.choice(p["hook_templates"])

    return f"""Write a 45-second script for {c['name']} the {c['species']}.

CHARACTER:
- Archetype: {c['archetype']}
- Voice: {', '.join(c['voice_traits'])}
- Verbal tics: {', '.join(c['verbal_tics'])}
- Example line: "{c['sample_dialogue']}"

STORY: {p['name']}
- Formula: {p['formula']}
- Theme: {theme}
- Hook style: "{hook}"

STRUCTURE:
[0-3s]  HOOK — emotional opening line + visual
[3-15s] SETUP — the hope or dream
[15-30s] CONFLICT — the twist that changes everything
[30-42s] EMOTIONAL PEAK — vulnerability, internal monologue
[42-45s] RESOLUTION — bittersweet or hopeful ending

Return ONLY this JSON:
{{
  "title": "episode title",
  "hook_line": "caption opening line",
  "scenes": [
    {{"timestamp": "0-3s", "visual": "image prompt for this scene", "dialogue": "spoken line", "emotion": "primary emotion"}},
    {{"timestamp": "3-15s", "visual": "...", "dialogue": "...", "emotion": "..."}},
    {{"timestamp": "15-30s", "visual": "...", "dialogue": "...", "emotion": "..."}},
    {{"timestamp": "30-42s", "visual": "...", "dialogue": "...", "emotion": "..."}},
    {{"timestamp": "42-45s", "visual": "...", "dialogue": "...", "emotion": "..."}}
  ],
  "full_voiceover": "All dialogue concatenated as a single voiceover script with Fish Audio emotion tags like (sigh), (whisper), (sob), (laugh) inserted where appropriate",
  "caption": "Facebook caption with emojis, engagement question, and hashtags (English)",
  "caption_es": "Same caption translated to Spanish with culturally appropriate emojis",
  "caption_pt": "Same caption translated to Portuguese with culturally appropriate emojis",
  "shareability_score": "Rate 1-10 how likely this is to be shared based on: emotional peak intensity, universal relatability, curiosity gap in hook"
}}"""


def generate_script() -> dict:
    """Generate one complete script via GPT-4o-mini."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=OPENAI_API_KEY)
    characters, templates = load_prompts()
    character, pillar = pick_content(characters, templates)

    logger.info(f"Generating script: {character} / {pillar}")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(
                character, pillar, characters, templates
            )},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
    )

    script = json.loads(response.choices[0].message.content)
    script["character"] = character
    script["pillar"] = pillar
    script["generated_at"] = datetime.now().isoformat()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_DIR / "scripts" / f"{character}_{pillar}_{ts}.json"
    out.write_text(json.dumps(script, indent=2))

    logger.info(f"Script saved: {out.name}")
    return script


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(generate_script(), indent=2))
