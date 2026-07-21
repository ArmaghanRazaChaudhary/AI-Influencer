from __future__ import annotations

"""
Scene image generation — supports two backends:
  - "api"     : OpenAI gpt-image-1 (default, pay per image)
  - "chatgpt" : ChatGPT web UI via Playwright (uses subscription, no per-image cost)

Set IMAGE_BACKEND in .env to switch.
"""

import base64
import time
from pathlib import Path

from openai import OpenAI

from config.settings import OPENAI_API_KEY, IMAGE_BACKEND, RAW_DIR

client = OpenAI(api_key=OPENAI_API_KEY)

_MERGE_PROMPT = (
    "Integrate a face into an existing scene. Substitute the face in the reference image "
    "with the face from the donor image. The objective is a seamless merge: the new face "
    "must inherit the exact expression, pose, and lighting interaction from the reference, "
    "while its color attributes (hair and eyes) are adapted from the donor for a perfectly "
    "harmonious and natural result. Photo taken on an iPhone, photorealistic, natural skin texture."
)

_FIRST_FRAME_PROMPT = (
    "Create a high-quality lifestyle photo of this exact person. Keep their face, hair, skin tone, "
    "and features identical. Place them in a natural, candid pose — slightly turned, relaxed body "
    "language, authentic expression. Photorealistic, shot on iPhone, natural lighting, social media "
    "quality. The person is real, alive, not a doll or CGI."
)

_IDENTITY_PREFIX = (
    "This is a specific real person — preserve their exact face, hair color, skin tone, eye color, "
    "and facial features with complete accuracy. Do not alter or idealize their appearance. "
)
_IDENTITY_SUFFIX = (
    " The result must look like a candid lifestyle photo of this exact person in that scene, "
    "not a model or stock photo. Photorealistic, shot on iPhone, natural lighting."
)


def _save_b64(b64_data: str, output_path: Path) -> Path:
    output_path.write_bytes(base64.b64decode(b64_data))
    return output_path


def merge_faces(
    base_path: str | Path,
    donor_path: str | Path,
    output_name: str | None = None,
    prompt: str = _MERGE_PROMPT,
) -> Path:
    """Merge donor face onto base face image using gpt-image-1. Returns path to merged image."""
    base_path = Path(base_path)
    donor_path = Path(donor_path)
    output_name = output_name or f"merged_{int(time.time())}.png"
    output_path = RAW_DIR / output_name

    with open(base_path, "rb") as base_f, open(donor_path, "rb") as donor_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=[base_f, donor_f],
            prompt=prompt,
            n=1,
            size="1024x1024",
        )

    return _save_b64(response.data[0].b64_json, output_path)


def create_first_frame(
    face_path: str | Path,
    output_name: str | None = None,
    prompt: str = _FIRST_FRAME_PROMPT,
) -> Path:
    """
    Generate a scene image from a face photo.

    Routes to the active backend:
      IMAGE_BACKEND=api      → OpenAI gpt-image-1 (default)
      IMAGE_BACKEND=chatgpt  → ChatGPT web UI via Playwright
    """
    if IMAGE_BACKEND == "chatgpt":
        from pipeline.chatgpt_image_gen import generate_image
        # Use the scene prompt directly — chatgpt_image_gen handles identity wrapping
        scene = prompt if prompt != _FIRST_FRAME_PROMPT else "A natural, candid lifestyle portrait."
        return generate_image(scene, face_path, output_name)

    # --- OpenAI API backend ---
    face_path = Path(face_path)
    output_name = output_name or f"first_frame_{int(time.time())}.png"
    output_path = RAW_DIR / output_name

    if prompt != _FIRST_FRAME_PROMPT:
        full_prompt = _IDENTITY_PREFIX + prompt + _IDENTITY_SUFFIX
    else:
        full_prompt = prompt

    with open(face_path, "rb") as f:
        response = client.images.edit(
            model="gpt-image-1",
            image=f,
            prompt=full_prompt,
            n=1,
            size="1024x1024",
        )

    return _save_b64(response.data[0].b64_json, output_path)
