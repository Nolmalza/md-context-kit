# 02 — Current State (md-context-kit)

Snapshot, not history. Detail: `CHANGELOG.md`; rationale: `docs/why-md-context-kit.md`.

## Stage

**0.2.0 released.** Merged to `main` (PR #1, merge commit `340771c`), tagged `v0.2.0`, and
published as a GitHub release with notes from `CHANGELOG.md`. Previous release: `v0.1.0`
(`888a9ce`).

Shipped in 0.2.0: `.mdctxignore` + `mdctx.json` project configuration, `--json` on every
command, `check --strict` as a CI gate, `mdctx tasks` and `mdctx dupes`, registry health
checks (dangling references, `read_when: never` in the startup set, loose docs), and a
language-aware token fallback for Thai-heavy projects.

**In review, unreleased** (branch `chore/self-context`): this repository's own context set —
the dogfooding work below — plus a fix for ignore patterns on dot-directories. Dogfooding
found that `_match_pattern` stripped the leading dot, so `.pytest_cache/`, `.venv/` and the
rest of the default list were still counted as context and could not be excluded by a
project either. That fix belongs in a **0.2.1** patch release.

## Test status

`pytest -q` → **23 passed** (21 at the `v0.2.0` tag; two regression tests were added for the
ignore bug). No CI workflow is configured yet; the suite is run locally before every release.

## Context budget (this repository, measured)

Startup set (read every session): `AGENTS.md`, `docs/00_INDEX.md`,
`docs/context_registry.yml`, `docs/01_PROJECT_BRIEF.md`, `docs/02_CURRENT_STATE.md`.
The repository is dogfooding `mdctx` on itself since 0.2.0.

## Open items (not scheduled)

- **0.2.1 patch release pending** for the ignore-pattern fix currently on `chore/self-context`.
- No PyPI publication yet — install is from source (`pip install -e ".[tokens]"`).
- No GitHub Actions workflow to run `pytest` and `mdctx check --strict` on pull requests.
- `mdctx rotate` handles snapshots only; rotating a changelog is still a manual edit.
- Template payload Markdown (`templates/`, `examples/`) is excluded from context by
  `.mdctxignore`; a future version could ship a project-level preset for that.

## Next action

Merge `chore/self-context`, then cut **0.2.1** (tag + release notes from the `[Unreleased]`
section of `CHANGELOG.md`) so the ignore-pattern fix is published. The first candidate for a
real milestone after that is a GitHub Actions workflow running `pytest` plus
`mdctx check --strict` on every pull request.
