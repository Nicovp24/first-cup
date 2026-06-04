"""
agent/main.py

Entry point for a single Nexus Digest run.

Usage:
    python -m agent.main          # run once and exit
    python agent/main.py          # equivalent

The function ``run_agent()`` is also imported by the scheduler so both
manual and scheduled runs share identical logic.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone

import structlog

from agent.graph.graph import build_graph
from agent.graph.nodes import AgentState

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Core async runner
# ---------------------------------------------------------------------------


async def run_agent() -> None:
    """
    Execute a full Nexus Digest pipeline run.

    Steps:
      1. Build an initial :class:`~agent.graph.nodes.AgentState`.
      2. Compile the LangGraph pipeline.
      3. Invoke the graph asynchronously.
      4. Log a structured summary of the run.

    Any unhandled exception is caught, logged, and re-raised so the caller
    (scheduler or CLI) can decide how to respond.
    """
    run_date = datetime.now(tz=timezone.utc).isoformat()
    log = logger.bind(run_date=run_date)
    log.info("agent_run_start")

    initial_state: AgentState = {
        "scraped_items": [],
        "written_posts": [],
        "published_slugs": [],
        "errors": [],
        "run_date": run_date,
    }

    try:
        graph = build_graph()
        log.info("graph_ready")
    except Exception as exc:
        log.error("graph_build_error", error=str(exc))
        raise

    try:
        final_state: AgentState = await graph.ainvoke(initial_state)
    except Exception as exc:
        log.error("graph_invoke_error", error=str(exc))
        raise

    # -----------------------------------------------------------------------
    # Structured summary
    # -----------------------------------------------------------------------
    scraped_count = len(final_state.get("scraped_items") or [])
    written_count = len(final_state.get("written_posts") or [])
    published_slugs = final_state.get("published_slugs") or []
    errors = final_state.get("errors") or []

    log.info(
        "agent_run_complete",
        scraped=scraped_count,
        written=written_count,
        published=len(published_slugs),
        published_slugs=published_slugs,
        error_count=len(errors),
    )

    if errors:
        for error in errors:
            log.warning("run_error_recorded", detail=error)

    if len(errors) > 0 and written_count == 0:
        # Hard failure: nothing was produced
        log.error(
            "agent_run_failed",
            reason="no posts written and errors present",
            errors=errors,
        )
        raise RuntimeError(
            f"Nexus Digest run failed with {len(errors)} error(s): {errors}"
        )


# ---------------------------------------------------------------------------
# Synchronous wrapper
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Synchronous entry point.  Calls :func:`run_agent` via ``asyncio.run``.

    Exits with status code 1 on unhandled error so the process signals
    failure to the OS / container runtime.
    """
    try:
        asyncio.run(run_agent())
    except Exception as exc:
        logger.error("main_fatal_error", error=str(exc))
        sys.exit(1)


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
