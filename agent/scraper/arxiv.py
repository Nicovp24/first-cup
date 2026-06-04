"""
ArXiv scraper – fetches recent papers from cs.AI, cs.LG and cs.CL using the
ArXiv Atom/XML API and returns those published in the last 24 hours.

No third-party XML library is required; the standard-library
``xml.etree.ElementTree`` is used for parsing.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

_ARXIV_API_URL = "http://export.arxiv.org/api/query"
_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_NS = "http://arxiv.org/schemas/atom"
_OPENSEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"

_QUERY = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL"
_MAX_RESULTS = 20
_LOOKBACK_HOURS = 24
_ABSTRACT_MAX_CHARS = 400


class ArXivScraper(ScraperBase):
    """
    Queries the ArXiv Atom API for recent papers in AI/ML/NLP categories.

    Only papers whose ``published`` date falls within the last 24 hours are
    returned.  All items receive a ``score`` of ``1.0`` (no numeric ranking
    signal from ArXiv).

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: paper title (whitespace-normalised)
    - ``url``: canonical ArXiv HTML page (``https://arxiv.org/abs/<id>``)
    - ``summary``: abstract truncated to 400 characters
    - ``source``: ``"arxiv"``
    - ``score``: ``1.0``
    - ``tags``: ArXiv category codes (e.g. ``["cs.AI", "cs.LG"]``)
    - ``extra``: ``{"authors": list[str], "pdf_url": str, "arxiv_id": str}``
    """

    def __init__(
        self,
        *,
        max_results: int = _MAX_RESULTS,
        lookback_hours: int = _LOOKBACK_HOURS,
    ) -> None:
        super().__init__()
        self._max_results = max_results
        self._lookback_hours = lookback_hours

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info("scrape_start", source="arxiv")

        params: dict[str, str] = {
            "search_query": _QUERY,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(self._max_results),
        }

        try:
            raw_xml = await self._fetch(_ARXIV_API_URL, params=params)
        except Exception as exc:
            self._log.error("fetch_failed", source="arxiv", detail=str(exc))
            return []

        try:
            items = self._parse_feed(raw_xml)
        except Exception as exc:
            self._log.error("parse_failed", source="arxiv", detail=str(exc))
            return []

        self._log.info("scrape_done", source="arxiv", item_count=len(items))
        return items

    # ------------------------------------------------------------------
    # XML parsing
    # ------------------------------------------------------------------

    def _parse_feed(self, raw_xml: str) -> list[ScrapedItem]:
        """Parse the ArXiv Atom feed and return papers from the last 24 h."""
        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError as exc:
            self._log.error("xml_parse_error", detail=str(exc))
            return []

        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=self._lookback_hours)
        items: list[ScrapedItem] = []

        for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
            try:
                item = self._parse_entry(entry, cutoff)
                if item is not None:
                    items.append(item)
            except Exception as exc:
                entry_id = self._text(entry, f"{{{_ATOM_NS}}}id") or "unknown"
                self._log.warning(
                    "entry_parse_error", entry_id=entry_id, detail=str(exc)
                )
                continue

        return items

    def _parse_entry(
        self, entry: ET.Element, cutoff: datetime
    ) -> ScrapedItem | None:
        """Convert a single Atom <entry> element into a ScrapedItem."""
        # Published date
        published_str = self._text(entry, f"{{{_ATOM_NS}}}published") or ""
        published_at = self._parse_dt(published_str)
        if published_at is None:
            self._log.debug("entry_no_date", raw=published_str)
            return None

        if published_at < cutoff:
            return None

        # Title
        title = self._clean_whitespace(
            self._text(entry, f"{{{_ATOM_NS}}}title") or "No title"
        )

        # Abstract
        abstract_raw = self._text(entry, f"{{{_ATOM_NS}}}summary") or ""
        summary = self._clean_whitespace(abstract_raw)[:_ABSTRACT_MAX_CHARS]

        # ArXiv ID and canonical URL
        raw_id = self._text(entry, f"{{{_ATOM_NS}}}id") or ""
        arxiv_id = self._extract_arxiv_id(raw_id)
        abs_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else raw_id
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else ""

        # Authors
        authors: list[str] = []
        for author_el in entry.findall(f"{{{_ATOM_NS}}}author"):
            name = self._text(author_el, f"{{{_ATOM_NS}}}name") or ""
            if name:
                authors.append(name.strip())

        # Categories / tags
        tags: list[str] = []
        for cat_el in entry.findall(f"{{{_ATOM_NS}}}category"):
            term = cat_el.get("term", "")
            if term and term not in tags:
                tags.append(term)

        return ScrapedItem(
            title=title,
            url=abs_url,
            summary=summary,
            source="arxiv",
            score=1.0,
            published_at=published_at,
            tags=tags,
            extra={
                "authors": authors,
                "pdf_url": pdf_url,
                "arxiv_id": arxiv_id,
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _text(element: ET.Element, tag: str) -> str | None:
        """Return the stripped text content of a child element, or None."""
        child = element.find(tag)
        if child is None or child.text is None:
            return None
        return child.text.strip()

    @staticmethod
    def _parse_dt(raw: str) -> datetime | None:
        """Parse an ISO 8601 date string into a timezone-aware datetime."""
        if not raw:
            return None
        try:
            normalized = raw.strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _extract_arxiv_id(raw_id: str) -> str:
        """
        Extract the paper ID (e.g. ``2406.12345``) from an ArXiv URI.

        ArXiv IDs appear at the end of URLs like:
        ``http://arxiv.org/abs/2406.12345v1``
        """
        match = re.search(r"arxiv\.org/abs/([^\s]+)", raw_id, re.IGNORECASE)
        if match:
            # Strip version suffix (v1, v2, …)
            return re.sub(r"v\d+$", "", match.group(1))
        return raw_id

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        """Collapse internal newlines / tabs / runs of spaces into single spaces."""
        return re.sub(r"\s+", " ", text).strip()
