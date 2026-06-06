"""
agent/main.py

Entry point for a single First Cup run.

Usage:
    python -m agent.main          # run once and exit
    python agent/main.py          # equivalent

The function ``run_agent()`` is also imported by the scheduler so both
manual and scheduled runs share identical logic.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from agent.config import settings
from agent.db.posts import is_published_url, save_post
from agent.graph.graph import build_graph
from agent.graph.nodes import AgentState
from agent.publisher.git_publisher import GitPublisher
from agent.scraper.base import ScrapedItem

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Core async runner
# ---------------------------------------------------------------------------


async def run_agent() -> None:
    """
    Execute a full First Cup pipeline run.

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
            f"First Cup run failed with {len(errors)} error(s): {errors}"
        )


# ---------------------------------------------------------------------------
# Breaking-news pipeline
# ---------------------------------------------------------------------------


async def run_breaking_news() -> None:
    """
    Lightweight pipeline that runs every N minutes looking for truly urgent news.

    Flow:
      1. Scrape all sources (same scrapers as the full run).
      2. Filter to items published in the last 2 hours that haven't been published yet.
      3. Ask Claude to score each item for urgency (1-10).
      4. For any item scoring >= settings.breaking_news_urgency_threshold:
         write and publish immediately, WITHOUT waiting for the next scheduled run.

    This function is intentionally fire-and-forget safe: errors are logged
    but never raise so APScheduler keeps the job running.
    """
    log = logger.bind(mode="breaking_news")
    log.info("breaking_news_check_start")

    # -- Lazy imports so module loads even if optional deps are missing --
    try:
        from agent.graph.nodes import scrape_node, AgentState as _AgentState
        from agent.writer.writer import DigestWriter
        from agent.writer.prompts import PROMPT_URGENCY_CHECK
    except ImportError as exc:
        log.warning("breaking_news_deps_missing", error=str(exc))
        return

    try:
        from agent.writer.gemini_client import GeminiClient as _AIClient
    except ImportError:
        try:
            from agent.writer.claude_client import ClaudeClient as _AIClient  # type: ignore[assignment]
        except ImportError:
            log.warning("breaking_news_ai_client_missing")
            return

    # 1. Scrape (reuse the same node logic)
    empty_state: Any = {
        "scraped_items": [],
        "written_posts": [],
        "published_slugs": [],
        "errors": [],
        "run_date": datetime.now(tz=timezone.utc).isoformat(),
    }
    try:
        scrape_result = await scrape_node(empty_state)
    except Exception as exc:
        log.error("breaking_news_scrape_failed", error=str(exc))
        return

    all_items: list[ScrapedItem] = scrape_result.get("scraped_items") or []

    # 2. Filter to items published in the last 2 hours
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=2)
    recent = [
        item for item in all_items
        if item.published_at.tzinfo is not None and item.published_at >= cutoff
    ]

    if not recent:
        log.info("breaking_news_no_recent_items")
        return

    # 3. Remove items already published as a post
    pub_checks = await asyncio.gather(
        *[is_published_url(item.url) for item in recent],
        return_exceptions=True,
    )
    unpublished = [
        item for item, already in zip(recent, pub_checks)
        if not (isinstance(already, bool) and already)
    ]

    if not unpublished:
        log.info("breaking_news_all_already_published", checked=len(recent))
        return

    # 4. Ask Claude to score urgency
    rows = [
        {
            "index": i,
            "title": item.title,
            "url": item.url,
            "summary": item.summary,
            "source": item.source,
            "score": item.score,
            "published_at": item.published_at.isoformat(),
            "tags": item.tags,
        }
        for i, item in enumerate(unpublished)
    ]
    prompt = PROMPT_URGENCY_CHECK.format(items_json=json.dumps(rows, ensure_ascii=False, indent=2))

    try:
        client = _AIClient()
        raw = await client.complete(prompt)
    except Exception as exc:
        log.error("breaking_news_urgency_call_failed", error=str(exc))
        return

    try:
        from agent.writer.writer import _extract_json  # type: ignore[attr-defined]
        parsed: dict = _extract_json(raw)  # type: ignore[assignment]
    except Exception as exc:
        log.error("breaking_news_urgency_parse_failed", error=str(exc), raw=raw[:200])
        return

    if not parsed.get("has_breaking"):
        log.info("breaking_news_nothing_urgent")
        return

    urgent_indices = [
        entry["index"]
        for entry in (parsed.get("urgent_items") or [])
        if entry.get("urgency_score", 0) >= settings.breaking_news_urgency_threshold
    ]

    if not urgent_indices:
        log.info("breaking_news_below_threshold")
        return

    urgent_items = [unpublished[i] for i in urgent_indices if i < len(unpublished)]
    log.info("breaking_news_urgent_found", count=len(urgent_items), titles=[i.title for i in urgent_items])

    # 5. Write and publish
    try:
        writer = DigestWriter(client=_AIClient())
        posts = await writer.write_digest(urgent_items)
    except Exception as exc:
        log.error("breaking_news_write_failed", error=str(exc))
        return

    if not posts:
        log.warning("breaking_news_writer_returned_empty")
        return

    try:
        git_publisher = GitPublisher()
        slugs = await git_publisher.publish_posts(posts)
        log.info("breaking_news_published", slugs=slugs)
    except Exception as exc:
        log.error("breaking_news_publish_failed", error=str(exc))
        return

    save_results = await asyncio.gather(
        *[save_post(post) for post in posts],
        return_exceptions=True,
    )
    for post, res in zip(posts, save_results):
        if isinstance(res, BaseException):
            log.error("breaking_news_save_failed", slug=post.slug, error=str(res))
        else:
            log.info("breaking_news_saved", slug=post.slug)


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
