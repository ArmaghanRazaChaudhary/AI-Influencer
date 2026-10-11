from __future__ import annotations

"""
LivePair generation backend — set IMAGE_BACKEND=livepair / VIDEO_BACKEND=livepair.

LivePair (livepairai.com) exposes image and video generation as one prepaid
balance: text-to-image, image-to-image (identity-preserving edits off a
reference), and image-to-video on open-weight models, billed per result —
no monthly subscription, renders auto-delete server-side after 48 hours.

Why it fits this pipeline:
  * i2i models (*-edit ids) keep the persona's face consistent across scenes
    the same way gpt-image-1 edits do — pass the face photo as `image` and
    describe the scene.
  * i2v animates the approved still in the same call shape — a first frame
    becomes a 5s clip without a second provider.
  * Per-result pricing (~cents/image) suits batch character pages.

Auth: `LP_KEY` env — create a key at https://livepairai.com/settings.
Source images are vision-screened server-side — use your own owned photos
or AI-generated faces, per https://livepairai.com terms.
"""

import base64
import json
import mimetypes
import time
import urllib.error
import urllib.request
from pathlib import Path

from config.settings import (
    LIVEPAIR_API_KEY,
    LIVEPAIR_BASE_URL,
    LIVEPAIR_IMAGE_MODEL,
    LIVEPAIR_VIDEO_MODEL,
    RAW_DIR,
)

_POLL_INTERVAL_S = 2.0
_POLL_TIMEOUT_S = 300.0


def _request(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{LIVEPAIR_BASE_URL}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            "x-api-key": LIVEPAIR_API_KEY or "",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read()).get("error", "")
        except Exception:
            pass
        raise RuntimeError(f"livepair HTTP {e.code}: {detail}") from e


def _poll(job_id: str) -> str:
    deadline = time.time() + _POLL_TIMEOUT_S
    while time.time() < deadline:
        data = _request("GET", f"/v1/agent/jobs/{job_id}")
        if data.get("status") == "done" and data.get("url"):
            return data["url"]
        if data.get("status") == "failed":
            raise RuntimeError(f"livepair job failed: {data.get('error', 'unknown')}")
        time.sleep(_POLL_INTERVAL_S)
    raise TimeoutError(f"livepair job {job_id} did not finish in {_POLL_TIMEOUT_S}s")


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _submit(model_id: str, prompt: str, **extra) -> str:
    body = {"modelId": model_id, "prompt": prompt, **extra}
    res = _request("POST", "/v1/agent/generate", body)
    if res.get("url"):
        return res["url"]
    job_id = res.get("jobId")
    if not job_id:
        raise RuntimeError(f"livepair returned no job: {res}")
    return _poll(job_id)


def _download(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    return output_path


def generate_scene_image(
    scene_prompt: str,
    face_path: str | Path,
    output_name: str | None = None,
) -> Path:
    """Face photo + scene prompt → persona image (i2i identity-preserving edit)."""
    output_name = output_name or f"livepair_frame_{int(time.time())}.png"
    url = _submit(
        LIVEPAIR_IMAGE_MODEL,
        scene_prompt,
        image=_data_uri(Path(face_path)),
    )
    return _download(url, RAW_DIR / output_name)


def generate_scene_image_t2i(
    scene_prompt: str,
    output_name: str | None = None,
    model_id: str | None = None,
) -> Path:
    """Prompt-only scene render — for building a persona from a written spec."""
    output_name = output_name or f"livepair_t2i_{int(time.time())}.png"
    url = _submit(model_id or "qwen-image-3", scene_prompt)
    return _download(url, RAW_DIR / output_name)


def generate_video(
    first_frame_path: str | Path,
    prompt: str,
    output_name: str | None = None,
    duration: int = 5,
) -> Path:
    """Animate an approved still — the clip inherits the persona's face."""
    output_name = output_name or f"livepair_clip_{int(time.time())}.mp4"
    url = _submit(
        LIVEPAIR_VIDEO_MODEL,
        prompt,
        image=_data_uri(Path(first_frame_path)),
        duration=duration,
    )
    return _download(url, RAW_DIR / output_name)
