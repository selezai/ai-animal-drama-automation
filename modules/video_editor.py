"""
Video Editor — FFmpeg compositing (FREE)
Concatenates scene clips, overlays voiceover audio, burns in captions.
"""
import logging
import subprocess
from pathlib import Path
from datetime import datetime

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)


def _find_ffmpeg() -> str:
    """Find FFmpeg binary — checks PATH, /tmp, and FFMPEG_PATH env var."""
    import os
    import shutil
    custom = os.getenv("FFMPEG_PATH")
    if custom and Path(custom).exists():
        return custom
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    if Path("/tmp/ffmpeg").exists():
        return "/tmp/ffmpeg"
    raise FileNotFoundError(
        "FFmpeg not found. Install it or set FFMPEG_PATH env var."
    )


def _run_ffmpeg(args: list[str]) -> None:
    """Run FFmpeg and raise on failure."""
    ffmpeg = _find_ffmpeg()
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")


def concat_clips(clip_paths: list[Path]) -> Path:
    """Concatenate video clips into a single video."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    concat_file = OUTPUT_DIR / "video" / f"concat_{ts}.txt"
    output = OUTPUT_DIR / "video" / f"joined_{ts}.mp4"

    concat_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in clip_paths)
    )

    _run_ffmpeg([
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output),
    ])

    concat_file.unlink(missing_ok=True)
    logger.info(f"Concatenated {len(clip_paths)} clips → {output.name}")
    return output


def overlay_audio(video_path: Path, audio_path: Path) -> Path:
    """Replace video audio track with voiceover. Trim to shorter duration."""
    output = video_path.with_name(video_path.stem + "_voiced.mp4")

    _run_ffmpeg([
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output),
    ])

    logger.info(f"Audio overlaid → {output.name}")
    return output


def generate_subtitles(script: dict) -> Path:
    """Generate SRT file from script scenes."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    srt_path = OUTPUT_DIR / "final" / f"subs_{ts}.srt"
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    idx = 1
    for scene in script.get("scenes", []):
        dialogue = scene.get("dialogue", "").strip()
        if not dialogue:
            continue

        # Parse "0-3s" → 0, 3
        parts = scene.get("timestamp", "0-5s").replace("s", "").split("-")
        start = int(parts[0])
        end = int(parts[1]) if len(parts) > 1 else start + 5

        lines.append(str(idx))
        lines.append(f"00:00:{start:02d},000 --> 00:00:{end:02d},000")
        lines.append(dialogue)
        lines.append("")
        idx += 1

    srt_path.write_text("\n".join(lines))
    return srt_path


def burn_subtitles(video_path: Path, srt_path: Path) -> Path:
    """Burn SRT subtitles into video — mobile-friendly large white text."""
    output = video_path.with_name(video_path.stem + "_captioned.mp4")

    style = (
        "FontSize=22,FontName=Arial,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=40"
    )

    _run_ffmpeg([
        "-i", str(video_path),
        "-vf", f"subtitles={srt_path}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output),
    ])

    logger.info(f"Subtitles burned → {output.name}")
    return output


def composite(clip_paths: list[Path], audio_path: Path,
              script: dict) -> Path:
    """
    Full composite pipeline:
    1. Concatenate scene clips
    2. Overlay voiceover audio
    3. Burn in captions
    Returns path to final video.
    """
    character = script.get("character", "unknown")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    joined = concat_clips(clip_paths)
    voiced = overlay_audio(joined, audio_path)

    srt = generate_subtitles(script)
    final = burn_subtitles(voiced, srt)

    # Move to final output
    final_path = OUTPUT_DIR / "final" / f"{character}_{ts}.mp4"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final.rename(final_path)

    # Cleanup intermediates
    for tmp in [joined, voiced, srt]:
        tmp.unlink(missing_ok=True)

    logger.info(f"Final video: {final_path.name} ({final_path.stat().st_size} bytes)")
    return final_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Verifies FFmpeg is available
    _run_ffmpeg(["-version"])
    print("FFmpeg OK")
