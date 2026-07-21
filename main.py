from __future__ import annotations

"""
AI Influencer Pipeline — Orchestrator

Full pipeline per run:
  1. Load persona JSON → content_director decides today's scene
  2. Generate scene image with influencer's face (gpt-image-1)
  3. Animate into a short video (Higgsfield)
  4. Post-process with ffmpeg (grain/sharpness/brightness/vignette)
  5. Strip metadata (exiftool)
  6. Generate caption in persona's voice (Claude)
  7. Post to X + Instagram
  8. Record to SQLite
"""

import argparse
import json
import logging
import random
import sys
from pathlib import Path

from config.settings import BASE_DIR, FACES_DIR, NICHE
from db.state import init_db, create_job, update_job, register_persona
from pipeline.content_director import decide as direct_content
from pipeline.face_gen import create_first_frame
from pipeline.video_gen import generate_video
from pipeline.postprocess import process_video, check_ffmpeg
from pipeline.metadata import strip_metadata
from pipeline.caption_gen import generate_caption, generate_caption_for_persona
from pipeline.poster import post
from pipeline.scheduler import build_scheduler, run_once_now

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

PERSONAS_DIR = BASE_DIR / "personas"


def _pick_random_persona() -> Path:
    personas = list(PERSONAS_DIR.glob("*.json"))
    if not personas:
        raise FileNotFoundError(f"No persona JSON files found in {PERSONAS_DIR}")
    return random.choice(personas)


def _pick_random_face() -> Path:
    files = [f for f in FACES_DIR.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")]
    if not files:
        raise FileNotFoundError(f"No face images found in {FACES_DIR}")
    return random.choice(files)


def run_pipeline(
    persona_path: Path | None = None,
    face_path: Path | None = None,
    platforms: list[str] | None = None,
) -> int:
    """Execute one full pipeline run for a persona. Returns the job_id."""

    # --- 1. Load persona + decide today's content ---
    persona_path = persona_path or _pick_random_persona()
    persona = json.loads(persona_path.read_text(encoding="utf-8"))
    logger.info("Persona: %s (%s)", persona["name"], persona["niche"])

    logger.info("[0/6] Content director deciding today's scene...")
    decision = direct_content(persona_path)
    logger.info("Scene: %s | Mood: %s", decision.location, decision.mood)
    logger.info("Prompt: %s", decision.scene_prompt[:120])

    # Face: persona's own face takes priority, then explicit override, then random
    face_path = face_path or BASE_DIR / persona.get("face", "") or _pick_random_face()
    if not face_path.exists():
        logger.warning("Persona face not found at %s, picking randomly", face_path)
        face_path = _pick_random_face()
    logger.info("Face: %s", face_path.name)

    job_id = create_job(persona["niche"], str(face_path), decision.scene_prompt)
    update_job(job_id, status="running")

    try:
        # --- 2. Generate scene image ---
        logger.info("[1/6] Generating scene image via gpt-image-1...")
        first_frame = create_first_frame(face_path, prompt=decision.scene_prompt)
        update_job(job_id, raw_path=str(first_frame))

        # --- 3. Animate into video ---
        logger.info("[2/6] Generating video via Higgsfield...")
        raw_video = generate_video(first_frame)
        update_job(job_id, raw_path=str(raw_video), status="generated")

        # --- 4. Post-process with ffmpeg ---
        logger.info("[3/6] Applying post-processing (grain/sharpness/vignette)...")
        final_video = process_video(raw_video)
        update_job(job_id, final_path=str(final_video))

        # --- 5. Strip metadata ---
        logger.info("[4/6] Stripping AI metadata...")
        strip_metadata(final_video)

        # --- 6. Generate caption in persona's voice ---
        logger.info("[5/6] Generating caption for %s...", persona["name"])
        caption = generate_caption_for_persona(
            persona=persona,
            context=decision.caption_context,
        )
        update_job(job_id, caption=caption)
        logger.info("Caption: %s", caption[:120])

        # --- 7. Post ---
        platforms = platforms or ["x", "instagram"]
        logger.info("[6/6] Posting to: %s", platforms)
        post_ids = post(caption, final_video, platforms=platforms)
        update_job(
            job_id,
            status="posted",
            platform=",".join(post_ids.keys()),
            post_id=",".join(post_ids.values()),
        )
        logger.info("Posted successfully: %s", post_ids)

    except Exception as exc:
        logger.error("Pipeline failed for job %d: %s", job_id, exc, exc_info=True)
        update_job(job_id, status="failed", error=str(exc))
        raise

    return job_id


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Influencer Pipeline")
    parser.add_argument(
        "--run-now", action="store_true",
        help="Execute one pipeline run immediately and exit",
    )
    parser.add_argument(
        "--platforms", nargs="+", default=["x", "instagram"],
        choices=["x", "instagram"],
        help="Platforms to post to",
    )
    parser.add_argument(
        "--persona", type=Path, default=None,
        help="Path to a persona JSON (default: random from personas/)",
    )
    parser.add_argument(
        "--face", type=Path, default=None,
        help="Override face image (default: from persona JSON)",
    )
    args = parser.parse_args()

    if not check_ffmpeg():
        logger.error("ffmpeg not found. Install it and ensure it is on PATH.")
        sys.exit(1)

    init_db()

    # Auto-register all personas found in personas/ into the DB
    for pf in PERSONAS_DIR.glob("*.json"):
        try:
            p = json.loads(pf.read_text(encoding="utf-8"))
            register_persona(
                persona_id=p["id"],
                name=p["name"],
                niche=p["niche"],
                json_path=str(pf),
                face_dir=str(BASE_DIR / p.get("face_dir", "")),
            )
        except Exception:
            pass

    if args.run_now:
        run_once_now(lambda: run_pipeline(args.persona, args.face, args.platforms))
        return

    logger.info(
        "Starting scheduler (POSTS_PER_DAY=%d)...",
        __import__("config.settings", fromlist=["POSTS_PER_DAY"]).POSTS_PER_DAY,
    )
    scheduler = build_scheduler(lambda: run_pipeline(platforms=args.platforms))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
