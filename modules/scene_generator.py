"""
Scene Generator — GPT-4o-mini (prompts) + Google Nano Banana (images)
Generates 4 scene illustration prompts per tip, then generates images via Gemini 2.5 Flash Image.
Cost: FREE (Google AI Studio free tier — ~500 images/day)
"""
import base64
import json
import logging
import shutil
import time
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import google.genai as genai
from google.genai import types

from config import OPENAI_API_KEY, OPENAI_MODEL, GOOGLE_API_KEY, OUTPUT_DIR

logger = logging.getLogger(__name__)

SCENE_DIR = OUTPUT_DIR / "scenes"
SCENE_DIR.mkdir(parents=True, exist_ok=True)

ART_STYLE_PREFIX = (
    "Flat 2D cartoon illustration in Kurzgesagt style. "
    "Bold vibrant colors, clean vector lines, simple shapes, no outlines on characters. "
    "Full-bleed composition filling entire frame, no white borders. "
    "9:16 portrait orientation. NO TEXT, NO WORDS, NO LETTERS anywhere in the image."
)

IMAGE_GENERATION_RETRIES = 3

SCENE_PROMPT_SYSTEM = """You generate visual scene descriptions for a 30-second pet care tip video.

Given a pet tip (hook, teach, why, cta), output EXACTLY 4 scene descriptions.
Each scene must be a specific, concrete visual moment that illustrates what the narrator is saying.

Rules:
- Describe what the viewer SEES — characters, actions, setting, emotion
- Be specific about the pet breed/type, the setting, and what's happening
- Each scene should be visually DIFFERENT from the others (different angle, setting, or action)
- Scene 1 = hook moment (dramatic/attention-grabbing)
- Scene 2 = teaching moment (showing the tip in action)
- Scene 3 = consequence/importance (why it matters — show the impact)
- Scene 4 = positive resolution (happy pet, call to action energy)

Return ONLY this JSON:
{
  "scenes": [
    {"id": 1, "description": "specific visual description for DALL-E"},
    {"id": 2, "description": "specific visual description for DALL-E"},
    {"id": 3, "description": "specific visual description for DALL-E"},
    {"id": 4, "description": "specific visual description for DALL-E"}
  ]
}"""


def generate_scene_prompts(tip: dict) -> list[str]:
    """Use GPT to generate 4 scene descriptions based on the tip content."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=OPENAI_API_KEY)

    user_prompt = f"""Generate 4 scene descriptions for this pet tip video:

PET TYPE: {tip.get('pet_type', 'dog')}
TOPIC: {tip.get('topic', tip.get('pillar', 'health'))}
HOOK: {tip.get('hook', '')}
TEACH: {tip.get('teach', '')}
WHY: {tip.get('why', '')}
CTA: {tip.get('cta', 'Follow for daily pet tips')}"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SCENE_PROMPT_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
    )

    data = json.loads(response.choices[0].message.content)
    scenes = data.get("scenes", [])

    prompts = []
    for scene in scenes[:4]:
        full_prompt = f"{ART_STYLE_PREFIX} {scene['description']}"
        prompts.append(full_prompt)
        logger.info(f"Scene {scene['id']}: {scene['description'][:80]}...")

    return prompts


def generate_scene_images(prompts: list[str], tip: dict) -> list[Path]:
    """Generate images via Google Nano Banana (Gemini 2.5 Flash Image). Free tier ~500/day."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set")

    client = genai.Client(api_key=GOOGLE_API_KEY)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pet_type = tip.get("pet_type", "pet")
    pillar = tip.get("pillar", "tip")

    image_paths = []

    for i, prompt in enumerate(prompts):
        logger.info(f"Generating scene image {i+1}/4 via Nano Banana...")

        img_data = None
        last_response_text = ""
        for attempt in range(1, IMAGE_GENERATION_RETRIES + 1):
            response = client.models.generate_content(
                model="gemini-3.1-flash-image",
                contents=prompt,
            )
            last_response_text = str(getattr(response, "text", "") or "")[:500]

            for part in getattr(response, "parts", []) or []:
                if getattr(part, "inline_data", None):
                    img_data = part.inline_data.data
                    if isinstance(img_data, str):
                        img_data = base64.b64decode(img_data)
                    break

            if img_data:
                break

            if attempt < IMAGE_GENERATION_RETRIES:
                logger.warning(
                    "Scene %s returned no image on attempt %s/%s; retrying",
                    i + 1,
                    attempt,
                    IMAGE_GENERATION_RETRIES,
                )
                time.sleep(2 * attempt)

        if not img_data:
            details = f" Response text: {last_response_text}" if last_response_text else ""
            raise RuntimeError(f"Scene {i+1}: No image returned by Nano Banana after {IMAGE_GENERATION_RETRIES} attempts.{details}")

        filename = f"{pet_type}_{pillar}_{ts}_scene{i+1}.png"
        img_path = SCENE_DIR / filename
        img_path.write_bytes(img_data)
        logger.info(f"Scene {i+1} saved: {filename} ({len(img_data) // 1024} KB)")

        image_paths.append(img_path)

    return image_paths


def generate_scenes(tip: dict) -> list[Path]:
    """Full pipeline: generate prompts → generate images. Returns 4 image paths."""
    logger.info(f"Generating scenes for: {tip.get('pet_type')} / {tip.get('pillar')}")
    prompts = generate_scene_prompts(tip)
    images = generate_scene_images(prompts, tip)
    logger.info(f"All {len(images)} scene images generated")
    return images


def copy_scenes_to_remotion(image_paths: list[Path], remotion_public: Path) -> list[str]:
    """Copy scene images into remotion/public/scenes/ and return relative paths for staticFile()."""
    scenes_dir = remotion_public / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    rel_paths = []
    for img in image_paths:
        dest = scenes_dir / img.name
        shutil.copy2(img, dest)
        rel_paths.append(f"scenes/{img.name}")

    return rel_paths


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_tip = {
        "pet_type": "dog",
        "pillar": "health",
        "topic": "ear infections",
        "hook": "Your dog's head shaking could be a sign of a painful ear infection",
        "teach": "Look out for redness, bad smell, or discharge from the ears. If your dog scratches at their ears or seems irritable, it could indicate an ear infection.",
        "why": "Left untreated, ear infections can spread to the inner ear and cause permanent hearing loss or neurological damage.",
        "cta": "Follow for daily pet tips",
    }
    prompts = generate_scene_prompts(test_tip)
    for i, p in enumerate(prompts):
        print(f"\nScene {i+1}:\n{p}")
