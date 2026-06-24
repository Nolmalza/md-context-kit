# Changelog

All notable changes to MD Context Kit are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

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

[Unreleased]: https://github.com/botbas/md-context-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/botbas/md-context-kit/releases/tag/v0.1.0
