"""
agent/scheduler.py

APScheduler-based scheduler for First Cup.

Jobs:
  - Morning digest  (daily_run_hour, default 07:00)
  - Midday digest   (midday_run_hour, default 13:00)
  - Evening digest  (evening_run_hour, default 20:00)
  - Breaking-news checker (every breaking_news_interval_minutes, default 30 min)

Usage:
    python -m agent.scheduler     # start the scheduler process (blocking)
    python agent/scheduler.py     # equivalent
"""

from __future__ import annotations

import asyncio
import signal
import sys

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from agent.config import settings
from agent.main import run_agent, run_breaking_news

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Job wrapper
# ---------------------------------------------------------------------------


async def _scheduled_job() -> None:
    """Full digest run — called at each scheduled time slot."""
    log = logger.bind(job="daily_digest")
    log.info("scheduled_job_start")
    try:
        await run_agent()
        log.info("scheduled_job_done")
    except Exception as exc:
        log.error("scheduled_job_error", error=str(exc))


async def _breaking_news_job() -> None:
    """Breaking-news check — runs every N minutes, publishes only if truly urgent."""
    log = logger.bind(job="breaking_news")
    log.debug("breaking_news_job_start")
    try:
        await run_breaking_news()
        log.debug("breaking_news_job_done")
    except Exception as exc:
        log.error("breaking_news_job_error", error=str(exc))


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------


def _build_scheduler() -> AsyncIOScheduler:
    """
    Create and configure an :class:`~apscheduler.schedulers.asyncio.AsyncIOScheduler`.

    Scheduled jobs:
    - Morning digest   (daily_run_hour, default 07:00)
    - Midday digest    (midday_run_hour, default 13:00)
    - Evening digest   (evening_run_hour, default 20:00)
    - Breaking-news checker (every breaking_news_interval_minutes, default 30 min)
    """
    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    # -- Three daily full-digest runs --
    for job_id, hour in (
        ("digest_morning", settings.daily_run_hour),
        ("digest_midday",  settings.midday_run_hour),
        ("digest_evening", settings.evening_run_hour),
    ):
        scheduler.add_job(
            _scheduled_job,
            trigger=CronTrigger(hour=hour, minute=settings.daily_run_minute, timezone=settings.timezone),
            id=job_id,
            name=f"First Cup — {job_id.replace('digest_', '')} digest",
            replace_existing=True,
            misfire_grace_time=60 * 30,
            coalesce=True,
        )
        logger.info("digest_job_configured", job_id=job_id, hour=hour, minute=settings.daily_run_minute)

    # -- Breaking-news checker --
    from apscheduler.triggers.interval import IntervalTrigger  # local import to avoid top-level dep
    scheduler.add_job(
        _breaking_news_job,
        trigger=IntervalTrigger(minutes=settings.breaking_news_interval_minutes),
        id="breaking_news",
        name="First Cup — breaking news checker",
        replace_existing=True,
        misfire_grace_time=60 * 5,
        coalesce=True,
    )
    logger.info(
        "breaking_news_job_configured",
        interval_minutes=settings.breaking_news_interval_minutes,
        urgency_threshold=settings.breaking_news_urgency_threshold,
    )

    return scheduler


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def start_scheduler() -> None:
    """
    Start the APScheduler and block indefinitely, waiting for scheduled jobs.

    Handles ``SIGINT`` / ``SIGTERM`` gracefully by shutting down the scheduler
    before exiting.
    """
    scheduler = _build_scheduler()

    # Register OS signal handlers for clean shutdown
    loop = asyncio.get_running_loop()

    def _shutdown(sig_name: str) -> None:
        logger.info("scheduler_shutdown_signal", signal=sig_name)
        if scheduler.running:
            scheduler.shutdown(wait=False)
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig.name)

    scheduler.start()
    morning_job = scheduler.get_job("digest_morning")
    logger.info(
        "scheduler_started",
        next_morning_run=str(morning_job.next_run_time) if morning_job else "unknown",
    )

    # Keep the coroutine alive until the loop is stopped
    try:
        while True:
            await asyncio.sleep(60)
            if scheduler.running:
                job = scheduler.get_job("digest_morning")
                if job is not None:
                    logger.debug(
                        "scheduler_heartbeat",
                        next_run=str(job.next_run_time),
                    )
    except asyncio.CancelledError:
        logger.info("scheduler_cancelled")
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=True)
            logger.info("scheduler_stopped")


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Synchronous entry point for running the scheduler as a script."""
    try:
        asyncio.run(start_scheduler())
    except (KeyboardInterrupt, SystemExit):
        logger.info("scheduler_exit")
        sys.exit(0)
    except Exception as exc:
        logger.error("scheduler_fatal_error", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
