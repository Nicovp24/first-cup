"""
agent/writer/writer.py

DigestWriter: orchestrates Claude/Gemini to turn scraped items into individual
publication-ready PublishedPost objects — one article per story.

Pipeline for each run:
  1. Select top N items       (PROMPT_SELECTION → AI → JSON)
  2. For each selected item, write one article in parallel  (PROMPT_ARTICLE → AI)
  3. Generate SEO headline    (PROMPT_HEADLINE → AI → JSON)
  4. Build slug + cover image
  5. Return list[PublishedPost]

Breaking-news items (flagged by PROMPT_SELECTION) are placed first in the
returned list so the publish node can prioritise them.
"""

from __future__ import annotations

import asyncio
import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from agent.db.posts import PublishedPost
from agent.scraper.base import ScrapedItem
from agent.writer.claude_client import ClaudeClient
from agent.writer.prompts import (
    PROMPT_ARTICLE,
    PROMPT_HEADLINE,
    PROMPT_SELECTION,
    SYSTEM_PROMPT_EDITOR,
)

logger = structlog.get_logger(__name__)

STORIES_PER_RUN: int = 6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = re.sub(r"-{2,}", "-", text)
    return text


def _serialize_items(items: list[ScrapedItem]) -> str:
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        rows.append({
            "index": idx,
            "title": item.title,
            "url": item.url,
            "summary": item.summary,
            "source": item.source,
            "score": item.score,
            "published_at": item.published_at.isoformat(),
            "tags": item.tags,
        })
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _extract_json(text: str) -> dict | list:
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    candidate = fenced.group(1) if fenced else text.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"(\{|\[)", candidate)
        if match:
            try:
                return json.loads(candidate[match.start():])
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not parse JSON from AI response:\n{text[:500]}")


_TOPIC_COVERS: dict[str, str] = {
    "artificial intelligence": "photo-1677442135703-1787eea5ce01",
    "machine learning": "photo-1620712943543-bcc4688e7485",
    "neural network": "photo-1555949963-aa79dcee981c",
    "language model": "photo-1677442135703-1787eea5ce01",
    "transformer": "photo-1677442135703-1787eea5ce01",
    "llm": "photo-1677442135703-1787eea5ce01",
    "agent": "photo-1677442135703-1787eea5ce01",
    "token": "photo-1620712943543-bcc4688e7485",
    "python": "photo-1526379095098-d400fd0bf935",
    "javascript": "photo-1555066931-4365d14bab8c",
    "typescript": "photo-1555066931-4365d14bab8c",
    "rust": "photo-1629654297299-c8506221ca97",
    "go ": "photo-1629654297299-c8506221ca97",
    "open source": "photo-1618401471353-b98afee0b2eb",
    "github": "photo-1618401471353-b98afee0b2eb",
    "security": "photo-1550751827-4bd374c3f58b",
    "cloud": "photo-1451187580459-43490279c0fa",
    "kubernetes": "photo-1667372393119-3d4c48d07fc9",
    "docker": "photo-1667372393119-3d4c48d07fc9",
    "devops": "photo-1667372393119-3d4c48d07fc9",
    "server": "photo-1451187580459-43490279c0fa",
    "database": "photo-1544383835-bda2bc66a55d",
    "api": "photo-1461749280684-dccba630e2f6",
    "web": "photo-1558494949-ef010cbdcc31",
    "frontend": "photo-1559028012-481c04fa702d",
    "backend": "photo-1629654297299-c8506221ca97",
    "terminal": "photo-1461749280684-dccba630e2f6",
    "cli": "photo-1461749280684-dccba630e2f6",
    "compiler": "photo-1461749280684-dccba630e2f6",
    "code": "photo-1461749280684-dccba630e2f6",
    "startup": "photo-1559028012-481c04fa702d",
    "model": "photo-1620712943543-bcc4688e7485",
    "paper": "photo-1620712943543-bcc4688e7485",
    "research": "photo-1620712943543-bcc4688e7485",
    "benchmark": "photo-1620712943543-bcc4688e7485",
}


def _build_cover_url(slug: str, keywords: str = "") -> str:
    kw = keywords.lower() if keywords else ""
    for topic, photo_id in _TOPIC_COVERS.items():
        if topic in kw:
            return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=800&q=75"
    return f"https://picsum.photos/seed/{slug}/800/400"


async def _fetch_og_image(url: str) -> str | None:
    """
    Try to get a topic-relevant image from a source URL.

    - github.com/{owner}/{repo} → opengraph.github.com social preview (no HTTP request)
    - All other URLs → fetch first ~32 KB of the page, extract og:image or twitter:image
    Returns None on any failure so the caller can fall back.
    """
    try:
        from urllib.parse import urlparse as _urlparse
        parsed = _urlparse(url)
        hostname = (parsed.hostname or "").lower()

        if hostname in ("github.com", "www.github.com"):
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1].split("?")[0]
                return f"https://opengraph.github.com/{owner}/{repo}"

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            async with client.stream(
                "GET", url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; FirstCupBot/1.0)"},
            ) as resp:
                if resp.status_code >= 400:
                    return None
                content = b""
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    content += chunk
                    low = content.lower()
                    if b"</head>" in low or len(content) > 32_000:
                        break

        head_html = content.decode("utf-8", errors="ignore")

        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]
        for pat in patterns:
            m = re.search(pat, head_html, re.IGNORECASE)
            if m:
                img = m.group(1).strip()
                if img.startswith("http"):
                    return img

    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# DigestWriter
