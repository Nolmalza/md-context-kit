"""Generic, blank Markdown context templates.

Every template here uses neutral placeholders only ("Project Name", "Module A",
"Service X", "Feature Y"). They contain no real project, company, or business
details, so they are safe to adapt to any project and to publish.

These embedded strings are the source of truth used by ``mdctx init`` and
``mdctx refresh --apply``. The ``templates/generic/`` directory in the
repository mirrors them for browsing.
"""

from __future__ import annotations

# Maps a template name to the path (relative to the project root) where the file
# is created. Keys mirror the files in ``templates/generic/``.
TEMPLATE_TARGETS = {
    "AGENTS.md": "AGENTS.md",
    "00_INDEX.md": "docs/00_INDEX.md",
    "context_registry.yml": "docs/context_registry.yml",
    "01_PROJECT_BRIEF.md": "docs/01_PROJECT_BRIEF.md",
    "02_CURRENT_STATE.md": "docs/02_CURRENT_STATE.md",
    "CHANGELOG.md": "docs/CHANGELOG.md",
}


AGENTS_MD = """# AGENTS.md

Start here. This file tells an AI coding agent how to read this project's
context efficiently, without token bloat.

## How to read this project

1. Read the startup docs in order:
   - `AGENTS.md` (this file)
   - `docs/00_INDEX.md`
   - `docs/context_registry.yml`
   - `docs/01_PROJECT_BRIEF.md`
   - `docs/02_CURRENT_STATE.md`
2. Only open other docs when a task needs them.
3. Do not read `docs/archive/` unless explicitly asked.

## Working rules

- Keep `docs/02_CURRENT_STATE.md` short. It is a snapshot, not a log.
- Record decisions in `docs/01_PROJECT_BRIEF.md` or a dedicated decisions doc.
- Do not paste long logs, full diffs, full source code, or long JSON into
  Markdown. Link to the source instead.
- When context changes, run a context update (a "refresh"), not a manual edit
  spree.

## Terms used in this project

- **refresh** — re-check the context files and fill in anything missing.
- **snapshot** — a short, dated capture of the current state.
- **context update** / **docs update** — editing the context docs to match
  reality.
- **update summary** — a short note describing what changed.

## Placeholders

Replace every placeholder below with your own project's details:

- Project Name
- Module A, Module B
- Service X
- Feature Y
"""


INDEX_MD = """# 00 — Index

A short map of the context docs. Keep this list current and brief.

## Startup docs (read first)

- `AGENTS.md` — how to read this project.
- `docs/00_INDEX.md` — this map.
- `docs/context_registry.yml` — machine-readable registry of context files.
- `docs/01_PROJECT_BRIEF.md` — what the project is and the key rules.
- `docs/02_CURRENT_STATE.md` — where things stand right now (kept short).

## Active docs

- `docs/CHANGELOG.md` — dated update summaries.
- Add other docs here as you create them (e.g. `docs/03_ARCHITECTURE.md`).

## Archive

- `docs/archive/` — older snapshots and superseded notes. Not read by default.

## Placeholders

- Project Name
- Module A
- Service X
- Feature Y
"""


CONTEXT_REGISTRY_YML = """# context_registry.yml
# Machine-readable registry of context files for AI agents.
# Each entry describes one context file. See docs/registry-format.md for the
# meaning of every field. Keep this list short and current.

version: 1
project: "Project Name"

context:
  - id: agents
    title: Agent guide
    type: guide
    status: active
    file: AGENTS.md
    read_when: startup
    scope: global
    last_updated: YYYY-MM-DD

  - id: index
    title: Context index
    type: index
    status: active
    file: docs/00_INDEX.md
    read_when: startup
    scope: global
    last_updated: YYYY-MM-DD

  - id: registry
    title: Context registry
    type: registry
    status: active
    file: docs/context_registry.yml
    read_when: startup
    scope: global
    last_updated: YYYY-MM-DD

  - id: brief
    title: Project brief
    type: brief
    status: active
    file: docs/01_PROJECT_BRIEF.md
    read_when: startup
    scope: global
    last_updated: YYYY-MM-DD

  - id: current_state
    title: Current state
    type: state
    status: active
    file: docs/02_CURRENT_STATE.md
    read_when: startup
    scope: global
    last_updated: YYYY-MM-DD

  - id: changelog
    title: Context changelog
    type: changelog
    status: active
    file: docs/CHANGELOG.md
    read_when: on-demand
    scope: global
    last_updated: YYYY-MM-DD

# Soft limits (estimated tokens unless noted). Documentation for humans and
# agents; mdctx uses matching built-in defaults for its warnings.
limits:
  current_state_max_lines: 120
  current_state_max_tokens: 1500
  changelog_max_tokens: 3000
  active_file_warn_tokens: 2500
  startup_total_warn_tokens: 3500
"""


PROJECT_BRIEF_MD = """# 01 — Project Brief

A stable, slow-changing description of the project. Update it when the goal,
scope, or key rules change — not on every task.

## Overview

Project Name is a [one-sentence description of what it does and for whom].

## Goals

- Goal 1
- Goal 2

## Scope

- In scope: Feature Y, Module A.
- Out of scope: [list anything explicitly excluded].

## Important rules

- Rule 1 (e.g. "Service X is the only place that talks to the database").
- Rule 2

## Key components

- **Module A** — [responsibility].
- **Module B** — [responsibility].
- **Service X** — [responsibility].

## Decisions

Record significant decisions here, newest first.

- YYYY-MM-DD — Decision: [what was decided]. Why: [short reason].

## Next steps

- Next step 1
- Next step 2
"""


CURRENT_STATE_MD = """# 02 — Current State

A short snapshot of where things stand right now. Keep this under ~120 lines.
If it grows, move detail into the brief, the changelog, or the archive.

## Status

- One or two sentences on the overall state.

## Working on now

- Current focus 1
- Current focus 2

## Known issues

- Issue 1

## Next steps

- Next step 1
- Next step 2

## Last update

- YYYY-MM-DD — [update summary in one line].
"""


CHANGELOG_MD = """# Changelog (context)

Short, dated update summaries for this project's context. Newest first.
Keep entries to a few lines each. This is not a place for full diffs or logs.

## Unreleased

- YYYY-MM-DD — [update summary].
"""


# Maps template name -> content string.
TEMPLATES = {
    "AGENTS.md": AGENTS_MD,
    "00_INDEX.md": INDEX_MD,
    "context_registry.yml": CONTEXT_REGISTRY_YML,
    "01_PROJECT_BRIEF.md": PROJECT_BRIEF_MD,
    "02_CURRENT_STATE.md": CURRENT_STATE_MD,
    "CHANGELOG.md": CHANGELOG_MD,
}


# Template used by ``mdctx snapshot`` (dated short captures).
SNAPSHOT_TEMPLATE = """# Snapshot — {timestamp}

A short, point-in-time capture of the project context. Keep it brief.

## Status

- [One or two lines on the overall state.]

## Working on now

- [Current focus.]

## Next steps

- [Next step.]

## Update summary

- {timestamp} — [what changed since the last snapshot].
"""


def get_template(name: str) -> str:
    """Return the content for a named template."""
    return TEMPLATES[name]
