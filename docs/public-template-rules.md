# Public template rules

MD Context Kit ships templates that are meant to be published and reused by
anyone. To keep them safe to share and adaptable to any project, every template,
example, and doc must follow these rules.

## Templates must be generic

- Templates describe *structure*, not a specific project.
- They should read as a blank starting point that any team can adopt.

## Use placeholders only

- Use neutral placeholders: `Project Name`, `Module A`, `Module B`,
  `Service X`, `Feature Y`, and dates as `YYYY-MM-DD`.
- Replace placeholders in your own copy after running `mdctx init` — never bake
  real values into the shipped templates.

## No private examples

- Do not include screenshots, snippets, or notes copied from a real, private
  project.
- Examples in `examples/` must also be generic and use placeholder names only.

## No business-specific content

- Do not include any content specific to the author's own projects or business.
- The templates must be domain-neutral so they fit any kind of software project.

## No trading examples

- Do not use trading, brokerage, foreign-exchange, market, or
  expert-advisor/EA examples in templates, examples, or docs.
- Keep example domains generic (a "service", a "module", a "feature").

## No secrets

- Never include API keys, tokens, passwords, connection strings, or private
  URLs — not in templates, examples, docs, or test fixtures.
- The tool itself is built so that secrets should never be stored in Markdown.

## No real customer data

- Do not include real names, emails, account numbers, or any personal or
  customer data. Use obvious placeholders if an example needs a value.

## No internal project names

- Do not reference internal codenames, private repositories, or unreleased
  product names. Use `Project Name` and the neutral module/service placeholders.

## Before publishing

- Search the repo for real names, paths, secrets, and the disallowed example
  domains above.
- Confirm every example uses a neutral placeholder.
- Keep each template within the recommended token limits (see
  [token-limits.md](token-limits.md)).
