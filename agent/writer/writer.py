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
_MAX_REPOS_IN_POOL = 3


def _serialize_items(items: list[ScrapedItem]) -> tuple[str, list[int]]:
    """
    Returns (json_str, mapping) where mapping[serialized_idx] = original_idx in `items`.
    The LLM sees 0-based indices over the top-scored subset; mapping translates them back.
    """
    repos = [(i, it) for i, it in enumerate(items) if it.source in _REPO_SOURCES]
    news  = [(i, it) for i, it in enumerate(items) if it.source not in _REPO_SOURCES]
    repos_sorted = sorted(repos, key=lambda x: x[1].score or 0, reverse=True)[:_MAX_REPOS_IN_POOL]
    news_sorted  = sorted(news,  key=lambda x: x[1].score or 0, reverse=True)[:25 - len(repos_sorted)]
    top = news_sorted + repos_sorted  # (orig_idx, item) tuples
    mapping = [orig_idx for orig_idx, _ in top]
    rows: list[dict[str, Any]] = []
    for serialized_idx, (orig_idx, item) in enumerate(top):
        rows.append({
            "index": serialized_idx,
            "title": item.title[:80],
            "url": item.url,
            "summary": (item.summary or "")[:100],
            "source": item.source,
            "score": item.score,
        })
    return json.dumps(rows, ensure_ascii=False, separators=(',', ':')), mapping


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


