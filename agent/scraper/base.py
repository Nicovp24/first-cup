"""
Base scraper: shared dataclass ScrapedItem and abstract class ScraperBase.
All scrapers in this package must inherit from ScraperBase and implement scrape().
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger(__name__)

_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

_REQUEST_TIMEOUT: float = 30.0


@dataclass
class ScrapedItem:
    """Canonical data unit returned by every scraper."""

    title: str
    url: str
    summary: str
    source: str
    score: float
    published_at: datetime
    tags: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


class ScraperBase(ABC):
    """
    Abstract base class for all FIRST CUP scrapers.

    Subclasses must implement :meth:`scrape` and may call :meth:`_fetch`
    for raw HTML / text retrieval over HTTPS.
    """

    def __init__(self, *, extra_headers: dict[str, str] | None = None) -> None:
        self._headers: dict[str, str] = {**_DEFAULT_HEADERS, **(extra_headers or {})}
        self._log = structlog.get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def scrape(self) -> list[ScrapedItem]:
        """
        Execute the scraping logic and return a list of ScrapedItem objects.

        Must be implemented by every concrete scraper.
        """
        ...

    # ------------------------------------------------------------------
    # Protected helpers
    # ------------------------------------------------------------------

    async def _fetch(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        method: str = "GET",
        json_body: dict | None = None,
    ) -> str:
        """
        Perform an async HTTP request and return the response body as text.

        Args:
            url: Full URL to request.
            params: Optional query-string parameters.
            headers: Additional headers merged on top of the default set.
            method: HTTP method (default ``"GET"``).
            json_body: Optional JSON payload for POST/PUT requests.

        Returns:
            The decoded response body.

        Raises:
            httpx.HTTPError: Re-raised after logging if the request fails.
        """
        merged_headers = {**self._headers, **(headers or {})}
        self._log.debug("fetching_url", url=url, method=method)

        try:
            async with httpx.AsyncClient(
                timeout=_REQUEST_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=merged_headers,
                    json=json_body,
                )
                response.raise_for_status()

            self._log.debug(
                "fetch_ok",
                url=url,
                status_code=response.status_code,
                content_length=len(response.text),
            )
            return response.text

        except httpx.HTTPStatusError as exc:
            self._log.error(
                "http_status_error",
                url=url,
                status_code=exc.response.status_code,
                detail=str(exc),
            )
            raise

        except httpx.RequestError as exc:
            self._log.error("request_error", url=url, detail=str(exc))
            raise

    async def _fetch_json(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict | list:
        """
        Convenience wrapper around :meth:`_fetch` that returns parsed JSON.

        Returns:
            Parsed JSON object (dict or list).

        Raises:
            ValueError: If the response body is not valid JSON.
            httpx.HTTPError: On HTTP-level failure.
        """
        merged_headers = {
            **self._headers,
            "Accept": "application/json",
            **(headers or {}),
        }
        self._log.debug("fetching_json", url=url)

        try:
            async with httpx.AsyncClient(
                timeout=_REQUEST_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=merged_headers,
                )
                response.raise_for_status()

            data = response.json()
            self._log.debug("fetch_json_ok", url=url, type=type(data).__name__)
            return data

        except httpx.HTTPStatusError as exc:
            self._log.error(
                "http_status_error",
                url=url,
                status_code=exc.response.status_code,
                detail=str(exc),
            )
            raise

        except httpx.RequestError as exc:
            self._log.error("request_error", url=url, detail=str(exc))
            raise

        except ValueError as exc:
            self._log.error("json_decode_error", url=url, detail=str(exc))
            raise
