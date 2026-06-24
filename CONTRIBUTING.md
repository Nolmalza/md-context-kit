# Contributing to MD Context Kit

Thanks for your interest in improving MD Context Kit. This guide covers how to
set up locally, run the CLI, add templates, and keep everything generic and free
of private data.

## Set up locally

You need Python 3.9 or newer.

```bash
git clone https://github.com/botbas/md-context-kit
cd md-context-kit

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install in editable mode, with dev and token extras
pip install -e ".[dev,tokens]"
```

The `tokens` extra installs `tiktoken` for accurate token counts. Without it,
the tool falls back to a `chars / 4` estimate.

## Run the CLI

Once installed, the `mdctx` command is available:

```bash
mdctx --help
mdctx init
mdctx check
mdctx tokens
```

You can also run it as a module without installing the script:

```bash
python -m md_context_kit.cli check
python -m md_context_kit.cli tokens
python -m md_context_kit.cli refresh --apply --tokens
```

Use `-C / --path` to operate on a project in another directory:

```bash
mdctx check -C ./some/project
```

## Run the tests

```bash
pytest
```

## Add or change a template

The templates live in two places that must stay in sync:

- `src/md_context_kit/templates.py` — the embedded strings used by `mdctx init`
  and `mdctx refresh --apply`. **This is the source of truth.**
- `templates/generic/` — a browsable mirror of the same content.

To add or edit a template:

1. Edit the relevant string in `src/md_context_kit/templates.py`.
2. If you add a new file, register it in `TEMPLATE_TARGETS` (template name →
   path under the project root).
3. Regenerate the mirror so `templates/generic/` matches:

   ```bash
   python - <<'PY'
   from md_context_kit.templates import TEMPLATES
   import pathlib
   out = pathlib.Path("templates/generic")
   out.mkdir(parents=True, exist_ok=True)
   for name, content in TEMPLATES.items():
       (out / name).write_text(content, encoding="utf-8")
   PY
   ```

4. Run `mdctx init` in a throwaway directory and confirm the files are created
   as expected.

## Keep templates generic

Templates describe structure, not a specific project. Follow
[docs/public-template-rules.md](docs/public-template-rules.md):

- Use placeholders only (`Project Name`, `Module A`, `Service X`, `Feature Y`).
- No business-specific content, and no trading, brokerage, foreign-exchange, or
  expert-advisor (EA) examples.
- No internal or codename project names.

## Avoid private data in examples

- Never include secrets (API keys, tokens, passwords, private URLs).
- Never include real customer or personal data.
- Keep `examples/` generic and placeholder-only.
- Do not paste full logs, full diffs, full source files, or long JSON into any
  Markdown — link to the source instead.

## Workflow terms

This project avoids "commit" as a workflow verb. Prefer **refresh**,
**snapshot**, **context update**, **docs update**, or **update summary**. (The
literal `git commit` may appear only inside a *suggested* Git command that the
user runs themselves.)

## Pull requests

- Keep changes focused and described clearly.
- Update `CHANGELOG.md` under "Unreleased".
- Make sure `mdctx check` passes and the content scans in
  [docs/public-template-rules.md](docs/public-template-rules.md) are clean.
