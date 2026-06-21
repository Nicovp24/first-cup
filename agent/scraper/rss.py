"""
RSS scraper – fetches multiple feeds in parallel and returns recent articles.

For each feed up to 3 articles published in the last 24 hours are included.
Uses ``feedparser`` for feed parsing and ``httpx`` (via the base class) for
the actual HTTP download so that the shared timeout / headers config applies.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import structlog

from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

RSS_FEEDS: list[str] = [
    # ── AI / Research ──────────────────────────────────────────────
    "https://simonwillison.net/atom/everything/",        # LLM tracking, imprescindible
    "https://huggingface.co/blog/feed.xml",              # HF releases
    "https://www.technologyreview.com/feed/",            # MIT Tech Review
    # ── Tech news con sustancia ────────────────────────────────────
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    # ── Dev / open source ──────────────────────────────────────────
    "https://lobste.rs/rss",                             # Lobsters: curated tech
    "https://github.blog/feed/",                         # GitHub blog oficial
    "https://tldr.tech/api/rss/tech",                    # TLDR Tech
    "https://thenewstack.io/feed/",                      # The New Stack: infra/cloud
    # ── Seguridad ──────────────────────────────────────────────────
    "https://krebsonsecurity.com/feed/",                 # Krebs: seguridad
    "https://www.schneier.com/blog/atom.xml",            # Schneier on Security
]

_ARTICLES_PER_FEED = 5
_SUMMARY_MAX_CHARS = 300
_LOOKBACK_HOURS = 48


class RSSScraper(ScraperBase):
    """
    Fetches a configurable list of RSS / Atom feeds and returns recent articles.

    All feeds are fetched concurrently.  For each feed, only articles
    published within the last :data:`_LOOKBACK_HOURS` hours are returned,
    up to :data:`_ARTICLES_PER_FEED` per feed.

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: article title
    - ``url``: article link
    - ``summary``: first 300 chars of content/summary
    - ``source``: feed hostname (e.g. ``"simonwillison.net"``)
    - ``score``: ``1.0`` (RSS feeds have no numeric ranking signal)
    - ``tags``: tags/categories from the feed entry
    - ``extra``: ``{"feed_url": str, "feed_title": str, "author": str}``
    """

    def __init__(
        self,
        feed_urls: list[str] | None = None,
        *,
        articles_per_feed: int = _ARTICLES_PER_FEED,
        lookback_hours: int = _LOOKBACK_HOURS,
    ) -> None:
        super().__init__()
        self._feed_urls: list[str] = feed_urls if feed_urls is not None else RSS_FEEDS
        self._articles_per_feed = articles_per_feed
        self._lookback_hours = lookback_hours

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info(
            "scrape_start",
            source="rss",
            feed_count=len(self._feed_urls),
        )

        # Fetch all feeds concurrently; individual failures are caught per-feed
        tasks = [self._scrape_feed(url) for url in self._feed_urls]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[list[ScrapedItem]] = []
        for url, result in zip(self._feed_urls, raw_results):
            if isinstance(result, BaseException):
                self._log.error("feed_gather_error", url=url, detail=str(result))
            else:
                results.append(result)

        # Flatten and sort by published_at descending
        all_items: list[ScrapedItem] = [
            item for feed_items in results for item in feed_items
        ]
        all_items.sort(key=lambda i: i.published_at, reverse=True)

        self._log.info("scrape_done", source="rss", item_count=len(all_items))
        return all_items

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _scrape_feed(self, feed_url: str) -> list[ScrapedItem]:
        """Download and parse a single feed URL."""
        self._log.debug("fetching_feed", url=feed_url)

        try:
            raw_xml = await self._fetch(feed_url)
        except Exception as exc:
            self._log.error(
                "feed_fetch_failed", url=feed_url, detail=str(exc)
            )
            return []

        try:
            return self._parse_feed(raw_xml, feed_url)
        except Exception as exc:
            self._log.error(
                "feed_parse_failed", url=feed_url, detail=str(exc)
            )
            return []

    def _parse_feed(self, raw_xml: str, feed_url: str) -> list[ScrapedItem]:
        """Parse raw feed XML and return up to _articles_per_feed recent items."""
        parsed = feedparser.parse(raw_xml)

        feed_title: str = parsed.feed.get("title", "") if hasattr(parsed, "feed") else ""
        source_host: str = self._host_from_url(feed_url)

        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=self._lookback_hours)

        items: list[ScrapedItem] = []
        for entry in parsed.entries:
            if len(items) >= self._articles_per_feed:
                break

            try:
                published_at = self._parse_entry_date(entry)
            except Exception as exc:
                self._log.debug(
                    "entry_date_parse_failed",
                    feed=feed_url,
                    entry_id=entry.get("id", ""),
                    detail=str(exc),
                )
                # Skip entries whose date we cannot determine
                continue

            if published_at < cutoff:
                # Feeds are usually ordered newest-first; we can stop early
                # but some feeds are not ordered, so we continue checking all
                continue

            try:
                item = self._build_item(entry, feed_url, feed_title, source_host, published_at)
                items.append(item)
            except Exception as exc:
                self._log.warning(
                    "entry_build_failed",
                    feed=feed_url,
                    entry_id=entry.get("id", ""),
                    detail=str(exc),
                )
                continue

        self._log.debug(
            "feed_parsed",
            url=feed_url,
            total_entries=len(parsed.entries),
            recent_items=len(items),
        )
        return items

    def _build_item(
        self,
        entry: Any,
        feed_url: str,
        feed_title: str,
        source_host: str,
        published_at: datetime,
    ) -> ScrapedItem:
        """Convert a feedparser entry to a ScrapedItem."""
        title: str = entry.get("title", "No title").strip()

        # Link: prefer 'link' attribute; fall back to 'id' if it looks like a URL
        link: str = entry.get("link", "")
        if not link:
            entry_id: str = entry.get("id", "")
            if entry_id.startswith("http"):
                link = entry_id

        summary = self._extract_summary(entry)
        author: str = entry.get("author", "")

        # Collect tags / categories
        tags: list[str] = []
        for tag_obj in entry.get("tags", []):
            term = tag_obj.get("term", "")
            if term and term not in tags:
                tags.append(term)

        return ScrapedItem(
            title=title,
            url=link,
            summary=summary,
            source=source_host,
            score=1.0,
            published_at=published_at,
            tags=tags,
            extra={
                "feed_url": feed_url,
                "feed_title": feed_title,
                "author": author,
            },
        )

    # --- date parsing --------------------------------------------------

    def _parse_entry_date(self, entry: Any) -> datetime:
        """
        Return a timezone-aware datetime from a feedparser entry.

        Tries, in order:
        1. ``published_parsed`` (time.struct_time)
        2. ``updated_parsed`` (time.struct_time)
        3. ``published`` raw string (RFC 2822 / ISO 8601)
        4. ``updated`` raw string

        Raises :class:`ValueError` if none of the above succeed.
        """
        import calendar
        import time as _time

        # feedparser provides *_parsed as UTC time.struct_time
        for attr in ("published_parsed", "updated_parsed"):
            struct = entry.get(attr)
            if struct is not None:
                try:
                    timestamp = calendar.timegm(struct)
                    return datetime.fromtimestamp(timestamp, tz=timezone.utc)
                except (TypeError, OverflowError, OSError):
                    continue

        # Fall back to raw string fields
        for attr in ("published", "updated"):
            raw: str = entry.get(attr, "")
            if raw:
                dt = self._try_parse_date_string(raw)
                if dt is not None:
                    return dt

        raise ValueError("No parseable date field found in feed entry")

    @staticmethod
    def _try_parse_date_string(raw: str) -> datetime | None:
        """Try RFC 2822 then ISO 8601 parsing; return None on failure."""
        # RFC 2822 (e.g. "Mon, 02 Jan 2006 15:04:05 +0000")
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

        # ISO 8601 (e.g. "2006-01-02T15:04:05Z", "2006-01-02T15:04:05+00:00")
        try:
            normalized = raw.strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            pass

        return None

    # --- summary extraction --------------------------------------------

    def _extract_summary(self, entry: Any) -> str:
        """
        Build a plain-text summary from the entry.

        Priority: ``summary`` → ``content[0].value`` → ``title``.
        HTML tags are stripped and the result is truncated to
        :data:`_SUMMARY_MAX_CHARS` characters.
        """
        raw = ""

        # feedparser 'summary' field
        summary_raw: str = entry.get("summary", "")
        if summary_raw:
            raw = summary_raw
        else:
            # feedparser 'content' is a list of dicts
            content_list = entry.get("content", [])
            if content_list and isinstance(content_list, list):
                raw = content_list[0].get("value", "")

        if not raw:
            return ""

        cleaned = self._strip_html(raw)
        return cleaned[:_SUMMARY_MAX_CHARS].strip()

    @staticmethod
    def _strip_html(html: str) -> str:
        """Remove HTML tags and collapse whitespace."""
        no_tags = re.sub(r"<[^>]+>", " ", html)
        collapsed = re.sub(r"\s+", " ", no_tags)
        return collapsed.strip()

    # --- utility -------------------------------------------------------

    @staticmethod
    def _host_from_url(url: str) -> str:
        """Extract the hostname from a URL for use as the ``source`` field."""
        match = re.search(r"https?://(?:www\.)?([^/]+)", url)
        return match.group(1) if match else url
