"""
agent/scheduler.py

APScheduler-based daily scheduler for Nexus Digest.

The scheduler runs ``run_agent()`` once per day at the time configured via
``settings.DAILY_RUN_HOUR`` and ``settings.DAILY_RUN_MINUTE`` in the
``settings.TIMEZONE`` timezone.

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
from agent.main import run_agent

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Job wrapper
# ---------------------------------------------------------------------------


async def _scheduled_job() -> None:
    """
    Wrapper executed by APScheduler on each scheduled tick.

    Catches all exceptions so APScheduler does not mark the job as broken
    and continues to schedule future runs.
    """
    log = logger.bind(job="daily_digest")
    log.info("scheduled_job_start")
    try:
        await run_agent()
        log.info("scheduled_job_done")
    except Exception as exc:
        log.error("scheduled_job_error", error=str(exc))


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------


def _build_scheduler() -> AsyncIOScheduler:
    """
    Create and configure an :class:`~apscheduler.schedulers.asyncio.AsyncIOScheduler`
    with the daily digest job.

    Returns:
        A configured (but not yet started) scheduler instance.
    """
    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    trigger = CronTrigger(
        hour=settings.daily_run_hour,
        minute=settings.daily_run_minute,
        timezone=settings.timezone,
    )

    scheduler.add_job(
        _scheduled_job,
        trigger=trigger,
        id="daily_digest",
        name="Nexus Digest — daily run",
        replace_existing=True,
        misfire_grace_time=60 * 30,   # 30-minute grace window
        coalesce=True,                 # run at most once if multiple misfires
    )

    logger.info(
        "scheduler_configured",
        job_id="daily_digest",
        hour=settings.daily_run_hour,
        minute=settings.daily_run_minute,
        timezone=settings.timezone,
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
    logger.info(
        "scheduler_started",
        next_run=str(
            scheduler.get_job("daily_digest").next_run_time  # type: ignore[union-attr]
        ),
    )

    # Keep the coroutine alive until the loop is stopped
    try:
        while True:
            await asyncio.sleep(60)
            if scheduler.running:
                job = scheduler.get_job("daily_digest")
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
