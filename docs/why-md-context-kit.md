# Why MD Context Kit

MD Context Kit exists to solve a specific, recurring problem in long-running,
AI-assisted coding projects: the Markdown that is supposed to *help* an AI agent
gradually becomes the thing that *slows it down*.

## Markdown is useful — until it isn't

Markdown is the natural place to keep a project's working knowledge: what the
project is, how it is built, what the rules are, and what to do next. It is
plain text, it diffs well, and both people and AI agents can read it.

In a long-running project, though, those same Markdown files tend to grow. A
"current state" note becomes a running journal. A design doc accumulates every
decision ever discussed. A changelog turns into a log of everything. What began
as a helpful, skimmable set of notes becomes a large, mixed pile of old and
current information.

## Large Markdown files increase token usage

AI coding agents re-read your context on every session, and often on every task.
Every line they read costs tokens — and tokens are finite, metered, and shared
with the actual work you want the agent to do. A bloated set of `.md` files
means the agent spends a large share of its context window reading documentation
before it writes a single line of code. Bigger context also tends to mean slower
and less focused responses.

## Old context confuses AI agents

Size is not the only problem. When current and outdated notes live in the same
file, an agent cannot easily tell which is which. It may act on a decision that
was later reversed, follow a rule that no longer applies, or "remember" a plan
that was abandoned. Stale context does not just waste tokens — it produces wrong
answers with confidence.

## Project history does not belong inside Markdown

There is a strong temptation to paste full Git history, long terminal logs,
complete diffs, entire source files, or long JSON responses into Markdown so the
agent "has everything." This is the single biggest source of bloat, and it is
unnecessary:

- **Git already stores the exact history of file changes.** Diffs, blame, and
  full file contents are one command away. Duplicating them in Markdown adds
  tokens without adding meaning.
- **Logs and raw responses are data, not context.** They are huge, rarely
  reread in full, and quickly outdated.

Markdown should link to these things, not contain them.

## Markdown should store meaning, not data

A healthy context set keeps a small, deliberate amount of high-value
information:

- **Project overview** — what the project is and who it is for.
- **Current state** — where things stand right now, kept short.
- **Important rules** — constraints that should always hold.
- **Decisions** — what was decided and why.
- **Next steps** — what to do next.
- **Short context snapshots** — dated, point-in-time captures.

It deliberately leaves out: full Git history, long terminal logs, full diffs,
full source code, long JSON responses, and any private business data.

This is the division of labour MD Context Kit assumes:

- **Git** stores the exact, complete history of file changes.
- **Markdown** stores the *meaning*: current state, rules, decisions, and next
  steps.

## What MD Context Kit does about it

MD Context Kit makes a project's AI context more selective, structured, and
lightweight:

- It defines a small set of **startup docs** an agent reads first, so the agent
  loads the right context instead of everything.
- It keeps a machine-readable **registry** (`context_registry.yml`) describing
  each file — its type, status, when to read it, and what it covers.
- It **estimates token usage** so the cost of your context is visible, and warns
  when a file or the startup set grows too large.
- It separates **current state**, **snapshots**, **decisions**, and **archive**,
  so old material is kept for history without being reloaded every session.
- It encourages a **refresh / snapshot / archive** workflow instead of an
  ever-growing journal, and never touches your application code or your Git
  history — it only prints suggested Git commands for you to run.

The result is context that stays cheap to read, easy to trust, and quick for an
AI agent to act on — even after the project has been running for months.
