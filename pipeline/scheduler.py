"""
APScheduler-based posting scheduler.
Spreads posts across the day with randomised offsets to mimic human behaviour.
"""

import random
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import POSTS_PER_DAY

logger = logging.getLogger(__name__)

# Peak engagement windows by hour (24h). Scheduler picks from these.
_PEAK_HOURS = [8, 12, 17, 19, 21]


def _pick_post_times(n: int) -> list[tuple[int, int]]:
    """Return n (hour, minute) pairs spread across peak windows."""
    hours = random.sample(_PEAK_HOURS, min(n, len(_PEAK_HOURS)))
    hours.sort()
    return [(h, random.randint(0, 59)) for h in hours]


def build_scheduler(run_pipeline_fn) -> BlockingScheduler:
    """
    Create and configure the APScheduler instance.

    Args:
        run_pipeline_fn: Callable that executes one full content pipeline run.

    Returns:
        Configured BlockingScheduler (not yet started).
    """
    scheduler = BlockingScheduler(timezone="UTC")
    post_times = _pick_post_times(POSTS_PER_DAY)

    for i, (hour, minute) in enumerate(post_times):
        # Add ±5 min jitter each day to avoid pattern detection
        jitter_minutes = random.randint(-5, 5)
        trigger = CronTrigger(
            hour=hour,
            minute=max(0, minute + jitter_minutes),
            jitter=300,  # APScheduler built-in jitter: ±5 min
        )
        scheduler.add_job(
            run_pipeline_fn,
            trigger=trigger,
            id=f"post_job_{i}",
            name=f"Post slot {i+1} (~{hour:02d}:{minute:02d} UTC)",
            max_instances=1,
            coalesce=True,
        )
        logger.info("Scheduled post slot %d at ~%02d:%02d UTC", i + 1, hour, minute)

    return scheduler


def run_once_now(run_pipeline_fn) -> None:
    """Trigger a single pipeline run immediately — useful for testing."""
    logger.info("Running pipeline immediately (manual trigger)")
    run_pipeline_fn()
