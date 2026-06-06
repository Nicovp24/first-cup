"""
agent/notifier/telegram.py

Sends a daily digest summary to a Telegram channel after the agent publishes
new posts.

Features:
- One message per published post with title, description, and blog link.
- Graceful degradation: if the token or channel ID is missing, the notifier
  silently skips rather than crashing the pipeline.
- Optional premium group ping for subscribers.
- Markdown V2 formatting (Telegram's preferred rich-text mode).
"""

from __future__ import annotations

import re
from typing import Any

import httpx
import structlog

from agent.config import settings
from agent.db.posts import PublishedPost

logger = structlog.get_logger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
_BLOG_BASE_URL = "https://first-cup-kappa.vercel.app"  # update to custom domain when ready
_TIMEOUT = 20.0


def _escape_md2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    # Characters that must be escaped: _ * [ ] ( ) ~ ` > # + - = | { } . !
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!\\])", r"\\\1", text)


class TelegramNotifier:
    """
    Posts digest summaries to a Telegram channel.

    The notifier is a no-op when ``TELEGRAM_BOT_TOKEN`` or
    ``TELEGRAM_CHANNEL_ID`` are not configured — the rest of the pipeline
    is unaffected.
    """

    def __init__(self) -> None:
        self._token: str = settings.telegram_bot_token or ""
        self._channel: str = settings.telegram_channel_id or ""
        self._premium_group: str = settings.telegram_premium_group_id or ""
        self._enabled = bool(self._token and self._channel)
        self._log = structlog.get_logger(self.__class__.__name__)

        if not self._enabled:
            self._log.info(
                "telegram_disabled",
                reason="TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID not set",
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def notify(self, posts: list[PublishedPost]) -> None:
        """
        Send one Telegram message per published post to the configured channel.

        Args:
            posts: The posts that were published in the current run.
        """
        if not self._enabled or not posts:
            return

        self._log.info("telegram_notify_start", post_count=len(posts))

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for post in posts:
                try:
                    await self._send_post_message(client, post, self._channel)
                except Exception as exc:
                    self._log.error(
                        "telegram_send_error",
                        slug=post.slug,
                        chat=self._channel,
                        error=str(exc),
                    )

            # Ping the premium group with a short digest roundup
            if self._premium_group and len(posts) > 1:
                try:
                    await self._send_roundup(client, posts, self._premium_group)
                except Exception as exc:
                    self._log.error(
                        "telegram_premium_send_error",
                        error=str(exc),
                    )

        self._log.info("telegram_notify_done", post_count=len(posts))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _send_post_message(
        self,
        client: httpx.AsyncClient,
        post: PublishedPost,
        chat_id: str,
    ) -> None:
        """Send a single post notification to *chat_id*."""
        url = f"{_BLOG_BASE_URL}/{post.slug}"
        tag_line = " ".join(f"\\#{_escape_md2(t.replace(' ', '_'))}" for t in post.tags[:3])

        title = _escape_md2(post.title)
        description = _escape_md2(post.description)
        url_escaped = _escape_md2(url)

        text = (
            f"☕ *{title}*\n\n"
            f"{description}\n\n"
            f"{tag_line}\n\n"
            f"[Leer en First Cup]({url_escaped})"
        )

        await self._send_message(client, chat_id, text)
        self._log.info("telegram_post_sent", slug=post.slug, chat=chat_id)

    async def _send_roundup(
        self,
        client: httpx.AsyncClient,
        posts: list[PublishedPost],
        chat_id: str,
    ) -> None:
        """Send a bullet-list roundup of all today's posts to the premium group."""
        lines = ["☕ *First Cup — resumen de hoy*\n"]
        for post in posts:
            url = f"{_BLOG_BASE_URL}/{post.slug}"
            title = _escape_md2(post.title)
            url_escaped = _escape_md2(url)
            lines.append(f"• [{title}]({url_escaped})")

        text = "\n".join(lines)
        await self._send_message(client, chat_id, text)
        self._log.info("telegram_roundup_sent", post_count=len(posts), chat=chat_id)

    async def _send_message(
        self,
        client: httpx.AsyncClient,
        chat_id: str,
        text: str,
    ) -> dict[str, Any]:
        """POST to the Telegram sendMessage endpoint."""
        endpoint = _TELEGRAM_API.format(token=self._token, method="sendMessage")
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": False,
        }

        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        result: dict[str, Any] = response.json()

        if not result.get("ok"):
            raise RuntimeError(
                f"Telegram API returned ok=false: {result.get('description', 'unknown error')}"
            )

        return result
