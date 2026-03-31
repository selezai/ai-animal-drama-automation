"""
Voice Generator — ElevenLabs API (Budget Setup)
High-quality TTS with emotion control.
$5/month Starter plan = 30,000 characters (~46 videos)
"""
import logging
import requests
from pathlib import Path
from datetime import datetime

from config import (
    ELEVENLABS_API_KEY, ELEVENLABS_MODEL,
    ELEVENLABS_VOICE_IDS, OUTPUT_DIR
)

logger = logging.getLogger(__name__)

ELEVENLABS_API = "https://api.elevenlabs.io/v1"


def generate_voice(text: str, character: str, output_path: Path = None) -> Path:
    """
    Generate voice audio using ElevenLabs.
    
    Args:
        text: The dialogue text
        character: Character name to select voice ID
        output_path: Optional custom output path
    
    Returns:
        Path to generated audio file
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set")
    
    voice_id = ELEVENLABS_VOICE_IDS.get(character.lower())
    if not voice_id:
        raise ValueError(f"No voice ID configured for character: {character}")
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / "audio" / f"{character}_{timestamp}.mp3"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.post(
        f"{ELEVENLABS_API}/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,  # Emotion expressiveness
                "use_speaker_boost": True,
            },
        },
        timeout=60,
    )
    
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    logger.info(f"Generated voice: {output_path.name} ({len(text)} chars)")
    return output_path


def generate_voice_from_script(script: dict) -> Path:
    """
    Generate full voiceover from a script's full_voiceover field.
    
    Args:
        script: Script dict with 'character' and 'full_voiceover' keys
    
    Returns:
        Path to generated audio file
    """
    character = script["character"]
    voiceover_text = script.get("full_voiceover", "")
    
    if not voiceover_text:
        dialogues = [s.get("dialogue", "") for s in script.get("scenes", [])]
        voiceover_text = " ".join(dialogues)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / "audio" / f"{character}_full_{timestamp}.mp3"
    
    return generate_voice(voiceover_text, character, output_path)


def get_available_voices() -> list:
    """List available voices in your ElevenLabs account."""
    if not ELEVENLABS_API_KEY:
        return []
    
    resp = requests.get(
        f"{ELEVENLABS_API}/voices",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("voices", [])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if ELEVENLABS_API_KEY:
        voices = get_available_voices()
        print(f"Available voices: {len(voices)}")
        for v in voices[:5]:
            print(f"  - {v['name']}: {v['voice_id']}")
    else:
        print("Set ELEVENLABS_API_KEY to test.")
