# CascadeScope headline results

36 seeded scenarios, 3 systems (clinic 22 nodes, research 20 nodes,
PHM 24 nodes). Analyzer scored against the independent oracle.

- mean precision: 0.6167 (median 0.8000)
- mean recall: 1.0000 (structural: the analyzer is a sound
  over-approximation, so recall 1.0 is guaranteed, not measured)
- mean F1: 0.6779 (median 0.8889)
- mean BFS overreach: 3.8027 (median 1.250)
- mean regression set / affected scope: 0.4334
- mean regression-set coverage of oracle-affected nodes: 1.0000

Regenerate with: python scripts/reproduce_results.py
