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
    Generate full voiceover from a script with multiple characters speaking.
    Each scene's dialogue is spoken by the correct character voice.
    All clips are concatenated into one audio file.

    Args:
        script: Script dict with 'scenes' containing 'speaker' and 'dialogue' keys

    Returns:
        Path to generated audio file
    """
    import subprocess

    scenes = script.get("scenes", [])
    if not scenes:
        raise ValueError("No scenes found in script")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_parts = []

    logger.info(f"Generating dialogue audio with {len(scenes)} scenes...")

    for i, scene in enumerate(scenes):
        speaker = scene.get("speaker", script.get("main_character", "charlie"))
        dialogue = scene.get("dialogue", "")

        if not dialogue:
            continue

        # Extract just the spoken line (remove "CHARACTER: " prefix if present)
        if ": " in dialogue:
            spoken_text = dialogue.split(": ", 1)[1]
        else:
            spoken_text = dialogue

        part_path = OUTPUT_DIR / "audio" / f"part{i}_{speaker}_{timestamp}.mp3"
        generate_voice(spoken_text, speaker, part_path)
        audio_parts.append(str(part_path))

    # Concatenate all parts using ffmpeg
    final_path = OUTPUT_DIR / "audio" / f"dialogue_{timestamp}.mp3"

    if len(audio_parts) == 1:
        # Just one part, copy it
        Path(audio_parts[0]).rename(final_path)
    else:
        # Concatenate multiple parts
        concat_file = OUTPUT_DIR / "audio" / f"concat_{timestamp}.txt"
        with open(concat_file, "w") as f:
            for part in audio_parts:
                f.write(f"file '{part}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(final_path)
        ], check=True)

        # Cleanup temp files
        for part in audio_parts:
            Path(part).unlink(missing_ok=True)
        concat_file.unlink(missing_ok=True)

    logger.info(f"Dialogue audio saved: {final_path.name}")
    return final_path


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
