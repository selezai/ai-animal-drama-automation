"""
Voice Generator — ElevenLabs API
Single warm narrator voice for all pet tip videos.
Uses the with-timestamps endpoint for word-level caption sync.
"""
from __future__ import annotations
import json
import logging
import base64
import requests
from pathlib import Path
from datetime import datetime

from config import ELEVENLABS_API_KEY, ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID, OUTPUT_DIR

logger = logging.getLogger(__name__)
ELEVENLABS_API = "https://api.elevenlabs.io/v1"


def generate_voice(text: str, output_path: Path = None) -> tuple[Path, list[dict]]:
    """Generate narration audio and word-level timestamps via ElevenLabs.

    Returns:
        (audio_path, word_timestamps) where word_timestamps is a list of
        {word, start, end} dicts with times in seconds.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set")
    if not ELEVENLABS_VOICE_ID:
        raise ValueError("ELEVENLABS_VOICE_ID not set")

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / "audio" / f"narration_{ts}.mp3"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.post(
        f"{ELEVENLABS_API}/text-to-speech/{ELEVENLABS_VOICE_ID}/with-timestamps",
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

    data = response.json()

    audio_bytes = base64.b64decode(data["audio_base64"])
    output_path.write_bytes(audio_bytes)

    alignment = data.get("alignment", {})
    chars = alignment.get("characters", [])
    char_starts = alignment.get("character_start_times_seconds", [])
    char_ends = alignment.get("character_end_times_seconds", [])

    word_timestamps = _build_word_timestamps(chars, char_starts, char_ends)

    timestamps_path = output_path.with_suffix(".json")
    timestamps_path.write_text(json.dumps(word_timestamps))

    logger.info(f"Voice generated: {output_path.name} ({len(text)} chars, {len(word_timestamps)} words)")
    return output_path, word_timestamps


def _build_word_timestamps(chars: list, starts: list, ends: list) -> list[dict]:
    """Convert character-level alignment data into word-level timestamps."""
    words = []
    current_word = ""
    word_start = None
    word_end = None

    for i, char in enumerate(chars):
        s = starts[i] if i < len(starts) else 0
        e = ends[i] if i < len(ends) else 0

        if char == " " or char == "\n":
            if current_word:
                words.append({"word": current_word, "start": word_start, "end": word_end})
                current_word = ""
                word_start = None
        else:
            if word_start is None:
                word_start = s
            current_word += char
            word_end = e

    if current_word:
        words.append({"word": current_word, "start": word_start, "end": word_end})

    return words


def generate_voice_from_tip(tip: dict) -> tuple[Path, list[dict]]:
    """Generate narration audio and timestamps from a tip dict."""
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
