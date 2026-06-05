"""
agent/publisher/git_publisher.py

Writes Markdown posts to the blog directory on disk.
Git commit and push are handled externally (GitHub Actions workflow or local script).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from agent.config import settings
from agent.db.posts import PublishedPost
from agent.publisher.markdown import MarkdownPublisher

logger = structlog.get_logger(__name__)


class GitPublisher:
    """
    Writes Markdown posts to the blog posts directory.
    Git operations (add/commit/push) are left to the caller environment.
    """

    def __init__(self) -> None:
        self._repo_path = Path(settings.blog_repo_path)
        self._posts_subdir = Path(settings.blog_posts_subdir)
        self._markdown_publisher = MarkdownPublisher()

    async def publish_posts(self, posts: list[PublishedPost]) -> list[str]:
        """
        Write Markdown files to disk and return the list of slugs saved.
        """
        if not posts:
            logger.info("publish_posts_skipped", reason="empty post list")
            return []

        output_dir = self._repo_path / self._posts_subdir

        try:
            saved_paths: list[Path] = await asyncio.to_thread(
                self._write_all_markdown, posts, output_dir
            )
        except Exception as exc:
            logger.error("markdown_generation_error", error=str(exc))
            raise

        staged_stems = {p.stem for p in saved_paths}
        slugs = [post.slug for post in posts if post.slug in staged_stems]

        logger.info("publish_posts_done", count=len(slugs), slugs=slugs)
        return slugs

    def _write_all_markdown(
        self, posts: list[PublishedPost], output_dir: Path
    ) -> list[Path]:
        paths: list[Path] = []
        for post in posts:
            try:
                path = self._markdown_publisher.save_to_disk(post, output_dir)
                paths.append(path)
                logger.debug("markdown_written", slug=post.slug, path=str(path))
            except OSError as exc:
                logger.error("markdown_write_error", slug=post.slug, error=str(exc))
        return paths
