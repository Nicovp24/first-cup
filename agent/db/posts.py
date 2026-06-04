"""
agent/db/posts.py

CRUD operations for the `posts` and `scraped_items` tables in Supabase.

All functions are async-compatible: Supabase-py's synchronous client is
wrapped with asyncio.to_thread so callers can await them without blocking
the event loop.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import structlog

from agent.db.supabase_client import get_client
from agent.scraper.base import ScrapedItem

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class PublishedPost:
    """Represents a digest post ready to be stored and published."""

    title: str
    slug: str
    content: str
    description: str
    source_urls: list[str]
    tags: list[str]
    published_at: datetime
    cover: str = ""
    id: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _post_to_row(post: PublishedPost) -> dict:
    """Serialise a PublishedPost into a Supabase-compatible dict."""
    row: dict = {
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "description": post.description,
        "source_urls": post.source_urls,
        "tags": post.tags,
        "published_at": post.published_at.isoformat(),
    }
    if post.cover:
        row["cover"] = post.cover
    return row


def _row_to_post(row: dict) -> PublishedPost:
    """Deserialise a Supabase row into a PublishedPost."""
    published_at = row.get("published_at")
    if isinstance(published_at, str):
        published_at = datetime.fromisoformat(published_at)

    return PublishedPost(
        id=str(row.get("id", "")),
        title=row.get("title", ""),
        slug=row.get("slug", ""),
        content=row.get("content", ""),
        description=row.get("description", ""),
        source_urls=row.get("source_urls") or [],
        tags=row.get("tags") or [],
        published_at=published_at or datetime.now(tz=timezone.utc),
        cover=row.get("cover") or "",
    )


# ---------------------------------------------------------------------------
# Public CRUD functions
# ---------------------------------------------------------------------------


async def save_post(post: PublishedPost) -> str:
    """
    Insert a post into the ``posts`` table.

    Args:
        post: The post to persist.

    Returns:
        The UUID (string) of the newly inserted row.

    Raises:
        Exception: Re-raised after logging on Supabase error.
    """
    row = _post_to_row(post)
    log = logger.bind(slug=post.slug, title=post.title)

    try:
        def _insert() -> list[dict]:
            client = get_client()
            response = client.table("posts").insert(row).execute()
            return response.data

        data = await asyncio.to_thread(_insert)

        inserted_id = str(data[0]["id"]) if data else ""
        log.info("post_saved", post_id=inserted_id)
        return inserted_id

    except Exception as exc:
        log.error("save_post_error", error=str(exc))
        raise


async def is_duplicate(url: str) -> bool:
    """
    Check whether a URL has already been scraped and recorded.

    Args:
        url: The canonical URL to look up.

    Returns:
        ``True`` if the URL exists in ``scraped_items``, ``False`` otherwise.
    """
    try:
        def _query() -> list[dict]:
            client = get_client()
            response = (
                client.table("scraped_items")
                .select("id")
                .eq("url", url)
                .limit(1)
                .execute()
            )
            return response.data

        data = await asyncio.to_thread(_query)
        found = len(data) > 0
        logger.debug("is_duplicate_check", url=url, found=found)
        return found

    except Exception as exc:
        # On error be conservative: treat as non-duplicate so scraping continues
        logger.error("is_duplicate_error", url=url, error=str(exc))
        return False


async def mark_scraped(item: ScrapedItem) -> None:
    """
    Record a scraped URL so it is skipped on future runs (deduplication).

    Args:
        item: The ScrapedItem whose URL should be recorded.
    """
    row = {
        "url": item.url,
        "title": item.title,
        "source": item.source,
        "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    log = logger.bind(url=item.url, source=item.source)

    try:
        def _upsert() -> None:
            client = get_client()
            # Upsert on `url` to avoid unique constraint violations if called
            # concurrently or on retry.
            client.table("scraped_items").upsert(row, on_conflict="url").execute()

        await asyncio.to_thread(_upsert)
        log.debug("mark_scraped_ok")

    except Exception as exc:
        log.error("mark_scraped_error", error=str(exc))
        raise


async def get_recent_posts(days: int = 7) -> list[PublishedPost]:
    """
    Retrieve posts published within the last ``days`` days.

    Args:
        days: Window size in days (default 7).

    Returns:
        List of :class:`PublishedPost` objects ordered by ``published_at`` DESC.
    """
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()
    log = logger.bind(days=days, cutoff=cutoff)

    try:
        def _query() -> list[dict]:
            client = get_client()
            response = (
                client.table("posts")
                .select("*")
                .gte("published_at", cutoff)
                .order("published_at", desc=True)
                .execute()
            )
            return response.data

        rows = await asyncio.to_thread(_query)
        posts = [_row_to_post(r) for r in rows]
        log.info("get_recent_posts_ok", count=len(posts))
        return posts

    except Exception as exc:
        log.error("get_recent_posts_error", error=str(exc))
        raise
