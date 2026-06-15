"""
Reddit scraper – authenticates via OAuth2 and fetches top posts of the day
from a curated list of subreddits.

Token rotation is handled automatically: the access token and its expiry
timestamp are stored on the instance, and a fresh token is requested whenever
the current one has less than 60 seconds of lifetime remaining.
"""

from __future__ import annotations

import asyncio
import base64
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog

from agent.config import settings
from .base import ScraperBase, ScrapedItem

logger = structlog.get_logger(__name__)

_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_OAUTH_BASE = "https://oauth.reddit.com"
_MIN_SCORE = 50
_POSTS_PER_SUB = 5
_TOKEN_EXPIRY_BUFFER_SECS = 60  # refresh token this many seconds before expiry


SUBREDDITS: list[str] = [
    # ── AI / ML ───────────────────────────────────────
    "MachineLearning",
    "LocalLLaMA",
    "artificial",
    # ── Repos / proyectos ─────────────────────────────
    "coolgithubprojects",   # el mejor sub para descubrir repos
    "opensource",
    # ── Lenguajes ─────────────────────────────────────
    "Python",
    "rust",
    "golang",
    "typescript",
    # ── Dev general ───────────────────────────────────
    "programming",
    "webdev",
    "devops",
]


class RedditScraper(ScraperBase):
    """
    Fetches the top posts of the last 24 hours from a set of subreddits.

    Authentication uses Reddit's OAuth2 *client credentials* (app-only) flow.
    The access token is cached on the instance and automatically refreshed
    when it is about to expire.

    Each :class:`~agent.scraper.base.ScrapedItem` has:
    - ``title``: post title
    - ``url``: link to the Reddit post (``permalink``)
    - ``summary``: selftext[:300] if present, else the post title
    - ``source``: ``"reddit"``
    - ``score``: upvote score
    - ``tags``: ``[subreddit_name, "reddit"]``
    - ``extra``: ``{"author", "num_comments", "subreddit", "post_url"}``
    """

    def __init__(
        self,
        subreddits: list[str] | None = None,
        *,
        min_score: int = _MIN_SCORE,
        posts_per_sub: int = _POSTS_PER_SUB,
    ) -> None:
        super().__init__()
        self._subreddits: list[str] = subreddits if subreddits is not None else SUBREDDITS
        self._min_score = min_score
        self._posts_per_sub = posts_per_sub

        # Token state
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0  # Unix timestamp

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def scrape(self) -> list[ScrapedItem]:
        self._log.info("scrape_start", source="reddit", subreddits=self._subreddits)

        try:
            await self._ensure_token()
        except Exception as exc:
            self._log.error("auth_failed", source="reddit", detail=str(exc))
            return []

        tasks = [self._scrape_subreddit(sub) for sub in self._subreddits]
        results: list[list[ScrapedItem] | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        all_items: list[ScrapedItem] = []
        for sub, result in zip(self._subreddits, results):
            if isinstance(result, BaseException):
                self._log.error(
                    "subreddit_scrape_failed", subreddit=sub, detail=str(result)
                )
            else:
                self._log.debug("subreddit_scraped", subreddit=sub, count=len(result))
                all_items.extend(result)

        self._log.info("scrape_done", source="reddit", item_count=len(all_items))
        return all_items

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    async def _ensure_token(self) -> None:
        """Obtain a new access token if we don't have one or it's about to expire."""
        now = time.monotonic()
        if self._access_token and now < self._token_expires_at - _TOKEN_EXPIRY_BUFFER_SECS:
            self._log.debug("token_still_valid", expires_in=self._token_expires_at - now)
            return

        self._log.info("requesting_new_token", source="reddit")

        credentials = f"{settings.reddit_client_id}:{settings.reddit_client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "User-Agent": settings.reddit_user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "grant_type=client_credentials"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    _TOKEN_URL,
                    content=data,
                    headers=headers,
                )
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
        except httpx.HTTPStatusError as exc:
            self._log.error(
                "token_http_error",
                status_code=exc.response.status_code,
                detail=str(exc),
            )
            raise
        except httpx.RequestError as exc:
            self._log.error("token_request_error", detail=str(exc))
            raise

        token: str | None = payload.get("access_token")
        expires_in: int = int(payload.get("expires_in", 3600))

        if not token:
            raise ValueError(f"Reddit token response missing access_token: {payload}")

        self._access_token = token
        self._token_expires_at = time.monotonic() + expires_in
        self._log.info("token_acquired", expires_in_secs=expires_in)

    # ------------------------------------------------------------------
    # Per-subreddit scraping
    # ------------------------------------------------------------------

    async def _scrape_subreddit(self, subreddit: str) -> list[ScrapedItem]:
        """Fetch top posts of the day for a single subreddit."""
        url = f"{_OAUTH_BASE}/r/{subreddit}/top"
        params: dict[str, str] = {
            "t": "day",
            "limit": str(self._posts_per_sub),
        }
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": settings.reddit_user_agent,
        }

        try:
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True
            ) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
        except httpx.HTTPStatusError as exc:
            self._log.error(
                "subreddit_http_error",
                subreddit=subreddit,
                status_code=exc.response.status_code,
                detail=str(exc),
            )
            return []
        except httpx.RequestError as exc:
            self._log.error(
                "subreddit_request_error", subreddit=subreddit, detail=str(exc)
            )
            return []
        except ValueError as exc:
            self._log.error(
                "subreddit_json_error", subreddit=subreddit, detail=str(exc)
            )
            return []

        return self._parse_listing(data, subreddit)

    def _parse_listing(
        self, data: dict[str, Any], subreddit: str
    ) -> list[ScrapedItem]:
        """Convert a Reddit listing JSON response into ScrapedItems."""
        try:
            children: list[dict[str, Any]] = (
                data.get("data", {}).get("children", [])
            )
        except AttributeError:
            self._log.warning("unexpected_listing_shape", subreddit=subreddit)
            return []

        items: list[ScrapedItem] = []
        for child in children:
            try:
                item = self._parse_post(child.get("data", {}), subreddit)
                if item is not None:
                    items.append(item)
            except Exception as exc:
                self._log.warning(
                    "post_parse_error",
                    subreddit=subreddit,
                    detail=str(exc),
                )
                continue

        return items

    def _parse_post(
        self, post: dict[str, Any], subreddit: str
    ) -> ScrapedItem | None:
        """Convert a single Reddit post dict to a ScrapedItem, or None if filtered."""
        score: int = int(post.get("score") or 0)
        if score < self._min_score:
            return None

        title: str = post.get("title") or "No title"
        permalink: str = post.get("permalink") or ""
        url: str = f"https://www.reddit.com{permalink}" if permalink else ""
        post_url: str = post.get("url") or url

        selftext: str = (post.get("selftext") or "").strip()
        summary: str = selftext[:300] if selftext else title

        author: str = post.get("author") or ""
        num_comments: int = int(post.get("num_comments") or 0)

        # created_utc is a Unix timestamp
        created_utc: float | None = post.get("created_utc")
        if created_utc is not None:
            published_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
        else:
            published_at = datetime.now(tz=timezone.utc)

        # Filter posts older than 24 hours (API may still return stale results)
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        if published_at < cutoff:
            return None

        return ScrapedItem(
            title=title,
            url=url,
            summary=summary,
            source="reddit",
            score=float(score),
            published_at=published_at,
            tags=[subreddit, "reddit"],
            extra={
                "author": author,
                "num_comments": num_comments,
                "subreddit": subreddit,
                "post_url": post_url,
            },
        )
