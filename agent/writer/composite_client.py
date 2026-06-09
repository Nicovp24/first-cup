"""
agent/writer/composite_client.py

Tries clients in order per call — if the primary fails, falls back to the next.
"""
from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class CompositeClient:
    def __init__(self, clients: list) -> None:
        self._clients = clients

    async def complete(self, prompt: str, system: str = "") -> str:
        last_exc: Exception | None = None
        for client in self._clients:
            name = type(client).__name__
            try:
                result = await client.complete(prompt, system=system)
                logger.debug("composite_client_ok", client=name)
                return result
            except Exception as exc:
                logger.warning("composite_client_failed", client=name, error=str(exc))
                last_exc = exc
        raise last_exc  # type: ignore[misc]
