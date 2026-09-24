"""Optional per-project configuration for ``mdctx``.

Two dependency-free files are read from the project root (both optional):

- ``.mdctxignore`` — plain text, one pattern per line, ``#`` starts a comment.
  Mirrors the ``.gitignore`` habit so nobody has to learn a new format.
- ``mdctx.json`` — small JSON file for structured overrides::

      {
        "ignore": ["artifacts/**"],
        "startup_files": ["AGENTS.md", "docs/02_CURRENT_STATE.md"],
        "required_files": ["AGENTS.md", "docs/02_CURRENT_STATE.md"],
        "limits": {"current_state_max_lines": 120}
      }

Why: a context scanner that counts dependency folders and generated
artifacts as "context" produces numbers nobody can act on. Defaults ignore
the usual dependency/build directories; projects add their own.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from pathlib import Path

IGNORE_FILENAME = ".mdctxignore"
CONFIG_FILENAME = "mdctx.json"

# Dependency, build and cache directories never hold agent context.
DEFAULT_IGNORE_DIRS = (
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "vendor",
    "bower_components",
    "site-packages",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".cache",
    "dist",
    "build",
    "out",
    "target",
    "coverage",
    ".idea",
    ".vscode",
)

DEFAULT_LIMITS = {
    "current_state_max_lines": 120,
    "current_state_max_tokens": 1500,
    "changelog_max_tokens": 3000,
    "active_file_warn_tokens": 2500,
    "startup_total_warn_tokens": 3500,
    "snapshots_to_keep": 5,
    "max_listed_files": 40,
}

CURRENT_STATE = "docs/02_CURRENT_STATE.md"
CHANGELOG = "docs/CHANGELOG.md"

DEFAULT_REQUIRED_FILES = (
    "AGENTS.md",
    "docs/00_INDEX.md",
    "docs/context_registry.yml",
    "docs/01_PROJECT_BRIEF.md",
    "docs/02_CURRENT_STATE.md",
    "docs/CHANGELOG.md",
)

DEFAULT_STARTUP_FILES = (
    "AGENTS.md",
    "docs/00_INDEX.md",
    "docs/context_registry.yml",
    "docs/01_PROJECT_BRIEF.md",
    "docs/02_CURRENT_STATE.md",
)

REGISTRY_CANDIDATES = ("docs/context_registry.yml", "docs/context_registry.yaml")


@dataclass
class ProjectConfig:
    """Resolved configuration for one project root."""

    root: Path
    ignore: list[str] = field(default_factory=list)
    custom_ignore: list[str] = field(default_factory=list)
    startup_files: tuple[str, ...] = DEFAULT_STARTUP_FILES
    required_files: tuple[str, ...] = DEFAULT_REQUIRED_FILES
    limits: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_LIMITS))
    current_state: str = CURRENT_STATE
    changelog: str = CHANGELOG
    registry: str | None = None
    loaded_from: list[str] = field(default_factory=list)

    # -- ignore matching ---------------------------------------------------
    @property
    def all_ignore(self) -> list[str]:
        return list(DEFAULT_IGNORE_DIRS) + list(self.custom_ignore)

    def is_ignored(self, rel: str) -> bool:
        """True when a root-relative POSIX path matches an ignore rule."""
        parts = rel.split("/")
        for pat in self.all_ignore:
            if _match_pattern(rel, parts, pat):
                return True
        return False


def _match_pattern(rel: str, parts: list[str], pat: str) -> bool:
    pat = pat.strip()
    if not pat or pat.startswith("#"):
        return False
    if pat.startswith("/"):
        pat = pat.lstrip("/")          # "/artifacts/" -> root-anchored
    elif pat.startswith("./"):
        pat = pat[2:]                  # "./artifacts/" == "artifacts/"

    # "artifacts/" or "artifacts" -> that directory and everything under it
    if pat.endswith("/"):
        head = pat.rstrip("/")
        return rel == head or rel.startswith(head + "/")
    if "/" not in pat and not any(ch in pat for ch in "*?["):
        # bare name matches any single path segment (like .gitignore) — this is
        # how the default dot-directories (.venv, .pytest_cache, …) are matched,
        # so a leading dot must survive normalisation
        return pat in parts
    if fnmatch.fnmatch(rel, pat):
        return True
    # "artifacts/**" should also drop the directory itself
    if pat.endswith("/**") and rel.startswith(pat[:-3].rstrip("/") + "/"):
        return True
    return False


def _read_ignore_file(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def detect_registry(root: Path) -> str | None:
    for rel in REGISTRY_CANDIDATES:
        if (root / rel).is_file():
            return rel
    return None


def load_config(root) -> ProjectConfig:
    """Load configuration for *root*, filling in every default."""
    root = Path(root)
    cfg = ProjectConfig(root=root)

    ignore_file = root / IGNORE_FILENAME
    customs = _read_ignore_file(ignore_file)
    if customs:
        cfg.loaded_from.append(IGNORE_FILENAME)

    data = _read_json(root / CONFIG_FILENAME)
    if data:
        cfg.loaded_from.append(CONFIG_FILENAME)
        extra = data.get("ignore") or []
        if isinstance(extra, list):
            customs.extend(str(x) for x in extra)
        startup = data.get("startup_files")
        if isinstance(startup, list) and startup:
            cfg.startup_files = tuple(str(x) for x in startup)
        req = data.get("required_files")
        if isinstance(req, list) and req:
            cfg.required_files = tuple(str(x) for x in req)
        limits = data.get("limits")
        if isinstance(limits, dict):
            for key, value in limits.items():
                if key in DEFAULT_LIMITS:
                    try:
                        cfg.limits[key] = int(value)
                    except (TypeError, ValueError):
                        pass
        if isinstance(data.get("current_state"), str):
            cfg.current_state = data["current_state"]
        if isinstance(data.get("changelog"), str):
            cfg.changelog = data["changelog"]
        if isinstance(data.get("registry"), str):
            cfg.registry = data["registry"]

    cfg.custom_ignore = customs
    if cfg.registry is None:
        cfg.registry = detect_registry(root)
    return cfg
