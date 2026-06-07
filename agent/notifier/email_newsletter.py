"""
agent/notifier/email_newsletter.py

Sends the daily digest email to all confirmed subscribers via Resend.

One email per subscriber (avoids BCC leakage). Uses Resend's batch
endpoint when available for efficiency, falling back to serial sends.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
import structlog

from agent.config import settings
from agent.db.posts import PublishedPost
from agent.db.subscribers import get_confirmed_subscribers

logger = structlog.get_logger(__name__)

_RESEND_URL   = "https://api.resend.com/emails"
_RESEND_BATCH = "https://api.resend.com/emails/batch"


class EmailNewsletter:
    """Sends digest emails to confirmed subscribers."""

    def __init__(self) -> None:
        self._api_key  = settings.resend_api_key or ""
        self._from     = getattr(settings, "email_from", None) or "First Cup <hola@firstcup.es>"
        self._site     = "https://first-cup-kappa.vercel.app"
        self._log      = structlog.get_logger(self.__class__.__name__)

    async def send_digest(self, posts: list[PublishedPost]) -> int:
        """
        Send the digest email to all confirmed subscribers.
        Returns the number of emails successfully sent.
        """
        if not self._api_key:
            self._log.warning("email_newsletter_skipped", reason="RESEND_API_KEY not set")
            return 0

        if not posts:
            self._log.warning("email_newsletter_skipped", reason="no posts")
            return 0

        subscribers = await get_confirmed_subscribers()
        if not subscribers:
            self._log.info("email_newsletter_no_subscribers")
            return 0

        self._log.info(
            "email_newsletter_start",
            posts=len(posts),
            subscribers=len(subscribers),
        )

        edition_date = datetime.now(tz=timezone.utc).strftime("%-d de %B de %Y")
        subject      = f"☕ First Cup — {edition_date}"

        # Build payload list for batch send
        batch: list[dict] = []
        for sub in subscribers:
            token    = sub.get("confirm_token", "")
            unsubUrl = f"{self._site}/api/unsubscribe?token={token}"
            batch.append({
                "from":    self._from,
                "to":      [sub["email"]],
                "subject": subject,
                "html":    self._build_html(posts, unsubUrl, edition_date),
            })

        sent = await self._send_batch(batch)
        self._log.info("email_newsletter_done", sent=sent, total=len(batch))
        return sent

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _send_batch(self, batch: list[dict]) -> int:
        """Try batch endpoint first; fall back to serial sends on failure."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Attempt batch (Resend supports up to 100 per call)
            try:
                chunks = [batch[i:i+100] for i in range(0, len(batch), 100)]
                sent = 0
                for chunk in chunks:
                    resp = await client.post(_RESEND_BATCH, json=chunk, headers=headers)
                    if resp.status_code in (200, 201):
                        sent += len(chunk)
                    else:
                        self._log.warning(
                            "resend_batch_failed",
                            status=resp.status_code,
                            body=resp.text[:200],
                        )
                        # Fall back: send individually for this chunk
                        sent += await self._send_serial(chunk, client, headers)
                return sent
            except Exception as exc:
                self._log.error("resend_batch_error", error=str(exc))
                return await self._send_serial(batch, client, headers)

    async def _send_serial(
        self,
        batch: list[dict],
        client: httpx.AsyncClient,
        headers: dict,
    ) -> int:
        sent = 0
        for email in batch:
            try:
                resp = await client.post(_RESEND_URL, json=email, headers=headers)
                if resp.status_code in (200, 201):
                    sent += 1
                else:
                    self._log.warning(
                        "resend_serial_failed",
                        to=email.get("to"),
                        status=resp.status_code,
                    )
                await asyncio.sleep(0.05)  # 50ms throttle
            except Exception as exc:
                self._log.error("resend_serial_error", to=email.get("to"), error=str(exc))
        return sent

    def _build_html(
        self,
        posts: list[PublishedPost],
        unsubscribe_url: str,
        edition_date: str,
    ) -> str:
        posts_html = "".join(self._post_block(p) for p in posts)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body{{margin:0;padding:0;background:#f5f0e8;font-family:Georgia,'Times New Roman',serif;color:#2a1f14;}}
    table{{border-collapse:collapse;}}
    a{{color:#8b4513;}}
  </style>
</head>
<body>
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0e8;padding:2rem 1rem;">
  <tr><td>
    <table width="600" align="center" cellpadding="0" cellspacing="0"
           style="max-width:600px;width:100%;margin:0 auto;background:#f5f0e8;">

      <!-- Masthead -->
      <tr><td style="border-top:3px solid #1a0f06;border-bottom:1px solid #c5a882;
                      padding:1.5rem 0;text-align:center;">
        <span style="display:block;font-family:monospace;font-size:0.58rem;
                      letter-spacing:0.2em;text-transform:uppercase;color:#8b4513;
                      margin-bottom:0.35rem;">
          {edition_date} · La Gaceta Digital
        </span>
        <span style="font-size:2.8rem;font-weight:900;color:#1a0f06;
                      font-family:Georgia,serif;letter-spacing:-0.02em;">First Cup</span>
        <span style="display:block;font-family:monospace;font-size:0.58rem;
                      letter-spacing:0.16em;text-transform:uppercase;color:#6b5744;
                      margin-top:0.35rem;">
          IA · Desarrollo · Tecnología
        </span>
      </td></tr>

      <!-- Posts -->
      <tr><td style="padding:1.75rem 0 0;">
        {posts_html}
      </td></tr>

      <!-- CTA -->
      <tr><td style="padding:1.5rem 0 0;text-align:center;border-top:1px solid #c5a882;">
        <a href="{self._site}"
           style="display:inline-block;background:#8b4513;color:#f5f0e8;
                   text-decoration:none;font-family:monospace;font-size:0.72rem;
                   font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                   padding:0.8rem 2rem;">
          Ver todas las ediciones →
        </a>
      </td></tr>

      <!-- Footer -->
      <tr><td style="border-top:1px solid #c5a882;padding:1.25rem 0;margin-top:2rem;">
        <p style="font-family:monospace;font-size:0.6rem;color:#9a8572;
                   letter-spacing:0.06em;margin:0 0 0.35rem;text-align:center;">
          © 2026 First Cup ·
          <a href="{self._site}" style="color:#8b4513;text-decoration:none;">firstcup.es</a>
        </p>
        <p style="font-family:monospace;font-size:0.58rem;color:#b0a090;
                   letter-spacing:0.04em;margin:0;line-height:1.6;text-align:center;">
          <a href="{unsubscribe_url}" style="color:#b0a090;">Cancelar suscripción</a>
        </p>
      </td></tr>

    </table>
  </td></tr>
  </table>
</body>
</html>"""

    def _post_block(self, post: PublishedPost) -> str:
        post_url = f"{self._site}/{post.slug}"
        tags_html = " · ".join(
            f'<span style="font-family:monospace;font-size:0.6rem;color:#8b4513;'
            f'letter-spacing:0.1em;text-transform:uppercase;">{t}</span>'
            for t in (post.tags or [])[:3]
        )
        cover_block = ""
        if post.cover:
            cover_block = (
                f'<a href="{post_url}">'
                f'<img src="{post.cover}" alt="" width="600" '
                f'style="display:block;width:100%;max-height:280px;object-fit:cover;'
                f'border-top:2px solid #1a0f06;margin-bottom:0;" /></a>'
            )

        return f"""
<table width="100%" cellpadding="0" cellspacing="0"
       style="margin-bottom:2rem;border-bottom:1px solid #c5a882;padding-bottom:2rem;">
  <tr><td>
    {cover_block}
    <div style="padding:{'1rem 0 0' if cover_block else '0'};">
      <div style="margin-bottom:0.5rem;">{tags_html}</div>
      <h2 style="font-family:Georgia,serif;font-size:1.35rem;font-weight:800;
                  color:#1a0f06;margin:0 0 0.65rem;line-height:1.2;
                  letter-spacing:-0.01em;">
        <a href="{post_url}" style="color:#1a0f06;text-decoration:none;">{post.title}</a>
      </h2>
      <p style="font-size:0.92rem;line-height:1.7;color:#4a3728;font-style:italic;
                 margin:0 0 1rem;">{post.description}</p>
      <a href="{post_url}"
         style="font-family:monospace;font-size:0.68rem;font-weight:700;
                 color:#8b4513;text-decoration:none;letter-spacing:0.1em;
                 text-transform:uppercase;">
        Leer artículo →
      </a>
    </div>
  </td></tr>
</table>"""
