# Registry format — `context_registry.yml`

`docs/context_registry.yml` is a small, machine-readable description of a
project's context files. It tells an AI agent what each file is, when to read
it, and what it covers — so the agent can load the right context and skip the
rest.

It is itself a startup doc, so keep it short.

## Shape

```yaml
version: 1
project: "Project Name"

context:
  - id: current_state
    title: Current state
    type: state
    status: active
    file: docs/02_CURRENT_STATE.md
    read_when: startup
    scope: global
    last_updated: 2026-06-25

limits:
  current_state_max_lines: 120
  current_state_max_tokens: 1500
  changelog_max_tokens: 3000
  active_file_warn_tokens: 2500
  startup_total_warn_tokens: 3500
```

The top level has a `version`, a `project` name, a `context` list of entries,
and an optional `limits` block. Each entry in `context` uses the fields below.

## Entry fields

### `id`

A short, stable, machine-friendly identifier for the entry, in
`snake_case` (for example `current_state`, `brief`, `auth_notes`). Use the `id`
to refer to a piece of context from other docs or from an agent prompt instead
of repeating a rule or pasting a path. IDs should not change once set.

### `title`

A short human-readable name (for example `Current state`, `Project brief`).
Shown to people scanning the registry.

### `type`

What kind of context the file holds. Suggested values:

- `guide` — how to work in the project (e.g. `AGENTS.md`).
- `index` — a map of the other docs.
- `registry` — this file.
- `brief` — the stable project overview.
- `state` — the short current-state snapshot.
- `changelog` — dated update summaries.
- `snapshot` — a dated point-in-time capture.
- `notes` — focused notes for a module or feature.

### `status`

The lifecycle of the entry. Suggested values:

- `active` — current and in use.
- `draft` — being written, not yet authoritative.
- `archived` — superseded; kept for history, not read by default.

### `file`

The path to the file, relative to the project root (for example
`docs/02_CURRENT_STATE.md`). Use forward slashes.

### `read_when`

A hint about when an agent should load the file:

- `startup` — read at the start of every session (startup docs).
- `on-demand` — read only when a task needs it.
- `never` — do not auto-load (for example archived material).

### `scope`

How broadly the entry applies:

- `global` — relevant to the whole project.
- A module or area name (for example `module-a`, `service-x`) — relevant only
  to that part.

### `last_updated`

The date the file's content was last meaningfully updated, in `YYYY-MM-DD`
form. Helps an agent judge whether a note is still current.

## Rules of thumb

- Give every file an entry, and keep `read_when: startup` to the smallest set
  an agent truly needs up front.
- Keep IDs stable; change `title`, `status`, or `last_updated` as things evolve.
- Mark superseded files `status: archived` and `read_when: never` rather than
  deleting their history.
- The `limits` block documents your intended thresholds; `mdctx` enforces its
  own matching built-in defaults when it warns.

## How `mdctx` uses it

The current release treats `context_registry.yml` as one of the startup docs:
it checks the file exists and counts it toward the startup token budget. The
field schema above is read by humans and AI agents; future `mdctx` versions may
parse it directly.
