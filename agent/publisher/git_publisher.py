"""
agent/publisher/git_publisher.py

Publishes Markdown posts to the Astro blog repository via GitPython.

Flow:
  1. Clone the remote repo if it is not already present locally.
  2. Generate .md files with MarkdownPublisher.
  3. Stage them with ``git add``.
  4. Commit with a dated message.
  5. Push to the remote (GitHub) using the stored token for auth.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import git
import structlog

from agent.config import settings
from agent.db.posts import PublishedPost
from agent.publisher.markdown import MarkdownPublisher

logger = structlog.get_logger(__name__)

# Path inside the repo where Astro stores blog posts
_POSTS_SUBDIR = Path("src") / "content" / "posts"


class GitPublisher:
    """
    Clones (if needed) and pushes Markdown posts to the GitHub blog repository.

    Authentication uses a token-embedded HTTPS remote URL so no SSH key is
    required in the runtime environment.
    """

    def __init__(self) -> None:
        self._repo_path = Path(settings.blog_repo_path)
        self._remote_url = self._authenticated_url(
            settings.blog_github_repo,
            settings.blog_github_token,
        )
        self._markdown_publisher = MarkdownPublisher()
        self._repo: git.Repo = self._ensure_repo()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def publish_posts(self, posts: list[PublishedPost]) -> list[str]:
        """
        Generate Markdown files, commit them, and push to GitHub.

        Args:
            posts: Posts to publish.

        Returns:
            List of slugs that were successfully committed and pushed.

        Raises:
            git.GitCommandError: If the commit or push fails.
        """
        if not posts:
            logger.info("publish_posts_skipped", reason="empty post list")
            return []

        published_slugs: list[str] = []
        output_dir = self._repo_path / _POSTS_SUBDIR

        # --- Generate .md files (sync I/O, offloaded to thread) ----------
        saved_paths: list[Path] = []
        try:
            saved_paths = await asyncio.to_thread(
                self._write_all_markdown, posts, output_dir
            )
        except Exception as exc:
            logger.error("markdown_generation_error", error=str(exc))
            raise

        # --- Git stage + commit + push (sync GitPython, offloaded) -------
        try:
            slugs = await asyncio.to_thread(
                self._git_commit_and_push, saved_paths, posts
            )
            published_slugs.extend(slugs)
        except Exception as exc:
            logger.error("git_publish_error", error=str(exc))
            raise

        logger.info(
            "publish_posts_done",
            count=len(published_slugs),
            slugs=published_slugs,
        )
        return published_slugs

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _authenticated_url(repo_slug: str, token: str) -> str:
        """Build a GitHub HTTPS URL with embedded token credentials."""
        return f"https://{token}@github.com/{repo_slug}.git"

    def _ensure_repo(self) -> git.Repo:
        """
        Return a :class:`git.Repo` object, cloning from GitHub if the local
        path does not yet contain a valid Git repository.
        """
        if (self._repo_path / ".git").exists():
            logger.info("git_repo_found", path=str(self._repo_path))
            try:
                repo = git.Repo(str(self._repo_path))
                # Update the remote URL so the token is always current
                origin = repo.remotes["origin"]
                origin.set_url(self._remote_url)
                return repo
            except git.InvalidGitRepositoryError as exc:
                logger.error(
                    "git_invalid_repo",
                    path=str(self._repo_path),
                    error=str(exc),
                )
                raise

        logger.info(
            "git_clone_start",
            remote=f"https://github.com/{settings.blog_github_repo}.git",
            dest=str(self._repo_path),
        )
        try:
            repo = git.Repo.clone_from(
                self._remote_url,
                str(self._repo_path),
            )
            logger.info("git_clone_done", path=str(self._repo_path))
            return repo
        except git.GitCommandError as exc:
            logger.error("git_clone_error", error=str(exc))
            raise

    def _write_all_markdown(
        self, posts: list[PublishedPost], output_dir: Path
    ) -> list[Path]:
        """Write all posts to disk and return the list of created paths."""
        paths: list[Path] = []
        for post in posts:
            try:
                path = self._markdown_publisher.save_to_disk(post, output_dir)
                paths.append(path)
                logger.debug("markdown_written", slug=post.slug, path=str(path))
            except OSError as exc:
                logger.error(
                    "markdown_write_error",
                    slug=post.slug,
                    error=str(exc),
                )
                # Continue with the other posts; failed ones won't be staged
        return paths

    def _git_commit_and_push(
        self, file_paths: list[Path], posts: list[PublishedPost]
    ) -> list[str]:
        """
        Stage *file_paths*, create a dated commit, push to origin, and return
        the list of slugs that were staged.
        """
        repo = self._repo

        # Stage only the new / modified Markdown files
        relative_paths = [
            str(p.relative_to(self._repo_path)) for p in file_paths
        ]
        repo.index.add(relative_paths)
        logger.info("git_staged", files=relative_paths)

        # Build commit message
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        commit_msg = f"chore: add {len(file_paths)} posts - {today}"

        try:
            repo.index.commit(commit_msg)
            logger.info("git_committed", message=commit_msg)
        except Exception as exc:
            logger.error("git_commit_error", error=str(exc))
            raise

        # Push to origin
        try:
            origin = repo.remotes["origin"]
            push_info = origin.push()
            for info in push_info:
                logger.info(
                    "git_push_info",
                    summary=info.summary.strip(),
                    flags=info.flags,
                )
        except Exception as exc:
            logger.error("git_push_error", error=str(exc))
            raise

        slugs = [post.slug for post in posts if (self._repo_path / _POSTS_SUBDIR / f"{post.slug}.md") in file_paths]
        # Fallback: return slugs for all posts whose files were written
        if not slugs:
            staged_stems = {p.stem for p in file_paths}
            slugs = [post.slug for post in posts if post.slug in staged_stems]

        return slugs
