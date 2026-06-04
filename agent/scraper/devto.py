"""
Dev.to scraper – fetches the most popular articles of the last day via the
public Dev.to API (no authentication required).

Uses the ``top=1`` parameter which returns articles ranked by popularity
over the previous day.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

_DEVTO_API_URL = "https://dev.to/api/articles"
_MIN_REACTIONS = 20
_PER_PAGE = 20


class DevToScraper(ScraperBase):
    """
    Fetches popular Dev.to articles published or trending in the last 24 hours.

    The ``top=1`` query parameter instructs the Dev.to API to rank articles
    by popularity over the past day.  Articles with fewer than
    :data:`_MIN_REACTIONS` positive reactions are filtered out.

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: article title
    - ``url``: canonical Dev.to article URL
    - ``summary``: article description
    - ``source``: ``"dev.to"``
    - ``score``: ``positive_reactions_count``
    - ``tags``: ``tag_list`` from the API
    - ``published_at``: parsed from the API ``published_at`` ISO 8601 field
    - ``extra``: ``{"user": str, "reading_time_minutes": int, "comments_count": int}``
    """

    def __init__(
        self,
        *,
        min_reactions: int = _MIN_REACTIONS,
        per_page: int = _PER_PAGE,
    ) -> None:
        super().__init__()
        self._min_reactions = min_reactions
        self._per_page = per_page

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info("scrape_start", source="dev.to")

        params: dict[str, str] = {
            "top": "1",
            "per_page": str(self._per_page),
        }

        try:
            data = await self._fetch_json(_DEVTO_API_URL, params=params)
        except Exception as exc:
            self._log.error("fetch_failed", source="dev.to", detail=str(exc))
            return []

        if not isinstance(data, list):
            self._log.error(
                "unexpected_response_shape",
                source="dev.to",
                got=type(data).__name__,
            )
            return []

        items: list[ScrapedItem] = []
        for article in data:
            try:
                item = self._parse_article(article)
                if item is not None:
                    items.append(item)
            except Exception as exc:
                self._log.warning(
                    "article_parse_error",
                    article_id=article.get("id", "unknown"),
                    detail=str(exc),
                )
                continue

        self._log.info("scrape_done", source="dev.to", item_count=len(items))
        return items

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_article(self, article: dict[str, Any]) -> ScrapedItem | None:
        """Convert a Dev.to API article dict to a ScrapedItem."""
        reactions: int = int(article.get("positive_reactions_count") or 0)
        if reactions < self._min_reactions:
            return None

        title: str = (article.get("title") or "").strip() or "No title"
        url: str = article.get("url") or ""
        description: str = (article.get("description") or "").strip()

        tag_list: list[str] = article.get("tag_list") or []
        # tag_list can be a list of strings or a comma-separated string
        if isinstance(tag_list, str):
            tag_list = [t.strip() for t in tag_list.split(",") if t.strip()]

        # Author info
        user: dict[str, Any] = article.get("user") or {}
        username: str = user.get("username") or article.get("username") or ""

        reading_time: int = int(article.get("reading_time_minutes") or 0)
        comments_count: int = int(article.get("comments_count") or 0)

        # published_at
        published_at_raw: str = article.get("published_at") or ""
        published_at = self._parse_dt(published_at_raw)

        return ScrapedItem(
            title=title,
            url=url,
            summary=description,
            source="dev.to",
            score=float(reactions),
            published_at=published_at,
            tags=tag_list,
            extra={
                "user": username,
                "reading_time_minutes": reading_time,
                "comments_count": comments_count,
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_dt(self, raw: str) -> datetime:
        """
        Parse an ISO 8601 date string into a timezone-aware datetime.

        Falls back to ``datetime.now(UTC)`` and logs a warning if parsing fails.
        """
        if not raw:
            self._log.debug("missing_published_at")
            return datetime.now(tz=timezone.utc)
        try:
            normalized = raw.strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError) as exc:
            self._log.warning("published_at_parse_failed", raw=raw, detail=str(exc))
            return datetime.now(tz=timezone.utc)