_TOPIC_COVERS: dict[str, list[str]] = {
    # ── AI / LLM ──────────────────────────────────────────────────
    "chatgpt":          ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "openai":           ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "claude":           ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "gemini":           ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "llama":            ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "mistral":          ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "language model":   ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "llm":              ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "transformer":      ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "gpt":              ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "agent":            ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "artificial intel": ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c"],
    "machine learning": ["photo-1620712943543-bcc4688e7485", "photo-1677442135703-1787eea5ce01", "photo-1555949963-aa79dcee981c"],
    "neural network":   ["photo-1555949963-aa79dcee981c", "photo-1620712943543-bcc4688e7485", "photo-1677442135703-1787eea5ce01"],
    "deep learning":    ["photo-1555949963-aa79dcee981c", "photo-1620712943543-bcc4688e7485", "photo-1677442135703-1787eea5ce01"],
    "inference":        ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "embedding":        ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "fine-tun":         ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "rag":              ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "diffusion":        ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "multimodal":       ["photo-1620712943543-bcc4688e7485", "photo-1677442135703-1787eea5ce01", "photo-1555949963-aa79dcee981c"],
    "token":            ["photo-1620712943543-bcc4688e7485", "photo-1677442135703-1787eea5ce01", "photo-1555949963-aa79dcee981c"],
    "gpu":              ["photo-1620712943543-bcc4688e7485", "photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9"],
    "cuda":             ["photo-1620712943543-bcc4688e7485", "photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9"],
    "paper":            ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "research":         ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "arxiv":            ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "benchmark":        ["photo-1620712943543-bcc4688e7485", "photo-1555949963-aa79dcee981c", "photo-1677442135703-1787eea5ce01"],
    "model":            ["photo-1620712943543-bcc4688e7485", "photo-1677442135703-1787eea5ce01", "photo-1555949963-aa79dcee981c"],
    # ── Languages ─────────────────────────────────────────────────
    "python":           ["photo-1526379095098-d400fd0bf935", "photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97"],
    "javascript":       ["photo-1555066931-4365d14bab8c", "photo-1558494949-ef010cbdcc31", "photo-1461749280684-dccba630e2f6"],
    "typescript":       ["photo-1555066931-4365d14bab8c", "photo-1559028012-481c04fa702d", "photo-1461749280684-dccba630e2f6"],
    "react":            ["photo-1559028012-481c04fa702d", "photo-1555066931-4365d14bab8c", "photo-1558494949-ef010cbdcc31"],
    "vue":              ["photo-1559028012-481c04fa702d", "photo-1555066931-4365d14bab8c", "photo-1558494949-ef010cbdcc31"],
    "svelte":           ["photo-1559028012-481c04fa702d", "photo-1555066931-4365d14bab8c", "photo-1558494949-ef010cbdcc31"],
    "next.js":          ["photo-1559028012-481c04fa702d", "photo-1555066931-4365d14bab8c", "photo-1558494949-ef010cbdcc31"],
    "rust":             ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1555066931-4365d14bab8c"],
    "go ":              ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1526379095098-d400fd0bf935"],
    "golang":           ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1526379095098-d400fd0bf935"],
    "c++":              ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1555066931-4365d14bab8c"],
    "cpp":              ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1555066931-4365d14bab8c"],
    "swift":            ["photo-1555066931-4365d14bab8c", "photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6"],
    "kotlin":           ["photo-1555066931-4365d14bab8c", "photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6"],
    "java":             ["photo-1555066931-4365d14bab8c", "photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6"],
    "wasm":             ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1555066931-4365d14bab8c"],
    "llvm":             ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1555066931-4365d14bab8c"],
    "compiler":         ["photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97", "photo-1555066931-4365d14bab8c"],
    # ── Security ──────────────────────────────────────────────────
    "security":         ["photo-1550751827-4bd374c3f58b", "photo-1510915228515-cf8f87e2d517", "photo-1614064641938-3bbee52942c7"],
    "vulnerabilit":     ["photo-1550751827-4bd374c3f58b", "photo-1614064641938-3bbee52942c7", "photo-1510915228515-cf8f87e2d517"],
    "exploit":          ["photo-1550751827-4bd374c3f58b", "photo-1614064641938-3bbee52942c7", "photo-1510915228515-cf8f87e2d517"],
    "cve":              ["photo-1550751827-4bd374c3f58b", "photo-1614064641938-3bbee52942c7", "photo-1510915228515-cf8f87e2d517"],
    "zero-day":         ["photo-1550751827-4bd374c3f58b", "photo-1614064641938-3bbee52942c7", "photo-1510915228515-cf8f87e2d517"],
    "encrypt":          ["photo-1550751827-4bd374c3f58b", "photo-1510915228515-cf8f87e2d517", "photo-1614064641938-3bbee52942c7"],
    "crypto":           ["photo-1550751827-4bd374c3f58b", "photo-1510915228515-cf8f87e2d517", "photo-1614064641938-3bbee52942c7"],
    # ── Infra / Cloud / DevOps ─────────────────────────────────────
    "kubernetes":       ["photo-1667372393119-3d4c48d07fc9", "photo-1451187580459-43490279c0fa", "photo-1558494949-ef010cbdcc31"],
    "docker":           ["photo-1667372393119-3d4c48d07fc9", "photo-1451187580459-43490279c0fa", "photo-1558494949-ef010cbdcc31"],
    "container":        ["photo-1667372393119-3d4c48d07fc9", "photo-1451187580459-43490279c0fa", "photo-1558494949-ef010cbdcc31"],
    "devops":           ["photo-1667372393119-3d4c48d07fc9", "photo-1451187580459-43490279c0fa", "photo-1461749280684-dccba630e2f6"],
    "cicd":             ["photo-1667372393119-3d4c48d07fc9", "photo-1451187580459-43490279c0fa", "photo-1461749280684-dccba630e2f6"],
    "ci/cd":            ["photo-1667372393119-3d4c48d07fc9", "photo-1451187580459-43490279c0fa", "photo-1461749280684-dccba630e2f6"],
    "cloud":            ["photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9", "photo-1558494949-ef010cbdcc31"],
    "aws":              ["photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9", "photo-1558494949-ef010cbdcc31"],
    "azure":            ["photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9", "photo-1558494949-ef010cbdcc31"],
    "gcp":              ["photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9", "photo-1558494949-ef010cbdcc31"],
    "server":           ["photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9", "photo-1558494949-ef010cbdcc31"],
    "serverless":       ["photo-1451187580459-43490279c0fa", "photo-1667372393119-3d4c48d07fc9", "photo-1558494949-ef010cbdcc31"],
    # ── Data / DB ──────────────────────────────────────────────────
    "database":         ["photo-1544383835-bda2bc66a55d", "photo-1526374965328-7f61d4dc18c5", "photo-1558494949-ef010cbdcc31"],
    "postgres":         ["photo-1544383835-bda2bc66a55d", "photo-1526374965328-7f61d4dc18c5", "photo-1558494949-ef010cbdcc31"],
    "mysql":            ["photo-1544383835-bda2bc66a55d", "photo-1526374965328-7f61d4dc18c5", "photo-1558494949-ef010cbdcc31"],
    "mongodb":          ["photo-1544383835-bda2bc66a55d", "photo-1526374965328-7f61d4dc18c5", "photo-1558494949-ef010cbdcc31"],
    "sql":              ["photo-1544383835-bda2bc66a55d", "photo-1526374965328-7f61d4dc18c5", "photo-1558494949-ef010cbdcc31"],
    "data engineer":    ["photo-1544383835-bda2bc66a55d", "photo-1526374965328-7f61d4dc18c5", "photo-1451187580459-43490279c0fa"],
    "analytics":        ["photo-1544383835-bda2bc66a55d", "photo-1526374965328-7f61d4dc18c5", "photo-1451187580459-43490279c0fa"],
    # ── Web / Frontend ────────────────────────────────────────────
    "frontend":         ["photo-1559028012-481c04fa702d", "photo-1558494949-ef010cbdcc31", "photo-1555066931-4365d14bab8c"],
    "web":              ["photo-1558494949-ef010cbdcc31", "photo-1559028012-481c04fa702d", "photo-1555066931-4365d14bab8c"],
    "browser":          ["photo-1558494949-ef010cbdcc31", "photo-1559028012-481c04fa702d", "photo-1555066931-4365d14bab8c"],
    "css":              ["photo-1559028012-481c04fa702d", "photo-1558494949-ef010cbdcc31", "photo-1555066931-4365d14bab8c"],
    "html":             ["photo-1559028012-481c04fa702d", "photo-1558494949-ef010cbdcc31", "photo-1555066931-4365d14bab8c"],
    # ── Open source / GitHub ──────────────────────────────────────
    "open source":      ["photo-1618401471353-b98afee0b2eb", "photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97"],
    "github":           ["photo-1618401471353-b98afee0b2eb", "photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97"],
    "repository":       ["photo-1618401471353-b98afee0b2eb", "photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97"],
    "trending":         ["photo-1618401471353-b98afee0b2eb", "photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97"],
    # ── Tools / Dev ───────────────────────────────────────────────
    "terminal":         ["photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97", "photo-1555066931-4365d14bab8c"],
    "cli":              ["photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97", "photo-1555066931-4365d14bab8c"],
    "api":              ["photo-1461749280684-dccba630e2f6", "photo-1558494949-ef010cbdcc31", "photo-1629654297299-c8506221ca97"],
    "framework":        ["photo-1461749280684-dccba630e2f6", "photo-1559028012-481c04fa702d", "photo-1629654297299-c8506221ca97"],
    "library":          ["photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97", "photo-1555066931-4365d14bab8c"],
    "backend":          ["photo-1629654297299-c8506221ca97", "photo-1461749280684-dccba630e2f6", "photo-1451187580459-43490279c0fa"],
    "performance":      ["photo-1461749280684-dccba630e2f6", "photo-1629654297299-c8506221ca97", "photo-1451187580459-43490279c0fa"],
    "code":             ["photo-1461749280684-dccba630e2f6", "photo-1555066931-4365d14bab8c", "photo-1629654297299-c8506221ca97"],
    # ── Business / Industry ───────────────────────────────────────
    "startup":          ["photo-1559028012-481c04fa702d", "photo-1451187580459-43490279c0fa", "photo-1618401471353-b98afee0b2eb"],
    "acquisition":      ["photo-1559028012-481c04fa702d", "photo-1451187580459-43490279c0fa", "photo-1618401471353-b98afee0b2eb"],
    "funding":          ["photo-1559028012-481c04fa702d", "photo-1451187580459-43490279c0fa", "photo-1618401471353-b98afee0b2eb"],
    "ipo":              ["photo-1559028012-481c04fa702d", "photo-1451187580459-43490279c0fa", "photo-1618401471353-b98afee0b2eb"],
}


