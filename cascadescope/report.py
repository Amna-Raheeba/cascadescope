"""Markdown rendering of a scope report."""

from __future__ import annotations

from .analyze import ScopeReport


def render_markdown(report: ScopeReport) -> str:
    """Render a scope report as a Markdown document."""
    lines = [
        "# CascadeScope report",
        "",
        "**System:** " + report.system,
        "",
        "**Change:** " + report.change.description,
        "",
        "## Scope",
        "",
        "| class | count | nodes |",
        "|---|---|---|",
        "| directly affected (hop 1) | "
        + str(len(report.directly_affected))
        + " | " + ", ".join(report.directly_affected) + " |",
        "| reachable (forward closure) | "
        + str(len(report.reachable))
        + " | " + ", ".join(report.reachable) + " |",
        "| actually affected | "
        + str(len(report.actually_affected))
        + " | " + ", ".join(report.actually_affected) + " |",
        "| reachable but unaffected | "
        + str(len(report.reachable_but_unaffected))
        + " | " + ", ".join(report.reachable_but_unaffected) + " |",
        "| provably unaffected | "
        + str(len(report.unaffected))
        + " | " + ", ".join(report.unaffected) + " |",
        "",
        "## Numbers",
        "",
        "- Blast radius: %.3f" % report.blast_radius,
        "- Max cascade depth: " + str(report.max_depth),
        "- Overreach (reachable / affected): %.2f" % report.overreach,
        "",
        "## Greedy regression set",
        "",
        "Checks: " + ", ".join(report.regression_set),
        "",
        "Coverage of the affected scope: %.3f" % report.regression_coverage,
        "",
        "## Per-node delta",
        "",
    ]
    for node_id in report.actually_affected:
        hop = report.hop_distance.get(node_id, 0)
        delta = report.delta.get(node_id, 0.0)
        lines.append(
            "- " + node_id + " (hop " + str(hop) + ", delta %.3f)" % delta
        )
    lines.append("")
    return "\n".join(lines)
