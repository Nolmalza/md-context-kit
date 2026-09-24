"""Command line interface for MD Context Kit (``mdctx``).

Commands
--------
- ``mdctx init``                      create missing context files from templates
- ``mdctx check``                     required files, size limits, registry health
- ``mdctx scan``                      list tracked context files with stats
- ``mdctx tokens``                    report estimated token usage
- ``mdctx tasks``                     token cost of each task's reading list
- ``mdctx dupes``                     find duplicated context files
- ``mdctx refresh``                   dry run: report what a refresh would do
- ``mdctx refresh --apply``           create missing files from templates
- ``mdctx refresh --apply --tokens``  apply and also print the token report
- ``mdctx snapshot``                  create a short, dated snapshot
- ``mdctx rotate``                    move old snapshots into the archive

Every command accepts ``-C/--path`` and ``--json``. ``--json`` emits a single
machine-readable object so an agent (or CI) can act on the numbers instead of
scraping text. ``check --strict`` exits non-zero when there are warnings.

Safety rules enforced here:
- Files are only created in ``init`` mode or ``refresh --apply`` mode.
- Application code is never modified.
- ``git commit`` and ``git push`` are never run. If files changed, a suggested
  Git command is printed for the user to run themselves.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, git_status
from .project_config import (
    ProjectConfig,
    load_config,
)
from .registry import Registry, parse_registry, referenced_paths
from .scanner import ScanResult, find_duplicates, scan_detailed
from .templates import (
    SNAPSHOT_TEMPLATE,
    TEMPLATE_TARGETS,
    TEMPLATES,
)
from .token_estimator import thai_needs_tiktoken, using_tiktoken


SNAPSHOT_DIR = "docs/snapshots"
ARCHIVE_SNAPSHOT_DIR = "docs/archive/snapshots"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
@dataclass
class Report:
    """Accumulates the standard end-of-command summary."""

    command: str = ""
    files_checked: int = 0
    files_created: list[str] = field(default_factory=list)
    files_updated: list[str] = field(default_factory=list)
    token_totals: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    next_action: str = ""
    git_suggestion: str = ""
    data: dict = field(default_factory=dict)
    body: list[str] = field(default_factory=list)

    def changed(self) -> bool:
        return bool(self.files_created or self.files_updated)

    def render(self) -> str:
        lines: list[str] = []
        if self.body:
            lines.extend(self.body)
            lines.append("")

        lines.append("")
        lines.append("Summary")
        lines.append("-------")
        lines.append(f"Files checked:  {self.files_checked}")

        lines.append(f"Files created:  {len(self.files_created)}")
        for rel in self.files_created:
            lines.append(f"  + {rel}")

        lines.append(f"Files updated:  {len(self.files_updated)}")
        for rel in self.files_updated:
            lines.append(f"  ~ {rel}")

        if self.token_totals:
            lines.append("Estimated Markdown tokens:")
            for label, value in self.token_totals.items():
                lines.append(f"  {label}: {value:,}")

        if self.notices:
            for n in self.notices:
                lines.append(f"  i {n}")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  ! {w}")
        else:
            lines.append("Warnings: none")

        if self.next_action:
            lines.append(f"Next recommended action: {self.next_action}")

        if self.changed() and self.git_suggestion:
            lines.append("Suggested Git command (review and run yourself):")
            lines.append(f"  {self.git_suggestion}")

        return "\n".join(lines)

    def to_json(self, root: Path) -> str:
        payload = {
            "tool": "mdctx",
            "version": __version__,
            "command": self.command,
            "path": str(root),
            "tokenizer": "tiktoken/cl100k_base" if using_tiktoken() else "heuristic",
            "files_checked": self.files_checked,
            "files_created": self.files_created,
            "files_updated": self.files_updated,
            "token_totals": self.token_totals,
            "notices": self.notices,
            "warnings": self.warnings,
            "warning_count": len(self.warnings),
            "next_action": self.next_action,
            "git_suggestion": self.git_suggestion,
            "data": self.data,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Context (single scan shared by every command)
# ---------------------------------------------------------------------------
@dataclass
class Ctx:
    root: Path
    cfg: ProjectConfig
    visible: ScanResult
    all_docs: ScanResult
    registry: Registry

    def by_rel(self) -> dict:
        return {f.rel: f for f in self.visible.files}


def build_ctx(root: Path) -> Ctx:
    cfg = load_config(root)
    visible = scan_detailed(root, include_archive=False, cfg=cfg)
    all_docs = scan_detailed(root, include_archive=True, cfg=cfg, report_ignored=False)
    reg = Registry()
    if cfg.registry:
        reg = parse_registry(root, cfg.registry, estimator=_estimate)
    return Ctx(root=root, cfg=cfg, visible=visible, all_docs=all_docs, registry=reg)


def _estimate(text: str) -> int:
    from .token_estimator import estimate_tokens

    return estimate_tokens(text)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def token_totals(ctx: Ctx) -> dict[str, int]:
    """Estimated token totals for startup, active, and all docs."""
    visible = ctx.visible.files
    startup = sum(f.tokens for f in visible if f.category == "startup")
    active = sum(f.tokens for f in visible if f.category in ("startup", "active"))
    everything = sum(f.tokens for f in ctx.all_docs.files)
    return {
        "startup docs": startup,
        "active docs": active,
        "all docs (incl. archive)": everything,
    }


def _limits(ctx: Ctx) -> dict[str, int]:
    return ctx.cfg.limits


def collect_warnings(ctx: Ctx) -> list[str]:
    """Check size limits, registry health, duplicates and tokenizer quality."""
    warnings: list[str] = []
    lim = _limits(ctx)
    by_rel = ctx.by_rel()
    cs_rel = ctx.cfg.current_state
    cl_rel = ctx.cfg.changelog

    cs = by_rel.get(cs_rel)
    if cs is not None:
        if cs.lines > lim["current_state_max_lines"]:
            warnings.append(
                f"{cs_rel} is {cs.lines} lines "
                f"(max {lim['current_state_max_lines']}). Trim it to a short snapshot."
            )
        if cs.tokens > lim["current_state_max_tokens"]:
            warnings.append(
                f"{cs_rel} is ~{cs.tokens:,} tokens "
                f"(max {lim['current_state_max_tokens']:,}). Move detail to the brief "
                f"or changelog."
            )

    cl = by_rel.get(cl_rel)
    if cl is not None and cl.tokens > lim["changelog_max_tokens"]:
        warnings.append(
            f"{cl_rel} is ~{cl.tokens:,} tokens "
            f"(max {lim['changelog_max_tokens']:,}). Rotate old entries to the archive."
        )

    for f in ctx.visible.files:
        if f.rel in (cs_rel, cl_rel):
            continue
        if f.category in ("startup", "active") and f.tokens > lim["active_file_warn_tokens"]:
            warnings.append(
                f"{f.rel} is ~{f.tokens:,} tokens "
                f"(warn above {lim['active_file_warn_tokens']:,}). Consider splitting it."
            )

    totals = token_totals(ctx)
    if totals["startup docs"] > lim["startup_total_warn_tokens"]:
        warnings.append(
            f"Startup docs total ~{totals['startup docs']:,} tokens "
            f"(warn above {lim['startup_total_warn_tokens']:,}). Slim the startup set."
        )

    # registry health
    reg = ctx.registry
    if reg.exists:
        for ref in reg.refs:
            if not ref.exists:
                warnings.append(
                    f"Registry section '{ref.section}' references a missing file: {ref.path}"
                )
        for path in reg.startup:
            if path in ctx.cfg.startup_files:
                continue
            if (ctx.root / path).is_file():
                f = by_rel.get(path)
                if f is not None and f.category not in ("startup",):
                    warnings.append(
                        f"Registry marks {path} as 'read_when: startup' but it is not in "
                        f"the startup set. Add it to startup_files in mdctx.json."
                    )
        for path in reg.never_read:
            f = by_rel.get(path)
            if f is not None and f.category == "startup":
                warnings.append(
                    f"{path} is marked 'read_when: never' but is treated as a startup doc."
                )

    # duplicated content
    dupes = find_duplicates(ctx.visible.files)
    if dupes:
        groups = len(dupes)
        redundant = sum(sum(x.tokens for x in g[1:]) for g in dupes)
        warnings.append(
            f"{groups} duplicated context file group(s) ~{redundant:,} redundant tokens. "
            f"Run 'mdctx dupes' to see them."
        )

    # tokenizer quality for Thai-heavy documents
    if not using_tiktoken():
        thai_files = [f.rel for f in ctx.visible.files if f.thai_ratio >= 0.10]
        if thai_files:
            warnings.append(
                f"tiktoken is not installed and {len(thai_files)} file(s) are Thai-heavy "
                f"(e.g. {thai_files[0]}). The fallback heuristic is approximate for Thai — "
                f"install with: pip install \"md-context-kit[tokens]\"."
            )

    return warnings


def collect_notices(ctx: Ctx) -> list[str]:
    notices: list[str] = []
    if ctx.cfg.loaded_from:
        notices.append("config: " + ", ".join(ctx.cfg.loaded_from))
    elif ctx.cfg.custom_ignore:
        notices.append("config: custom ignore rules in use")
    if ctx.visible.ignored_files:
        notices.append(
            f"ignored {ctx.visible.ignored_files:,} file(s) / ~{ctx.visible.ignored_tokens:,} "
            f"tokens (dependency, generated or archived content)"
        )
    if ctx.registry.exists:
        notices.append(
            f"registry: {ctx.cfg.registry} — {len(ctx.registry.sections)} section(s), "
            f"{len(ctx.registry.refs)} file reference(s)"
        )
    return notices


def missing_required(ctx: Ctx) -> list[str]:
    return [rel for rel in ctx.cfg.required_files if not (ctx.root / rel).exists()]


def startup_set(ctx: Ctx) -> tuple[int, list[str]]:
    """Token cost and members of the effective startup set."""
    by_rel = ctx.by_rel()
    total = 0
    members: list[str] = []
    for rel in ctx.cfg.startup_files:
        f = by_rel.get(rel)
        if f is not None:
            total += f.tokens
            members.append(rel)
    return total, members


def orphan_docs(ctx: Ctx) -> list:
    """Active docs that nothing points at: not startup output, not in the registry.

    These are the loose documents that quietly grow in a project root. They cost
    tokens whenever an agent greps the folder, and they are the first place to
    look for duplicated or superseded context.
    """
    refs = referenced_paths(ctx.registry) if ctx.registry.exists else set()
    startup = set(ctx.cfg.startup_files)
    out = [
        f
        for f in ctx.visible.files
        if f.category == "active" and f.rel not in refs and f.rel not in startup
    ]
    out.sort(key=lambda f: -f.tokens)
    return out


def write_template(root: Path, name: str) -> str:
    """Create one template file. Returns the relative path written."""
    rel = TEMPLATE_TARGETS[name]
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(TEMPLATES[name], encoding="utf-8")
    return rel


def create_missing(root: Path, cfg: ProjectConfig) -> list[str]:
    """Create any missing template file that the project requires.

    Existing files are never overwritten, and templates that a project has
    renamed or dropped (see ``required_files`` in mdctx.json) are left alone.
    """
    created: list[str] = []
    for name, rel in TEMPLATE_TARGETS.items():
        if rel not in cfg.required_files:
            continue
        if (root / rel).exists():
            continue
        created.append(write_template(root, name))
    return created


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_init(root: Path, args) -> Report:
    ctx = build_ctx(root)
    report = Report(command="init")
    report.files_created = create_missing(root, ctx.cfg)
    ctx = build_ctx(root)
    report.files_checked = len(ctx.cfg.required_files)
    report.token_totals = token_totals(ctx)
    report.notices = collect_notices(ctx)
    report.warnings = collect_warnings(ctx)
    report.git_suggestion = git_status.suggested_command("docs: initialize context")

    still_missing = missing_required(ctx)
    if still_missing:
        report.next_action = (
            "Fill in placeholders, then run 'mdctx check'. Missing: " + ", ".join(still_missing)
        )
    elif report.files_created:
        report.next_action = "Replace the placeholders in the new files with your project details."
    else:
        report.next_action = "All context files already exist. Run 'mdctx check'."
    report.data = {"missing": still_missing}
    return report


def cmd_check(root: Path, args) -> Report:
    ctx = build_ctx(root)
    report = Report(command="check")
    report.files_checked = len(ctx.cfg.required_files)

    missing = missing_required(ctx)
    for rel in missing:
        report.warnings.append(f"Missing required file: {rel}")

    report.warnings.extend(collect_warnings(ctx))
    report.notices = collect_notices(ctx)
    report.token_totals = token_totals(ctx)

    startup_tokens, members = startup_set(ctx)
    report.body.append("Startup set (read every session):")
    for rel in members:
        f = ctx.by_rel()[rel]
        report.body.append(f"  {f.tokens:>7,} tok  {rel}")
    report.body.append(f"  {startup_tokens:>7,} tok  TOTAL (budget {ctx.cfg.limits['startup_total_warn_tokens']:,})")

    orphans = orphan_docs(ctx)
    if orphans:
        loose = sum(f.tokens for f in orphans)
        root_loose = [f for f in orphans if "/" not in f.rel]
        report.notices.append(
            f"{len(orphans)} doc(s) ~{loose:,} tokens are not referenced by the registry or the "
            f"startup set"
            + (f"; {len(root_loose)} of them sit in the project root" if root_loose else "")
            + f" (largest: {orphans[0].rel} ~{orphans[0].tokens:,} tok)"
        )

    if missing:
        report.next_action = (
            "Run 'mdctx init' (or 'mdctx refresh --apply') to create missing files."
        )
    elif report.warnings:
        report.next_action = "Address the warnings above, then re-run 'mdctx check'."
    else:
        report.next_action = "Context looks healthy. Nothing to do."

    report.data = {
        "missing": missing,
        "startup_tokens": startup_tokens,
        "startup_files": members,
        "orphan_count": len(orphans),
        "orphan_docs": [{"path": f.rel, "tokens": f.tokens} for f in orphans[:20]],
    }
    return report


def cmd_scan(root: Path, args) -> Report:
    ctx = build_ctx(root)
    report = Report(command="scan")
    files = ctx.visible.files
    report.files_checked = len(files)

    limit = int(ctx.cfg.limits.get("max_listed_files", 40))
    ordered = sorted(files, key=lambda f: -f.tokens)
    show = ordered if getattr(args, "all", False) else ordered[:limit]

    report.body.append("Tracked context files, largest first (archive not read by default):")
    report.body.append(f"  {'category':<9} {'lines':>6} {'tokens':>8}  path")
    for f in show:
        report.body.append(f"  {f.category:<9} {f.lines:>6} {f.tokens:>8,}  {f.rel}")
    if len(show) < len(files):
        report.body.append(f"  ... {len(files) - len(show)} more (use --all to list everything)")

    report.token_totals = token_totals(ctx)
    report.notices = collect_notices(ctx)
    report.warnings = collect_warnings(ctx)
    report.next_action = "Run 'mdctx tasks' for per-task cost, or 'mdctx check' for health."
    report.data = {
        "files": [
            {
                "path": f.rel,
                "category": f.category,
                "lines": f.lines,
                "tokens": f.tokens,
                "thai_ratio": f.thai_ratio,
            }
            for f in ordered
        ],
        "ignored": {
            "files": ctx.visible.ignored_files,
            "tokens": ctx.visible.ignored_tokens,
            "samples": [
                {"path": s.rel, "tokens": s.tokens, "rule": s.rule}
                for s in ctx.visible.ignored_samples[:20]
            ],
        },
    }
    return report


def cmd_tokens(root: Path, args) -> Report:
    ctx = build_ctx(root)
    report = Report(command="tokens")
    report.files_checked = len(ctx.visible.files)
    report.token_totals = token_totals(ctx)
    report.notices = collect_notices(ctx)
    report.warnings = collect_warnings(ctx)
    report.next_action = "Keep startup docs lean so agents load context cheaply."

    startup_tokens, members = startup_set(ctx)
    report.data = {
        "startup_tokens": startup_tokens,
        "startup_files": members,
        "ignored_tokens": ctx.visible.ignored_tokens,
        "tokenizer": "tiktoken" if using_tiktoken() else "heuristic",
    }
    return report


def cmd_tasks(root: Path, args) -> Report:
    """Token cost of each task's reading list, from the context registry."""
    ctx = build_ctx(root)
    report = Report(command="tasks")

    if not ctx.registry.exists:
        report.next_action = (
            "No registry found. Add docs/context_registry.yml (see docs/registry-format.md)."
        )
        report.warnings.append("No context registry found; nothing to price.")
        return report

    reg = ctx.registry
    report.files_checked = len(reg.sections)
    sections = sorted(reg.sections, key=lambda s: -s.tokens)
    skip = {"limits", "version", "project"}

    report.body.append(f"Task reading lists from {ctx.cfg.registry}:")
    report.body.append(f"  {'tokens':>8}  {'files':>5}  task")
    for s in sections:
        if s.name in skip:
            continue
        report.body.append(f"  {s.tokens:>8,}  {len(s.refs):>5}  {s.name}")

    reg_startup = [r for r in reg.refs if r.read_when == "startup"]
    if reg_startup:
        total = sum(r.tokens for r in reg_startup if r.exists)
        report.body.append("")
        report.body.append(f"  registry startup set: {total:,} tokens ({len(reg_startup)} files)")

    for ref in reg.refs:
        if not ref.exists:
            report.warnings.append(f"Registry references a missing file: {ref.path}")

    orphan = orphan_docs(ctx)
    if orphan:
        redundant = sum(f.tokens for f in orphan)
        report.warnings.append(
            f"{len(orphan)} active doc(s) ~{redundant:,} tokens are not referenced by any "
            f"registry section (largest: {orphan[0].rel} ~{orphan[0].tokens:,})."
        )

    report.notices = collect_notices(ctx)
    report.next_action = "Read only the sections a task needs; never the whole folder."
    report.data = {
        "sections": [
            {
                "name": s.name,
                "tokens": s.tokens,
                "files": [
                    {"path": r.path, "tokens": r.tokens, "exists": r.exists, "read_when": r.read_when}
                    for r in s.refs
                ],
            }
            for s in sections
            if s.name not in skip
        ],
        "orphan_docs": [{"path": f.rel, "tokens": f.tokens} for f in orphan[:20]],
    }
    return report


