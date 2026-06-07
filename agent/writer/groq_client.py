"""
agent/writer/groq_client.py

Async wrapper around the Groq API (OpenAI-compatible) for First Cup.
Drop-in replacement for GeminiClient / ClaudeClient.

Free tier: 14 400 requests/day, 30 req/min — far above what we need.
Model: llama-3.3-70b-versatile (quality comparable to GPT-4o).
"""

from __future__ import annotations

import asyncio

import httpx
import structlog

from agent.config import settings

logger = structlog.get_logger(__name__)

_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096
_RETRY_ATTEMPTS = 4
_BACKOFF_BASE = 10.0
_TIMEOUT = 60.0


class GroqClient:
    """
    Async Groq client matching the complete(prompt, system) interface.
    Uses raw httpx to avoid adding the openai SDK as a dependency.
    """

    def __init__(self) -> None:
        self._api_key: str = settings.groq_api_key or ""
        self._log = structlog.get_logger(self.__class__.__name__)

    async def complete(self, prompt: str, system: str = "") -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_exc: Exception | None = None
        backoff = _BACKOFF_BASE

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for attempt in range(1, _RETRY_ATTEMPTS + 1):
                log = self._log.bind(model=MODEL, attempt=attempt)
                try:
                    log.debug("groq_request_start")
                    resp = await client.post(_BASE_URL, json=payload, headers=headers)

                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("retry-after", backoff))
                        log.warning("groq_rate_limit", retry_after=retry_after, attempt=attempt)
                        last_exc = RuntimeError(f"Groq 429 rate limit (attempt {attempt})")
                        if attempt < _RETRY_ATTEMPTS:
                            await asyncio.sleep(retry_after)
                            backoff = min(backoff * 2, 120)
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    text: str = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    log.info(
                        "groq_request_ok",
                        input_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                        output_chars=len(text),
                    )
                    return text

                except httpx.HTTPStatusError as exc:
                    log.warning("groq_http_error", status=exc.response.status_code, attempt=attempt)
                    last_exc = exc
                except Exception as exc:
                    log.warning("groq_request_error", error=str(exc), attempt=attempt)
                    last_exc = exc

                if attempt < _RETRY_ATTEMPTS:
                    log.info("groq_retry_backoff", wait_seconds=backoff)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 120)

        self._log.error("groq_all_retries_failed", attempts=_RETRY_ATTEMPTS, error=str(last_exc))
        raise last_exc  # type: ignore[misc]
