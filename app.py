"""CascadeScope dashboard.

Run: streamlit run app.py
Tab 1 — Scope Explorer: pick a system and a change, see the ranked
scope report and the minimal regression set.
Tab 2 — Oracle vs Analyzer: per-scenario precision/recall from the
evaluation results.
Tab 3 — Evaluation: aggregate metrics and the worst-precision
scenarios, i.e. where the analyzer over-claims.
"""

from pathlib import Path

import streamlit as st

from cascadescope.analyze import analyze
from cascadescope.evaluation import run_evaluation
from cascadescope.graph import SystemGraph
from cascadescope.models import Change, ChangeKind
from cascadescope.simulate import oracle_affected, score_analyzer

HERE = Path(__file__).resolve().parent
SYSTEMS_DIR = HERE / "data" / "systems"
SCENARIOS_PATH = HERE / "data" / "scenarios.json"


@st.cache_data
def load_system(name: str) -> SystemGraph:
    return SystemGraph.load(str(SYSTEMS_DIR / (name + ".json")))


@st.cache_data
def load_results():
    return run_evaluation(str(SYSTEMS_DIR), str(SCENARIOS_PATH))


def scope_explorer_tab() -> None:
    st.header("Scope Explorer")
    systems = ["clinic", "research", "phm"]
    system = st.selectbox("System", systems)
    graph = load_system(system)
    node_id = st.selectbox("Changed node", sorted(graph.nodes))
    kind = st.selectbox("Change kind", [k.value for k in ChangeKind])
    severity = st.slider("Severity", 0.05, 1.0, 1.0, 0.05)
    keys_text = st.text_input("Keys touched (memory edits, comma-separated)", "")
    keys = [k.strip() for k in keys_text.split(",") if k.strip()]
    if st.button("Compute scope"):
        change = Change(node_id, ChangeKind(kind), severity,
                        kind + " on " + node_id, keys=keys)
        report = analyze(graph, change)
        oracle = oracle_affected(graph, change)
        scores = score_analyzer(report.actually_affected, oracle.affected)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Reachable", len(report.reachable))
        col2.metric("Actually affected", len(report.actually_affected))
        col3.metric("Blast radius", "%.3f" % report.blast_radius)
        col4.metric("Max depth", report.max_depth)
        st.subheader("Ranked scope")
        st.table({
            "class": ["directly affected", "actually affected",
                      "reachable but unaffected", "provably unaffected"],
            "count": [len(report.directly_affected),
                      len(report.actually_affected),
                      len(report.reachable_but_unaffected),
                      len(report.unaffected)],
            "nodes": [", ".join(report.directly_affected),
                      ", ".join(report.actually_affected),
                      ", ".join(report.reachable_but_unaffected),
                      ", ".join(report.unaffected)],
        })
        st.subheader("Greedy regression set")
        st.write(", ".join(report.regression_set)
                 or "No checks needed — nothing affected.")
        st.write("Coverage of the affected scope: %.3f"
                 % report.regression_coverage)
        st.subheader("Oracle comparison")
        st.write("Oracle-affected: %d — analyzer precision %.3f, "
                 "recall %.3f" % (len(oracle.affected),
                                  scores["precision"], scores["recall"]))


def oracle_tab() -> None:
    st.header("Oracle vs Analyzer")
    results = load_results()
    rows = results["rows"]
    st.write("36 seeded scenarios across 3 systems. The analyzer is "
             "scored against an independent oracle simulation that uses "
             "each node's own transfer function.")
    display = [{
        "scenario": r["scenario"],
        "system": r["system"],
        "analyzer": r["analyzer_affected"],
        "oracle": r["oracle_affected"],
        "precision": r["precision"],
        "recall": r["recall"],
        "F1": r["f1"],
        "BFS overreach": r["bfs_overreach"],
        "regression set": r["regression_set_size"],
    } for r in rows]
    st.dataframe(display, use_container_width=True)


def evaluation_tab() -> None:
    st.header("Evaluation")
    results = load_results()
    agg = results["aggregate"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Mean precision", "%.4f" % agg["mean_precision"])
    col2.metric("Mean recall", "%.4f" % agg["mean_recall"])
    col3.metric("Mean F1", "%.4f" % agg["mean_f1"])
    col1.metric("Median precision", "%.4f" % agg["median_precision"])
    col2.metric("Mean BFS overreach", "%.3f" % agg["mean_bfs_overreach"])
    col3.metric("Median BFS overreach", "%.3f" % agg["median_bfs_overreach"])
    st.write("Regression set size / affected scope: %.3f"
             % agg["mean_regression_vs_affected"])
    st.write("Regression-set coverage of oracle-affected nodes: %.4f"
             % agg["mean_oracle_coverage"])
    st.subheader("Where the analyzer over-claims")
    st.write("The analyzer is a sound over-approximation: it never "
             "misses a real effect (recall 1.000), but it cannot see "
             "which record keys a reader uses or a decision node's "
             "flip threshold, so it over-claims on keyed memory reads "
             "and small-severity changes.")
    worst = sorted(results["rows"], key=lambda r: r["precision"])[:6]
    st.table([{"scenario": r["scenario"], "precision": r["precision"],
               "analyzer": r["analyzer_affected"],
               "oracle": r["oracle_affected"], "change": r["change"]}
              for r in worst])


def main() -> None:
    st.title("CascadeScope")
    st.write("Forward blast-radius analysis for agentic systems: what "
             "will a change affect, what is merely reachable, and what "
             "is provably unaffected?")
    tab1, tab2, tab3 = st.tabs(["Scope Explorer", "Oracle vs Analyzer",
                                "Evaluation"])
    with tab1:
        scope_explorer_tab()
    with tab2:
        oracle_tab()
    with tab3:
        evaluation_tab()


if __name__ == "__main__":
    main()
