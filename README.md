# CascadeScope

**You changed one thing in your agent system. What breaks?** CascadeScope
answers that question before you ship the change. Give it a system graph
— tools, memory records, plans, decisions, agents, prompts, models,
configs — and a change (a tool update, a memory edit, a prompt or config
change, a model swap), and it returns a ranked scope report: what is
directly affected, what is reachable, what is *actually* affected, what
is provably unaffected, and the smallest set of checks that covers the
affected scope.

Test-impact tools (Chisel, TDAD, GraQle) do blast-radius analysis on
**source code**: which tests cover a changed function. Security scanners
(agent-bom, blastradius) map what a compromised prompt can *reach*:
credentials, files, exfiltration paths. Neither asks the question
CascadeScope asks: when a memory record, a prompt, or a model changes
inside a running multi-agent system, which downstream decisions actually
change their output — and which are merely reachable? Reachable is not
affected, and a naive BFS over-claims the blast radius by 3.8x on our
benchmark. CascadeScope separates the two with edge gates and
attenuation, and scores itself against an independent oracle simulation
that uses each node's own transfer function.

This is the forward direction of
[plan-change-attribution](https://github.com/Amna-Raheeba/plan-change-attribution)
(which finds what *caused* a plan change). CascadeScope asks what a
change *will* affect.

## 1. The idea in 30 seconds

1. Describe the agent system as a directed graph. Nodes are tools,
   memory records, plans, decisions, agents, prompts, models, and
   configs. Edges are dependencies: the target consumes something the
   source produces. Each edge carries an attenuation (how much of a
   change survives the hop) and a gate (which change kinds may cross
   it at all — a model swap does not cross a memory-read edge).
2. Inject the change as a delta at its node (severity 0–1) and
   propagate it: a delta crosses an edge only if the gate allows the
   change kind, and is multiplied by the attenuation at every hop. A
   node is *actually affected* when the arriving delta is at least
   0.10. At each node the strongest incoming path wins.
3. Report five classes: directly affected (hop 1), reachable (forward
   closure), actually affected, reachable-but-unaffected, and provably
   unaffected (outside the closure). Plus blast radius, max cascade
   depth, and overreach (reachable / affected).
4. Compute the regression set: a greedy set cover over the affected
   nodes, where a check on node X covers X and its affected
   successors. Greedy, not proven optimal (set cover is NP-hard), but
   deterministic and, on our benchmark, 43% of the affected scope.

## 2. Quick start

```bash
pip install -e .
python -m cascadescope demo
python -m cascadescope scope --system clinic --node tool_lab_api --kind tool_update
python -m cascadescope scope --system clinic --node mem_guidelines --kind memory_edit --keys sepsis_threshold --format md
python -m cascadescope evaluate --out results
streamlit run app.py
```

```python
from cascadescope.analyze import analyze
from cascadescope.graph import SystemGraph
from cascadescope.models import Change, ChangeKind

graph = SystemGraph.load("data/systems/clinic.json")
change = Change("tool_lab_api", ChangeKind.TOOL_UPDATE, 1.0,
                "Lab API updated: units mg/dL -> mmol/L")
report = analyze(graph, change)
print(report.summary())
# Reachable: 11 | Actually affected: 11 | Blast radius: 0.524
# Greedy regression set: 5 checks, coverage 1.000
```

## 3. Measured results

36 seeded scenarios across 3 hand-built systems (clinic triage, 22
nodes; research assistant, 20 nodes; PHM maintenance, 24 nodes).
The analyzer is scored against an independent oracle that simulates
each node's own transfer function (passthrough, scale, threshold,
keyed, absorbing) to fixpoint. The analyzer never sees the transfer
functions — only the graph's edge gates and attenuation.

| metric | value |
|---|---|
| mean precision (analyzer vs oracle) | 0.6167 |
| median precision | 0.8000 |
| mean recall | 1.0000 |
| mean F1 | 0.6779 |
| median F1 | 0.8889 |
| mean BFS overreach (reachable / oracle-affected) | 3.8027 |
| median BFS overreach | 1.250 |
| mean regression set / affected scope | 0.4334 |
| mean regression-set coverage of oracle-affected nodes | 1.0000 |

Two readings matter. First, **recall 1.000 is structural, not
empirical**: the analyzer is a sound over-approximation — its deltas
are always at least the oracle's, so it cannot miss a real effect.
The honest measurement is therefore precision (0.6167): the price of
soundness. Second, a naive BFS claims 3.8x the truly-affected nodes
on average (median 1.25x); the analyzer's gate/attenuation
propagation is what closes most of that gap.

Regenerate every number with `python scripts/reproduce_results.py`
(it fails if a headline drifts from `results/HEADLINE.md`).

## 4. Where the analyzer over-claims

The six worst-precision scenarios (0.000) are all the same two
failure modes, and both are documented, not tuned away:

- **Key-blindness.** The analyzer does not model which record keys a
  reader uses. A memory edit to an unrelated key (clinic-03: patient
  history, key `insurance_id`; phm-02: baselines, key `humidity`)
  changes nothing downstream in the oracle, but the analyzer claims
  the whole reachable scope. The oracle's `keyed` transfer is what
  blocks it.
- **Threshold-blindness.** A small-severity change (clinic-08,
  research-08: model swap at severity 0.3) never crosses a decision
  node's flip threshold in the oracle, but the analyzer's fixed 0.10
  threshold lets it through.

Fixing either means giving the analyzer the oracle's information —
which would make the evaluation circular. The current design keeps
the separation honest: the analyzer is the cheap thing a team would
actually run before a change, and its over-claims are named.

## 5. Honest limits

- The three systems are hand-built and synthetic, not traces from a
  real agent deployment. Edge gates and attenuations are declared by
  the system author, not learned from data.
- The regression set is greedy set cover: near-minimal, not proven
  minimal.
- The oracle is itself a model — per-node transfer functions are
  declared in the system data, not measured from a real LLM. The
  evaluation measures the analyzer against the oracle, not against
  reality.
- The analyzer assumes a change propagates independently along each
  path (strongest path wins); it does not model two small changes
  combining into one large effect.
- Pure Python, stdlib only, offline, deterministic. No network calls,
  no API keys, no `.env` files.

## 6. Layout

- `cascadescope/` — `models.py` (nodes, edges, changes),
  `graph.py` (system graph, closures, JSON), `analyze.py` (scope
  analysis + regression set), `simulate.py` (oracle + scoring),
  `evaluation.py` (36-scenario harness), `report.py` (Markdown),
  `cli.py` (`demo`, `scope`, `evaluate`).
- `data/systems/` — clinic, research, phm system graphs (JSON).
- `data/scenarios.json` — the 36 seeded change scenarios.
- `notebooks/` — `01_demo_run.py`, `02_evaluation_experiment.py`.
- `examples/` — `demo_clinic.py`, `sample_report.md`.
- `scripts/` — `build_systems.py` (regenerates the data),
  `reproduce_results.py` (regenerates `results/`).
- `results/` — measured aggregates (`evaluation.json`,
  `evaluation.csv`, `evaluation_summary.md`, `HEADLINE.md`).
- `app.py` — Streamlit dashboard: Scope Explorer, Oracle vs
  Analyzer, Evaluation.
- `tests/` — 78 tests, plain `pytest`.
