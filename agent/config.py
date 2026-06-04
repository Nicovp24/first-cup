"""
agent/config.py

Centralised configuration for Nexus Digest.
All settings are loaded from environment variables (or a .env file).
A single `settings` singleton is exported so every module imports from here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Model / generation constants
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# Content sources
# ---------------------------------------------------------------------------
RSS_FEEDS: List[str] = [
    "https://simonwillison.net/atom/everything/",
    "https://www.deeplearning.ai/the-batch/feed/",
    "https://huggingface.co/blog/feed.xml",
    "https://openai.com/blog/rss/",
    "https://www.anthropic.com/rss.xml",
    "https://feeds.feedburner.com/TowardsDataScience",
]

SUBREDDITS: List[str] = [
    "MachineLearning",
    "LocalLLaMA",
    "Python",
    "webscraping",
    "programming",
    "artificial",
]


# ---------------------------------------------------------------------------
# Settings class
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    """
    All configuration values loaded from environment variables.
    Fields without a default are required — the application will raise a
    clear ValidationError at startup if any of them are missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Claude / Anthropic
    # ------------------------------------------------------------------
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic API key. Get one at https://console.anthropic.com/",
    )

    # ------------------------------------------------------------------
    # Supabase
    # ------------------------------------------------------------------
    supabase_url: str = Field(
        ...,
        description="Supabase project URL, e.g. https://xxxx.supabase.co",
    )
    supabase_key: str = Field(
        ...,
        description="Supabase service-role (or anon) key.",
    )

    # ------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------
    github_token: str = Field(
        ...,
        description="GitHub personal access token with repo scope.",
    )

    # ------------------------------------------------------------------
    # Reddit
    # ------------------------------------------------------------------
    reddit_client_id: str = Field(
        ...,
        description="Reddit OAuth2 client ID.",
    )
    reddit_client_secret: str = Field(
        ...,
        description="Reddit OAuth2 client secret.",
    )
    reddit_user_agent: str = Field(
        default="nexus-digest/1.0",
        description="User-agent string for Reddit API requests.",
    )

    # ------------------------------------------------------------------
    # Resend (email) — Fase 3, opcional por ahora
    # ------------------------------------------------------------------
    resend_api_key: str | None = Field(
        default=None,
        description="Resend API key for transactional email delivery.",
    )
    email_from: str = Field(
        default="newsletter@nexusdigest.com",
        description="Sender address used for outgoing newsletters.",
    )

    # ------------------------------------------------------------------
    # Telegram — Fase 3, opcional por ahora
    # ------------------------------------------------------------------
    telegram_bot_token: str | None = Field(
        default=None,
        description="Telegram Bot API token from @BotFather.",
    )
    telegram_channel_id: str = Field(
        default="@nexusdigest",
        description="Public channel username or numeric chat ID.",
    )
    telegram_premium_group_id: str | None = Field(
        default=None,
        description="Numeric ID of the premium subscribers supergroup (e.g. -100...).",
    )

    # ------------------------------------------------------------------
    # WhatsApp (360dialog) — Fase 4, opcional por ahora
    # ------------------------------------------------------------------
    whatsapp_api_key: str | None = Field(
        default=None,
        description="360dialog API key for WhatsApp Business API.",
    )
    whatsapp_phone_number: str | None = Field(
        default=None,
        description="WhatsApp sender phone number in E.164 format.",
    )

    # ------------------------------------------------------------------
    # Stripe — Fase 4, opcional por ahora
    # ------------------------------------------------------------------
    stripe_secret_key: str | None = Field(
        default=None,
        description="Stripe secret key (sk_live_... or sk_test_...).",
    )
    stripe_webhook_secret: str | None = Field(
        default=None,
        description="Stripe webhook signing secret (whsec_...).",
    )
    stripe_premium_price_id: str | None = Field(
        default=None,
        description="Stripe Price ID for the premium subscription plan.",
    )

    # ------------------------------------------------------------------
    # Blog / publisher
    # ------------------------------------------------------------------
    blog_repo_path: str = Field(
        default="/app/blog",
        description="Absolute path to the local clone of the blog repository.",
    )
    blog_github_repo: str = Field(
        ...,
        description="GitHub repo slug for the blog, e.g. usuario/nexus-digest-blog.",
    )
    blog_github_token: str = Field(
        ...,
        description="GitHub token with write access to the blog repository.",
    )

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------
    daily_run_hour: int = Field(
        default=7,
        ge=0,
        le=23,
        description="Hour (0-23, local time) at which the daily digest runs.",
    )
    daily_run_minute: int = Field(
        default=0,
        ge=0,
        le=59,
        description="Minute (0-59) at which the daily digest runs.",
    )
    timezone: str = Field(
        default="Europe/Madrid",
        description="IANA timezone name used by the scheduler.",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("anthropic_api_key")
    @classmethod
    def _validate_anthropic_key(cls, v: str) -> str:
        if not v.startswith("sk-ant-"):
            raise ValueError(
                "ANTHROPIC_API_KEY must start with 'sk-ant-'. "
                "Get a valid key at https://console.anthropic.com/"
            )
        return v

    @field_validator("supabase_url")
    @classmethod
    def _validate_supabase_url(cls, v: str) -> str:
        if not v.startswith("https://") or ".supabase.co" not in v:
            raise ValueError(
                "SUPABASE_URL must be a valid Supabase project URL "
                "(e.g. https://xxxx.supabase.co)."
            )
        return v.rstrip("/")

    @field_validator("stripe_secret_key")
    @classmethod
    def _validate_stripe_key(cls, v: str | None) -> str | None:
        if v is not None and not (v.startswith("sk_live_") or v.startswith("sk_test_")):
            raise ValueError(
                "STRIPE_SECRET_KEY must start with 'sk_live_' or 'sk_test_'."
            )
        return v

    @field_validator("stripe_webhook_secret")
    @classmethod
    def _validate_stripe_webhook(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith("whsec_"):
            raise ValueError(
                "STRIPE_WEBHOOK_SECRET must start with 'whsec_'."
            )
        return v

    @field_validator("blog_github_repo")
    @classmethod
    def _validate_github_repo(cls, v: str) -> str:
        if "/" not in v or v.startswith("/") or v.endswith("/"):
            raise ValueError(
                "BLOG_GITHUB_REPO must be in 'owner/repo' format "
                "(e.g. usuario/nexus-digest-blog)."
            )
        return v


# ---------------------------------------------------------------------------
# Singleton — import `settings` everywhere instead of instantiating directly
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _get_settings() -> Settings:
    """
    Cached factory so the .env file is parsed exactly once per process.
    Raises pydantic.ValidationError with clear field-level messages if any
    required variable is missing or invalid.
    """
    return Settings()


settings: Settings = _get_settings()
