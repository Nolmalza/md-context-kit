"""Read a project's context registry and price it in tokens.

Two shapes are understood, because real projects use both:

1. **mdctx spec** — a ``context:`` list where each entry has ``file`` plus
   metadata such as ``read_when`` / ``status``.
2. **task map** — top-level sections mapping a task type to the files an agent
   should read for it, e.g.::

       meta_api:
         - docs/07_META_API_INTEGRATION.md
         - docs/05_DATABASE_SCHEMA.md

The parser is deliberately line-based and dependency-free: the registry is a
small hand-written file, not a data store. It reports what each section would
cost to read, which references point at files that do not exist, and (with
``read_when: never`` / ``status: archived``) which files should not be
auto-loaded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SECTION_RE = re.compile(r"^([A-Za-z0-9_.\-]+):\s*$")
FILE_KEY_RE = re.compile(r"^\s*(?:-\s*)?file:\s*[\"']?([^\"'\s#]+)")
PLAIN_REF_RE = re.compile(
    r"^\s*-\s*[\"']?([A-Za-z0-9_./\-]+\.(?:md|markdown|yml|yaml|txt))[\"']?\s*(?:#.*)?$"
)
META_RE = re.compile(r"^\s*(id|title|type|status|read_when|scope|last_updated):\s*(.*?)\s*$")


@dataclass
class Ref:
    path: str
    section: str
    exists: bool = False
    tokens: int = 0
    read_when: str = ""
    status: str = ""

    @property
    def auto_loaded(self) -> bool:
        if self.read_when == "never":
            return False
        if self.status == "archived":
            return False
        return True


@dataclass
class Section:
    name: str
    refs: list[Ref] = field(default_factory=list)

    @property
    def tokens(self) -> int:
        return sum(r.tokens for r in self.refs if r.exists)

    @property
    def missing(self) -> list[Ref]:
        return [r for r in self.refs if not r.exists]


@dataclass
class Registry:
    path: str | None = None
    exists: bool = False
    version: str = ""
    project: str = ""
    sections: list[Section] = field(default_factory=list)
    startup: list[str] = field(default_factory=list)
    never_read: list[str] = field(default_factory=list)

    @property
    def refs(self) -> list[Ref]:
        return [r for s in self.sections for r in s.refs]

    def section(self, name: str) -> Section | None:
        for s in self.sections:
            if s.name == name:
                return s
        return None


def _token_of(root: Path, rel: str, estimator) -> int:
    p = root / rel
    if not p.is_file():
        return 0
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    return estimator(text)


def parse_registry(root, rel_path: str, estimator) -> Registry:
    """Parse the registry at *rel_path* (root-relative POSIX path)."""
    root = Path(root)
    reg = Registry(path=rel_path)
    full = root / rel_path
    if not full.is_file():
        return reg
    reg.exists = True

    current: Section | None = None
    last_ref: Ref | None = None

    for raw in full.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        m = SECTION_RE.match(raw)
        if m and not raw.startswith((" ", "\t")):
            name = m.group(1)
            if name == "version":
                continue
            current = Section(name=name)
            reg.sections.append(current)
            last_ref = None
            continue

        if current is not None and raw.strip().startswith("-") and "file:" not in raw:
            # a metadata bullet such as "- id: current_state" starts a new entry
            pass

        m = FILE_KEY_RE.match(raw)
        if m and current is not None:
            ref = _make_ref(root, current.name, m.group(1), estimator)
            current.refs.append(ref)
            last_ref = ref
            continue

        m = PLAIN_REF_RE.match(raw)
        if m and current is not None:
            ref = _make_ref(root, current.name, m.group(1), estimator)
            current.refs.append(ref)
            last_ref = ref
            continue

        m = META_RE.match(raw)
        if m:
            key, value = m.group(1), m.group(2).strip().strip("\"'")
            if key == "version":
                reg.version = value
            elif key == "title":
                # a top-level title belongs to the registry/context
                if current is not None and current.name in ("context", "version"):
                    reg.project = value
            elif key == "read_when" and last_ref is not None:
                last_ref.read_when = value
                if value == "never" and last_ref.path not in reg.never_read:
                    reg.never_read.append(last_ref.path)
            elif key == "status" and last_ref is not None:
                last_ref.status = value
            elif key == "id" and last_ref is None and current is not None:
                pass
            continue

        # `project: "Name"` at top level
        if ":" in raw and not raw.startswith((" ", "\t")):
            key, _, value = raw.partition(":")
            if key.strip() == "project":
                reg.project = value.strip().strip("\"'")

    # startup set = refs explicitly marked read_when: startup (mdctx spec shape)
    for ref in reg.refs:
        if ref.read_when == "startup" and ref.path not in reg.startup:
            reg.startup.append(ref.path)
    return reg


def _make_ref(root: Path, section: str, path: str, estimator) -> Ref:
    return Ref(
        path=path,
        section=section,
        exists=(root / path).is_file(),
        tokens=_token_of(root, path, estimator),
    )


def referenced_paths(reg: Registry) -> set[str]:
    return {r.path for r in reg.refs}
