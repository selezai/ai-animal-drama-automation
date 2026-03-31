"""
Configuration for AI Animal Drama Automation Pipeline
All generation via cloud APIs — no local GPU, no VM.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PROMPTS_DIR = BASE_DIR / "prompts"

for d in [OUTPUT_DIR / "scripts", OUTPUT_DIR / "audio",
          OUTPUT_DIR / "video", OUTPUT_DIR / "final"]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys (all from environment — never hardcoded) ──────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
LUMA_API_KEY = os.getenv("LUMA_API_KEY", "")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")

# ── Script Generation (OpenAI GPT-4o-mini) ─────────────────────────
OPENAI_MODEL = "gpt-4o-mini"  # ~$0.002 per script

# ── Voice Generation (ElevenLabs) ──────────────────────────────────
# Budget: Starter plan $5/mo = 30,000 characters (~46 videos)
# Premium: Fish Audio Plus $11/mo = 250,000 credits (see UPGRADE_TO_PREMIUM.md)
ELEVENLABS_MODEL = "eleven_flash_v2_5"  # Fast, cheap, good quality
ELEVENLABS_VOICE_IDS = {
    "charlie": os.getenv("ELEVENLABS_VOICE_CHARLIE", ""),  # Warm, friendly
    "milo": os.getenv("ELEVENLABS_VOICE_MILO", ""),        # Dry, witty
    "bella": os.getenv("ELEVENLABS_VOICE_BELLA", ""),      # Energetic
    "duke": os.getenv("ELEVENLABS_VOICE_DUKE", ""),        # Deep, gravelly
}

# ── Video Generation (Luma Labs) ───────────────────────────────────
# Budget: ray-flash-2 @ $0.24/video (720p, 5s)
# Premium: Hailuo 02 Pro via fal.ai @ $0.48/video (1080p) — see UPGRADE_TO_PREMIUM.md
LUMA_VIDEO_MODEL = os.getenv("LUMA_VIDEO_MODEL", "ray-flash-2")
LUMA_IMAGE_MODEL = "photon-flash-1"  # Fast image gen for character frames
VIDEO_DURATION_SEC = 5
VIDEO_ASPECT_RATIO = "9:16"

# ── Character Reference Images (for visual consistency) ───────────
# Place PNG/JPG images in prompts/character_images/
# If a reference image exists, it's used as the base for image-to-video
# If not, falls back to generating a new image per scene
CHARACTER_IMAGES_DIR = PROMPTS_DIR / "character_images"
CHARACTER_IMAGES = {
    "charlie": CHARACTER_IMAGES_DIR / "charlie.png",
    "milo": CHARACTER_IMAGES_DIR / "milo.png",
    "bella": CHARACTER_IMAGES_DIR / "bella.png",
    "duke": CHARACTER_IMAGES_DIR / "duke.png",
}

# ── Facebook ──────────────────────────────────────────────────────
TIMEZONE = "Africa/Johannesburg"

# ── Content Settings ──────────────────────────────────────────────
CHARACTERS = ["charlie", "milo", "bella", "duke"]
PILLARS = [
    "betrayal_loyalty",
    "unexpected_kindness",
    "secrets_revealed",
    "jealousy_insecurity",
    "found_family",
]
PILLAR_WEIGHTS = [0.40, 0.25, 0.20, 0.10, 0.05]

# ── Virality Settings ─────────────────────────────────────────────
# Generate captions in multiple languages for global reach
# Facebook auto-detects user language and shows appropriate version
CAPTION_LANGUAGES = ["en", "es", "pt"]  # English, Spanish, Portuguese
# Top 3 languages = 1.5B+ Facebook users

# Viral hook patterns (first 3 seconds determine share rate)
VIRAL_HOOK_PATTERNS = [
    "pattern_interrupt",  # Unexpected visual/statement
    "emotional_extreme",  # Peak emotion immediately
    "curiosity_gap",      # Question that demands answer
]
