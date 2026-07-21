from __future__ import annotations

"""
Higgsfield AI video generation via official higgsfield_client SDK.
Animates a static image into a short video using preset motion styles.

Models:
  dop-turbo   — fastest, lower quality, good for testing
  dop-preview — balanced quality/speed  (default)
  dop-lite    — lightweight
"""

import urllib.request
from pathlib import Path

import higgsfield_client

from config.settings import (
    HIGGSFIELD_MODEL,
    HIGGSFIELD_MOTION_ID,
    HIGGSFIELD_MOTION_STRENGTH,
    RAW_DIR,
)

# Default prompt for social media influencer animation
ANIMATION_PROMPT = (
    "Animate the person naturally and realistically. Subtle body movement, hair flowing slightly, "
    "natural breathing motion, eyes blinking. The character maintains their exact appearance, "
    "skin texture, clothing, and facial features. No morphing, no style change, photorealistic, "
    "social media quality, smooth motion."
)


def generate_video(
    first_frame_path: str | Path,
    prompt: str = ANIMATION_PROMPT,
    output_name: str | None = None,
) -> Path:
    """
    Animate a static image into a short video using Higgsfield.
    Returns path to the downloaded raw video.
    """
    first_frame_path = Path(first_frame_path)

    # Upload image to Higgsfield CDN
    image_url = higgsfield_client.upload_file(str(first_frame_path))

    # Submit generation job and wait for result
    result = higgsfield_client.subscribe(
        HIGGSFIELD_MODEL,
        {
            "image_urls": [image_url],
            "prompt": prompt,
            "seed": 42,
            "motion_id": HIGGSFIELD_MOTION_ID,
            "motion_strength": HIGGSFIELD_MOTION_STRENGTH,
            "enhance_prompt": True,
        },
    )

    video_url = result["videos"][0]["url"]

    output_name = output_name or f"higgsfield_{first_frame_path.stem}.mp4"
    output_path = RAW_DIR / output_name
    urllib.request.urlretrieve(video_url, output_path)

    return output_path
