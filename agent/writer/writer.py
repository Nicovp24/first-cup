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

from agent.config import settings as _settings

logger = structlog.get_logger(__name__)

STORIES_PER_RUN: int = _settings.stories_per_run


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


_REPO_SOURCES = frozenset({"github_trending", "github_api"})
_MAX_REPOS_IN_POOL = 2


def _serialize_items(items: list[ScrapedItem]) -> str:
    # Hard-cap repos at 2 so the LLM can never select more than 2 even if it ignores the prompt.
    repos = [i for i in items if i.source in _REPO_SOURCES]
    news  = [i for i in items if i.source not in _REPO_SOURCES]
    repos_sorted = sorted(repos, key=lambda x: x.score or 0, reverse=True)[:_MAX_REPOS_IN_POOL]
    news_sorted  = sorted(news,  key=lambda x: x.score or 0, reverse=True)[:15 - len(repos_sorted)]
    top = news_sorted + repos_sorted
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(top):
        row: dict[str, Any] = {
            "index": idx,
            "title": item.title[:80],
            "url": item.url,
            "summary": (item.summary or "")[:100],
            "source": item.source,
            "score": item.score,
        }
        rows.append(row)
    return json.dumps(rows, ensure_ascii=False, separators=(',', ':'))


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
    # ── AI / LLM ──────────────────────────────────────────────────
    "chatgpt":          "photo-1677442135703-1787eea5ce01",
    "openai":           "photo-1677442135703-1787eea5ce01",
    "claude":           "photo-1677442135703-1787eea5ce01",
    "gemini":           "photo-1677442135703-1787eea5ce01",
    "llama":            "photo-1677442135703-1787eea5ce01",
    "mistral":          "photo-1677442135703-1787eea5ce01",
    "language model":   "photo-1677442135703-1787eea5ce01",
    "llm":              "photo-1677442135703-1787eea5ce01",
    "transformer":      "photo-1677442135703-1787eea5ce01",
    "gpt":              "photo-1677442135703-1787eea5ce01",
    "agent":            "photo-1677442135703-1787eea5ce01",
    "artificial intel": "photo-1677442135703-1787eea5ce01",
    "machine learning": "photo-1620712943543-bcc4688e7485",
    "neural network":   "photo-1555949963-aa79dcee981c",
    "deep learning":    "photo-1555949963-aa79dcee981c",
    "inference":        "photo-1620712943543-bcc4688e7485",
    "embedding":        "photo-1620712943543-bcc4688e7485",
    "fine-tun":         "photo-1620712943543-bcc4688e7485",
    "rag":              "photo-1620712943543-bcc4688e7485",
    "diffusion":        "photo-1620712943543-bcc4688e7485",
    "multimodal":       "photo-1620712943543-bcc4688e7485",
    "token":            "photo-1620712943543-bcc4688e7485",
    "gpu":              "photo-1620712943543-bcc4688e7485",
    "cuda":             "photo-1620712943543-bcc4688e7485",
    "paper":            "photo-1620712943543-bcc4688e7485",
    "research":         "photo-1620712943543-bcc4688e7485",
    "arxiv":            "photo-1620712943543-bcc4688e7485",
    "benchmark":        "photo-1620712943543-bcc4688e7485",
    "model":            "photo-1620712943543-bcc4688e7485",
    # ── Languages ─────────────────────────────────────────────────
    "python":           "photo-1526379095098-d400fd0bf935",
    "javascript":       "photo-1555066931-4365d14bab8c",
    "typescript":       "photo-1555066931-4365d14bab8c",
    "react":            "photo-1559028012-481c04fa702d",
    "vue":              "photo-1559028012-481c04fa702d",
    "svelte":           "photo-1559028012-481c04fa702d",
    "next.js":          "photo-1559028012-481c04fa702d",
    "rust":             "photo-1629654297299-c8506221ca97",
    "go ":              "photo-1629654297299-c8506221ca97",
    "golang":           "photo-1629654297299-c8506221ca97",
    "c++":              "photo-1629654297299-c8506221ca97",
    "cpp":              "photo-1629654297299-c8506221ca97",
    "swift":            "photo-1555066931-4365d14bab8c",
    "kotlin":           "photo-1555066931-4365d14bab8c",
    "java":             "photo-1555066931-4365d14bab8c",
    "wasm":             "photo-1629654297299-c8506221ca97",
    "llvm":             "photo-1629654297299-c8506221ca97",
    "compiler":         "photo-1461749280684-dccba630e2f6",
    # ── Security ──────────────────────────────────────────────────
    "security":         "photo-1550751827-4bd374c3f58b",
    "vulnerabilit":     "photo-1550751827-4bd374c3f58b",
    "exploit":          "photo-1550751827-4bd374c3f58b",
    "cve":              "photo-1550751827-4bd374c3f58b",
    "zero-day":         "photo-1550751827-4bd374c3f58b",
    "encrypt":          "photo-1550751827-4bd374c3f58b",
    "crypto":           "photo-1550751827-4bd374c3f58b",
    # ── Infra / Cloud / DevOps ─────────────────────────────────────
    "kubernetes":       "photo-1667372393119-3d4c48d07fc9",
    "docker":           "photo-1667372393119-3d4c48d07fc9",
    "container":        "photo-1667372393119-3d4c48d07fc9",
    "devops":           "photo-1667372393119-3d4c48d07fc9",
    "cicd":             "photo-1667372393119-3d4c48d07fc9",
    "ci/cd":            "photo-1667372393119-3d4c48d07fc9",
    "cloud":            "photo-1451187580459-43490279c0fa",
    "aws":              "photo-1451187580459-43490279c0fa",
    "azure":            "photo-1451187580459-43490279c0fa",
    "gcp":              "photo-1451187580459-43490279c0fa",
    "server":           "photo-1451187580459-43490279c0fa",
    "serverless":       "photo-1451187580459-43490279c0fa",
    # ── Data / DB ──────────────────────────────────────────────────
    "database":         "photo-1544383835-bda2bc66a55d",
    "postgres":         "photo-1544383835-bda2bc66a55d",
    "mysql":            "photo-1544383835-bda2bc66a55d",
    "mongodb":          "photo-1544383835-bda2bc66a55d",
    "sql":              "photo-1544383835-bda2bc66a55d",
    "data engineer":    "photo-1544383835-bda2bc66a55d",
    "analytics":        "photo-1544383835-bda2bc66a55d",
    # ── Web / Frontend ────────────────────────────────────────────
    "frontend":         "photo-1559028012-481c04fa702d",
    "web":              "photo-1558494949-ef010cbdcc31",
    "browser":          "photo-1558494949-ef010cbdcc31",
    "css":              "photo-1559028012-481c04fa702d",
    "html":             "photo-1559028012-481c04fa702d",
    # ── Open source / GitHub ──────────────────────────────────────
    "open source":      "photo-1618401471353-b98afee0b2eb",
    "github":           "photo-1618401471353-b98afee0b2eb",
    "repository":       "photo-1618401471353-b98afee0b2eb",
    "trending":         "photo-1618401471353-b98afee0b2eb",
    # ── Tools / Dev ───────────────────────────────────────────────
    "terminal":         "photo-1461749280684-dccba630e2f6",
    "cli":              "photo-1461749280684-dccba630e2f6",
    "api":              "photo-1461749280684-dccba630e2f6",
    "framework":        "photo-1461749280684-dccba630e2f6",
    "library":          "photo-1461749280684-dccba630e2f6",
    "backend":          "photo-1629654297299-c8506221ca97",
    "performance":      "photo-1461749280684-dccba630e2f6",
    "code":             "photo-1461749280684-dccba630e2f6",
    # ── Business / Industry ───────────────────────────────────────
    "startup":          "photo-1559028012-481c04fa702d",
    "acquisition":      "photo-1559028012-481c04fa702d",
    "funding":          "photo-1559028012-481c04fa702d",
    "ipo":              "photo-1559028012-481c04fa702d",
}


