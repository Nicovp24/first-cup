"""
agent/db/subscribers.py

Async helpers for the `subscribers` Supabase table.
"""

from __future__ import annotations

import httpx
import structlog

from agent.config import settings

logger = structlog.get_logger(__name__)

_HEADERS = {
    "apikey": settings.supabase_service_key or "",
    "Authorization": f"Bearer {settings.supabase_service_key or ''}",
    "Content-Type": "application/json",
}


async def get_confirmed_subscribers() -> list[dict]:
    """
    Return all confirmed, still-subscribed (unsubscribed_at IS NULL) subscribers.
    """
    if not settings.supabase_url or not settings.supabase_service_key:
        logger.warning("get_confirmed_subscribers: Supabase not configured")
        return []

    url = (
        f"{settings.supabase_url}/rest/v1/subscribers"
        "?confirmed=eq.true&unsubscribed_at=is.null"
        "&select=id,email,tier,confirm_token"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("get_confirmed_subscribers_error", error=str(exc))
        return []


async def update_subscriber_tier(email: str, tier: str, stripe_id: str | None = None) -> None:
    """Update a subscriber's tier (free | premium) and optionally their Stripe customer ID."""
    if not settings.supabase_url or not settings.supabase_service_key:
        return

    payload: dict = {"tier": tier}
    if stripe_id:
        payload["stripe_id"] = stripe_id

    url = (
        f"{settings.supabase_url}/rest/v1/subscribers"
        f"?email=eq.{email}"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(url, json=payload, headers={**_HEADERS, "Prefer": "return=minimal"})
            resp.raise_for_status()
            logger.info("subscriber_tier_updated", email=email, tier=tier)
    except Exception as exc:
        logger.error("update_subscriber_tier_error", email=email, error=str(exc))
