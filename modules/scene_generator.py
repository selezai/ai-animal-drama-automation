"""
Scene Generator — GPT-4o-mini (prompts) + Google Nano Banana (images)
Generates 4 scene illustration prompts per tip, then generates images via Gemini 2.5 Flash Image.
Cost: FREE (Google AI Studio free tier — ~500 images/day)
"""
import base64
import hashlib
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
FALLBACK_SCENE_COUNT = 4
_IMAGE_PROVIDER_QUOTA_BLOCKED = False

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


def _is_image_quota_exhausted(exc: Exception) -> bool:
    text = str(exc).lower()
    return "resource_exhausted" in text or "quota" in text or "429" in text


def generate_fallback_scene_images(prompts: list[str], tip: dict, reason: str = "") -> list[Path]:
    """Generate local visual fallback scenes when the image provider is quota-blocked."""
    from PIL import Image, ImageDraw

    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pet_type = tip.get("pet_type", "pet")
    pillar = tip.get("pillar", "tip")
    seed = int(hashlib.sha256("|".join(prompts).encode("utf-8")).hexdigest()[:8], 16)

    palette = _fallback_palette(pet_type, pillar)
    image_paths = []
    prompt_list = (prompts[:FALLBACK_SCENE_COUNT] or [""])[:FALLBACK_SCENE_COUNT]
    while len(prompt_list) < FALLBACK_SCENE_COUNT:
        prompt_list.append(prompt_list[-1] if prompt_list else "")

    for i, prompt in enumerate(prompt_list):
        filename = f"{pet_type}_{pillar}_{ts}_fallback_scene{i + 1}.png"
        img_path = SCENE_DIR / filename
        image = _draw_fallback_scene(pet_type, i, seed, palette)
        image.save(img_path, "PNG")
        logger.info(
            "Fallback scene %s saved: %s (%s KB)",
            i + 1,
            filename,
            img_path.stat().st_size // 1024,
        )
        image_paths.append(img_path)

    if reason:
        logger.warning("Generated local fallback scenes because image generation failed: %s", reason[:300])
    return image_paths


def _fallback_palette(pet_type: str, pillar: str) -> dict[str, tuple[int, int, int]]:
    palettes = {
        "safety": {"top": (33, 38, 51), "bottom": (237, 94, 67), "accent": (255, 214, 102)},
        "behaviour": {"top": (28, 49, 68), "bottom": (68, 156, 148), "accent": (255, 199, 95)},
        "health": {"top": (31, 71, 68), "bottom": (84, 186, 146), "accent": (244, 238, 214)},
        "training": {"top": (42, 43, 74), "bottom": (113, 97, 239), "accent": (255, 209, 102)},
        "fun_facts": {"top": (29, 53, 87), "bottom": (241, 144, 102), "accent": (255, 244, 174)},
    }
    palette = palettes.get(pillar, palettes["health"]).copy()
    palette["pet"] = (248, 218, 169) if pet_type == "dog" else (203, 190, 255)
    palette["shadow"] = (18, 22, 30)
    return palette


