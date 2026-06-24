# MD Context Kit

**A lightweight Markdown context system for AI-assisted projects.**

MD Context Kit (`mdctx`) helps developers keep their Markdown context **fast,
small, structured, and easy for AI coding agents to read — without token
bloat.**

---

## What it does

`mdctx` gives a project a small, deliberate set of Markdown context files,
checks that they stay within sensible size limits, and estimates how many tokens
an AI agent will spend reading them. It defines which files an agent should read
first ("startup docs"), keeps a machine-readable registry of every context file,
and provides a simple **refresh / snapshot / archive** workflow so old notes do
not pile up in front of the agent.

It is intentionally generic: the templates are blank and use neutral
placeholders, so you can adapt them to any project.

## Why it exists

AI coding agents re-read your project's docs on every session — and often on
every task. If those docs are large, unstructured, or full of logs and diffs,
the agent burns a big share of its context window on documentation before it
does any useful work, and it can be misled by outdated notes. MD Context Kit
keeps the context small, current, and structured so the agent loads the right
information cheaply.

## The problem with traditional Markdown project notes

In a long-running, AI-assisted project, ordinary Markdown notes tend to decay in
predictable ways:

- **They grow without bound.** A "current state" note becomes a journal; a
  design doc accumulates every decision ever discussed.
- **Old and current information get mixed together,** so neither a person nor an
  agent can tell which parts still apply.
- **History gets duplicated into Markdown** — full Git logs, diffs, terminal
  output, whole source files, long JSON — even though Git already stores all of
  it.
- **Token cost is invisible.** Nothing tells you that your docs now cost
  thousands of tokens to read.

The result is context that is expensive to load and easy to get wrong.

## How MD Context Kit solves it

- A small set of **startup docs** the agent reads first, instead of everything.
- A **registry** (`context_registry.yml`) describing each file — its type,
  status, when to read it, and what it covers.
- **Token estimation** so the cost of your context is visible, with warnings
  when files get too big.
- A clear separation of **current state**, **snapshots**, **decisions**, and
  **archive**, so old material is kept for history without being reloaded every
  session.
- A **refresh / snapshot / archive** workflow that replaces the ever-growing
  journal — and never touches your application code or Git history.

The division of labour is simple: **Git stores the exact history of file
changes; Markdown stores the meaning** — current state, rules, decisions, and
next steps. See [docs/why-md-context-kit.md](docs/why-md-context-kit.md) for the
full rationale.

## Benefits compared with normal `.md` documentation

- Smaller, focused files instead of one large catch-all note.
- The agent reads the right context first, not the whole folder.
- Current information is clearly separated from old material.
- Token usage is measured and capped with warnings, not invisible.
- A repeatable workflow keeps context fresh over months, not just on day one.
- Nothing is automated against your repository — you stay in control of Git.

## Old Markdown Workflow vs MD Context Kit

| Old Markdown workflow                       | MD Context Kit                                              |
|---------------------------------------------|-------------------------------------------------------------|
| Long, growing Markdown files                | Short, focused context files                                |
| The AI reads all docs every time            | The AI reads startup docs first, others on demand           |
| Old and current notes mixed in one place    | Separated current state, snapshots, decisions, and archive  |
| The same rules repeated across files        | Rules referenced by stable context IDs                      |
| Token usage is invisible                    | A token estimate report for every command                   |
| Bloated changelog / pasted history         | Compact context updates; Git keeps the real history         |
| Hard to continue after a break              | A clear current state and explicit next steps               |

## Features

- `mdctx` command line with `init`, `check`, `scan`, `tokens`, `refresh`
  (`--apply`, `--tokens`), `snapshot`, and `rotate`.
- Generic, blank Markdown templates you adapt to your project.
- Required-file checks with clear warnings.
- Token estimation via `tiktoken` when installed, with a `chars / 4` fallback.
- Size limits for the current-state doc, changelog, individual files, and the
  startup set.
- A machine-readable context registry.
- A read-only Git helper that only ever **prints** a suggested command.
- No dependencies required for the core tool.

## Installation (local development)

You need Python 3.9 or newer.

```bash
git clone https://github.com/Nolmalza/md-context-kit
cd md-context-kit

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install in editable mode, with accurate token counting
pip install -e ".[tokens]"
```

Once published to PyPI you will also be able to:

```bash
pip install md-context-kit
pip install "md-context-kit[tokens]"   # accurate token counts
```

## CLI command examples

```bash
mdctx init                          # create missing context files from templates
mdctx check                         # check required files exist and are healthy
mdctx scan                          # list context files with line and token counts
mdctx tokens                        # estimated tokens: startup / active / all docs
mdctx refresh                       # dry run: report what a refresh would create
mdctx refresh --apply               # create missing files from templates
mdctx refresh --apply --tokens      # apply, and also print the token report
mdctx snapshot                      # create a short, dated snapshot
mdctx rotate                        # move old snapshots into the archive

# Operate on another directory
mdctx check -C ./path/to/project
```

You can also run it as a module: `python -m md_context_kit.cli check`.

## Recommended project structure