def cmd_dupes(root: Path, args) -> Report:
    """Find context files whose content is identical."""
    ctx = build_ctx(root)
    report = Report(command="dupes")
    groups = find_duplicates(ctx.visible.files)
    report.files_checked = len(ctx.visible.files)

    if not groups:
        report.body.append("No duplicated context files found.")
    else:
        total_redundant = 0
        report.body.append("Duplicated context files (identical content):")
        for g in groups:
            redundant = sum(x.tokens for x in g[1:])
            total_redundant += redundant
            report.body.append("")
            report.body.append(
                f"  {len(g)} copies, ~{redundant:,} redundant tokens, ~{g[0].tokens:,} each:"
            )
            for f in g:
                report.body.append(f"      {f.rel}")
        report.body.append("")
        report.body.append(
            f"Total redundant tokens if you keep one copy of each group: ~{total_redundant:,}"
        )
        report.warnings.append(
            f"{len(groups)} duplicated group(s); ~{total_redundant:,} redundant tokens."
        )

    report.token_totals = token_totals(ctx)
    report.notices = collect_notices(ctx)
    report.next_action = "Keep one copy and link to it; archive or delete the rest."
    report.data = {
        "groups": [
            {
                "count": len(g),
                "tokens_each": g[0].tokens,
                "redundant_tokens": sum(x.tokens for x in g[1:]),
                "files": [f.rel for f in g],
            }
            for g in groups
        ]
    }
    return report


