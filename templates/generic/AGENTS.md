# AGENTS.md

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
