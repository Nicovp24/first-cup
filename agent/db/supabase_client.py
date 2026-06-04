"""
agent/db/supabase_client.py

Supabase singleton client for First Cup.

Tables used by the system:
  - posts:          id, title, slug, content, source_urls (jsonb), tags (jsonb),
                    published_at, created_at
  - scraped_items:  id, url, title, source, scraped_at  (for deduplication)
"""

from __future__ import annotations

import structlog
from supabase import Client, create_client

from agent.config import settings

logger = structlog.get_logger(__name__)

_client: Client | None = None


def get_client() -> Client:
    """
    Return the process-wide Supabase client, creating it on first call.

    The client is intentionally module-level so it is initialised exactly once
    per interpreter process and reused across all async tasks.

    Returns:
        A fully initialised ``supabase.Client`` instance.

    Raises:
        Exception: Re-raised after logging if the client cannot be created.
    """
    global _client

    if _client is not None:
        return _client

    logger.info(
        "supabase_client_init",
        url=settings.supabase_url,
    )

    try:
        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("supabase_client_ready", url=settings.supabase_url)
    except Exception as exc:
        logger.error(
            "supabase_client_error",
            url=settings.supabase_url,
            error=str(exc),
        )
        raise

    return _client
