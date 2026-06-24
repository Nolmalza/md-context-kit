# Usage

A step-by-step guide to using `mdctx`, followed by a reference for every
command. Run `mdctx --help` or `mdctx <command> --help` for the built-in help.

All commands accept `-C` / `--path` to target a project other than the current
directory:

```bash
mdctx check -C ./path/to/project
```

Every command ends with a standard summary: files checked, files created, files
updated, estimated Markdown tokens, warnings, the next recommended action, and —
only when files changed — a suggested Git command.

## Step by step

### 1. Initialize a project

From the root of your project:

```bash
mdctx init
```

This creates any missing context files from the generic templates and leaves
existing files untouched. Then open the new files and replace the placeholders
(`Project Name`, `Module A`, `Service X`, `Feature Y`) with your own details.

### 2. Check the required files

```bash
mdctx check
```

Confirms the six required files exist and warns if any has grown too large. It
creates nothing.

### 3. Scan Markdown size

```bash
mdctx scan
```

Lists each tracked context file with its category, line count, and estimated
tokens, so you can see at a glance what is large. Archive content is not read.

### 4. Estimate tokens

```bash
mdctx tokens
```

Reports the estimated token cost of your context, grouped into startup, active,
and all-docs totals (see [token-limits.md](token-limits.md)).

### 5. Refresh the docs

```bash
mdctx refresh           # dry run — reports what it would do, changes nothing
mdctx refresh --apply   # creates any missing files from templates
```

Use a refresh to bring the context set back to the expected structure — for
example after starting a new module or pruning files.

### 6. Create a snapshot

```bash
mdctx snapshot
```

Writes a short, dated file under `docs/snapshots/` capturing the current state.
Fill in the status, focus, and next steps.

### 7. Rotate old notes into the archive

```bash
mdctx rotate
```

Keeps the newest few snapshots active and moves older ones into
`docs/archive/snapshots/`. Archive content is not read by default, so this keeps
your active context small.

## Command reference

### `mdctx init`

Create any of the six required context files that do not already exist, from the
generic templates. Existing files are never overwritten.

### `mdctx check`

Verify the required files exist and warn when a file exceeds its recommended
size. The required files, in order:

1. `AGENTS.md`
2. `docs/00_INDEX.md`
3. `docs/context_registry.yml`
4. `docs/01_PROJECT_BRIEF.md`
5. `docs/02_CURRENT_STATE.md` (and that it is short)
6. `docs/CHANGELOG.md`

### `mdctx scan`

List every tracked context file with its category (`startup`, `active`, or
`archive`), line count, and estimated tokens. Archive content is not read.

### `mdctx tokens`

Report estimated token usage for three groups:

- **startup docs** — the five files an agent reads first.
- **active docs** — startup docs plus all other non-archive Markdown.
- **all docs (incl. archive)** — everything, archive included.

### `mdctx refresh`

Dry run. Report what a refresh would create, but change nothing.

### `mdctx refresh --apply`

Create missing files from templates (like `init`), as part of a refresh.

### `mdctx refresh --apply --tokens`

Apply the refresh and also print the estimated-token report in the summary.

### `mdctx snapshot`

Create a short, dated snapshot under `docs/snapshots/` from the snapshot
template.

### `mdctx rotate`

Move all but the newest snapshots into `docs/archive/snapshots/`.

## Safety

- Files are created only by `init` and `refresh --apply`.
- Application code is never modified.
- `git commit` and `git push` are never run. When files change, a suggested Git
  command is printed for you to review and run yourself.
- Archive content (`docs/archive/`) is not read by default.
