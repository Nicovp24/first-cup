"""
agent.scraper – all scrapers and the shared ScrapedItem dataclass.
"""

from .base import ScrapedItem, ScraperBase
from .arxiv import ArXivScraper
from .devto import DevToScraper
from .github_api import GitHubAPIScraper
from .github_trending import GitHubTrendingScraper
from .hackernews import HackerNewsScraper
from .producthunt import ProductHuntScraper
from .reddit import RedditScraper, SUBREDDITS
from .rss import RSS_FEEDS, RSSScraper

__all__ = [
    "ScrapedItem",
    "ScraperBase",
    "ArXivScraper",
    "DevToScraper",
    "GitHubAPIScraper",
    "GitHubTrendingScraper",
    "HackerNewsScraper",
    "ProductHuntScraper",
    "RedditScraper",
    "SUBREDDITS",
    "RSSScraper",
    "RSS_FEEDS",
]
