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
Your scripts feature anthropomorphic animal characters who talk to each other like in Fruit Love Island.
Characters stand on two legs, wear clothes, have expressive human-like faces, and speak dialogue.

VIRALITY RULES:
- First 3 seconds must create pattern interrupt (shock, extreme emotion, or unanswered question)
- Show characters TALKING and INTERACTING with each other, not just animals in nature
- Each scene must feature characters speaking dialogue to each other
- Universal emotions only (no cultural/geographic references)
- Peak emotion at 30-35 seconds (the "share moment")

You output structured JSON only with dialogue between characters."""


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

    # Pick 1-2 supporting characters for dialogue
    other_chars = [k for k in characters["characters"].keys() if k != character]
    supporting = random.sample(other_chars, min(2, len(other_chars)))
    support_info = []
    for s in supporting:
        sc = characters["characters"][s]
        support_info.append(f"- {sc['name']} ({sc['species']}): {sc['archetype']}, voice: {', '.join(sc['voice_traits'])}")

    return f"""Write a 45-second dialogue script for {c['name']} the {c['species']}.

MAIN CHARACTER:
- Archetype: {c['archetype']}
- Voice: {', '.join(c['voice_traits'])}
- Verbal tics: {', '.join(c['verbal_tics'])}
- Example line: "{c['sample_dialogue']}"

SUPPORTING CHARACTERS in this episode:
{chr(10).join(support_info)}

STORY: {p['name']}
- Formula: {p['formula']}
- Theme: {theme}
- Hook style: "{hook}"

SCENE STRUCTURE (each scene shows characters TALKING and INTERACTING):
[0-3s]  HOOK — Character says something shocking/emotional to another character
[3-15s] SETUP — Characters talking, establishing the situation
[15-30s] CONFLICT — Twist revealed through dialogue between characters
[30-42s] EMOTIONAL PEAK — Vulnerable dialogue exchange
[42-45s] RESOLUTION — Final lines, connection or acceptance

IMPORTANT:
- Characters are ANTHROPOMORPHIC: stand on two legs, wear clothes, human-like faces
- Each scene MUST show characters speaking TO EACH OTHER (dialogue, not narration)
- Visual prompts must describe: characters talking, gesturing, emotional expressions, close-ups on faces

Return ONLY this JSON:
{{
  "title": "episode title",
  "hook_line": "caption opening line",
  "main_character": "{character}",
  "characters_present": ["charlie", "milo", etc],
  "scenes": [
    {{"timestamp": "0-3s", "visual": "character close-up, talking to another character, expressive face, anthropomorphic animal standing on two legs", "dialogue": "CHARACTER: spoken line", "speaker": "charlie", "emotion": "primary emotion"}},
    {{"timestamp": "3-15s", "visual": "two characters talking to each other, gesturing, emotional expressions", "dialogue": "CHARACTER: spoken line", "speaker": "milo", "emotion": "..."}},
    {{"timestamp": "15-30s", "visual": "characters in conversation, dramatic moment, expressive faces", "dialogue": "CHARACTER: spoken line", "speaker": "charlie", "emotion": "..."}},
    {{"timestamp": "30-42s", "visual": "intimate close-up, characters talking vulnerably to each other", "dialogue": "CHARACTER: spoken line", "speaker": "milo", "emotion": "..."}},
    {{"timestamp": "42-45s", "visual": "characters together, final moment, emotional connection", "dialogue": "CHARACTER: spoken line", "speaker": "charlie", "emotion": "..."}}
  ],
  "caption": "Facebook caption with emojis, engagement question, and hashtags (English)",
  "caption_es": "Same caption translated to Spanish",
  "caption_pt": "Same caption translated to Portuguese",
  "shareability_score": "Rate 1-10"
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
