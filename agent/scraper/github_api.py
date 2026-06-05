"""
Scraper for GitHub Search API.

Finds the 10 most-starred Python or JavaScript repositories created in the
last 24 hours with at least 50 stars, using the authenticated Search API.

Requires the GITHUB_TOKEN environment variable to be set.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

_SEARCH_URL = "https://api.github.com/search/repositories"
_GITHUB_BASE = "https://github.com"
_TOP_N = 15
_MIN_STARS = 500


class GitHubAPIScraper(ScraperBase):
    """
    Queries the GitHub Search API for recently-created, high-starred repos.

    The search window is the last 24 hours.  Only Python and JavaScript
    repositories with at least :data:`_MIN_STARS` stars are considered.

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: ``owner/repo``
    - ``url``: full GitHub repo URL
    - ``summary``: repository description
    - ``source``: ``"github_api"``
    - ``score``: ``stargazers_count``
    - ``tags``: primary language
    - ``extra``: ``{"language", "forks_count", "open_issues_count", "topics"}``
    """

    def __init__(
        self,
        *,
        github_token: str | None = None,
        min_stars: int = _MIN_STARS,
        top_n: int = _TOP_N,
    ) -> None:
        token = github_token or os.environ.get("GITHUB_TOKEN", "")
        auth_headers: dict[str, str] = {}
        if token:
            auth_headers["Authorization"] = f"token {token}"
        else:
            logger.warning(
                "github_token_missing",
                hint="Set GITHUB_TOKEN env var; unauthenticated rate limit is 10 req/min",
            )

        super().__init__(extra_headers=auth_headers)
        self._min_stars = min_stars
        self._top_n = top_n

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info("scrape_start", source="github_api")

        yesterday = (datetime.now(tz=timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )
        # Repos pushed today with many stars = viral / suddenly active repos
        query = f"pushed:>{yesterday} stars:>{self._min_stars}"
        params: dict[str, str] = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": str(self._top_n),
        }

        self._log.debug("search_query", query=query)

        try:
            data = await self._fetch_json(
                _SEARCH_URL,
                params=params,
                headers={"Accept": "application/vnd.github+json"},
            )
        except Exception as exc:
            self._log.error("fetch_failed", source="github_api", detail=str(exc))
            return []

        if not isinstance(data, dict):
            self._log.error("unexpected_response_type", got=type(data).__name__)
            return []

        items = self._parse_response(data)
        self._log.info("scrape_done", source="github_api", item_count=len(items))
        return items

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, data: dict[str, Any]) -> list[ScrapedItem]:
        """Convert the API search response to a list of ScrapedItems."""
        repos: list[dict[str, Any]] = data.get("items", [])
        if not repos:
            self._log.warning("no_repos_in_response", total_count=data.get("total_count"))
            return []

        items: list[ScrapedItem] = []
        for repo in repos[: self._top_n]:
            try:
                item = self._parse_repo(repo)
                items.append(item)
            except Exception as exc:
                self._log.warning(
                    "repo_parse_error",
                    repo_name=repo.get("full_name", "unknown"),
                    detail=str(exc),
                )
                continue

        return items

    def _parse_repo(self, repo: dict[str, Any]) -> ScrapedItem:
        """Convert a single GitHub API repository object to a ScrapedItem."""
        full_name: str = repo.get("full_name", "unknown/unknown")
        html_url: str = repo.get("html_url", f"{_GITHUB_BASE}/{full_name}")
        description: str = repo.get("description") or ""
        language: str = repo.get("language") or ""
        stars: int = int(repo.get("stargazers_count", 0))
        forks: int = int(repo.get("forks_count", 0))
        open_issues: int = int(repo.get("open_issues_count", 0))
        topics: list[str] = repo.get("topics") or []

        # Parse the creation timestamp
        created_at_raw: str = repo.get("created_at", "")
        try:
            published_at = datetime.fromisoformat(
                created_at_raw.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            self._log.debug(
                "created_at_parse_failed",
                raw=created_at_raw,
                repo=full_name,
            )
            published_at = datetime.now(tz=timezone.utc)

        tags: list[str] = []
        if language:
            tags.append(language)
        tags.extend(topics[:5])  # limit topics to avoid tag bloat

        return ScrapedItem(
            title=full_name,
            url=html_url,
            summary=description,
            source="github_api",
            score=float(stars),
            published_at=published_at,
            tags=tags,
            extra={
                "language": language,
                "forks_count": forks,
                "open_issues_count": open_issues,
                "topics": topics,
            },
        )
