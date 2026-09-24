# AGENTS.md — how an AI agent should read this repository

MD Context Kit is the `mdctx` CLI: a zero-dependency Python tool that keeps an AI agent's
Markdown context small, measured and structured. The product is `src/md_context_kit/`;
`templates/`, `examples/` and `assets/` are payload shipped with it.

## Read first (startup set)

1. `docs/02_CURRENT_STATE.md` — where the work stands right now (a snapshot, never a journal).
2. `docs/context_registry.yml` — every context file, what it covers, when to read it.
3. `docs/00_INDEX.md` — map of the documentation.
4. `docs/01_PROJECT_BRIEF.md` — scope, principles, non-goals.

## Read on demand

- `docs/usage.md` — full CLI behaviour, per command.
- `docs/token-limits.md` — the budgets `mdctx` warns about and how to change them.
- `docs/registry-format.md` — the `context_registry.yml` schema.
- `docs/why-md-context-kit.md` — the rationale and the measured evidence behind it.
- `README.md` / `CHANGELOG.md` — public front page and release history.

## Rules for working in this repository

- Run `pytest -q` (23 tests) before proposing any change; the tests are the release gate.
- Never stage, commit or push without the owner's explicit instruction.
- Keep the core path dependency-free; `tiktoken` stays an optional extra.
- The tool is read-only **by contract**: it must never modify a project's code, stage,
  commit or push. Any change that relaxes this is a breaking change, not a feature.
- Keep `docs/02_CURRENT_STATE.md` a snapshot; move detail into `CHANGELOG.md` or `docs/`.
- Context cost is a feature: check `mdctx tokens -C .` before adding documentation.