_FALLBACK_COVERS = [
    "photo-1461749280684-dccba630e2f6",
    "photo-1629654297299-c8506221ca97",
    "photo-1555066931-4365d14bab8c",
    "photo-1558494949-ef010cbdcc31",
    "photo-1526379095098-d400fd0bf935",
]


def _build_cover_url(slug: str, keywords: str = "") -> str:
    kw = keywords.lower() if keywords else ""
    # Use slug hash to pick deterministically but vary across articles
    pick = hash(slug) % 3
    for topic, photos in _TOPIC_COVERS.items():
        if topic in kw:
            photo_id = photos[pick % len(photos)]
            return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=900&q=80"
    fallback = _FALLBACK_COVERS[abs(hash(slug)) % len(_FALLBACK_COVERS)]
    return f"https://images.unsplash.com/{fallback}?auto=format&fit=crop&w=900&q=80"


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
        items_json, idx_mapping = _serialize_items(items)

        if recent_titles:
            titles_list = "\n".join(f"  - {t}" for t in recent_titles[:30])
            recent_titles_block = (
                f"TEMAS YA PUBLICADOS (últimos 30 días) — NO repitas ni cubras el mismo tema:\n"
                f"{titles_list}\n\n"
            )
        else:
            recent_titles_block = ""

        prompt = PROMPT_SELECTION.format(
            items_json=items_json,
            n=n,
            min_news=n - _MAX_REPOS_IN_POOL,
            max_repos=_MAX_REPOS_IN_POOL,
            recent_titles_block=recent_titles_block,
        )

        try:
            raw = await self._client.complete(prompt, system=SYSTEM_PROMPT_EDITOR)
            parsed = _extract_json(raw)
        except Exception as exc:
            self._log.error("selection_parse_error", error=str(exc))
            sorted_items = sorted(enumerate(items), key=lambda x: x[1].score or 0, reverse=True)
            return [i for i, _ in sorted_items[:n]], []

        if not isinstance(parsed, dict):
            self._log.warning("selection_unexpected_schema")
            sorted_items = sorted(enumerate(items), key=lambda x: x[1].score or 0, reverse=True)
            return [i for i, _ in sorted_items[:n]], []

        # Translate serialized indices → original indices via mapping
        selected = [
            idx_mapping[int(i)]
            for i in parsed.get("selected", [])
            if isinstance(i, (int, float)) and 0 <= int(i) < len(idx_mapping)
        ]
        breaking_raw = [
            idx_mapping[int(i)]
            for i in parsed.get("breaking", [])
            if isinstance(i, (int, float)) and 0 <= int(i) < len(idx_mapping)
        ]
        breaking = [i for i in breaking_raw if i in selected]

        # Hard-enforce max repos
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