def cmd_refresh(root: Path, args) -> Report:
    ctx = build_ctx(root)
    report = Report(command="refresh")
    report.files_checked = len(ctx.cfg.required_files)
    missing = missing_required(ctx)

    if args.apply:
        report.files_created = create_missing(root, ctx.cfg)
        ctx = build_ctx(root)
        report.git_suggestion = git_status.suggested_command("docs: context update")
    else:
        for rel in missing:
            report.body.append(f"Would create from template: {rel}")
        if not missing:
            report.body.append("Nothing to create. All required files exist.")

    report.warnings = collect_warnings(ctx)
    report.notices = collect_notices(ctx)

    if args.tokens:
        report.token_totals = token_totals(ctx)

    if not args.apply and missing:
        report.next_action = "Re-run with '--apply' to create the missing files."
    elif report.files_created:
        report.next_action = "Replace placeholders in the new files, then 'mdctx check'."
    elif report.warnings:
        report.next_action = "Address the warnings above."
    else:
        report.next_action = "Context is up to date."
    report.data = {"missing": missing}
    return report


def cmd_snapshot(root: Path, args) -> Report:
    snap_dir = root / SNAPSHOT_DIR
    snap_dir.mkdir(parents=True, exist_ok=True)

    stamp = _now_stamp()
    rel = f"{SNAPSHOT_DIR}/{stamp}.md"
    target = root / rel
    target.write_text(SNAPSHOT_TEMPLATE.format(timestamp=stamp), encoding="utf-8")

    ctx = build_ctx(root)
    report = Report(command="snapshot")
    report.files_created = [rel]
    report.files_checked = len(ctx.visible.files)
    report.token_totals = token_totals(ctx)
    report.warnings = collect_warnings(ctx)
    report.notices = collect_notices(ctx)
    report.git_suggestion = git_status.suggested_command(f"docs: snapshot {stamp}")
    report.next_action = "Fill in the snapshot, then run 'mdctx rotate' if snapshots pile up."
    report.data = {"snapshot": rel}
    return report


