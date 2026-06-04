"""
Configuration for Pet Tips Automation Pipeline
Generates and posts daily pet care tip videos to Facebook/Instagram.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PROMPTS_DIR = BASE_DIR / "prompts"
REMOTION_DIR = BASE_DIR / "remotion"

for d in [OUTPUT_DIR / "scripts", OUTPUT_DIR / "audio",
          OUTPUT_DIR / "video", OUTPUT_DIR / "queue", OUTPUT_DIR / "final"]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys (all from environment — never hardcoded) ──────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")

# ── Script Generation (OpenAI GPT-4o-mini) ─────────────────────────
OPENAI_MODEL = "gpt-4o-mini"  # ~$0.001 per tip

# ── Voice Generation (ElevenLabs — single narrator) ────────────────
ELEVENLABS_MODEL = "eleven_flash_v2_5"  # Fast, cheap, good quality

# ── Video (Remotion — rendered locally/GitHub Actions) ─────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_DURATION_FRAMES = 900  # 30 seconds at 30fps

# ── Content Settings ──────────────────────────────────────────────
PET_TYPES = ["dog", "cat"]
PET_WEIGHTS = [0.70, 0.30]  # 70% dogs, 30% cats

CONTENT_PILLARS = {
    "safety":    {"weight": 0.35, "label": "Safety & Danger"},
    "behaviour": {"weight": 0.25, "label": "Behaviour Decoded"},
    "health":    {"weight": 0.20, "label": "Health"},
    "training":  {"weight": 0.15, "label": "Training"},
    "fun_facts": {"weight": 0.05, "label": "Fun Facts"},
}

VIRALITY_THRESHOLD = 7  # Discard tips scoring below this (out of 10)
BATCH_SIZE = 14          # Videos generated per weekly batch (2/day × 7 days)

# ── Posting Schedule (UTC — SAST = UTC+2) ─────────────────────────
POST_TIMES_UTC = ["05:00", "16:00"]  # = 07:00 + 18:00 SAST
TIMEZONE = "Africa/Johannesburg"
