"""
agent/publisher/git_publisher.py

Writes Markdown posts to the blog directory on disk, then commits and pushes.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import structlog

from agent.config import settings
from agent.db.posts import PublishedPost
from agent.publisher.markdown import MarkdownPublisher

logger = structlog.get_logger(__name__)


class GitPublisher:
    """
    Writes Markdown posts to the blog posts directory, then git add/commit/push.
    """

    def __init__(self) -> None:
        self._repo_path = Path(settings.blog_repo_path)
        self._posts_subdir = Path(settings.blog_posts_subdir)
        self._markdown_publisher = MarkdownPublisher()

    async def publish_posts(self, posts: list[PublishedPost]) -> list[str]:
        """
        Write Markdown files to disk, commit, push, and return list of slugs.
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

        if saved_paths:
            await asyncio.to_thread(self._git_commit_push, saved_paths, slugs)

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

    def _git_commit_push(self, paths: list[Path], slugs: list[str]) -> None:
        repo = str(self._repo_path)
        date = slugs[0].split("-")[-1] if slugs else "unknown"

        def run(cmd: list[str]) -> None:
            result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"git {cmd[1]} failed: {result.stderr.strip()}")

        try:
            # Pull to avoid push rejections if remote has newer commits
            subprocess.run(["git", "pull", "--rebase", "origin", "main"],
                           cwd=repo, capture_output=True, text=True)
            run(["git", "add"] + [str(p) for p in paths])
            run(["git", "commit", "-m", f"feat: daily digest {date} — {len(slugs)} posts"])
            run(["git", "push", "origin", "main"])
            logger.info("git_push_ok", slugs=slugs)
        except Exception as exc:
            logger.error("git_push_error", error=str(exc))
