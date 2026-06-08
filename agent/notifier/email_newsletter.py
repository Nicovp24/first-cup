"""
agent/notifier/email_newsletter.py

Sends emails to Premium subscribers via Resend.

Three email types:
  - send_digest(posts, shots)     — daily digest at 07:00 with full articles + Shots
  - send_breaking_news(posts)     — instant alert when urgent news is detected
  - send_weekly_summary(posts)    — Sunday recap of the week's best posts
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import httpx
import structlog

from agent.config import settings
from agent.db.posts import PublishedPost
from agent.db.subscribers import get_premium_subscribers

if TYPE_CHECKING:
    from agent.scraper.base import ScrapedItem

logger = structlog.get_logger(__name__)

_RESEND_URL   = "https://api.resend.com/emails"
_RESEND_BATCH = "https://api.resend.com/emails/batch"
_SITE         = "https://first-cup.es"

# ── Brand tokens (latte theme) ────────────────────────────────────────────────
_INK       = "#1a0f06"
_PAPER     = "#f5f0e8"
_PAPER2    = "#ede7da"
_SPOT      = "#8b4513"
_SOFT      = "#4a3728"
_FAINT     = "#9a8572"
_RULE      = "#c5a882"
_MONO      = "monospace, 'Courier New', Courier"
_SERIF     = "Georgia, 'Times New Roman', serif"


class EmailNewsletter:
    """Sends Premium-only emails via Resend."""

    def __init__(self) -> None:
        self._api_key = settings.resend_api_key or ""
        self._from    = getattr(settings, "email_from", None) or f"First Cup <hola@first-cup.es>"
        self._log     = structlog.get_logger(self.__class__.__name__)

    # ── Public send methods ───────────────────────────────────────────────────

    async def send_digest(
        self,
        posts: list[PublishedPost],
        shots: list["ScrapedItem"] | None = None,
    ) -> int:
        """Daily digest email: full articles + Shots section. Premium only."""
        if not self._api_key or not posts:
            return 0

        subs = await get_premium_subscribers()
        if not subs:
            self._log.info("send_digest_skipped", reason="no premium subscribers")
            return 0

        date_str = datetime.now(tz=timezone.utc).strftime("%-d de %B de %Y")
        subject  = f"☕ First Cup — {date_str}"
        html     = self._build_digest_html(posts, shots or [], date_str)

        return await self._batch_send(subs, subject, html, "send_digest")

    async def send_breaking_news(self, posts: list[PublishedPost]) -> int:
        """Instant breaking-news alert. Premium only."""
        if not self._api_key or not posts:
            return 0

        subs = await get_premium_subscribers()
        if not subs:
            return 0

        title   = posts[0].title if len(posts) == 1 else f"{len(posts)} noticias urgentes"
        subject = f"🔴 Breaking — {title}"
        html    = self._build_breaking_html(posts)

        return await self._batch_send(subs, subject, html, "send_breaking_news")

    async def send_weekly_summary(self, posts: list[PublishedPost]) -> int:
        """Sunday weekly recap. Premium only."""
        if not self._api_key or not posts:
            return 0

        subs = await get_premium_subscribers()
        if not subs:
            self._log.info("send_weekly_summary_skipped", reason="no premium subscribers")
            return 0

        subject = "☕ First Cup — Lo mejor de la semana"
        html    = self._build_weekly_html(posts)

        return await self._batch_send(subs, subject, html, "send_weekly_summary")

    # ── HTML builders ─────────────────────────────────────────────────────────

    def _build_digest_html(
        self,
        posts: list[PublishedPost],
        shots: list["ScrapedItem"],
        date_str: str,
    ) -> str:
        posts_html = "".join(self._post_block(p) for p in posts)
        shots_html = self._shots_block(shots) if shots else ""

        return self._wrap(f"""
      {self._masthead(date_str, "EDICIÓN DIARIA")}

      <!-- Articles -->
      <tr><td style="padding:1.75rem 0 0;">
        {posts_html}
      </td></tr>

      {shots_html}

      {self._cta_block()}
        """)

    def _build_breaking_html(self, posts: list[PublishedPost]) -> str:
        posts_html = "".join(self._post_block(p) for p in posts)
        now_str = datetime.now(tz=timezone.utc).strftime("%-d de %B · %H:%M UTC")

        return self._wrap(f"""
      <!-- Breaking banner -->
      <tr><td style="background:{_INK};padding:0.9rem 1.5rem;text-align:center;">
        <span style="font-family:{_MONO};font-size:0.62rem;font-weight:700;
                      letter-spacing:0.2em;text-transform:uppercase;color:#ff6b35;">
          🔴 BREAKING NEWS — {now_str}
        </span>
      </td></tr>

      {self._masthead(now_str, "ALERTA PREMIUM")}

      <tr><td style="padding:1.75rem 0 0;">
        {posts_html}
      </td></tr>

      {self._cta_block()}
        """)

    def _build_weekly_html(self, posts: list[PublishedPost]) -> str:
        from datetime import timedelta
        now      = datetime.now(tz=timezone.utc)
        week_end = now.strftime("%-d de %B")
        week_start = (now - timedelta(days=6)).strftime("%-d de %B")
        date_range = f"{week_start} – {week_end}"

        posts_html = "".join(self._post_block(p, compact=True) for p in posts[:7])

        return self._wrap(f"""
      {self._masthead(date_range, "RESUMEN SEMANAL")}

      <tr><td style="padding:1.25rem 0 0.5rem;text-align:center;">
        <p style="font-family:{_MONO};font-size:0.65rem;letter-spacing:0.12em;
                   text-transform:uppercase;color:{_FAINT};margin:0;">
          Los mejores posts de la semana — solo para suscriptores Premium
        </p>
      </td></tr>

      <tr><td style="padding:0.5rem 0 0;">
        {posts_html}
      </td></tr>

      {self._cta_block()}
        """)

    # ── HTML components ───────────────────────────────────────────────────────

    def _wrap(self, inner: str) -> str:
        """Outer email shell (table-based, inbox-safe)."""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta name="color-scheme" content="light"/>
</head>
<body style="margin:0;padding:0;background:{_PAPER};font-family:{_SERIF};color:{_INK};">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:{_PAPER};padding:2rem 1rem;">
  <tr><td>
    <table width="600" align="center" cellpadding="0" cellspacing="0"
           style="max-width:600px;width:100%;margin:0 auto;background:{_PAPER};">
      {inner}
      {self._footer_block()}
    </table>
  </td></tr>
  </table>
</body>
</html>"""

    def _masthead(self, date_str: str, label: str) -> str:
        return f"""
      <tr><td style="border-top:3px solid {_INK};border-bottom:1px solid {_RULE};
                      padding:1.5rem 0;text-align:center;">
        <span style="display:block;font-family:{_MONO};font-size:0.55rem;
                      letter-spacing:0.22em;text-transform:uppercase;color:{_SPOT};
                      margin-bottom:0.4rem;">{date_str}</span>
        <span style="font-size:2.6rem;font-weight:900;color:{_INK};
                      font-family:{_SERIF};letter-spacing:-0.02em;line-height:1;">
          First Cup
        </span>
        <span style="display:block;font-family:{_MONO};font-size:0.52rem;
                      letter-spacing:0.2em;text-transform:uppercase;color:{_FAINT};
                      margin-top:0.4rem;border-top:1px solid {_RULE};
                      padding-top:0.4rem;">
          IA · Desarrollo · Tecnología &nbsp;—&nbsp; {label}
        </span>
      </td></tr>"""

    def _post_block(self, post: PublishedPost, compact: bool = False) -> str:
        post_url   = f"{_SITE}/{post.slug}"
        tags_html  = " &nbsp;·&nbsp; ".join(
            f'<span style="font-family:{_MONO};font-size:0.58rem;color:{_SPOT};'
            f'letter-spacing:0.1em;text-transform:uppercase;">{t}</span>'
            for t in (post.tags or [])[:3]
        )
        cover_block = ""
        if post.cover and not compact:
            cover_block = (
                f'<a href="{post_url}" style="display:block;">'
                f'<img src="{post.cover}" alt="" width="600"'
                f' style="display:block;width:100%;height:220px;object-fit:cover;'
                f'object-position:center 30%;border-top:2px solid {_INK};" /></a>'
            )

        padding = "0.75rem 0 0" if cover_block else "0"
        return f"""
<table width="100%" cellpadding="0" cellspacing="0"
       style="margin-bottom:2rem;border-bottom:1px solid {_RULE};padding-bottom:1.75rem;">
  <tr><td>
    {cover_block}
    <div style="padding:{padding};">
      <div style="margin-bottom:0.45rem;">{tags_html}</div>
      <h2 style="font-family:{_SERIF};font-size:1.28rem;font-weight:800;font-style:italic;
                  color:{_INK};margin:0 0 0.6rem;line-height:1.22;letter-spacing:-0.01em;">
        <a href="{post_url}" style="color:{_INK};text-decoration:none;">{post.title}</a>
      </h2>
      <p style="font-size:0.9rem;line-height:1.68;color:{_SOFT};font-style:italic;
                 margin:0 0 1rem;">{post.description}</p>
      <a href="{post_url}"
         style="font-family:{_MONO};font-size:0.65rem;font-weight:700;
                 color:{_SPOT};text-decoration:none;letter-spacing:0.1em;
                 text-transform:uppercase;border-bottom:1px solid {_SPOT};
                 padding-bottom:2px;">
        Leer artículo →
      </a>
    </div>
  </td></tr>
</table>"""

    def _shots_block(self, shots: list["ScrapedItem"]) -> str:
        if not shots:
            return ""

        items_html = ""
        for shot in shots[:6]:
            domain = shot.url
            try:
                from urllib.parse import urlparse
                domain = urlparse(shot.url).hostname.replace("www.", "")  # type: ignore[union-attr]
            except Exception:
                pass

            items_html += f"""
        <tr><td style="padding:0.55rem 0;border-bottom:1px solid {_RULE};">
          <a href="{shot.url}" target="_blank"
             style="text-decoration:none;color:{_INK};">
            <span style="font-family:{_SERIF};font-size:0.9rem;font-weight:700;
                          color:{_INK};">{shot.title}</span>
            <span style="display:block;font-family:{_MONO};font-size:0.6rem;
                          color:{_FAINT};letter-spacing:0.04em;margin-top:2px;">
              {domain}
            </span>
          </a>
        </td></tr>"""

        return f"""
      <!-- Shots -->
      <tr><td style="padding:1.5rem 0 0;">
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:{_PAPER2};border:1px solid {_RULE};
                       border-left:3px solid {_SPOT};padding:1.1rem 1.25rem;">
          <tr><td>
            <span style="font-family:{_MONO};font-size:0.58rem;font-weight:700;
                          letter-spacing:0.18em;text-transform:uppercase;color:{_SPOT};">
              ☕ SHOTS DEL DÍA
            </span>
            <span style="display:block;font-family:{_MONO};font-size:0.54rem;
                          color:{_FAINT};letter-spacing:0.06em;margin-top:3px;
                          margin-bottom:0.75rem;">
              Micro-dosis de lo que también pasó hoy
            </span>
          </td></tr>
          <table width="100%" cellpadding="0" cellspacing="0">
            {items_html}
          </table>
        </table>
      </td></tr>"""

    def _cta_block(self) -> str:
        return f"""
      <tr><td style="padding:1.5rem 0 0;text-align:center;border-top:1px solid {_RULE};">
        <a href="{_SITE}"
           style="display:inline-block;background:{_SPOT};color:{_PAPER};
                   text-decoration:none;font-family:{_MONO};font-size:0.68rem;
                   font-weight:700;letter-spacing:0.14em;text-transform:uppercase;
                   padding:0.8rem 2rem;">
          Ver en la web →
        </a>
      </td></tr>"""

    def _footer_block(self) -> str:
        return f"""
      <tr><td style="border-top:1px solid {_RULE};padding:1.25rem 0;margin-top:1.5rem;">
        <p style="font-family:{_MONO};font-size:0.58rem;color:{_FAINT};
                   letter-spacing:0.06em;margin:0 0 0.3rem;text-align:center;">
          © 2026 First Cup ·
          <a href="{_SITE}" style="color:{_SPOT};text-decoration:none;">first-cup.es</a>
          &nbsp;·&nbsp; Suscriptor Premium
        </p>
        <p style="font-family:{_MONO};font-size:0.54rem;color:#b0a090;
                   letter-spacing:0.04em;margin:0;line-height:1.6;text-align:center;">
          <a href="{_SITE}/cuenta" style="color:#b0a090;">Gestionar suscripción</a>
          &nbsp;·&nbsp;
          <a href="{_SITE}/privacidad" style="color:#b0a090;">Privacidad</a>
        </p>
      </td></tr>"""

    # ── Transport ─────────────────────────────────────────────────────────────

    async def _batch_send(
        self,
        subs: list[dict],
        subject: str,
        html: str,
        log_key: str,
    ) -> int:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        batch = [
            {"from": self._from, "to": [s["email"]], "subject": subject, "html": html}
            for s in subs
        ]

        self._log.info(f"{log_key}_start", subscribers=len(batch))
        sent = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for chunk in [batch[i:i+100] for i in range(0, len(batch), 100)]:
                try:
                    resp = await client.post(_RESEND_BATCH, json=chunk, headers=headers)
                    if resp.status_code in (200, 201):
                        sent += len(chunk)
                    else:
                        self._log.warning(
                            f"{log_key}_batch_failed",
                            status=resp.status_code,
                            body=resp.text[:200],
                        )
                        sent += await self._serial_send(chunk, client, headers, log_key)
                except Exception as exc:
                    self._log.error(f"{log_key}_batch_error", error=str(exc))
                    sent += await self._serial_send(chunk, client, headers, log_key)

        self._log.info(f"{log_key}_done", sent=sent, total=len(batch))
        return sent

    async def _serial_send(
        self,
        batch: list[dict],
        client: httpx.AsyncClient,
        headers: dict,
        log_key: str,
    ) -> int:
        sent = 0
        for email in batch:
            try:
                resp = await client.post(_RESEND_URL, json=email, headers=headers)
                if resp.status_code in (200, 201):
                    sent += 1
                else:
                    self._log.warning(
                        f"{log_key}_serial_failed",
                        to=email.get("to"),
                        status=resp.status_code,
                    )
                await asyncio.sleep(0.05)
            except Exception as exc:
                self._log.error(f"{log_key}_serial_error", to=email.get("to"), error=str(exc))
        return sent