```
your-project/
├── AGENTS.md                     How an AI agent should read this project
└── docs/
    ├── 00_INDEX.md               Map of the context docs
    ├── context_registry.yml      Machine-readable registry of context files
    ├── 01_PROJECT_BRIEF.md       Overview, rules, decisions, next steps
    ├── 02_CURRENT_STATE.md       Short snapshot of where things stand
    ├── CHANGELOG.md              Dated update summaries
    ├── snapshots/                Short, dated snapshots (from `snapshot`)
    └── archive/                  Older material; not read by default
```

## Startup docs

The **startup docs** are the files an AI agent should read first, every session.
They are the smallest set needed to understand the project and continue work:

- `AGENTS.md` — how to read this project.
- `docs/00_INDEX.md` — a map of the context docs.
- `docs/context_registry.yml` — the machine-readable registry.
- `docs/01_PROJECT_BRIEF.md` — the stable project overview and rules.
- `docs/02_CURRENT_STATE.md` — a short snapshot of where things stand.

Keeping this set small and within the token budget (see below) is the single
most effective way to control context cost.

## The `context_registry.yml` file

The registry is a small YAML file describing every context file. Each entry has
a stable `id`, a `title`, a `type`, a `status`, the `file` path, a `read_when`
hint (`startup`, `on-demand`, or `never`), a `scope`, and a `last_updated` date:

```yaml
context:
  - id: current_state
    title: Current state
    type: state
    status: active
    file: docs/02_CURRENT_STATE.md
    read_when: startup
    scope: global
    last_updated: 2026-06-25
```

The stable `id` lets you refer to a piece of context from elsewhere instead of
repeating a rule. Every field is documented in
[docs/registry-format.md](docs/registry-format.md).

## Refresh / snapshot / archive workflow

- **Refresh** — re-check the context set and fill in anything missing
  (`mdctx refresh`, or `mdctx refresh --apply` to create files). Use this to
  bring a project back to the expected structure.
- **Snapshot** — capture a short, dated view of the current state
  (`mdctx snapshot`). Snapshots live in `docs/snapshots/`.
- **Archive** — move old snapshots out of the active set with `mdctx rotate`,
  which keeps the newest few and moves the rest to `docs/archive/snapshots/`.
  Archive content is **not read by default**, so history is preserved without
  paying for it on every session.

This project deliberately avoids "commit" as a workflow verb. Prefer
**refresh**, **snapshot**, **context update**, **docs update**, or **update
summary**.

## Token usage estimation

`mdctx` estimates the token cost of your context so it is visible and
controllable:

- With [`tiktoken`](https://github.com/openai/tiktoken) installed, counts are
  accurate (`cl100k_base`). Otherwise `mdctx` estimates `character_count / 4`.
- `mdctx tokens` reports three totals: **startup docs**, **active docs**, and
  **all docs (incl. archive)**.

Recommended limits (`mdctx` warns, never edits):

| Target                            | Limit                                   |
|-----------------------------------|-----------------------------------------|
| `docs/02_CURRENT_STATE.md`        | max 120 lines or 1,500 estimated tokens |
| `docs/CHANGELOG.md`               | max 3,000 estimated tokens              |
| Any single active Markdown file   | warn above 2,500 estimated tokens       |
| Startup docs total                | warn above 3,500 estimated tokens       |

See [docs/token-limits.md](docs/token-limits.md).

## Safety rules

MD Context Kit is deliberately conservative:

- **It never modifies your application code.** It only ever creates or moves
  Markdown context files, and only when you ask it to.
- **It never runs `git commit` automatically.**
- **It never pushes automatically.**
- **It never reads `docs/archive/` content by default,** so archived material
  does not leak into context or token counts.

Files are only created in `init` mode or `refresh --apply` mode. When files
change, `mdctx` prints a **suggested** Git command for you to review and run.

## Example workflow: a new project

```bash
cd my-new-project
mdctx init                       # create the context files
# edit the files, replacing placeholders with your project details
mdctx check                      # confirm everything is present and small
mdctx tokens                     # see the startup token budget
# ... do work, keep docs/02_CURRENT_STATE.md updated ...
mdctx snapshot                   # capture a dated snapshot at a milestone
```

Then review the suggested Git command `mdctx` prints and run it yourself.

## Example workflow: an existing project

```bash
cd my-existing-project
mdctx refresh                    # dry run: see what is missing, change nothing
mdctx refresh --apply --tokens   # create missing files and show the token report
mdctx scan                       # find which docs are largest
# trim docs/02_CURRENT_STATE.md and split oversized files as flagged
mdctx rotate                     # move old snapshots into the archive
mdctx check                      # confirm the context is healthy
```

## Suggested Git commands (printed, never executed)

`mdctx` never stages, commits, or pushes. When files change, it prints a
suggestion like the following for you to review and run yourself:

```bash
git add -A && git commit -m "docs: context update"
```

For an initial setup it might suggest `docs: initialize context`, and for a
rotation `docs: rotate snapshots`. These are only suggestions — running them is
always your decision.

## Credits

Created and maintained by **botbas**.

## License

Released under the [MIT License](LICENSE). Copyright (c) 2026 botbas.
