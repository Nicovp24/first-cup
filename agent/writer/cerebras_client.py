"""
agent/writer/cerebras_client.py

Async wrapper around the Cerebras API (OpenAI-compatible).
Free tier: 60,000 TPM and 30 RPM — 10x more generous than Groq.
Model: llama-3.3-70b (same as Groq, same quality).
"""

from __future__ import annotations

import asyncio

import httpx
import structlog

from agent.config import settings

logger = structlog.get_logger(__name__)

_BASE_URL = "https://api.cerebras.ai/v1/chat/completions"
MODEL = "gpt-oss-120b"
MAX_TOKENS = 8192
_RETRY_ATTEMPTS = 6
_BACKOFF_BASE = 10.0
_TIMEOUT = 60.0
_DAILY_LIMIT_THRESHOLD = 600


class CerebrasClient:
    """
    Async Cerebras client matching the complete(prompt, system) interface.
    OpenAI-compatible API — behaves identically to GroqClient.
    """

    def __init__(self) -> None:
        self._api_key: str = settings.cerebras_api_key or ""
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
                log.debug("cerebras_request_start")
                try:
                    resp = await client.post(_BASE_URL, json=payload, headers=headers)
                except Exception as exc:
                    log.warning("cerebras_request_error", error=str(exc), attempt=attempt)
                    last_exc = exc
                    if attempt < _RETRY_ATTEMPTS:
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, 120)
                    continue

                if resp.status_code == 429:
                    raw_wait = int(resp.headers.get("retry-after", backoff))
                    if raw_wait > _DAILY_LIMIT_THRESHOLD:
                        last_exc = RuntimeError(f"Cerebras daily limit exceeded (retry-after={raw_wait}s)")
                        log.warning("cerebras_daily_limit_exceeded", retry_after=raw_wait)
                        break
                    log.warning("cerebras_rate_limit", retry_after=raw_wait, attempt=attempt)
                    last_exc = RuntimeError(f"Cerebras 429 rate limit (attempt {attempt})")
                    await asyncio.sleep(raw_wait + 2)
                    continue

                try:
                    resp.raise_for_status()
                    data = resp.json()
                    text: str = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    log.info(
                        "cerebras_request_ok",
                        input_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                        output_chars=len(text),
                    )
                    return text
                except Exception as exc:
                    log.warning("cerebras_http_error", status=resp.status_code, attempt=attempt)
                    last_exc = exc
                    if attempt < _RETRY_ATTEMPTS:
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, 120)

        self._log.error("cerebras_all_retries_failed", attempts=_RETRY_ATTEMPTS, error=str(last_exc))
        raise last_exc  # type: ignore[misc]
