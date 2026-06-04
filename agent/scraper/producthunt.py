"""
Product Hunt scraper – retrieves today's top products via the GraphQL API.

Primary strategy: unauthenticated POST to the Product Hunt GraphQL endpoint.
Fallback strategy: HTML scraping of https://www.producthunt.com using
BeautifulSoup when the API returns an authentication error or any non-2xx
response.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

_GQL_URL = "https://api.producthunt.com/v2/api/graphql"
_PH_HOME = "https://www.producthunt.com"

_GQL_QUERY = """
{
  posts(first: 10, order: VOTES) {
    edges {
      node {
        id
        name
        tagline
        url
        votesCount
        topics {
          edges {
            node {
              name
            }
          }
        }
        createdAt
      }
    }
  }
}
"""


class ProductHuntScraper(ScraperBase):
    """
    Fetches today's top-10 Product Hunt posts ordered by votes.

    **Primary path**: sends an unauthenticated POST to the Product Hunt
    GraphQL API.  If this returns an HTTP error or an ``errors`` key in
    the response, the scraper falls back to HTML scraping.

    **Fallback path**: downloads the Product Hunt homepage and parses product
    names, taglines and links with BeautifulSoup.  ``beautifulsoup4`` must be
    installed (it is already a common dependency in scraping projects).

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: product name
    - ``url``: product URL on Product Hunt
    - ``summary``: product tagline
    - ``source``: ``"producthunt"``
    - ``score``: vote count (``0.0`` when scraped from HTML)
    - ``tags``: topic names
    - ``published_at``: ``createdAt`` from the API, or ``datetime.now(UTC)``
      for the HTML fallback
    - ``extra``: ``{"ph_id": str}`` (empty dict for the HTML fallback)
    """

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info("scrape_start", source="producthunt")

        items = await self._scrape_graphql()
        if items:
            self._log.info("scrape_done", source="producthunt", path="graphql", item_count=len(items))
            return items

        self._log.info("graphql_failed_falling_back_to_html", source="producthunt")
        items = await self._scrape_html()
        self._log.info("scrape_done", source="producthunt", path="html", item_count=len(items))
        return items

    # ------------------------------------------------------------------
    # GraphQL path
    # ------------------------------------------------------------------

    async def _scrape_graphql(self) -> list[ScrapedItem]:
        """Attempt to fetch products via the GraphQL API without auth."""
        payload: dict[str, Any] = {"query": _GQL_QUERY}

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.post(_GQL_URL, json=payload, headers=headers)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
        except httpx.HTTPStatusError as exc:
            self._log.warning(
                "graphql_http_error",
                status_code=exc.response.status_code,
                detail=str(exc),
            )
            return []
        except httpx.RequestError as exc:
            self._log.warning("graphql_request_error", detail=str(exc))
            return []
        except ValueError as exc:
            self._log.warning("graphql_json_decode_error", detail=str(exc))
            return []

        # GraphQL errors block
        if data.get("errors"):
            self._log.warning(
                "graphql_response_errors", errors=data["errors"]
            )
            return []

        return self._parse_graphql_response(data)

    def _parse_graphql_response(self, data: dict[str, Any]) -> list[ScrapedItem]:
        """Convert the GraphQL response into ScrapedItems."""
        try:
            edges: list[dict[str, Any]] = (
                data.get("data", {}).get("posts", {}).get("edges", [])
            )
        except AttributeError:
            self._log.warning("unexpected_graphql_shape")
            return []

        items: list[ScrapedItem] = []
        for edge in edges:
            try:
                node: dict[str, Any] = edge.get("node") or {}
                item = self._node_to_item(node)
                if item is not None:
                    items.append(item)
            except Exception as exc:
                self._log.warning(
                    "node_parse_error",
                    node_id=edge.get("node", {}).get("id", "unknown"),
                    detail=str(exc),
                )
                continue

        return items

    def _node_to_item(self, node: dict[str, Any]) -> ScrapedItem | None:
        """Convert a single GraphQL post node to a ScrapedItem."""
        name: str = (node.get("name") or "").strip()
        tagline: str = (node.get("tagline") or "").strip()
        url: str = node.get("url") or ""
        votes: int = int(node.get("votesCount") or 0)
        ph_id: str = str(node.get("id") or "")

        if not name:
            return None

        # Topics
        topics_data: dict[str, Any] = node.get("topics") or {}
        topic_edges: list[dict[str, Any]] = topics_data.get("edges") or []
        tags: list[str] = []
        for te in topic_edges:
            topic_name = (te.get("node") or {}).get("name") or ""
            if topic_name and topic_name not in tags:
                tags.append(topic_name)

        # createdAt
        created_at_raw: str = node.get("createdAt") or ""
        published_at = self._parse_dt(created_at_raw)

        return ScrapedItem(
            title=name,
            url=url,
            summary=tagline,
            source="producthunt",
            score=float(votes),
            published_at=published_at,
            tags=tags,
            extra={"ph_id": ph_id},
        )

    # ------------------------------------------------------------------
    # HTML fallback
    # ------------------------------------------------------------------

    async def _scrape_html(self) -> list[ScrapedItem]:
        """Scrape product cards from the Product Hunt homepage."""
        try:
            html = await self._fetch(_PH_HOME)
        except Exception as exc:
            self._log.error("html_fetch_failed", source="producthunt", detail=str(exc))
            return []

        try:
            return self._parse_html(html)
        except Exception as exc:
            self._log.error("html_parse_failed", source="producthunt", detail=str(exc))
            return []

    def _parse_html(self, html: str) -> list[ScrapedItem]:
        """
        Parse product listings from the Product Hunt homepage HTML.

        Uses BeautifulSoup with the ``html.parser`` backend (stdlib, no lxml
        required).  Falls back to a regex approach if BeautifulSoup is not
        installed.
        """
        try:
            from bs4 import BeautifulSoup  # type: ignore[import]
            return self._parse_html_bs4(html)
        except ImportError:
            self._log.warning(
                "beautifulsoup4_not_installed",
                detail="pip install beautifulsoup4 for better HTML parsing",
            )
            return self._parse_html_regex(html)

    def _parse_html_bs4(self, html: str) -> list[ScrapedItem]:
        """BeautifulSoup-based parser for the Product Hunt homepage."""
        from bs4 import BeautifulSoup  # type: ignore[import]

        soup = BeautifulSoup(html, "html.parser")
        items: list[ScrapedItem] = []
        now = datetime.now(tz=timezone.utc)

        # Product Hunt renders post cards in <a> tags with data-test="post-name"
        # or inside list items with a specific structure.  We look for <a> links
        # whose href starts with "/posts/" and that have a meaningful text content.
        seen_urls: set[str] = set()

        for anchor in soup.find_all("a", href=re.compile(r"^/posts/[^/]+")):
            href: str = anchor.get("href", "")
            full_url = f"https://www.producthunt.com{href}"

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Try to find the product name: the first non-empty text node that
            # isn't just a number (vote count).
            texts = [t.strip() for t in anchor.stripped_strings]
            name = ""
            tagline = ""
            for t in texts:
                if not t:
                    continue
                # Skip pure-number strings (vote counts)
                if re.match(r"^\d+$", t):
                    continue
                if not name:
                    name = t
                elif not tagline and t != name:
                    tagline = t
                    break

            if not name:
                continue

            items.append(
                ScrapedItem(
                    title=name,
                    url=full_url,
                    summary=tagline,
                    source="producthunt",
                    score=0.0,
                    published_at=now,
                    tags=[],
                    extra={},
                )
            )

            if len(items) >= 10:
                break

        self._log.debug("html_bs4_parsed", item_count=len(items))
        return items

    def _parse_html_regex(self, html: str) -> list[ScrapedItem]:
        """Minimal regex fallback for extracting /posts/ links."""
        now = datetime.now(tz=timezone.utc)
        seen: set[str] = set()
        items: list[ScrapedItem] = []

        for match in re.finditer(
            r'href="(/posts/[a-z0-9\-]+)"[^>]*>([^<]{3,80})</a>',
            html,
        ):
            slug = match.group(1)
            full_url = f"https://www.producthunt.com{slug}"
            if full_url in seen:
                continue
            seen.add(full_url)

            name = match.group(2).strip()
            if not name or re.match(r"^\d+$", name):
                continue

            items.append(
                ScrapedItem(
                    title=name,
                    url=full_url,
                    summary="",
                    source="producthunt",
                    score=0.0,
                    published_at=now,
                    tags=[],
                    extra={},
                )
            )
            if len(items) >= 10:
                break

        return items

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_dt(self, raw: str) -> datetime:
        """Parse an ISO 8601 date string; returns ``datetime.now(UTC)`` on failure."""
        if not raw:
            return datetime.now(tz=timezone.utc)
        try:
            normalized = raw.strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError) as exc:
            self._log.warning("created_at_parse_failed", raw=raw, detail=str(exc))
            return datetime.now(tz=timezone.utc)
