"""
Scraper for Hacker News via the Algolia HN Search API.

Fetches the top-10 stories from the last 24 hours with more than 100 points,
sorted by points descending.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

_HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
_HN_ITEM_BASE = "https://news.ycombinator.com/item?id="
_MIN_POINTS = 100
_TOP_N = 10


class HackerNewsScraper(ScraperBase):
    """
    Queries the HN Algolia API for high-scoring stories published in the last
    24 hours and returns the top-10 sorted by points descending.

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: story title
    - ``url``: original article URL (falls back to HN item URL)
    - ``summary``: story text excerpt if available, else empty string
    - ``source``: ``"hackernews"``
    - ``score``: ``points``
    - ``tags``: ``["hacker_news"]`` plus the story's own tags from Algolia
    - ``extra``: ``{"hn_url", "author", "num_comments", "objectID"}``
    """

    def __init__(
        self,
        *,
        min_points: int = _MIN_POINTS,
        top_n: int = _TOP_N,
    ) -> None:
        super().__init__()
        self._min_points = min_points
        self._top_n = top_n

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info("scrape_start", source="hackernews")

        # Unix timestamp for 24 hours ago
        timestamp_24h = int(time.time()) - int(timedelta(hours=24).total_seconds())

        params: dict[str, str] = {
            "tags": "story",
            "numericFilters": f"points>{self._min_points},created_at_i>{timestamp_24h}",
            "hitsPerPage": str(self._top_n),
        }

        self._log.debug(
            "hn_query_params",
            min_points=self._min_points,
            timestamp_cutoff=timestamp_24h,
        )

        try:
            data = await self._fetch_json(_HN_ALGOLIA_URL, params=params)
        except Exception as exc:
            self._log.error("fetch_failed", source="hackernews", detail=str(exc))
            return []

        if not isinstance(data, dict):
            self._log.error("unexpected_response_type", got=type(data).__name__)
            return []

        items = self._parse_response(data)
        self._log.info("scrape_done", source="hackernews", item_count=len(items))
        return items

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, data: dict[str, Any]) -> list[ScrapedItem]:
        """Convert the Algolia API response into a sorted list of ScrapedItems."""
        hits: list[dict[str, Any]] = data.get("hits", [])
        if not hits:
            self._log.warning(
                "no_hits_in_response",
                nb_hits=data.get("nbHits", 0),
            )
            return []

        # Sort by points descending (Algolia may return by relevance)
        hits_sorted = sorted(hits, key=lambda h: int(h.get("points") or 0), reverse=True)

        items: list[ScrapedItem] = []
        for hit in hits_sorted[: self._top_n]:
            try:
                item = self._parse_hit(hit)
                items.append(item)
            except Exception as exc:
                self._log.warning(
                    "hit_parse_error",
                    object_id=hit.get("objectID", "unknown"),
                    detail=str(exc),
                )
                continue

        return items

    def _parse_hit(self, hit: dict[str, Any]) -> ScrapedItem:
        """Convert a single Algolia hit to a ScrapedItem."""
        object_id: str = str(hit.get("objectID", ""))
        title: str = hit.get("title") or hit.get("story_title") or "No title"

        # Use the external URL when available; fall back to the HN item page
        external_url: str = hit.get("url") or ""
        hn_url: str = f"{_HN_ITEM_BASE}{object_id}" if object_id else ""
        url: str = external_url if external_url else hn_url

        # Summary: story_text is the self-post body (HTML); clean it up
        raw_text: str = hit.get("story_text") or ""
        summary = self._clean_html(raw_text)[:500] if raw_text else ""

        points: int = int(hit.get("points") or 0)
        author: str = hit.get("author") or ""
        num_comments: int = int(hit.get("num_comments") or 0)

        # Algolia tags: usually ["story", "author_X", "story_Y"]
        algolia_tags: list[str] = hit.get("_tags") or []
        tags: list[str] = ["hacker_news"] + [
            t for t in algolia_tags if not t.startswith("author_") and t != "story"
        ]

        # Timestamp
        created_at_unix: int | None = hit.get("created_at_i")
        if created_at_unix:
            published_at = datetime.fromtimestamp(created_at_unix, tz=timezone.utc)
        else:
            created_at_str: str = hit.get("created_at") or ""
            try:
                published_at = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                self._log.debug(
                    "created_at_parse_failed",
                    raw=created_at_str,
                    object_id=object_id,
                )
                published_at = datetime.now(tz=timezone.utc)

        return ScrapedItem(
            title=title,
            url=url,
            summary=summary,
            source="hackernews",
            score=float(points),
            published_at=published_at,
            tags=tags,
            extra={
                "hn_url": hn_url,
                "author": author,
                "num_comments": num_comments,
                "objectID": object_id,
            },
        )

    @staticmethod
    def _clean_html(raw: str) -> str:
        """Strip basic HTML tags from a story_text field."""
        import re

        # Replace block-level tags with spaces so words don't merge
        cleaned = re.sub(r"<(p|br|div|li)[^>]*>", " ", raw, flags=re.IGNORECASE)
        # Remove all remaining tags
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        # Collapse whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
