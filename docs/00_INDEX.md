# docs/00_INDEX.md — map of the documentation

Read `docs/02_CURRENT_STATE.md` first, then only the section your task matches — one to
three documents, never the whole folder. Costs are estimates; refresh them with
`mdctx scan -C . --all --json`.

## Startup — read every session

- `AGENTS.md` — how an agent should read this repository, and the working rules.
- `docs/02_CURRENT_STATE.md` — short snapshot of where the work stands.
- `docs/context_registry.yml` — machine-readable registry of every context file.
- `docs/01_PROJECT_BRIEF.md` — scope, principles, non-goals.

## Product behaviour

- `README.md` — public front page: problem, quick start, CLI table, budgets, safety.
- `docs/usage.md` — every command, flag and output in detail.
- `docs/token-limits.md` — default budgets, how they warn, how to override them.
- `docs/registry-format.md` — the registry schema and its health checks.
- `docs/why-md-context-kit.md` — rationale plus the measurements behind the design.
- `docs/public-template-rules.md` — what may ship in the public templates.

## Project upkeep

- `CHANGELOG.md` — what changed in each version (Keep a Changelog format).
- `CONTRIBUTING.md` / `SECURITY.md` — how to contribute, how to report a vulnerability.
- `templates/generic/` — blank context files `mdctx init` copies into a project.
- `examples/generic/` — an example of the filled-in shape.