def cmd_rotate(root: Path, args) -> Report:
    """Move all but the newest snapshots into the archive."""
    snap_dir = root / SNAPSHOT_DIR
    keep = int(load_config(root).limits.get("snapshots_to_keep", 5))

    snapshots = sorted(snap_dir.glob("*.md")) if snap_dir.exists() else []
    ctx = build_ctx(root)
    report = Report(command="rotate")
    report.files_checked = len(snapshots)

    if len(snapshots) <= keep:
        report.next_action = (
            f"{len(snapshots)} snapshot(s); nothing to rotate (keeping newest {keep})."
        )
        report.token_totals = token_totals(ctx)
        report.data = {"moved": []}
        return report

    to_move = snapshots[:-keep]  # oldest first
    archive_dir = root / ARCHIVE_SNAPSHOT_DIR
    archive_dir.mkdir(parents=True, exist_ok=True)

    for src in to_move:
        dest = archive_dir / src.name
        src.replace(dest)
        report.files_updated.append(
            f"{SNAPSHOT_DIR}/{src.name} -> {ARCHIVE_SNAPSHOT_DIR}/{src.name}"
        )

    ctx = build_ctx(root)
    report.token_totals = token_totals(ctx)
    report.warnings = collect_warnings(ctx)
    report.notices = collect_notices(ctx)
    report.git_suggestion = git_status.suggested_command("docs: rotate snapshots")
    report.next_action = (
        f"Moved {len(to_move)} snapshot(s) to the archive. "
        "Archive content is not read by default."
    )
    report.data = {"moved": [f"{SNAPSHOT_DIR}/{s.name}" for s in to_move]}
    return report


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
COMMANDS = {
    "init": cmd_init,
    "check": cmd_check,
    "scan": cmd_scan,
    "tokens": cmd_tokens,
    "tasks": cmd_tasks,
    "dupes": cmd_dupes,
    "refresh": cmd_refresh,
    "snapshot": cmd_snapshot,
    "rotate": cmd_rotate,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdctx",
        description=(
            "MD Context Kit — keep project Markdown small, structured, and cheap "
            "for AI coding agents to read."
        ),
    )
    parser.add_argument("--version", action="version", version=f"mdctx {__version__}")

    # Shared options available on every subcommand, e.g. `mdctx check -C path`.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-C",
        "--path",
        default=".",
        help="Project root to operate on (default: current directory).",
    )
    common.add_argument(
        "--json",
        action="store_true",
        help="Emit a single machine-readable JSON object instead of text.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", parents=[common], help="Create missing context files from templates.")
    p_check = sub.add_parser(
        "check", parents=[common], help="Check required files, size limits and registry health."
    )
    p_check.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when there are warnings (useful as a gate).",
    )
    p_scan = sub.add_parser("scan", parents=[common], help="List tracked context files with stats.")
    p_scan.add_argument("--all", action="store_true", help="List every tracked file.")
    sub.add_parser("tokens", parents=[common], help="Report estimated token usage.")
    sub.add_parser("tasks", parents=[common], help="Token cost of each task's reading list.")
    sub.add_parser("dupes", parents=[common], help="Find duplicated context files.")

    p_refresh = sub.add_parser(
        "refresh",
        parents=[common],
        help="Re-check context; with --apply, create missing files.",
    )
    p_refresh.add_argument(
        "--apply",
        action="store_true",
        help="Create missing files from templates (otherwise dry run).",
    )
    p_refresh.add_argument(
        "--tokens",
        action="store_true",
        help="Also print the estimated token report.",
    )

    sub.add_parser("snapshot", parents=[common], help="Create a short, dated snapshot.")
    sub.add_parser("rotate", parents=[common], help="Move old snapshots into the archive.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"error: path does not exist: {root}", file=sys.stderr)
        return 2

    handler = COMMANDS[args.command]
    report = handler(root, args)

    if getattr(args, "json", False):
        print(report.to_json(root))
    else:
        print(report.render())

    if getattr(args, "strict", False) and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
