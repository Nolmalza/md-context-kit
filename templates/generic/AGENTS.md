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

Replace every `ALL CAPS` placeholder in this file and in the other template
files with your own project's details before use:

- **`PROJECT NAME`** — your project's real name (used in headings and the
  registry `project:` field).
- **`MODULE A`, `MODULE B`** — your main source modules or packages.
- **`SERVICE X`** — any external service or dependency your project relies on.
- **`FEATURE Y`** — any major feature or subsystem worth calling out.

Delete this section once placeholders have been replaced.