_FALLBACK_COVER = "photo-1461749280684-dccba630e2f6"  # generic code editor


def _build_cover_url(slug: str, keywords: str = "") -> str:
    kw = keywords.lower() if keywords else ""
    for topic, photo_id in _TOPIC_COVERS.items():
        if topic in kw:
            return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=900&q=80"
    return f"https://images.unsplash.com/{_FALLBACK_COVER}?auto=format&fit=crop&w=900&q=80"


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

        # GitHub: verify repo exists before returning opengraph URL
        if hostname in ("github.com", "www.github.com"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                og_url = f"https://opengraph.github.com/repo/{owner}/{repo}"
                async with httpx.AsyncClient(timeout=6.0) as client:
                    head = await client.head(og_url)
                    if head.status_code < 400:
                        return og_url
            return None

        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
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

    async def write_digest(
        self,
        items: list[ScrapedItem],
        recent_titles: list[str] | None = None,
    ) -> list[PublishedPost]:
        """
        Select the top stories and write one independent article per story.

        Args:
            items: Scraped items to choose from.
            recent_titles: Titles of posts published in the last ~7 days so the
                           selector can avoid covering the same topics again.

        Returns:
            List of PublishedPost objects; breaking-news posts come first.
        """
        if not items:
            self._log.warning("write_digest_no_items")
            return []

        self._log.info("write_digest_start", total_items=len(items))

        # Step 1: ask the AI to pick the best N stories
        selected_indices, breaking_indices = await self._select_items(
            items, n=STORIES_PER_RUN, recent_titles=recent_titles or []
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
        self,
        items: list[ScrapedItem],
        n: int,
        recent_titles: list[str] | None = None,
    ) -> tuple[list[int], list[int]]:
        """Ask the AI to pick the top N items and flag breaking news."""
        items_json = _serialize_items(items)

        if recent_titles:
            titles_list = "\n".join(f"  - {t}" for t in recent_titles[:15])
            recent_titles_block = (
                f"TEMAS YA PUBLICADOS (últimos 7 días) — NO repitas ni cubras el mismo tema:\n"
                f"{titles_list}\n\n"
            )
        else:
            recent_titles_block = ""

        prompt = PROMPT_SELECTION.format(
            items_json=items_json,
            n=n,
            recent_titles_block=recent_titles_block,
        )

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

        # Hard-enforce max 2 repos regardless of what the LLM chose.
        repo_count = 0
        enforced: list[int] = []
        for idx in selected:
            if items[idx].source in _REPO_SOURCES:
                if repo_count >= _MAX_REPOS_IN_POOL:
                    self._log.warning("repo_cap_enforced", dropped_idx=idx, title=items[idx].title)
                    continue
                repo_count += 1
            enforced.append(idx)
        breaking = [i for i in breaking if i in enforced]

        self._log.info("selection_ok", selected=enforced, breaking=breaking)
        return enforced, breaking

    async def _write_article(
        self, item: ScrapedItem, is_breaking: bool = False
    ) -> PublishedPost:
        """Draft one standalone article for a single scraped item."""
        # --- Step 0: fetch cover image ---
        source_cover = await _fetch_og_image(item.url)

        # --- Step A: article body ---
        # Build rich metadata block for GitHub repos
        extra_lines: list[str] = []
        if item.extra:
            lang = item.extra.get("language")
            if lang:
                extra_lines.append(f"Lenguaje:  {lang}")

            # Total stars: trending scraper → total_stars; API scraper → score
            total_stars: int = (
                item.extra.get("total_stars")
                or int(item.score)
                or 0
            )
            if total_stars:
                extra_lines.append(f"Estrellas: {total_stars:,}")

            # Stars gained today (trending only)
            if item.source == "github_trending" and item.score:
                extra_lines.append(f"Stars hoy: +{int(item.score):,}")

            # Forks: trending → forks; API → forks_count
            forks: int = item.extra.get("forks") or item.extra.get("forks_count") or 0
            if forks:
                extra_lines.append(f"Forks:     {forks:,}")

            topics: list[str] = item.extra.get("topics") or []
            if topics:
                extra_lines.append(f"Topics:    {', '.join(topics[:8])}")
        extra_block = ("\n" + "\n".join(extra_lines)) if extra_lines else ""

        body_prompt = PROMPT_ARTICLE.format(
            title=item.title,
            url=item.url,
            summary=item.summary or "(sin resumen disponible)",
            source=item.source,
            published_at=item.published_at.isoformat(),
            tags=", ".join(item.tags) if item.tags else "general",
            extra_block=extra_block,
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

        # --- Step D: cover image (use fetched, else build from keywords) ---
        cover = source_cover or _build_cover_url(slug, cover_keywords)

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
