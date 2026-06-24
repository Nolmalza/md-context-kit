"""Command line interface for MD Context Kit (``mdctx``).

Commands
--------
- ``mdctx init``                      create missing context files from templates
- ``mdctx check``                     check required files exist and are healthy
- ``mdctx scan``                      list tracked context files with stats
- ``mdctx tokens``                    report estimated token usage
- ``mdctx refresh``                   dry run: report what a refresh would do
- ``mdctx refresh --apply``           create missing files from templates
- ``mdctx refresh --apply --tokens``  apply and also print the token report
- ``mdctx snapshot``                  create a short, dated snapshot
- ``mdctx rotate``                    move old snapshots into the archive

Safety rules enforced here:
- Files are only created in ``init`` mode or ``refresh --apply`` mode.
- Application code is never modified.
- ``git commit`` and ``git push`` are never run. If files changed, a suggested
  Git command is printed for the user to run themselves.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, git_status
from .scanner import scan
from .templates import (
    SNAPSHOT_TEMPLATE,
    TEMPLATE_TARGETS,
    TEMPLATES,
)

# ---------------------------------------------------------------------------
# Recommended limits
# ---------------------------------------------------------------------------
CURRENT_STATE_MAX_LINES = 120
CURRENT_STATE_MAX_TOKENS = 1500
CHANGELOG_MAX_TOKENS = 3000
ACTIVE_FILE_WARN_TOKENS = 2500
STARTUP_TOTAL_WARN_TOKENS = 3500

CURRENT_STATE = "docs/02_CURRENT_STATE.md"
CHANGELOG = "docs/CHANGELOG.md"

# Files that should exist in a healthy project (the `check` order).
REQUIRED_FILES = (
    "AGENTS.md",
    "docs/00_INDEX.md",
    "docs/context_registry.yml",
    "docs/01_PROJECT_BRIEF.md",
    "docs/02_CURRENT_STATE.md",
    "docs/CHANGELOG.md",
)

SNAPSHOT_DIR = "docs/snapshots"
ARCHIVE_SNAPSHOT_DIR = "docs/archive/snapshots"
SNAPSHOTS_TO_KEEP = 5


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
@dataclass
class Report:
    """Accumulates the standard end-of-command summary."""

    files_checked: int = 0
    files_created: list[str] = field(default_factory=list)
    files_updated: list[str] = field(default_factory=list)
    token_totals: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    next_action: str = ""
    git_suggestion: str = ""

    def changed(self) -> bool:
        return bool(self.files_created or self.files_updated)

    def render(self) -> str:
        lines: list[str] = []
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def token_totals(root: Path) -> dict[str, int]:
    """Return estimated token totals for startup, active, and all docs."""
    visible = scan(root, include_archive=False)
    all_docs = scan(root, include_archive=True)

    startup = sum(f.tokens for f in visible if f.category == "startup")
    active = sum(f.tokens for f in visible if f.category in ("startup", "active"))
    everything = sum(f.tokens for f in all_docs)

    return {
        "startup docs": startup,
        "active docs": active,
        "all docs (incl. archive)": everything,
    }


def collect_warnings(root: Path) -> list[str]:
    """Check size limits and return human-readable warnings."""
    warnings: list[str] = []
    by_rel = {f.rel: f for f in scan(root, include_archive=False)}

    cs = by_rel.get(CURRENT_STATE)
    if cs is not None:
        if cs.lines > CURRENT_STATE_MAX_LINES:
            warnings.append(
                f"{CURRENT_STATE} is {cs.lines} lines "
                f"(max {CURRENT_STATE_MAX_LINES}). Trim it to a short snapshot."
            )
        if cs.tokens > CURRENT_STATE_MAX_TOKENS:
            warnings.append(
                f"{CURRENT_STATE} is ~{cs.tokens:,} tokens "
                f"(max {CURRENT_STATE_MAX_TOKENS:,}). Move detail to the brief "
                f"or changelog."
            )

    cl = by_rel.get(CHANGELOG)
    if cl is not None and cl.tokens > CHANGELOG_MAX_TOKENS:
        warnings.append(
            f"{CHANGELOG} is ~{cl.tokens:,} tokens "
            f"(max {CHANGELOG_MAX_TOKENS:,}). Rotate old entries to the archive."
        )

    for f in by_rel.values():
        if f.rel in (CURRENT_STATE, CHANGELOG):
            continue
        if f.category in ("startup", "active") and f.tokens > ACTIVE_FILE_WARN_TOKENS:
            warnings.append(
                f"{f.rel} is ~{f.tokens:,} tokens "
                f"(warn above {ACTIVE_FILE_WARN_TOKENS:,}). Consider splitting it."
            )

    totals = token_totals(root)
    if totals["startup docs"] > STARTUP_TOTAL_WARN_TOKENS:
        warnings.append(
            f"Startup docs total ~{totals['startup docs']:,} tokens "
            f"(warn above {STARTUP_TOTAL_WARN_TOKENS:,}). Slim the startup set."
        )

    return warnings


def missing_required(root: Path) -> list[str]:
    return [rel for rel in REQUIRED_FILES if not (root / rel).exists()]


def write_template(root: Path, name: str) -> str:
    """Create one template file. Returns the relative path written."""
    rel = TEMPLATE_TARGETS[name]
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(TEMPLATES[name], encoding="utf-8")
    return rel


def create_missing(root: Path) -> list[str]:
    """Create any missing template files. Existing files are left untouched."""
    created: list[str] = []
    for name, rel in TEMPLATE_TARGETS.items():
        if not (root / rel).exists():
            created.append(write_template(root, name))
    return created


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_init(root: Path, args) -> Report:
    report = Report()
    report.files_created = create_missing(root)
    report.files_checked = len(REQUIRED_FILES)
    report.token_totals = token_totals(root)
    report.warnings = collect_warnings(root)
    report.git_suggestion = git_status.suggested_command("docs: initialize context")

    still_missing = missing_required(root)
    if still_missing:
        report.next_action = (
            "Fill in placeholders, then run 'mdctx check'. Missing: "
            + ", ".join(still_missing)
        )
    elif report.files_created:
        report.next_action = (
            "Replace the placeholders in the new files with your project details."
        )
    else:
        report.next_action = "All context files already exist. Run 'mdctx check'."
    return report


def cmd_check(root: Path, args) -> Report:
    report = Report()
    report.files_checked = len(REQUIRED_FILES)

    missing = missing_required(root)
    for rel in missing:
        report.warnings.append(f"Missing required file: {rel}")

    report.warnings.extend(collect_warnings(root))
    report.token_totals = token_totals(root)

    if missing:
        report.next_action = (
            "Run 'mdctx init' (or 'mdctx refresh --apply') to create missing files."
        )
    elif report.warnings:
        report.next_action = "Address the warnings above, then re-run 'mdctx check'."
    else:
        report.next_action = "Context looks healthy. Nothing to do."
    return report


def cmd_scan(root: Path, args) -> Report:
    files = scan(root, include_archive=False)
    report = Report()
    report.files_checked = len(files)

    print("Tracked context files (archive content not read):")
    print(f"  {'category':<9} {'lines':>6} {'tokens':>8}  path")
    for f in files:
        print(f"  {f.category:<9} {f.lines:>6} {f.tokens:>8,}  {f.rel}")

    report.token_totals = token_totals(root)
    report.warnings = collect_warnings(root)
    report.next_action = "Run 'mdctx tokens' for budget totals, or 'mdctx check'."
    return report


def cmd_tokens(root: Path, args) -> Report:
    report = Report()
    files = scan(root, include_archive=False)
    report.files_checked = len(files)
    report.token_totals = token_totals(root)
    report.warnings = collect_warnings(root)
    report.next_action = "Keep startup docs lean so agents load context cheaply."
    return report


def cmd_refresh(root: Path, args) -> Report:
    report = Report()
    report.files_checked = len(REQUIRED_FILES)
    missing = missing_required(root)

    if args.apply:
        report.files_created = create_missing(root)
        report.git_suggestion = git_status.suggested_command("docs: context update")
    else:
        # Dry run: report what would be created, but change nothing.
        for rel in missing:
            print(f"Would create from template: {rel}")
        if not missing:
            print("Nothing to create. All required files exist.")

    report.warnings = collect_warnings(root)

    # Tokens always available; only added to the printed totals when asked.
    if args.tokens:
        report.token_totals = token_totals(root)

    if not args.apply and missing:
        report.next_action = "Re-run with '--apply' to create the missing files."
    elif report.files_created:
        report.next_action = "Replace placeholders in the new files, then 'mdctx check'."
    elif report.warnings:
        report.next_action = "Address the warnings above."
    else:
        report.next_action = "Context is up to date."
    return report


def cmd_snapshot(root: Path, args) -> Report:
    report = Report()
    snap_dir = root / SNAPSHOT_DIR
    snap_dir.mkdir(parents=True, exist_ok=True)

    stamp = _now_stamp()
    rel = f"{SNAPSHOT_DIR}/{stamp}.md"
    target = root / rel
    target.write_text(SNAPSHOT_TEMPLATE.format(timestamp=stamp), encoding="utf-8")

    report.files_created = [rel]
    report.files_checked = len(scan(root, include_archive=False))
    report.token_totals = token_totals(root)
    report.warnings = collect_warnings(root)
    report.git_suggestion = git_status.suggested_command(f"docs: snapshot {stamp}")
    report.next_action = (
        "Fill in the snapshot, then run 'mdctx rotate' if snapshots pile up."
    )
    return report


def cmd_rotate(root: Path, args) -> Report:
    """Move all but the newest snapshots into the archive."""
    report = Report()
    snap_dir = root / SNAPSHOT_DIR
    keep = SNAPSHOTS_TO_KEEP

    snapshots = sorted(snap_dir.glob("*.md")) if snap_dir.exists() else []
    report.files_checked = len(snapshots)

    if len(snapshots) <= keep:
        report.next_action = (
            f"{len(snapshots)} snapshot(s); nothing to rotate "
            f"(keeping newest {keep})."
        )
        report.token_totals = token_totals(root)
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

    report.token_totals = token_totals(root)
    report.warnings = collect_warnings(root)
    report.git_suggestion = git_status.suggested_command("docs: rotate snapshots")
    report.next_action = (
        f"Moved {len(to_move)} snapshot(s) to the archive. "
        "Archive content is not read by default."
    )
    return report


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
COMMANDS = {
    "init": cmd_init,
    "check": cmd_check,
    "scan": cmd_scan,
    "tokens": cmd_tokens,
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

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "init", parents=[common], help="Create missing context files from templates."
    )
    sub.add_parser(
        "check", parents=[common], help="Check required files exist and are healthy."
    )
    sub.add_parser(
        "scan", parents=[common], help="List tracked context files with stats."
    )
    sub.add_parser("tokens", parents=[common], help="Report estimated token usage.")

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
    print(report.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
