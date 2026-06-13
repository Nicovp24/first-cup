"""
agent/writer/gemini_client.py

Async wrapper around the Google Gemini SDK for First Cup.
Drop-in replacement for ClaudeClient — same complete(prompt, system) interface.
"""

from __future__ import annotations

import asyncio

import structlog
import google.generativeai as genai

from agent.config import settings

logger = structlog.get_logger(__name__)

MODEL = "models/gemini-2.0-flash"
MAX_TOKENS = 4096
_RETRY_ATTEMPTS = 5
_BACKOFF_BASE = 20.0   # seconds; rate-limit errors need at least 15s+


class GeminiClient:
    """
    Thin async wrapper around google.generativeai.
    Matches the ClaudeClient.complete(prompt, system) interface exactly.
    """

    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self._log = structlog.get_logger(self.__class__.__name__)

    async def complete(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        last_exc: Exception | None = None
        backoff = _BACKOFF_BASE

        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            log = self._log.bind(model=MODEL, attempt=attempt, prompt_chars=len(full_prompt))
            try:
                log.debug("gemini_request_start")
                model = genai.GenerativeModel(
                    MODEL,
                    generation_config=genai.GenerationConfig(max_output_tokens=MAX_TOKENS),
                )
                response = await model.generate_content_async(full_prompt)
                text = response.text
                log.info("gemini_request_ok", output_chars=len(text))
                return text

            except Exception as exc:
                log.warning("gemini_request_error", error=str(exc), attempt=attempt)
                last_exc = exc
                err_str = str(exc)

                # Daily quota exhausted — retrying won't help until tomorrow
                _DAILY_QUOTA_MARKERS = (
                    "PerDay",
                    "GenerateRequestsPerDay",
                    "RESOURCE_EXHAUSTED",
                )
                if any(m in err_str for m in _DAILY_QUOTA_MARKERS):
                    log.warning("gemini_daily_quota_exceeded_no_retry")
                    break

                # Per-minute rate limit — extract suggested wait and retry
                import re as _re
                m = _re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_str)
                wait = int(m.group(1)) + 2 if m else backoff
                # Cap wait so we fail fast and let Claude take over
                wait = min(wait, 30)
                if attempt < _RETRY_ATTEMPTS:
                    log.info("gemini_retry_backoff", wait_seconds=wait)
                    await asyncio.sleep(wait)
                    backoff = min(backoff * 2, 60)

        self._log.error("gemini_all_retries_failed", attempts=_RETRY_ATTEMPTS, error=str(last_exc))
        raise last_exc  # type: ignore[misc]
