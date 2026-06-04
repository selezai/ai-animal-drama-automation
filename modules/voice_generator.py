"""
Voice Generator — ElevenLabs API
Single warm narrator voice for all pet tip videos.
"""
import logging
import requests
from pathlib import Path
from datetime import datetime

from config import ELEVENLABS_API_KEY, ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID, OUTPUT_DIR

logger = logging.getLogger(__name__)
ELEVENLABS_API = "https://api.elevenlabs.io/v1"


def generate_voice(text: str, output_path: Path = None) -> Path:
    """Generate narration audio for a tip script via ElevenLabs."""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set")
    if not ELEVENLABS_VOICE_ID:
        raise ValueError("ELEVENLABS_VOICE_ID not set")

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / "audio" / f"narration_{ts}.mp3"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.post(
        f"{ELEVENLABS_API}/text-to-speech/{ELEVENLABS_VOICE_ID}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.75,
                "style": 0.45,
                "use_speaker_boost": True,
            },
        },
        timeout=60,
    )
    response.raise_for_status()

    output_path.write_bytes(response.content)
    logger.info(f"Voice generated: {output_path.name} ({len(text)} chars)")
    return output_path


def generate_voice_from_tip(tip: dict) -> Path:
    """Generate narration audio from a tip dict using its narrator_script field."""
    text = tip.get("narrator_script", "")
    if not text:
        raise ValueError("tip must have a 'narrator_script' field")

    pet_type = tip.get("pet_type", "pet")
    pillar = tip.get("pillar", "tip")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_DIR / "audio" / f"{pet_type}_{pillar}_{ts}.mp3"
    return generate_voice(text, out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        path = generate_voice(
            "Did you know grapes are toxic to dogs? "
            "Even a small amount can cause sudden kidney failure. "
            "If your dog eats grapes, call your vet immediately — don't wait for symptoms. "
            "Follow for daily pet tips."
        )
        print(f"Audio saved: {path}")
    else:
        print("Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID to test.")
