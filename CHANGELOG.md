# Changelog

All notable changes to MD Context Kit are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-09-24

### Added

- `.mdctxignore` and `mdctx.json` project configuration. Dependency, build and
  generated folders (`vendor`, `node_modules`, `dist`, `build`, …) are ignored by
  default, and a project can add its own patterns. Scanning a Laravel repo used
  to count `vendor/**` as context (90% of the reported tokens on a real project);
  it no longer does.
- `mdctx tasks` — prices each reading list in `context_registry.yml`. Both the
  per-entry `file:` schema and the simpler `task: → paths` map are understood.
- `mdctx dupes` — groups context files whose content is identical, and reports
  the redundant token cost.
- `--json` on every command, for agents and CI.
- `check --strict` — exits non-zero when there are warnings, so it can gate a
  workflow.
- Registry health checks: references to files that do not exist, docs marked
  `read_when: never` that are still startup docs, and "loose" docs that no
  section points at.
- Language-aware token fallback: Thai text costs ~1 token per character, not
  4 characters per token. A Thai-heavy document was under-counted by ~74% by the
  old `chars / 4` heuristic.
- Report of how many files and tokens the ignore rules removed, so the numbers
  stay explainable.

### Changed

- `mdctx check` prints the startup set with the token cost of each file.
- `mdctx scan` lists files largest-first and caps the list at 40 rows
  (`--all` for everything) — a large repo produced 1,900 rows before.
- Limits are configurable per project via the `limits` block in `mdctx.json`.
- `mdctx init` / `refresh --apply` only create templates that the project's
  `required_files` actually lists.

### Fixed

- `file:` entries in the documented registry schema are now parsed (previously
  only `- file:` bullets were).

### Documentation

- Rewrote `README.md` as a project front page: banner, a "how it works" diagram, real
  `mdctx check` output from two demo projects, and a measured context-cost chart. The
  images are generated from HTML in this repository (`assets/*.png`).
- The README now states plainly that the package is **not on PyPI yet** and is installed
  from source; the earlier "once published" wording was speculative.
- `README.md` keeps itself inside the tool's own budget: ~2,190 tokens, below the
  2,500-token warning threshold that the previous 3,234-token README triggered.

## [Unreleased]

### Changed

- Prepared the project for its first public GitHub release.
- `context_registry.yml` now uses a richer per-entry schema
  (`id`, `title`, `type`, `status`, `file`, `read_when`, `scope`,
  `last_updated`). See `docs/registry-format.md`.
- Expanded documentation: added `docs/why-md-context-kit.md`, `CONTRIBUTING.md`,
  and `SECURITY.md`; rewrote the README with full guidance and a comparison
  table.

## [0.1.0] - 2026-06-25

### Added

- `mdctx` command line with `init`, `check`, `scan`, `tokens`, `refresh`
  (`--apply`, `--tokens`), `snapshot`, and `rotate`.
- Generic, blank Markdown context templates (`AGENTS.md`, `docs/00_INDEX.md`,
  `docs/context_registry.yml`, `docs/01_PROJECT_BRIEF.md`,
  `docs/02_CURRENT_STATE.md`, `docs/CHANGELOG.md`).
- Token estimation via `tiktoken` when installed, with a `chars / 4` fallback.
- Size checks and warnings for current-state length, changelog size,
  per-file size, and startup-doc token budget.
- Read-only Git helper that only ever prints a suggested command.

[Unreleased]: https://github.com/Nolmalza/md-context-kit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Nolmalza/md-context-kit/releases/tag/v0.2.0
[0.1.0]: https://github.com/Nolmalza/md-context-kit/releases/tag/v0.1.0
