"""Read-only Git helpers.

This module never mutates a repository. It does not run ``git commit``, it does
not push, and it does not stage files. It can detect whether a directory is a
Git repository and build a *suggested* command string for the user to run
themselves.
"""

from __future__ import annotations

from pathlib import Path


def is_git_repo(root) -> bool:
    """Return True if *root* looks like the top of a Git working tree."""
    return (Path(root) / ".git").exists()


def suggested_command(message: str = "docs: context update") -> str:
    """Return a suggested Git command string.

    The command is only ever *printed* for the user to review and run. MD
    Context Kit never executes it.
    """
    safe = message.replace('"', "'")
    return f'git add -A && git commit -m "{safe}"'
