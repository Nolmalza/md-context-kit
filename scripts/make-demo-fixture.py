#!/usr/bin/env python3
"""Generate the throwaway demo project used by the README figures.

The figures in `assets/` quote real measurements, so the project they measure has to be
reproducible by anyone who clones this repository. This script writes that project into a
temporary directory (nothing is committed) and prints where it went, so the numbers can be
re-created with:

    python scripts/make-demo-fixture.py
    mdctx tokens -C <printed path> --json

Layout: a small app repository with six context documents and a dependency/generated tree
(vendor/, node_modules/, dist/) whose Markdown is what the default ignore rules remove.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

DOCS = {
    "AGENTS.md": """# AGENTS.md — demo app

A tiny example project used to illustrate mdctx's numbers. Six context documents and a
dependency tree that should never be read as context.

## Read first

1. `docs/02_CURRENT_STATE.md` — what is in flight.
2. `docs/context_registry.yml` — every context file and when to read it.
3. `docs/00_INDEX.md` — map of the documentation.
""",
    "docs/00_INDEX.md": """# docs/00_INDEX.md — map of the documentation

| document | read it when |
| --- | --- |
| `02_CURRENT_STATE.md` | always, first |
| `01_PROJECT_BRIEF.md` | you need scope or principles |
| `context_registry.yml` | you need to know what else exists |
""",
    "docs/01_PROJECT_BRIEF.md": """# 01 — Project brief (demo app)

Stable overview of the demo app: an HTTP service with a queue worker, shipped as a container.

## Scope

- In scope: request handling, background jobs, health endpoints.
- Out of scope: billing, administration UI, data science notebooks.

## Principles

- One process per concern; no scheduler inside the web process.
- Configuration from the environment only.
""",
    "docs/02_CURRENT_STATE.md": """# 02 — Current state (demo app)

Snapshot, not history.

## Stage

- In flight: nothing; the demo app is a fixture for documentation screenshots.
- Last release: 1.4.2, deployed to staging only.

## Next action

Nothing. This project exists so the numbers in the figures can be reproduced.
""",
    "docs/context_registry.yml": """context:
  - id: agents
    title: Agent entry rules
    type: rule
    status: active
    file: AGENTS.md
    read_when: startup
  - id: current_state
    title: Current state
    type: state
    status: active
    file: docs/02_CURRENT_STATE.md
    read_when: startup
""",
    "docs/CHANGELOG.md": """# Changelog

## [1.4.2] - 2026-08-30

### Fixed

- Worker restart loop when the queue connection dropped mid-job.
""",
}

FILLER = {
    "vendor/acme/http": ("README.md", 14),
    "vendor/acme/queue": ("README.md", 12),
    "vendor/acme/logging": ("README.md", 10),
    "node_modules/frontend-kit": ("README.md", 10),
    "node_modules/test-runner": ("README.md", 8),
    "dist/assets": ("chunk.md", 16),
}

BODY = """# {name}

Generated fixture documentation for `{path}`. Nothing here is project context: it ships with
a dependency or a build, and mdctx's default ignore rules keep it out of every token total.

## Usage

```bash
composer require {name}
```

## Configuration

| option | default | meaning |
| --- | --- | --- |
| `timeout` | 30 | seconds before a request is abandoned |
| `retries` | 3 | attempts before a job is marked failed |

## Notes

{notes}
"""


def build(root: Path) -> int:
    files = 0
    for rel, text in DOCS.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        files += 1

    for folder, (name, count) in FILLER.items():
        for index in range(count):
            target = root / folder / f"module-{index + 1}"
            target.mkdir(parents=True, exist_ok=True)
            notes = "\n".join(f"- generated line {n} for module {index + 1}" for n in range(1, 26))
            (target / name).write_text(
                BODY.format(name=f"{folder}/{index + 1}", path=folder, notes=notes),
                encoding="utf-8",
            )
            files += 1
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--into", help="write into this directory instead of a temp dir")
    args = parser.parse_args()

    root = Path(args.into).resolve() if args.into else Path(tempfile.mkdtemp(prefix="mdctx-demo-"))
    files = build(root)
    print(root)
    print(f"{files} files written")


if __name__ == "__main__":
    main()
