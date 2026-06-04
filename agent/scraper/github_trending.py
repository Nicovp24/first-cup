"""
Scraper for GitHub Trending – parses the public trending page via BeautifulSoup4.

Returns the top-10 trending repositories for today (daily window, English).
The ``score`` field is set to the number of stars gained today.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import structlog
from bs4 import BeautifulSoup, Tag

from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

_TRENDING_URL = "https://github.com/trending?since=daily&spoken_language_code=en"
_GITHUB_BASE = "https://github.com"
_TOP_N = 10


class GitHubTrendingScraper(ScraperBase):
    """
    Scrapes https://github.com/trending and returns the top-10 repositories
    trending today.

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: ``owner/repo``
    - ``url``: full GitHub repo URL
    - ``summary``: repository description (empty string if not provided)
    - ``source``: ``"github_trending"``
    - ``score``: stars earned today (0.0 if not parseable)
    - ``tags``: primary language, if detected
    - ``extra``: ``{"language": str, "total_stars": int, "forks": int}``
    """

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info("scrape_start", source="github_trending", url=_TRENDING_URL)

        try:
            html = await self._fetch(_TRENDING_URL)
        except Exception as exc:
            self._log.error("fetch_failed", source="github_trending", detail=str(exc))
            return []

        items = self._parse(html)
        self._log.info(
            "scrape_done", source="github_trending", item_count=len(items)
        )
        return items

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse(self, html: str) -> list[ScrapedItem]:
        """Parse the trending page HTML and return up to _TOP_N ScrapedItems."""
        soup = BeautifulSoup(html, "lxml")
        repo_list = soup.select("article.Box-row")

        if not repo_list:
            self._log.warning(
                "no_repo_rows_found",
                hint="GitHub may have changed its HTML structure",
            )
            return []

        items: list[ScrapedItem] = []
        now = datetime.now(tz=timezone.utc)

        for article in repo_list[:_TOP_N]:
            try:
                item = self._parse_article(article, now)
                if item is not None:
                    items.append(item)
            except Exception as exc:
                self._log.warning(
                    "article_parse_error",
                    detail=str(exc),
                    html_snippet=str(article)[:200],
                )
                continue

        return items

    def _parse_article(self, article: Tag, now: datetime) -> ScrapedItem | None:
        """Extract a single ScrapedItem from an <article> tag."""

        # --- repo path (owner/repo) ---
        name_tag = article.select_one("h2 a")
        if name_tag is None:
            self._log.debug("missing_name_tag")
            return None

        # href is like "/owner/repo"
        href = name_tag.get("href", "").strip()
        if not href or href.count("/") < 2:
            self._log.debug("unexpected_href", href=href)
            return None

        repo_path = href.lstrip("/")  # "owner/repo"
        repo_url = f"{_GITHUB_BASE}/{repo_path}"
        title = repo_path

        # --- description ---
        desc_tag = article.select_one("p.col-9")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # --- primary language ---
        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else ""

        # --- stars today ---
        stars_today = self._parse_stars_today(article)

        # --- total stars (optional, for extra) ---
        total_stars = self._parse_total_stars(article)

        # --- forks (optional, for extra) ---
        forks = self._parse_forks(article)

        tags: list[str] = [language] if language else []

        return ScrapedItem(
            title=title,
            url=repo_url,
            summary=description,
            source="github_trending",
            score=float(stars_today),
            published_at=now,
            tags=tags,
            extra={
                "language": language,
                "total_stars": total_stars,
                "forks": forks,
            },
        )

    # --- small extractors ----------------------------------------------

    def _parse_stars_today(self, article: Tag) -> int:
        """Return the number of stars earned today, or 0 on parse failure."""
        try:
            # The "stars today" span usually contains text like "123 stars today"
            for span in article.select("span"):
                text = span.get_text(strip=True)
                if "stars today" in text.lower() or "star today" in text.lower():
                    match = re.search(r"([\d,]+)", text)
                    if match:
                        return int(match.group(1).replace(",", ""))
        except Exception as exc:
            self._log.debug("stars_today_parse_error", detail=str(exc))
        return 0

    def _parse_total_stars(self, article: Tag) -> int:
        """Return total star count from the article's star link, or 0."""
        try:
            star_link = article.select_one("a[href$='/stargazers']")
            if star_link:
                text = star_link.get_text(strip=True).replace(",", "").replace("k", "000")
                match = re.search(r"([\d]+)", text)
                if match:
                    return int(match.group(1))
        except Exception as exc:
            self._log.debug("total_stars_parse_error", detail=str(exc))
        return 0

    def _parse_forks(self, article: Tag) -> int:
        """Return fork count, or 0."""
        try:
            fork_link = article.select_one("a[href$='/forks']")
            if fork_link:
                text = fork_link.get_text(strip=True).replace(",", "")
                match = re.search(r"([\d]+)", text)
                if match:
                    return int(match.group(1))
        except Exception as exc:
            self._log.debug("forks_parse_error", detail=str(exc))
        return 0
