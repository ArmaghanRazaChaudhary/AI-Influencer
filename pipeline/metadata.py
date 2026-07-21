from __future__ import annotations

"""
Strip AI-generation metadata from image and video files.
Replicates the "send via Telegram" trick from the guide — same effect,
no need to actually transfer the file anywhere.
Uses exiftool when available, falls back to piexif for JPEG images.
"""

import shutil
import subprocess
from pathlib import Path


def _exiftool_available() -> bool:
    return shutil.which("exiftool") is not None


def strip_metadata(file_path: str | Path) -> Path:
    """Remove all metadata from file in-place. Returns the file path."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if _exiftool_available():
        return _strip_with_exiftool(file_path)

    suffix = file_path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return _strip_jpeg_piexif(file_path)

    # For other formats without exiftool, warn but don't fail
    print(f"[metadata] Warning: exiftool not found. Metadata NOT stripped from {file_path.name}")
    return file_path


def _strip_with_exiftool(file_path: Path) -> Path:
    """Strip all tags using exiftool, overwrite in place."""
    result = subprocess.run(
        ["exiftool", "-all=", "-overwrite_original", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"exiftool failed:\n{result.stderr}")
    return file_path


def _strip_jpeg_piexif(file_path: Path) -> Path:
    """Fallback: remove EXIF from JPEG using piexif."""
    try:
        import piexif
        piexif.remove(str(file_path))
    except ImportError:
        print("[metadata] piexif not installed. Run: pip install piexif")
    except Exception as e:
        print(f"[metadata] piexif error: {e}")
    return file_path


def check_metadata(file_path: str | Path) -> dict:
    """Return metadata dict for inspection (requires exiftool)."""
    file_path = Path(file_path)
    if not _exiftool_available():
        return {"error": "exiftool not found"}
    result = subprocess.run(
        ["exiftool", "-json", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"error": result.stderr}
    import json
    data = json.loads(result.stdout)
    return data[0] if data else {}