# ---------------------------------------------------------------------------


class DigestWriter:
    """
    Turns scraped items into individual blog posts — one article per story.

    Args:
        client: An initialised ClaudeClient (or compatible AI client).
    """

    def __init__(self, client: ClaudeClient) -> None:
        self._client = client
        self._log = structlog.get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def write_digest(self, items: list[ScrapedItem]) -> list[PublishedPost]:
        """
        Select the top stories and write one independent article per story.

        Returns:
            List of PublishedPost objects; breaking-news posts come first.
        """
        if not items:
            self._log.warning("write_digest_no_items")
            return []

        self._log.info("write_digest_start", total_items=len(items))

        # Step 1: ask the AI to pick the best N stories
        selected_indices, breaking_indices = await self._select_items(
            items, n=STORIES_PER_RUN
        )
        if not selected_indices:
            self._log.error("write_digest_no_selection")
            return []

        breaking_set = set(breaking_indices)
        self._log.info(
            "write_digest_selection_done",
            selected=len(selected_indices),
            breaking=len(breaking_indices),
        )

        # Step 2: write articles sequentially to respect API rate limits
        valid_indices = [i for i in selected_indices if 0 <= i < len(items)]
        breaking_posts: list[PublishedPost] = []
        regular_posts: list[PublishedPost] = []

        for idx in valid_indices:
            try:
                result = await self._write_article(
                    items[idx], is_breaking=(idx in breaking_set)
                )
                if idx in breaking_set:
                    breaking_posts.append(result)
                else:
                    regular_posts.append(result)
                self._log.info("write_digest_article_ok", slug=result.slug)
            except Exception as exc:
                self._log.error(
                    "write_digest_article_failed",
                    item_idx=idx,
                    error=str(exc),
                )

        posts = breaking_posts + regular_posts
        self._log.info("write_digest_done", posts_written=len(posts))
        return posts

    # ------------------------------------------------------------------
    # Private steps
    # ------------------------------------------------------------------

    async def _select_items(
        self, items: list[ScrapedItem], n: int
    ) -> tuple[list[int], list[int]]:
        """Ask the AI to pick the top N items and flag breaking news."""
        items_json = _serialize_items(items)
        prompt = PROMPT_SELECTION.format(items_json=items_json, n=n)

        try:
            raw = await self._client.complete(prompt, system=SYSTEM_PROMPT_EDITOR)
            parsed = _extract_json(raw)
        except Exception as exc:
            self._log.error("selection_parse_error", error=str(exc))
            sorted_items = sorted(
                enumerate(items), key=lambda x: x[1].score or 0, reverse=True
            )
            return [i for i, _ in sorted_items[:n]], []

        if not isinstance(parsed, dict):
            self._log.warning("selection_unexpected_schema")
            sorted_items = sorted(
                enumerate(items), key=lambda x: x[1].score or 0, reverse=True
            )
            return [i for i, _ in sorted_items[:n]], []

        selected = [
            int(i) for i in parsed.get("selected", [])
            if isinstance(i, (int, float)) and 0 <= int(i) < len(items)
        ]
        breaking = [
            int(i) for i in parsed.get("breaking", [])
            if isinstance(i, (int, float)) and int(i) in selected
        ]

        self._log.info("selection_ok", selected=selected, breaking=breaking)
        return selected, breaking

    async def _write_article(
        self, item: ScrapedItem, is_breaking: bool = False
    ) -> PublishedPost:
        """Draft one standalone article for a single scraped item."""
        # --- Step A: article body ---
        body_prompt = PROMPT_ARTICLE.format(
            title=item.title,
            url=item.url,
            summary=item.summary or "(sin resumen disponible)",
            source=item.source,
            published_at=item.published_at.isoformat(),
            tags=", ".join(item.tags) if item.tags else "general",
        )
        self._log.debug("drafting_article", title=item.title, breaking=is_breaking)
        content = await self._client.complete(body_prompt, system=SYSTEM_PROMPT_EDITOR)
        content = content.strip()

        # --- Step B: SEO headline ---
        headline_prompt = PROMPT_HEADLINE.format(content=content)
        headline_raw = await self._client.complete(
            headline_prompt, system=SYSTEM_PROMPT_EDITOR
        )

        cover_keywords: str = ""
        tags: list[str] = list(item.tags)
        title: str = item.title
        description: str = item.summary or ""

        try:
            headline_data = _extract_json(headline_raw)
            title = headline_data.get("title", item.title)
            description = headline_data.get("description", item.summary or "")
            cover_keywords = headline_data.get("cover_keywords", "")
            claude_tags = headline_data.get("tags")
            if isinstance(claude_tags, list) and claude_tags:
                tags = [str(t) for t in claude_tags if t]
        except Exception as exc:
            self._log.warning("headline_parse_error", error=str(exc))

        # --- Step C: slug (title + date suffix for uniqueness) ---
        slug = _slugify(title)
        date_suffix = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
        slug = f"{slug}-{date_suffix}"

        # --- Step D: cover image ---
        cover = await _fetch_og_image(item.url) or _build_cover_url(slug, cover_keywords)

        self._log.info(
            "article_drafted",
            title=title,
            slug=slug,
            breaking=is_breaking,
            chars=len(content),
        )

        return PublishedPost(
            title=title,
            slug=slug,
            content=content,
            description=description,
            source_urls=[item.url],
            tags=tags,
            published_at=datetime.now(tz=timezone.utc),
            cover=cover,
        )
