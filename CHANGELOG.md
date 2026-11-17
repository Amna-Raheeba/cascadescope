# Changelog

## 0.1.0 — 2026-11-17

- First release.
- Forward scope analysis: directly affected, reachable, actually
  affected, reachable-but-unaffected, provably unaffected, blast
  radius, max cascade depth, overreach.
- Greedy regression set by set cover (mean 43.3% of the
  affected scope, 100% coverage of oracle-affected nodes).
- Independent oracle simulator with per-node transfer functions
  (passthrough, scale, threshold, keyed, absorbing) used as ground
  truth for the evaluation.
- Three hand-built agent systems (clinic triage, research assistant,
  PHM maintenance; 20–24 nodes each) and 36 seeded scenarios.
- Streamlit dashboard (Scope Explorer, Oracle vs Analyzer,
  Evaluation), demo + evaluation notebooks, reproduce script.
