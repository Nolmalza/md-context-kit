"""Discover Markdown context files and gather lightweight stats.

The scanner only reads small, structured Markdown (and the YAML registry). It
never reads ``docs/archive/`` content unless explicitly asked, and it honours
the project's ignore rules (``.mdctxignore`` / ``mdctx.json``) so dependency
folders and generated artifacts do not pollute the token report.

It can also group identical files, which is the cheapest way to cut context
cost: two copies of the same document cost twice as much and drift apart.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .project_config import ProjectConfig, load_config
from .token_estimator import estimate_tokens, thai_ratio

ARCHIVE_DIRNAME = "archive"

MARKDOWN_SUFFIXES = (".md", ".markdown")

# Belt-and-braces: these are also in DEFAULT_IGNORE_DIRS, but the scanner should
# stay cheap even when a project has no ignore file at all.
SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache"}


@dataclass
class FileStat:
    """Lightweight stats for a single context file."""

    path: Path  # absolute path on disk
    rel: str  # path relative to the project root, posix style
    lines: int
    chars: int
    tokens: int
    category: str  # "startup", "active", or "archive"
    sha256: str = ""
    thai_ratio: float = 0.0


@dataclass
class IgnoredSample:
    rel: str
    tokens: int
    rule: str


@dataclass
class ScanResult:
    files: list[FileStat] = field(default_factory=list)
    ignored_files: int = 0
    ignored_tokens: int = 0
    ignored_samples: list[IgnoredSample] = field(default_factory=list)
    config: ProjectConfig | None = None


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


def normalize_for_hash(text: str) -> str:
    """Content identity: line endings and trailing whitespace do not matter."""
    body = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in body.split("\n")).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode("utf-8")).hexdigest()


def categorize(rel: str, startup_files: tuple[str, ...]) -> str:
    if _is_archive(rel):
        return "archive"
    if rel in startup_files:
        return "startup"
    return "active"


def stat_file(path: Path, root: Path, startup_files: tuple[str, ...]) -> FileStat:
    rel = path.relative_to(root).as_posix()
    text = _read(path)
    return FileStat(
        path=path,
        rel=rel,
        lines=_count_lines(text),
        chars=len(text),
        tokens=estimate_tokens(text),
        category=categorize(rel, startup_files),
        sha256=content_hash(text) if text else "",
        thai_ratio=round(thai_ratio(text), 3),
    )


def _is_tracked(rel: str, path: Path, non_markdown_tracked: tuple[str, ...]) -> bool:
    if path.suffix.lower() in MARKDOWN_SUFFIXES:
        return True
    return rel in non_markdown_tracked


def _matching_rule(cfg: ProjectConfig, rel: str) -> str:
    for pat in cfg.all_ignore:
        if _rel_matches(rel, pat):
            return pat
    return "ignore"


def _rel_matches(rel: str, pat: str) -> bool:
    pat = pat.strip().lstrip("/")
    if not pat:
        return False
    if pat.endswith("/"):
        head = pat.rstrip("/")
        return rel == head or rel.startswith(head + "/")
    if "/" not in pat:
        return pat in rel.split("/")
    return rel.startswith(pat.rstrip("/*"))


def scan_detailed(
    root,
    include_archive: bool = False,
    cfg: ProjectConfig | None = None,
    report_ignored: bool = True,
) -> ScanResult:
    """Scan *root*; report kept files plus what the ignore rules removed."""
    root = Path(root)
    if cfg is None:
        cfg = load_config(root)

    non_markdown = (cfg.registry,) if cfg.registry else ()
    result = ScanResult(config=cfg)

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _is_skipped(rel):
            continue
        if not _is_tracked(rel, path, non_markdown):
            continue

        if cfg.is_ignored(rel):
            if report_ignored:
                tokens = estimate_tokens(_read(path))
                result.ignored_files += 1
                result.ignored_tokens += tokens
                result.ignored_samples.append(
                    IgnoredSample(rel=rel, tokens=tokens, rule=_matching_rule(cfg, rel))
                )
            continue

        if _is_archive(rel) and not include_archive:
            if report_ignored:
                tokens = estimate_tokens(_read(path))
                result.ignored_files += 1
                result.ignored_tokens += tokens
                result.ignored_samples.append(
                    IgnoredSample(rel=rel, tokens=tokens, rule="archive (not read by default)")
                )
            continue

        result.files.append(stat_file(path, root, cfg.startup_files))

    result.ignored_samples.sort(key=lambda s: -s.tokens)
    return result


def scan(root, include_archive: bool = False) -> list[FileStat]:
    """Convenience wrapper returning just the tracked files."""
    return scan_detailed(root, include_archive=include_archive).files


def find_duplicates(files: list[FileStat]) -> list[list[FileStat]]:
    """Group files whose normalized content is identical (2+ members)."""
    groups: dict[str, list[FileStat]] = {}
    for f in files:
        if not f.sha256:
            continue
        groups.setdefault(f.sha256, []).append(f)
    dupes = [g for g in groups.values() if len(g) > 1]
    dupes.sort(key=lambda g: -sum(x.tokens for x in g))
    return dupes
