"""Tests for the CLI."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from cascadescope.cli import main


def run_cli(*argv):
    return main(list(argv))


def test_demo_exits_zero(capsys):
    assert run_cli("demo") == 0
    out = capsys.readouterr().out
    assert "Blast radius" in out
    assert "Guideline memory" in out


def test_scope_text_output(capsys):
    assert run_cli("scope", "--system", "clinic", "--node", "tool_lab_api",
                   "--kind", "tool_update") == 0
    out = capsys.readouterr().out
    assert "Actually affected: 11" in out


def test_scope_json_output(capsys):
    assert run_cli("scope", "--system", "clinic", "--node", "tool_lab_api",
                   "--kind", "tool_update", "--format", "json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["blast_radius"] == pytest.approx(0.5238, abs=0.001)
    assert len(payload["actually_affected"]) == 11
    assert payload["oracle_affected"]


def test_scope_markdown_output(capsys):
    assert run_cli("scope", "--system", "research", "--node", "mem_notes",
                   "--kind", "memory_edit", "--format", "md") == 0
    out = capsys.readouterr().out
    assert out.startswith("# CascadeScope report")


def test_scope_writes_report_file(tmp_path):
    out_path = tmp_path / "report.md"
    assert run_cli("scope", "--system", "phm", "--node", "tool_vibration",
                   "--kind", "tool_update", "--out", str(out_path)) == 0
    assert out_path.exists()
    assert "# CascadeScope report" in out_path.read_text()


def test_scope_with_keys(capsys):
    assert run_cli("scope", "--system", "clinic", "--node",
                   "mem_patient_history", "--kind", "memory_edit",
                   "--keys", "allergies") == 0
    out = capsys.readouterr().out
    assert "Actually affected" in out


def test_scope_rejects_unknown_system():
    with pytest.raises(FileNotFoundError):
        run_cli("scope", "--system", "nope", "--node", "a",
                "--kind", "tool_update")


def test_evaluate_writes_results(tmp_path):
    assert run_cli("evaluate", "--out", str(tmp_path)) == 0
    assert (tmp_path / "evaluation.json").exists()
    assert (tmp_path / "evaluation.csv").exists()
    assert (tmp_path / "evaluation_summary.md").exists()
    data = json.loads((tmp_path / "evaluation.json").read_text())
    assert data["aggregate"]["scenarios"] == 36


def test_module_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "cascadescope", "demo"],
        capture_output=True, text=True, cwd=Path.cwd())
    assert result.returncode == 0
    assert "Blast radius" in result.stdout
