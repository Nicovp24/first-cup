"""
agent/notifier/linkedin.py

Posts new articles to LinkedIn automatically after publishing.

Requires two env vars:
  LINKEDIN_ACCESS_TOKEN  — OAuth2 access token (valid 60 days, refresh manually)
  LINKEDIN_AUTHOR_URN    — e.g. "urn:li:person:ABC123" or "urn:li:organization:456"

Get your person URN:
  curl -H "Authorization: Bearer {TOKEN}" https://api.linkedin.com/v2/me
  → use the "id" field as: urn:li:person:{id}
"""

from __future__ import annotations

import asyncio

import httpx
import structlog

from agent.config import settings
from agent.db.posts import PublishedPost

logger = structlog.get_logger(__name__)

_API = "https://api.linkedin.com/v2/ugcPosts"
_SITE = "https://first-cup.es"

_HASHTAGS = ["#Tech", "#IA", "#Programación", "#OpenSource", "#Dev"]


class LinkedInNotifier:
    def __init__(self) -> None:
        self._token  = getattr(settings, "linkedin_access_token", None) or ""
        self._author = getattr(settings, "linkedin_author_urn", None) or ""
        self._log    = structlog.get_logger(self.__class__.__name__)

    def _is_configured(self) -> bool:
        return bool(self._token and self._author)

    async def post_articles(self, posts: list[PublishedPost]) -> int:
        if not self._is_configured():
            self._log.info("linkedin_skipped", reason="LINKEDIN_ACCESS_TOKEN or LINKEDIN_AUTHOR_URN not set")
            return 0

        sent = 0
        for post in posts[:3]:  # max 3 per run to avoid spam
            try:
                ok = await self._post_one(post)
                if ok:
                    sent += 1
                await asyncio.sleep(2)  # brief pause between posts
            except Exception as exc:
                self._log.error("linkedin_post_error", title=post.title, error=str(exc))

        self._log.info("linkedin_done", sent=sent)
        return sent

    async def _post_one(self, post: PublishedPost) -> bool:
        url        = f"{_SITE}/{post.slug}"
        tags_str   = " ".join(_HASHTAGS[:3])
        # Build post text: hook + description + tags
        text = f"{post.title}\n\n{post.description}\n\n{tags_str}\n\n🔗 {url}"

        payload = {
            "author": self._author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "originalUrl": url,
                        "title": {"text": post.title},
                        "description": {"text": post.description[:200]},
                    }],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(_API, json=payload, headers=headers)

        if resp.status_code in (200, 201):
            self._log.info("linkedin_posted", title=post.title, url=url)
            return True

        self._log.warning(
            "linkedin_post_failed",
            title=post.title,
            status=resp.status_code,
            body=resp.text[:300],
        )
        return False
