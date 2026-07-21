from __future__ import annotations

"""
ffmpeg-based post-processing to remove the AI "plastic" look.
Applies grain, sharpness, brightness correction, and vignette.
"""

import subprocess
import shutil
from pathlib import Path
from config.settings import POSTPROCESS, FINAL_DIR


def _build_vf(grain: int, sharpness: int, brightness: float, vignette: int) -> str:
    """Build the ffmpeg -vf filter chain."""
    filters = []

    # Brightness/contrast via eq filter (-1.0 to 1.0 range; we convert from -20..20 scale)
    brightness_norm = brightness / 100.0
    filters.append(f"eq=brightness={brightness_norm:.3f}")

    # Sharpness via unsharp mask (luma_amount 0-1.5 range; map 0-100 → 0-1.5)
    sharp_amount = (sharpness / 100.0) * 1.5
    filters.append(f"unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount={sharp_amount:.3f}")

    # Film grain via noise filter (c0s = luma noise strength)
    grain_strength = int(grain * 0.4)  # scale 0-100 → 0-40 for noise strength
    filters.append(f"noise=c0s={grain_strength}:c0f=t+u")

    # Vignette (strength mapped from 0-100 → 0-PI/2)
    import math
    vignette_angle = (vignette / 100.0) * (math.pi / 2)
    filters.append(f"vignette=PI*{vignette_angle / math.pi:.4f}")

    return ",".join(filters)


def process_video(
    input_path: str | Path,
    output_path: str | Path | None = None,
    grain: int | None = None,
    sharpness: int | None = None,
    brightness: int | None = None,
    vignette: int | None = None,
) -> Path:
    """
    Apply post-processing to a video and return the output path.

    Defaults come from config.settings.POSTPROCESS so the guide values
    (grain=40, sharpness=20, brightness=-7, vignette=12) are used unless overridden.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    grain = grain if grain is not None else POSTPROCESS["grain"]
    sharpness = sharpness if sharpness is not None else POSTPROCESS["sharpness"]
    brightness = brightness if brightness is not None else POSTPROCESS["brightness"]
    vignette = vignette if vignette is not None else POSTPROCESS["vignette"]

    if output_path is None:
        output_path = FINAL_DIR / f"{input_path.stem}_processed{input_path.suffix}"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    vf = _build_vf(grain, sharpness, brightness, vignette)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", "18",          # near-lossless
        "-preset", "slow",
        "-c:a", "copy",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    return output_path


def process_image(
    input_path: str | Path,
    output_path: str | Path | None = None,
    grain: int | None = None,
    sharpness: int | None = None,
    brightness: int | None = None,
    vignette: int | None = None,
) -> Path:
    """Apply post-processing to a still image (for image posts)."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    grain = grain if grain is not None else POSTPROCESS["grain"]
    sharpness = sharpness if sharpness is not None else POSTPROCESS["sharpness"]
    brightness = brightness if brightness is not None else POSTPROCESS["brightness"]
    vignette = vignette if vignette is not None else POSTPROCESS["vignette"]

    if output_path is None:
        output_path = FINAL_DIR / f"{input_path.stem}_processed{input_path.suffix}"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    vf = _build_vf(grain, sharpness, brightness, vignette)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-frames:v", "1",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    return output_path


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None
