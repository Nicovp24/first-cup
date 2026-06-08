"""
agent/graph/nodes.py

LangGraph node functions and the shared AgentState TypedDict.

Each node receives the current AgentState, performs its work, and returns
a (partial) dict that LangGraph merges back into the state.

Nodes:
  - scrape_node  : Run all scrapers in parallel, deduplicate, mark as scraped.
  - write_node   : Generate blog posts from scraped items with Claude.
  - publish_node : Commit and push Markdown files; persist posts to Supabase.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from typing_extensions import TypedDict

from agent.db.posts import PublishedPost, is_published_url, mark_scraped, save_post
from agent.publisher.git_publisher import GitPublisher
from agent.scraper.base import ScrapedItem
from agent.scraper.github_api import GitHubAPIScraper
from agent.scraper.github_trending import GitHubTrendingScraper

try:
    from agent.notifier.telegram import TelegramNotifier  # type: ignore[import]
except ImportError:
    TelegramNotifier = None  # type: ignore[assignment,misc]

try:
    from agent.notifier.email_newsletter import EmailNewsletter  # type: ignore[import]
except ImportError:
    EmailNewsletter = None  # type: ignore[assignment,misc]

try:
    from agent.notifier.linkedin import LinkedInNotifier  # type: ignore[import]
except ImportError:
    LinkedInNotifier = None  # type: ignore[assignment,misc]

# These modules will exist once the rest of the project is complete.
# Import them lazily inside the node functions so missing modules raise
# at runtime (inside the node) rather than at import time.
try:
    from agent.scraper.hackernews import HackerNewsScraper  # type: ignore[import]
except ImportError:
    HackerNewsScraper = None  # type: ignore[assignment,misc]

try:
    from agent.scraper.rss import RSSScraper  # type: ignore[import]
except ImportError:
    RSSScraper = None  # type: ignore[assignment,misc]

try:
    from agent.scraper.reddit import RedditScraper  # type: ignore[import]
except ImportError:
    RedditScraper = None  # type: ignore[assignment,misc]

try:
    from agent.scraper.arxiv import ArXivScraper  # type: ignore[import]
except ImportError:
    ArXivScraper = None  # type: ignore[assignment,misc]

try:
    from agent.scraper.devto import DevToScraper  # type: ignore[import]
except ImportError:
    DevToScraper = None  # type: ignore[assignment,misc]

try:
    from agent.scraper.producthunt import ProductHuntScraper  # type: ignore[import]
except ImportError:
    ProductHuntScraper = None  # type: ignore[assignment,misc]

from agent.writer.writer import DigestWriter  # type: ignore[import]

def _build_ai_client():
    """
    Pick the best available AI client at runtime based on configured API keys.
    Priority: Groq (free, fast) → Claude → Gemini.
    """
    from agent.config import settings as _s
    if _s.groq_api_key:
        from agent.writer.groq_client import GroqClient
        return GroqClient()
    if _s.anthropic_api_key:
        from agent.writer.claude_client import ClaudeClient
        return ClaudeClient()
    if _s.gemini_api_key:
        from agent.writer.gemini_client import GeminiClient
        return GeminiClient()
    raise RuntimeError(
        "No AI API key configured. Set GROQ_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY."
    )

_AIClient = None  # kept for compat; actual client built per-run in write_node

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    """Shared mutable context threaded through the LangGraph pipeline."""

    scraped_items: list[ScrapedItem]
    written_posts: list[PublishedPost]
    published_slugs: list[str]
    errors: list[str]
    run_date: str


# ---------------------------------------------------------------------------
# Node: scrape
# ---------------------------------------------------------------------------


async def scrape_node(state: AgentState) -> dict[str, Any]:
    """
    Execute all scrapers in parallel, deduplicate results, and record each
    unique item in the ``scraped_items`` table.

    Returns a partial state update with ``scraped_items`` and any ``errors``
    appended.
    """
    log = logger.bind(node="scrape", run_date=state.get("run_date"))
    log.info("scrape_node_start")

    errors: list[str] = list(state.get("errors") or [])

    # Build scraper list — only include scrapers whose modules loaded
    scrapers: list[Any] = [
        GitHubTrendingScraper(),
        GitHubAPIScraper(),
    ]
    if HackerNewsScraper is not None:
        scrapers.append(HackerNewsScraper())
    else:
        log.warning("scraper_unavailable", scraper="HackerNewsScraper")

    if RSSScraper is not None:
        scrapers.append(RSSScraper())
    else:
        log.warning("scraper_unavailable", scraper="RSSScraper")

    if RedditScraper is not None:
        scrapers.append(RedditScraper())
    else:
        log.warning("scraper_unavailable", scraper="RedditScraper")

    if ArXivScraper is not None:
        scrapers.append(ArXivScraper())
    else:
        log.warning("scraper_unavailable", scraper="ArXivScraper")

    if DevToScraper is not None:
        scrapers.append(DevToScraper())
    else:
        log.warning("scraper_unavailable", scraper="DevToScraper")

    if ProductHuntScraper is not None:
        scrapers.append(ProductHuntScraper())
    else:
        log.warning("scraper_unavailable", scraper="ProductHuntScraper")

    # Run all scrapers in parallel
    raw_results: list[list[ScrapedItem] | BaseException] = await asyncio.gather(
        *[_run_scraper(s) for s in scrapers],
        return_exceptions=True,
    )

    all_items: list[ScrapedItem] = []
    for scraper, result in zip(scrapers, raw_results):
        scraper_name = type(scraper).__name__
        if isinstance(result, BaseException):
            msg = f"{scraper_name} failed: {result}"
            log.error("scraper_error", scraper=scraper_name, error=str(result))
            errors.append(msg)
        else:
            log.info("scraper_done", scraper=scraper_name, count=len(result))
            all_items.extend(result)

    log.info("scrape_total_raw", count=len(all_items))

    # Deduplicate within this run: same URL from multiple scrapers
    seen_in_run: set[str] = set()
    run_deduped: list[ScrapedItem] = []
    for item in all_items:
        if item.url not in seen_in_run:
            seen_in_run.add(item.url)
            run_deduped.append(item)
    if len(run_deduped) < len(all_items):
        log.info("scrape_intrarun_dedup", removed=len(all_items) - len(run_deduped))
    all_items = run_deduped

    # Deduplicate: skip URLs already published (not just scraped)
    # This allows re-scraping the same sources every run — the AI editor
    # picks the best stories and only published URLs are permanently skipped.
    unique_items: list[ScrapedItem] = []
    dedup_tasks = [is_published_url(item.url) for item in all_items]
    duplicate_flags: list[bool | BaseException] = await asyncio.gather(
        *dedup_tasks, return_exceptions=True
    )

    mark_tasks: list[Any] = []
    for item, flag in zip(all_items, duplicate_flags):
        if isinstance(flag, BaseException):
            log.error("dedup_check_error", url=item.url, error=str(flag))
            unique_items.append(item)
            mark_tasks.append(mark_scraped(item))
        elif not flag:
            unique_items.append(item)
            mark_tasks.append(mark_scraped(item))
        else:
            log.debug("already_published_skipped", url=item.url)

    # Fire-and-forget: mark scraped items concurrently
    if mark_tasks:
        mark_results = await asyncio.gather(*mark_tasks, return_exceptions=True)
        for item, res in zip(unique_items, mark_results):
            if isinstance(res, BaseException):
                log.error("mark_scraped_error", url=item.url, error=str(res))
                errors.append(f"mark_scraped failed for {item.url}: {res}")

    log.info("scrape_node_done", unique_count=len(unique_items))

    return {
        "scraped_items": unique_items,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Node: write
# ---------------------------------------------------------------------------


async def write_node(state: AgentState) -> dict[str, Any]:
    """
    Use DigestWriter (Claude) to turn scraped items into PublishedPost objects.

    Returns a partial state update with ``written_posts`` and any ``errors``
    appended.
    """
    log = logger.bind(node="write", run_date=state.get("run_date"))
    log.info("write_node_start", item_count=len(state.get("scraped_items") or []))

    errors: list[str] = list(state.get("errors") or [])
    scraped_items: list[ScrapedItem] = state.get("scraped_items") or []

    if not scraped_items:
        log.warning("write_node_skipped", reason="no scraped items")
        return {"written_posts": [], "errors": errors}

    written_posts: list[PublishedPost] = []
    try:
        ai_client = _build_ai_client()
        writer = DigestWriter(client=ai_client)
        log.info("write_node_client", client=type(ai_client).__name__)
        written_posts = await writer.write_digest(scraped_items)
        log.info("write_node_done", post_count=len(written_posts))
    except Exception as exc:
        msg = f"DigestWriter.write_digest failed: {exc}"
        log.error("write_node_error", error=str(exc))
        errors.append(msg)

    return {
        "written_posts": written_posts,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Node: publish
# ---------------------------------------------------------------------------


async def publish_node(state: AgentState) -> dict[str, Any]:
    """
    Commit Markdown files to the blog repository and persist posts to Supabase.

    Returns a partial state update with ``published_slugs`` and any ``errors``
    appended.
    """
    log = logger.bind(node="publish", run_date=state.get("run_date"))
    log.info("publish_node_start", post_count=len(state.get("written_posts") or []))

    errors: list[str] = list(state.get("errors") or [])
    written_posts: list[PublishedPost] = state.get("written_posts") or []

    if not written_posts:
        log.warning("publish_node_skipped", reason="no written posts")
        return {"published_slugs": [], "errors": errors}

    published_slugs: list[str] = []

    # -- Push to GitHub via GitPublisher --
    try:
        git_publisher = GitPublisher()
        published_slugs = await git_publisher.publish_posts(written_posts)
        log.info("git_publish_done", slugs=published_slugs)
    except Exception as exc:
        msg = f"GitPublisher.publish_posts failed: {exc}"
        log.error("git_publish_error", error=str(exc))
        errors.append(msg)

    # -- Persist to Supabase (even if git push partially failed) --
    save_tasks = [save_post(post) for post in written_posts]
    save_results = await asyncio.gather(*save_tasks, return_exceptions=True)

    for post, result in zip(written_posts, save_results):
        if isinstance(result, BaseException):
            msg = f"save_post failed for slug '{post.slug}': {result}"
            log.error("save_post_error", slug=post.slug, error=str(result))
            errors.append(msg)
        else:
            log.info("post_persisted", slug=post.slug, post_id=result)

    log.info("publish_node_done", published_count=len(published_slugs))

    return {
        "published_slugs": published_slugs,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Node: notify
# ---------------------------------------------------------------------------


async def notify_node(state: AgentState) -> dict[str, Any]:
    """
    Send Telegram notifications for published posts.

    This node is a no-op when TELEGRAM_BOT_TOKEN is not configured — it logs
    a debug line and returns without modifying the state.

    Returns a partial state update with any ``errors`` appended.
    """
    log = logger.bind(node="notify", run_date=state.get("run_date"))
    log.info("notify_node_start")

    errors: list[str] = list(state.get("errors") or [])
    written_posts: list[PublishedPost] = state.get("written_posts") or []

    if not written_posts:
        log.info("notify_node_skipped", reason="no posts to notify about")
        return {"errors": errors}

    if TelegramNotifier is None:
        log.warning("notify_node_skipped", reason="TelegramNotifier module unavailable")
        return {"errors": errors}

    if TelegramNotifier is not None:
        try:
            notifier = TelegramNotifier()
            await notifier.notify(written_posts)
            log.info("telegram_notify_done", post_count=len(written_posts))
        except Exception as exc:
            errors.append(f"TelegramNotifier.notify failed: {exc}")
            log.error("telegram_notify_error", error=str(exc))

    if LinkedInNotifier is not None:
        try:
            li = LinkedInNotifier()
            sent = await li.post_articles(written_posts)
            log.info("linkedin_notify_done", sent=sent)
        except Exception as exc:
            errors.append(f"LinkedInNotifier.post_articles failed: {exc}")
            log.error("linkedin_notify_error", error=str(exc))

    log.info("notify_node_done")
    return {"errors": errors}


# ---------------------------------------------------------------------------
# Node: email
# ---------------------------------------------------------------------------


async def email_node(state: AgentState) -> dict[str, Any]:
    """
    Send the daily digest + Shots to Premium subscribers via Resend.

    Shots = scraped items that were not selected for full articles.
    No-op when RESEND_API_KEY is not configured or no posts were published.
    """
    log = logger.bind(node="email", run_date=state.get("run_date"))
    log.info("email_node_start")

    errors: list[str] = list(state.get("errors") or [])
    written_posts: list[PublishedPost] = state.get("written_posts") or []
    scraped_items: list[ScrapedItem]   = state.get("scraped_items") or []

    if not written_posts:
        log.info("email_node_skipped", reason="no posts")
        return {"errors": errors}

    if EmailNewsletter is None:
        log.warning("email_node_skipped", reason="EmailNewsletter module unavailable")
        return {"errors": errors}

    # Build shots: scraped items not turned into full articles, sorted by score
    published_urls = {url for p in written_posts for url in (p.source_urls or [])}
    shots = sorted(
        [item for item in scraped_items if item.url not in published_urls],
        key=lambda x: x.score,
        reverse=True,
    )[:8]

    try:
        newsletter = EmailNewsletter()
        sent = await newsletter.send_digest(written_posts, shots)
        log.info("email_node_done", sent=sent, shots=len(shots))
    except Exception as exc:
        msg = f"EmailNewsletter.send_digest failed: {exc}"
        log.error("email_node_error", error=str(exc))
        errors.append(msg)

    return {"errors": errors}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _run_scraper(scraper: Any) -> list[ScrapedItem]:
    """Thin wrapper so gather() gets a coroutine for each scraper."""
    return await scraper.scrape()