def _draw_fallback_scene(
    pet_type: str,
    scene_index: int,
    seed: int,
    palette: dict[str, tuple[int, int, int]],
) -> "Image.Image":
    from PIL import Image, ImageDraw

    width, height = 1080, 1920
    image = Image.new("RGB", (width, height), palette["top"])
    draw = ImageDraw.Draw(image)

    top = palette["top"]
    bottom = palette["bottom"]
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(int(top[c] * (1 - t) + bottom[c] * t) for c in range(3))
        draw.line([(0, y), (width, y)], fill=color)

    offset = (seed + scene_index * 137) % 180
    accent = palette["accent"]
    shadow = palette["shadow"]
    pet = palette["pet"]

    draw.rounded_rectangle(
        [90 + offset // 6, 250 + scene_index * 24, 990 - offset // 9, 1410 - scene_index * 18],
        radius=90,
        fill=tuple(min(255, c + 30) for c in top),
        outline=accent,
        width=8,
    )
    draw.ellipse([120 - offset, 1160, 960 - offset, 2020], fill=tuple(min(255, c + 24) for c in bottom))
    draw.ellipse([470 + offset // 2, 140, 1220 + offset // 2, 890], fill=tuple(min(255, c + 18) for c in top))

    if pet_type == "cat":
        _draw_cat_icon(draw, pet, shadow, accent, scene_index)
    else:
        _draw_dog_icon(draw, pet, shadow, accent, scene_index)

    _draw_scene_marks(draw, accent, scene_index)
    return image


def _draw_dog_icon(draw: "ImageDraw.ImageDraw", pet: tuple[int, int, int], shadow: tuple[int, int, int], accent: tuple[int, int, int], scene_index: int) -> None:
    x_shift = (scene_index - 1) * 18
    draw.ellipse([245 + x_shift, 590, 835 + x_shift, 1180], fill=shadow)
    draw.ellipse([270 + x_shift, 540, 810 + x_shift, 1080], fill=pet)
    draw.ellipse([200 + x_shift, 650, 380 + x_shift, 980], fill=pet)
    draw.ellipse([700 + x_shift, 650, 880 + x_shift, 980], fill=pet)
    draw.ellipse([405 + x_shift, 725, 465 + x_shift, 785], fill=shadow)
    draw.ellipse([615 + x_shift, 725, 675 + x_shift, 785], fill=shadow)
    draw.rounded_rectangle([475 + x_shift, 840, 605 + x_shift, 925], radius=40, fill=shadow)
    draw.arc([410 + x_shift, 840, 670 + x_shift, 1035], 20, 160, fill=shadow, width=10)
    draw.ellipse([472 + x_shift, 1180, 608 + x_shift, 1310], fill=accent)


def _draw_cat_icon(draw: "ImageDraw.ImageDraw", pet: tuple[int, int, int], shadow: tuple[int, int, int], accent: tuple[int, int, int], scene_index: int) -> None:
    x_shift = (scene_index - 1) * 16
    draw.polygon([(305 + x_shift, 620), (430 + x_shift, 405), (500 + x_shift, 670)], fill=pet)
    draw.polygon([(775 + x_shift, 620), (650 + x_shift, 405), (580 + x_shift, 670)], fill=pet)
    draw.ellipse([260 + x_shift, 560, 820 + x_shift, 1120], fill=shadow)
    draw.ellipse([290 + x_shift, 520, 790 + x_shift, 1020], fill=pet)
    draw.ellipse([410 + x_shift, 710, 468 + x_shift, 780], fill=shadow)
    draw.ellipse([612 + x_shift, 710, 670 + x_shift, 780], fill=shadow)
    draw.polygon([(540 + x_shift, 815), (490 + x_shift, 875), (590 + x_shift, 875)], fill=shadow)
    draw.arc([430 + x_shift, 815, 540 + x_shift, 940], 20, 150, fill=shadow, width=8)
    draw.arc([540 + x_shift, 815, 650 + x_shift, 940], 30, 160, fill=shadow, width=8)
    draw.ellipse([470 + x_shift, 1145, 610 + x_shift, 1285], fill=accent)


def _draw_scene_marks(draw: "ImageDraw.ImageDraw", accent: tuple[int, int, int], scene_index: int) -> None:
    y = 1460
    for i in range(FALLBACK_SCENE_COUNT):
        x = 390 + i * 100
        fill = accent if i == scene_index else (255, 255, 255)
        draw.ellipse([x, y, x + 34, y + 34], fill=fill)


def generate_scenes(tip: dict) -> list[Path]:
    """Full pipeline: generate prompts → generate images. Returns 4 image paths."""
    global _IMAGE_PROVIDER_QUOTA_BLOCKED
    logger.info(f"Generating scenes for: {tip.get('pet_type')} / {tip.get('pillar')}")
    prompts = generate_scene_prompts(tip)
    if _IMAGE_PROVIDER_QUOTA_BLOCKED:
        logger.warning("Image generation quota already exhausted in this run; using local fallback scenes")
        images = generate_fallback_scene_images(prompts, tip, reason="provider quota already exhausted")
        logger.info(f"All {len(images)} scene images generated")
        return images

    try:
        images = generate_scene_images(prompts, tip)
    except Exception as e:
        if not _is_image_quota_exhausted(e):
            raise
        _IMAGE_PROVIDER_QUOTA_BLOCKED = True
        logger.warning("Image generation quota exhausted; using local fallback scenes")
        images = generate_fallback_scene_images(prompts, tip, reason=str(e))
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
