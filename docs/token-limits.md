# Token limits

`mdctx` estimates how many tokens an AI agent will spend reading your context
and warns when a file or group grows too large. It only warns — it never edits
your content.

## How tokens are estimated

- If [`tiktoken`](https://github.com/openai/tiktoken) is installed, `mdctx` uses
  it (the `cl100k_base` encoding) for accurate counts.
- Otherwise it falls back to a language-aware heuristic: Thai text costs about
  1 token per character and Latin text about 0.25 tokens per character. A flat
  `character_count / 4` was measured to under-count a pure-Thai document by ~74%,
  which is why the fallback weights Thai separately.

Install accurate counting with:

```bash
pip install "md-context-kit[tokens]"
```

## Configuring the limits

The limits below are the built-in defaults. Every one of them can be overridden
per project in `mdctx.json`:

```json
{ "limits": { "current_state_max_tokens": 1500, "startup_total_warn_tokens": 3500,
              "snapshots_to_keep": 5, "max_listed_files": 40 } }
```

Use this when a project legitimately has a bigger startup set (a workspace with
several role documents, for example) instead of silencing a warning that is
telling you something true.

## Recommended limits

| Target | Limit | Why |
| --- | --- | --- |
| `docs/02_CURRENT_STATE.md` | max 120 lines or 1,500 estimated tokens | It is a snapshot, not a log. Keep it skimmable. |
| `docs/CHANGELOG.md` | max 3,000 estimated tokens | Rotate old entries out before it bloats context. |
| Any single active Markdown file | warn above 2,500 estimated tokens | Large files are expensive to load; split them. |
| Startup docs total | warn above 3,500 estimated tokens | Agents read these every session, so keep them lean. |

`mdctx check`, `mdctx scan`, and `mdctx tokens` all apply these checks and list
any warnings in their summary.

## Token groups

`mdctx tokens` reports three totals:

- **startup docs** — the five files read first every session.
- **active docs** — startup docs plus all other non-archive Markdown.
- **all docs (incl. archive)** — everything, including archived material.

## Keeping within budget

- Move detail out of `docs/02_CURRENT_STATE.md` into the brief or changelog.
- Run `mdctx rotate` to push old snapshots into the archive.
- Never paste long logs, full diffs, full source code, or long JSON into
  Markdown. Link to the source instead.
- Split a large doc into focused files and list them in `docs/00_INDEX.md` and
  `docs/context_registry.yml`.
