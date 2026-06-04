"""
agent/publisher/markdown.py

Generates Astro-compatible Markdown files from PublishedPost objects.
"""

from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path

import structlog

from agent.db.posts import PublishedPost

logger = structlog.get_logger(__name__)


class MarkdownPublisher:
    """Converts PublishedPost objects into Astro-compatible Markdown files."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_markdown(self, post: PublishedPost) -> str:
        """
        Generate the full Markdown content (YAML frontmatter + body) for an
        Astro blog post.

        Args:
            post: The post to serialise.

        Returns:
            A string with valid YAML frontmatter followed by the post content.
        """
        frontmatter = self._build_frontmatter(post)
        body = post.content.strip()
        return f"{frontmatter}\n\n{body}\n"

    def save_to_disk(self, post: PublishedPost, output_dir: Path) -> Path:
        """
        Write the Markdown file for *post* into *output_dir*.

        The file is named ``{slug}.md``.  The output directory is created
        automatically if it does not exist.

        Args:
            post:       The post to write.
            output_dir: Directory where the file will be saved.

        Returns:
            The :class:`~pathlib.Path` of the written file.

        Raises:
            OSError: If the directory cannot be created or the file cannot be
                written.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"{post.slug}.md"

        markdown_content = self.generate_markdown(post)

        try:
            file_path.write_text(markdown_content, encoding="utf-8")
            logger.info(
                "markdown_saved",
                slug=post.slug,
                path=str(file_path),
            )
        except OSError as exc:
            logger.error(
                "markdown_save_error",
                slug=post.slug,
                path=str(file_path),
                error=str(exc),
            )
            raise

        return file_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_frontmatter(self, post: PublishedPost) -> str:
        """Return the YAML frontmatter block for *post*."""

        # Normalise published_at to a plain date string
        if isinstance(post.published_at, datetime):
            date_str = post.published_at.strftime("%Y-%m-%d")
        else:
            date_str = str(post.published_at)

        # Escape double-quotes inside the title / description
        safe_title = post.title.replace('"', '\\"')
        safe_description = post.description.replace('"', '\\"')

        # Build tags inline list:  ["ai", "python"]
        tags_list = ", ".join(f'"{tag}"' for tag in post.tags)
        tags_line = f"[{tags_list}]"

        # Build source_urls as a YAML sequence
        source_urls_block = "\n".join(
            f'  - "{url}"' for url in post.source_urls
        )

        cover_line = f'\ncover: "{post.cover}"' if post.cover else ""

        frontmatter = textwrap.dedent(f"""\
            ---
            title: "{safe_title}"
            date: "{date_str}"
            description: "{safe_description}"
            tags: {tags_line}
            source_urls:
            {source_urls_block}{cover_line}
            ---""")

        return frontmatter
