"""
agent/writer/claude_client.py

Async wrapper around the Anthropic SDK for Nexus Digest.

Features:
  - Automatic retry with exponential back-off (3 attempts: 1 s, 2 s, 4 s)
  - Per-request 60-second timeout enforced via httpx
  - Token usage logging
  - Structured error handling for RateLimitError and APIError
"""

from __future__ import annotations

import asyncio

import anthropic
import structlog

from agent.config import MAX_TOKENS, MODEL, settings

logger = structlog.get_logger(__name__)

_RETRY_ATTEMPTS = 3
_BACKOFF_BASE = 1.0          # seconds; doubled after each failure
_REQUEST_TIMEOUT = 60.0      # seconds


class ClaudeClient:
    """
    Thin async wrapper around ``anthropic.AsyncAnthropic``.

    Usage::

        client = ClaudeClient()
        text = await client.complete("Summarise this article…")
    """

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=_REQUEST_TIMEOUT,
        )
        self._log = structlog.get_logger(self.__class__.__name__)

    async def complete(self, prompt: str, system: str = "") -> str:
        """
        Send a user prompt to Claude and return the assistant's text response.

        Retries up to :data:`_RETRY_ATTEMPTS` times with exponential back-off
        on rate-limit and transient API errors.

        Args:
            prompt: The user message to send.
            system: Optional system prompt prepended to the conversation.

        Returns:
            The text content of Claude's first response block.

        Raises:
            anthropic.APIError: After all retry attempts are exhausted.
        """
        messages: list[dict] = [{"role": "user", "content": prompt}]
        kwargs: dict = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        last_exc: Exception | None = None
        backoff = _BACKOFF_BASE

        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            log = self._log.bind(
                model=MODEL,
                attempt=attempt,
                prompt_chars=len(prompt),
            )
            try:
                log.debug("claude_request_start")
                response = await self._client.messages.create(**kwargs)

                # Log token usage for cost tracking
                usage = response.usage
                log.info(
                    "claude_request_ok",
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                )

                # Extract the first text block
                for block in response.content:
                    if block.type == "text":
                        return block.text

                # Fallback: should not happen with standard text models
                log.warning("claude_no_text_block", content_types=[b.type for b in response.content])
                return ""

            except anthropic.RateLimitError as exc:
                log.warning(
                    "claude_rate_limit",
                    retry_after=getattr(exc, "retry_after", None),
                    attempt=attempt,
                )
                last_exc = exc

            except anthropic.APIStatusError as exc:
                # 5xx server errors are retriable; 4xx (except 429) are not
                if exc.status_code >= 500:
                    log.warning(
                        "claude_server_error",
                        status_code=exc.status_code,
                        attempt=attempt,
                    )
                    last_exc = exc
                else:
                    log.error(
                        "claude_client_error",
                        status_code=exc.status_code,
                        message=exc.message,
                    )
                    raise

            except anthropic.APIError as exc:
                log.warning("claude_api_error", error=str(exc), attempt=attempt)
                last_exc = exc

            if attempt < _RETRY_ATTEMPTS:
                log.info("claude_retry_backoff", wait_seconds=backoff)
                await asyncio.sleep(backoff)
                backoff *= 2

        self._log.error(
            "claude_all_retries_failed",
            attempts=_RETRY_ATTEMPTS,
            error=str(last_exc),
        )
        raise last_exc  # type: ignore[misc]
