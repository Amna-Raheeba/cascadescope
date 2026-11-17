"""Tests for scripts/reproduce_results.py."""

import json
import subprocess
import sys
from pathlib import Path


def test_reproduce_regenerates_results_and_matches_headlines(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/reproduce_results.py"],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Headlines match recorded values" in result.stdout
    data = json.loads(Path("results/evaluation.json").read_text())
    assert data["aggregate"]["scenarios"] == 36
    assert Path("results/evaluation.csv").exists()
    assert Path("results/evaluation_summary.md").exists()


def test_committed_results_match_reproduction():
    # The committed CSV must have one row per scenario.
    rows = Path("results/evaluation.csv").read_text().splitlines()
    assert len(rows) == 37  # header + 36 scenarios
