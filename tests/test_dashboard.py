"""Tests for the Streamlit dashboard (AppTest)."""

import pytest

pytest.importorskip("streamlit")

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_dashboard_renders_three_tabs():
    app = AppTest.from_file(APP_PATH, default_timeout=120)
    app.run()
    assert not app.exception
    assert app.title[0].value == "CascadeScope"
    assert len(app.tabs) == 3
    assert app.tabs[0].label == "Scope Explorer"
    assert app.tabs[1].label == "Oracle vs Analyzer"
    assert app.tabs[2].label == "Evaluation"


def test_scope_explorer_computes_a_report():
    app = AppTest.from_file(APP_PATH, default_timeout=120)
    app.run()
    assert not app.exception
    # Default selections: clinic / first node / first kind. Run it.
    app.button[0].click().run()
    assert not app.exception
    assert any("Actually affected" in str(m.label) for m in app.metric)
    assert any("Reachable" in str(m.label) for m in app.metric)


def test_evaluation_tab_shows_aggregate():
    # All tab bodies execute on run (Streamlit renders every tab's
    # widgets); the Evaluation tab's metrics are present without
    # switching tabs.
    app = AppTest.from_file(APP_PATH, default_timeout=120)
    app.run()
    assert not app.exception
    assert any("Mean precision" in str(m.label) for m in app.metric)
    assert any("Median BFS overreach" in str(m.label) for m in app.metric)
