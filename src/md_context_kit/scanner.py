"""Discover Markdown context files and gather lightweight stats.

The scanner only reads small, structured Markdown (and the YAML registry). It
never reads ``docs/archive/`` content unless explicitly asked, so scanning a
project stays fast and cheap even when the archive is large.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .token_estimator import estimate_tokens

ARCHIVE_DIRNAME = "archive"

MARKDOWN_SUFFIXES = (".md", ".markdown")

# Startup docs are what an AI agent should read first, every session.
STARTUP_DOCS = (
    "AGENTS.md",
    "docs/00_INDEX.md",
    "docs/context_registry.yml",
    "docs/01_PROJECT_BRIEF.md",
    "docs/02_CURRENT_STATE.md",
)

# Files that are part of the context system but are not Markdown.
NON_MARKDOWN_TRACKED = ("docs/context_registry.yml",)

# Directories that never hold context worth scanning.
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache"}


@dataclass
class FileStat:
    """Lightweight stats for a single context file."""

    path: Path  # absolute path on disk
    rel: str  # path relative to the project root, posix style
    lines: int
    chars: int
    tokens: int
    category: str  # "startup", "active", or "archive"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _is_archive(rel: str) -> bool:
    return ARCHIVE_DIRNAME in rel.split("/")


def _is_skipped(rel: str) -> bool:
    return any(part in SKIP_DIRS for part in rel.split("/"))


def _count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def categorize(rel: str) -> str:
    if _is_archive(rel):
        return "archive"
    if rel in STARTUP_DOCS:
        return "startup"
    return "active"


def stat_file(path: Path, root: Path) -> FileStat:
    rel = path.relative_to(root).as_posix()
    text = _read(path)
    return FileStat(
        path=path,
        rel=rel,
        lines=_count_lines(text),
        chars=len(text),
        tokens=estimate_tokens(text),
        category=categorize(rel),
    )


def _is_tracked(rel: str, path: Path) -> bool:
    if path.suffix.lower() in MARKDOWN_SUFFIXES:
        return True
    return rel in NON_MARKDOWN_TRACKED


def scan(root, include_archive: bool = False) -> list[FileStat]:
    """Return stats for every tracked context file under *root*.

    ``docs/archive/`` content is skipped unless *include_archive* is True. This
    keeps the common path cheap and honours the rule that archive content is not
    read by default.
    """
    root = Path(root)
    results: list[FileStat] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _is_skipped(rel):
            continue
        if not _is_tracked(rel, path):
            continue
        if _is_archive(rel) and not include_archive:
            continue
        results.append(stat_file(path, root))
    return results
