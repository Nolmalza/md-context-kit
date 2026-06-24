# Security Policy

## Do not report secrets publicly

If your report involves a leaked secret (an API key, token, password, private
URL, or any credential), **do not include the secret in a public issue or pull
request**. Public issues are visible to everyone and search engines. Report it
privately using the channel below, and rotate the affected credential
immediately.

## Reporting a vulnerability

Please report security issues privately rather than opening a public issue:

- Use GitHub's **"Report a vulnerability"** feature under the repository's
  **Security** tab (Private vulnerability reporting), or
- Contact the maintainer (botbas) privately through the repository profile.

When reporting, please include:

- A clear description of the issue and its impact.
- Steps to reproduce, or a minimal proof of concept.
- Any relevant environment details (OS, Python version, `mdctx` version).

Please give a reasonable amount of time for the issue to be addressed before any
public disclosure. We will acknowledge your report and keep you updated on
progress.

## Supported versions

MD Context Kit is at an early (0.x) stage. Security fixes are made on the latest
released version. Please upgrade to the latest version before reporting.

## Note: the tool should not store secrets in Markdown

MD Context Kit is designed so that secrets are never stored in Markdown context.
The templates use placeholders only, and the tool never reads or writes
credentials. When you adopt it:

- Keep secrets in environment variables or a secret manager — never in
  `AGENTS.md`, the brief, the current state, the changelog, or any context file.
- Do not paste tokens, keys, connection strings, or private URLs into Markdown.
- Add real secret files to `.gitignore` (for example `.env`, which this project
  ignores by default).

If you find a template, example, or doc in this repository that contains a
secret or real personal data, please report it using the private channel above
so it can be removed and any credential rotated.
