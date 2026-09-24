# 01 — Project Brief (md-context-kit)

Stable overview. Current work lives in `02_CURRENT_STATE.md`; history in `CHANGELOG.md`.

## What this project is

`mdctx` is a command-line tool that keeps the Markdown context of a repository — the files
an AI coding agent reads before it can work — **small, structured, measured and current**.

It defines which files are read every session ("startup docs"), checks them against explicit
line and token budgets, prices the reading list of each task, groups duplicated context, and
moves aged material into an archive that is never loaded by default.

## Who it is for

Developers who run AI coding agents on long-lived repositories — especially non-English
projects, where a flat `chars / 4` estimate under-counts tokens badly.

## Scope

In scope: measuring and structuring Markdown context; the registry format; budgets and
warnings; templates; a refresh / snapshot / rotate workflow; JSON output for agents and CI.

Out of scope: writing or refactoring application code; Git operations; hosting or syncing
context; anything that requires a network connection or a paid API.

## Principles (changes here are breaking by definition)

1. **Read-only by contract.** `mdctx` never edits a project's code, never stages, commits or
   pushes; it prints suggested Git commands for a human to run.
2. **No dependencies on the core path.** Python 3.9+ and the standard library only.
   `tiktoken` is an optional extra for accurate counts.
3. **Numbers must be explainable.** Every total can be traced to files, and every ignore rule
   reports what it removed.
4. **Current information stays separate from history.** Snapshots and archives are cheap to
   keep and are not part of the default reading set.
5. **A budget is a warning, not an edit.** The tool never rewrites a file to fit.

## Versioning

Semantic versioning. Release notes are generated from `CHANGELOG.md`; every version gets a
Git tag and a GitHub release page.
