# 02 — Current State (md-context-kit)

Snapshot, not history. Detail: `CHANGELOG.md`; rationale: `docs/why-md-context-kit.md`.

## Stage

**0.2.2 — documentation hygiene** (PR #4, tag `v0.2.2`). This release removes every reference to
a private project from this public repository: the README figures now measure the demo fixture
shipped in `scripts/make-demo-fixture.py` and this repository itself, and `LICENSE`,
`pyproject.toml`, `README.md` and `SECURITY.md` name the maintainer (Nolmalza) instead of the
company that builds the tool.

**0.2.1 released** (PR #2, merge commit `beedcda`, tag `v0.2.1`): this repository's own context
set — the dogfooding work — plus a fix for ignore patterns on dot-directories. Dogfooding found
that `_match_pattern` stripped the leading dot, so `.pytest_cache/`, `.venv/` and the rest of the
default list were still counted as context and could not be excluded by a project either.

Earlier, **0.2.0** (PR #1, merge commit `340771c`, tag `v0.2.0`) shipped `.mdctxignore` +
`mdctx.json` project configuration, `--json` on every command, `check --strict` as a CI gate,
`mdctx tasks` and `mdctx dupes`, registry health checks, and a language-aware token fallback for
Thai-heavy projects. First release: `v0.1.0` (`888a9ce`).

## Test status

`pytest -q` → **24 passed**. No CI workflow is configured yet; the suite is run locally before
every release.

## Context budget (this repository, measured)

Startup set (read every session): `AGENTS.md`, `docs/00_INDEX.md`,
`docs/context_registry.yml`, `docs/01_PROJECT_BRIEF.md`, `docs/02_CURRENT_STATE.md`.
The repository has been dogfooding `mdctx` on itself since 0.2.0.

## Open items (not scheduled)

- No PyPI publication yet — install is from source (`pip install -e ".[tokens]"`).
- No GitHub Actions workflow to run `pytest` and `mdctx check --strict` on pull requests.
- `mdctx rotate` handles snapshots only; rotating a changelog is still a manual edit.
- Template payload Markdown (`templates/`, `examples/`) is excluded from context by
  `.mdctxignore`; a future version could ship a project-level preset for that.

## Next action

Nothing is in flight. The next candidate milestone is a GitHub Actions workflow running
`pytest` plus `mdctx check --strict` on every pull request.
