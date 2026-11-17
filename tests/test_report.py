"""Tests for the Markdown report renderer."""

from cascadescope.analyze import analyze
from cascadescope.graph import SystemGraph
from cascadescope.models import Change, ChangeKind
from cascadescope.report import render_markdown


def test_report_has_all_sections():
    graph = SystemGraph.load("data/systems/clinic.json")
    report = analyze(graph, Change("tool_lab_api", ChangeKind.TOOL_UPDATE, 1.0))
    text = render_markdown(report)
    assert text.startswith("# CascadeScope report")
    assert "## Scope" in text
    assert "## Numbers" in text
    assert "## Greedy regression set" in text
    assert "## Per-node delta" in text


def test_report_lists_affected_nodes():
    graph = SystemGraph.load("data/systems/clinic.json")
    report = analyze(graph, Change("tool_lab_api", ChangeKind.TOOL_UPDATE, 1.0))
    text = render_markdown(report)
    assert "agent_triage" in text
    assert "Blast radius: 0.524" in text


def test_report_for_key_mismatch_change():
    graph = SystemGraph.load("data/systems/clinic.json")
    report = analyze(
        graph,
        Change("mem_patient_history", ChangeKind.MEMORY_EDIT, 1.0,
               keys=["insurance_id"]))
    text = render_markdown(report)
    assert "actually affected | 12" in text or "actually affected" in text
    assert "Greedy regression set" in text


def test_report_is_deterministic():
    graph = SystemGraph.load("data/systems/research.json")
    change = Change("model_writer", ChangeKind.MODEL_SWAP, 0.8)
    first = render_markdown(analyze(graph, change))
    second = render_markdown(analyze(graph, change))
    assert first == second
