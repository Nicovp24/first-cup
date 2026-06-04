"""
agent/writer/writer.py

DigestWriter: orchestrates Claude to turn a list of ScrapedItems into a
list of publication-ready PublishedPost objects.

Pipeline for each run:
  1. Group items by theme  (PROMPT_GROUPING → Claude → JSON)
  2. For each group, draft a Markdown post  (PROMPT_DIGEST_POST → Claude)
  3. Generate SEO title + description  (PROMPT_HEADLINE → Claude → JSON)
  4. Build slug from title
  5. Return list[PublishedPost]

If any individual group fails the error is logged and processing continues
with the remaining groups so one bad item cannot abort the whole digest.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

import structlog

from agent.db.posts import PublishedPost
from agent.scraper.base import ScrapedItem
from agent.writer.claude_client import ClaudeClient
from agent.writer.prompts import (
    PROMPT_DIGEST_POST,
    PROMPT_GROUPING,
    PROMPT_HEADLINE,
    SYSTEM_PROMPT_EDITOR,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """
    Convert an arbitrary string (including Spanish accented chars) into a
    URL-safe ASCII slug.

    Examples:
        "Inteligencia Artificial en España" → "inteligencia-artificial-en-espana"
        "Python 3.13: What's New?"          → "python-313-whats-new"
    """
    # NFD decomposition converts á→a+combining_accent; dropping combining marks gives ASCII
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = re.sub(r"-{2,}", "-", text)
    return text


def _serialize_items(items: list[ScrapedItem]) -> str:
    """Return a compact JSON array representation of the given items."""
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
    """
    Extract the first JSON object or array from a Claude response string.

    Claude sometimes wraps JSON in triple-backtick fences; this handles both
    raw JSON and fenced code blocks.

    Raises:
        ValueError: If no valid JSON can be found.
    """
    # Strip optional ```json … ``` fence
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    candidate = fenced.group(1) if fenced else text.strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Last resort: find first { or [ and try from there
        match = re.search(r"(\{|\[)", candidate)
        if match:
            start = match.start()
            try:
                return json.loads(candidate[start:])
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not parse JSON from Claude response:\n{text[:500]}")


_TOPIC_COVERS: dict[str, str] = {
    "artificial intelligence": "photo-1677442135703-1787eea5ce01",
    "machine learning": "photo-1620712943543-bcc4688e7485",
    "neural network": "photo-1555949963-aa79dcee981c",
    "language model": "photo-1677442135703-1787eea5ce01",
    "llm": "photo-1677442135703-1787eea5ce01",
    "python": "photo-1526379095098-d400fd0bf935",
    "javascript": "photo-1555066931-4365d14bab8c",
    "typescript": "photo-1555066931-4365d14bab8c",
    "rust": "photo-1629654297299-c8506221ca97",
    "open source": "photo-1618401471353-b98afee0b2eb",
    "github": "photo-1618401471353-b98afee0b2eb",
    "security": "photo-1550751827-4bd374c3f58b",
    "cloud": "photo-1451187580459-43490279c0fa",
    "database": "photo-1544383835-bda2bc66a55d",
    "web": "photo-1558494949-ef010cbdcc31",
    "frontend": "photo-1559028012-481c04fa702d",
    "backend": "photo-1629654297299-c8506221ca97",
    "devops": "photo-1667372393119-3d4c48d07fc9",
    "code": "photo-1461749280684-dccba630e2f6",
}


def _build_cover_url(slug: str, keywords: str = "") -> str:
    """
    Map cover_keywords from Claude to an Unsplash CDN photo URL.
    Falls back to a deterministic picsum.photos URL keyed by slug.
    """
    kw = keywords.lower() if keywords else ""
    for topic, photo_id in _TOPIC_COVERS.items():
        if topic in kw:
            return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=800&q=75"
    # Deterministic fallback — same image every run for the same slug
    return f"https://picsum.photos/seed/{slug}/800/400"


# ---------------------------------------------------------------------------
# DigestWriter
# ---------------------------------------------------------------------------


class DigestWriter:
    """
    Orchestrates the multi-step Claude pipeline to produce digest posts.

    Args:
        client: An initialised :class:`~agent.writer.claude_client.ClaudeClient`.
    """

    def __init__(self, client: ClaudeClient) -> None:
        self._client = client
        self._log = structlog.get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def write_digest(self, items: list[ScrapedItem]) -> list[PublishedPost]:
        """
        Convert a flat list of scraped items into themed digest posts.

        Args:
            items: Items collected during the current scraping run.

        Returns:
            A list of :class:`~agent.db.posts.PublishedPost` objects ready
            to be saved and published.  The list may be shorter than the
            number of groups if some groups fail during generation.
        """
        if not items:
            self._log.warning("write_digest_no_items")
            return []

        self._log.info("write_digest_start", total_items=len(items))

        # Step 1: cluster items into themes
        groups = await self._group_items(items)
        if not groups:
            self._log.error("write_digest_no_groups")
            return []

        self._log.info("write_digest_groups_ready", group_count=len(groups))

        posts: list[PublishedPost] = []
        for group_idx, group in enumerate(groups):
            theme: str = group.get("theme", f"Topic {group_idx + 1}")
            indices: list[int] = group.get("item_indices", [])

            group_log = self._log.bind(theme=theme, item_count=len(indices))

            if not indices:
                group_log.warning("write_digest_empty_group")
                continue

            # Resolve items for this group (guard against out-of-range indices)
            group_items = [items[i] for i in indices if 0 <= i < len(items)]
            if not group_items:
                group_log.warning("write_digest_no_valid_items")
                continue

            try:
                post = await self._write_post(theme, group_items)
                posts.append(post)
                group_log.info("write_digest_post_ok", slug=post.slug)
            except Exception as exc:
                group_log.error(
                    "write_digest_post_failed",
                    error=str(exc),
                    exc_info=True,
                )
                # Continue with remaining groups

        self._log.info("write_digest_done", posts_written=len(posts))
        return posts

    # ------------------------------------------------------------------
    # Private steps
    # ------------------------------------------------------------------

    async def _group_items(self, items: list[ScrapedItem]) -> list[dict]:
        """
        Ask Claude to cluster items into 2-4 themes.

        Returns:
            List of group dicts, each with ``"theme"`` and ``"item_indices"``.
        """
        items_json = _serialize_items(items)
        prompt = PROMPT_GROUPING.format(items_json=items_json)

        self._log.debug("grouping_request", item_count=len(items))

        try:
            raw = await self._client.complete(prompt, system=SYSTEM_PROMPT_EDITOR)
            parsed = _extract_json(raw)
        except Exception as exc:
            self._log.error("grouping_parse_error", error=str(exc))
            # Fallback: put all items into one group
            return [{"theme": "Today's Digest", "item_indices": list(range(len(items)))}]

        if not isinstance(parsed, dict) or "groups" not in parsed:
            self._log.warning(
                "grouping_unexpected_schema",
                keys=list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__,
            )
            return [{"theme": "Today's Digest", "item_indices": list(range(len(items)))}]

        groups: list[dict] = parsed["groups"]
        self._log.info("grouping_ok", group_count=len(groups))
        return groups

    async def _write_post(
        self,
        theme: str,
        group_items: list[ScrapedItem],
    ) -> PublishedPost:
        """
        Draft one digest post for a given theme and its associated items.

        Steps:
            1. Generate Markdown body with ``PROMPT_DIGEST_POST``.
            2. Generate title + description with ``PROMPT_HEADLINE``.
            3. Build slug from title.
            4. Return a :class:`PublishedPost`.
        """
        items_json = _serialize_items(group_items)
        source_urls = [item.url for item in group_items]
        # Tags will be replaced by Claude-generated Spanish tags from the headline step
        raw_tags = list({tag for item in group_items for tag in item.tags})

        # --- Step A: draft Markdown body ---
        body_prompt = PROMPT_DIGEST_POST.format(theme=theme, items_json=items_json)
        self._log.debug("drafting_body", theme=theme)
        content = await self._client.complete(body_prompt, system=SYSTEM_PROMPT_EDITOR)
        content = content.strip()

        # --- Step B: generate SEO headline ---
        headline_prompt = PROMPT_HEADLINE.format(content=content)
        self._log.debug("generating_headline", theme=theme)
        headline_raw = await self._client.complete(
            headline_prompt, system=SYSTEM_PROMPT_EDITOR
        )

        cover_keywords: str = ""
        tags: list[str] = raw_tags
        try:
            headline_data = _extract_json(headline_raw)
            title: str = headline_data.get("title", theme)
            description: str = headline_data.get("description", "")
            cover_keywords = headline_data.get("cover_keywords", "")
            claude_tags = headline_data.get("tags")
            if isinstance(claude_tags, list) and claude_tags:
                tags = [str(t) for t in claude_tags if t]
        except Exception as exc:
            self._log.warning(
                "headline_parse_error",
                theme=theme,
                error=str(exc),
            )
            title = theme
            description = ""

        # --- Step C: slug ---
        slug = _slugify(title)
        # Append date to guarantee uniqueness across runs
        date_suffix = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
        slug = f"{slug}-{date_suffix}"

        # --- Step D: cover image (deterministic Picsum fallback) ---
        cover = _build_cover_url(slug, cover_keywords)

        self._log.info(
            "post_drafted",
            theme=theme,
            title=title,
            slug=slug,
            content_chars=len(content),
            cover=cover,
        )

        return PublishedPost(
            title=title,
            slug=slug,
            content=content,
            description=description,
            source_urls=source_urls,
            tags=tags,
            published_at=datetime.now(tz=timezone.utc),
            cover=cover,
        )
