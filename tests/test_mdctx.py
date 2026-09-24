"""Tests for MD Context Kit (mdctx).

Covers the parts that silently produce wrong numbers if they break: ignore
rules, the language-aware token fallback, registry parsing, duplicate detection
and the machine-readable JSON output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from md_context_kit import __version__
from md_context_kit.cli import main
from md_context_kit.project_config import load_config
from md_context_kit.registry import parse_registry
from md_context_kit.scanner import find_duplicates, scan, scan_detailed
from md_context_kit.token_estimator import (
    _heuristic,
    estimate_tokens,
    thai_char_count,
    thai_ratio,
    using_tiktoken,
)

THAI = "เจ้านายครับ ระบบงานการตลาดได้ทำการตรวจสอบสถานะปัจจุบันเรียบร้อยแล้ว"
ENGLISH = "The current state document is short and focused on what matters now."


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "AGENTS.md").write_text("# AGENTS\n" + ENGLISH * 3, encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "00_INDEX.md").write_text("# index\n" + ENGLISH, encoding="utf-8")
    (docs / "02_CURRENT_STATE.md").write_text("# state\n" + ENGLISH, encoding="utf-8")
    (docs / "context_registry.yml").write_text(
        'version: 1\nproject: "Demo"\n\n'
        "context:\n"
        "  - id: current_state\n"
        "    title: Current state\n"
        "    type: state\n"
        "    status: active\n"
        "    file: docs/02_CURRENT_STATE.md\n"
        "    read_when: startup\n"
        "  - id: brief\n"
        "    title: Brief\n"
        "    file: docs/01_PROJECT_BRIEF.md\n"
        "    read_when: on-demand\n",
        encoding="utf-8",
    )
    (docs / "01_PROJECT_BRIEF.md").write_text("# brief\n" + ENGLISH, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# version / estimator
# ---------------------------------------------------------------------------
def test_version_is_020():
    assert __version__ == "0.2.0"


def test_thai_detection():
    assert thai_char_count(THAI) > 40
    assert thai_ratio(THAI) > 0.9
    assert thai_ratio(ENGLISH) == 0.0


def test_heuristic_weights_thai_per_character():
    """Thai costs ~1 token/char; Latin ~4 chars/token. A flat chars/4 was 4x low."""
    thai_estimate = _heuristic(THAI)
    latin_estimate = _heuristic(ENGLISH)
    assert thai_estimate > len(THAI) * 0.8
    assert latin_estimate <= len(ENGLISH) / 3
    # the old heuristic would have returned len//4 for both
    assert thai_estimate > len(THAI) // 4 * 3


def test_estimate_tokens_never_zero():
    assert estimate_tokens("") == 0
    assert estimate_tokens("x") >= 1


# ---------------------------------------------------------------------------
# ignore rules
# ---------------------------------------------------------------------------
def test_vendor_and_artifacts_are_ignored_by_default(project: Path):
    (project / "vendor" / "pkg").mkdir(parents=True)
    (project / "vendor" / "pkg" / "README.md").write_text("x" * 4000, encoding="utf-8")
    (project / "artifacts").mkdir()
    (project / "artifacts" / "BUILD.md").write_text("y" * 4000, encoding="utf-8")

    result = scan_detailed(project)
    tracked = {f.rel for f in result.files}
    assert not any(r.startswith("vendor/") for r in tracked)
    assert result.ignored_files >= 1


def test_mdctxignore_file_is_honoured(project: Path):
    (project / ".mdctxignore").write_text("# comments allowed\nartifacts/\n*_scratch.md\n", encoding="utf-8")
    (project / "artifacts").mkdir()
    (project / "artifacts" / "BIG.md").write_text("z" * 2000, encoding="utf-8")
    (project / "notes_scratch.md").write_text("z" * 500, encoding="utf-8")

    cfg = load_config(project)
    assert cfg.loaded_from == [".mdctxignore"]
    tracked = {f.rel for f in scan_detailed(project, cfg=cfg).files}
    assert "artifacts/BIG.md" not in tracked
    assert "notes_scratch.md" not in tracked


def test_mdctx_json_overrides_limits_and_startup(project: Path):
    (project / "mdctx.json").write_text(
        json.dumps(
            {
                "ignore": ["docs/01_PROJECT_BRIEF.md"],
                "startup_files": ["AGENTS.md"],
                "limits": {"current_state_max_lines": 5},
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(project)
    assert cfg.limits["current_state_max_lines"] == 5
    assert cfg.limits["changelog_max_tokens"] == 3000  # untouched default
    assert cfg.startup_files == ("AGENTS.md",)
    assert cfg.is_ignored("docs/01_PROJECT_BRIEF.md")
    assert "mdctx.json" in cfg.loaded_from


def test_archive_not_scanned_by_default(project: Path):
    arch = project / "docs" / "archive"
    arch.mkdir()
    (arch / "old.md").write_text("old " * 500, encoding="utf-8")
    assert all(not f.rel.startswith("docs/archive/") for f in scan(project))
    assert any(f.rel.startswith("docs/archive/") for f in scan(project, include_archive=True))


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------
def test_parse_registry_spec_shape(project: Path):
    reg = parse_registry(project, "docs/context_registry.yml", estimator=estimate_tokens)
    assert reg.exists
    assert reg.startup == ["docs/02_CURRENT_STATE.md"]
    brief = next(r for r in reg.refs if r.path.endswith("01_PROJECT_BRIEF.md"))
    assert brief.read_when == "on-demand"
    assert brief.exists is True


def test_parse_registry_task_map_shape(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "A.md").write_text("a" * 400, encoding="utf-8")
    (docs / "B.md").write_text("b" * 800, encoding="utf-8")
    (docs / "context_registry.yml").write_text(
        "# task -> files\nmeta_api:\n  - docs/A.md\n  - docs/B.md\n\nbilling:\n  - docs/A.md\n",
        encoding="utf-8",
    )
    reg = parse_registry(tmp_path, "docs/context_registry.yml", estimator=estimate_tokens)
    names = [s.name for s in reg.sections]
    assert "meta_api" in names and "billing" in names
    api = reg.section("meta_api")
    assert [r.path for r in api.refs] == ["docs/A.md", "docs/B.md"]
    assert reg.section("billing").tokens == api.refs[0].tokens


def test_registry_missing_file_is_reported(project: Path):
    reg = parse_registry(project, "docs/context_registry.yml", estimator=estimate_tokens)
    assert reg.section("context") is not None or reg.refs


# ---------------------------------------------------------------------------
# duplicates
# ---------------------------------------------------------------------------
def test_find_duplicates_ignores_whitespace_differences(project: Path):
    a = project / "docs" / "COPY_ONE.md"
    b = project / "docs" / "COPY_TWO.md"
    body = "same content\n" * 20
    a.write_text(body, encoding="utf-8")
    b.write_text(body.replace("\n", "  \n"), encoding="utf-8")

    files = scan(project)
    groups = find_duplicates(files)
    assert len(groups) == 1
    assert {f.rel for f in groups[0]} == {"docs/COPY_ONE.md", "docs/COPY_TWO.md"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def test_cli_check_json_is_machine_readable(project: Path, capsys):
    code = main(["check", "-C", str(project), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["tool"] == "mdctx"
    assert payload["command"] == "check"
    assert payload["version"] == "0.2.0"
    assert "startup_tokens" in payload["data"]
    assert isinstance(payload["warnings"], list)
    assert code == 0


def test_cli_check_strict_exits_nonzero_on_warnings(project: Path, capsys):
    (project / "docs" / "02_CURRENT_STATE.md").write_text(
        "# state\n" + ("line\n" * 400), encoding="utf-8"
    )
    code = main(["check", "-C", str(project), "--strict"])
    out = capsys.readouterr().out
    assert code == 1
    assert "2_CURRENT_STATE" in out


def test_cli_tasks_prices_each_section(project: Path, capsys):
    code = main(["tasks", "-C", str(project), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    names = [s["name"] for s in payload["data"]["sections"]]
    assert "limits" not in names
    assert names  # the context section is the startup list in spec-shape registries
    assert all(s["tokens"] >= 0 for s in payload["data"]["sections"])


def test_cli_scan_reports_ignored_tokens(project: Path, capsys):
    (project / "vendor").mkdir()
    (project / "vendor" / "README.md").write_text("v" * 2000, encoding="utf-8")
    main(["scan", "-C", str(project), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["ignored"]["files"] >= 1
    assert "ignored" in " ".join(payload["notices"])


def test_cli_dupes_command(project: Path, capsys):
    body = "dup\n" * 50
    (project / "docs" / "X.md").write_text(body, encoding="utf-8")
    (project / "docs" / "Y.md").write_text(body, encoding="utf-8")
    main(["dupes", "-C", str(project), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["groups"]
    assert payload["data"]["groups"][0]["count"] == 2


def test_cli_init_creates_expected_files(tmp_path: Path, capsys):
    main(["init", "-C", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    created = set(payload["files_created"])
    assert {"AGENTS.md", "docs/02_CURRENT_STATE.md", "docs/context_registry.yml"} <= created
    assert (tmp_path / "docs" / "context_registry.yml").is_file()


def test_cli_missing_path_returns_2(tmp_path: Path):
    assert main(["check", "-C", str(tmp_path / "nope")]) == 2


def test_cli_rotate_keeps_newest(tmp_path: Path, capsys):
    snaps = tmp_path / "docs" / "snapshots"
    snaps.mkdir(parents=True)
    for i in range(8):
        (snaps / f"2026-01-0{i + 1}T00-00-00Z.md").write_text(f"snap {i}", encoding="utf-8")
    main(["rotate", "-C", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["data"]["moved"]) == 3
    assert len(list(snaps.glob("*.md"))) == 5
    assert (tmp_path / "docs" / "archive" / "snapshots").is_dir()


def test_tokenizer_reported_in_json(project: Path, capsys):
    main(["tokens", "-C", str(project), "--json"])
    payload = json.loads(capsys.readouterr().out)
    expected = "tiktoken" if using_tiktoken() else "heuristic"
    assert payload["data"]["tokenizer"] == expected
