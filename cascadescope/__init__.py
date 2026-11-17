"""CascadeScope: forward blast-radius analysis for agentic systems.

Given a change (tool update, memory edit, prompt/config change, model
swap), compute what it can cascade into across an agent system:
which downstream tools, memory records, plans, and decisions are
reachable, which are actually affected, and which are provably
unaffected — plus the smallest regression set that covers the
affected scope.
"""

from .analyze import ScopeReport, analyze, regression_set
from .graph import SystemGraph
from .models import Change, ChangeKind, Edge, Node, NodeKind
from .simulate import OracleResult, oracle_affected

__all__ = [
    "Change",
    "ChangeKind",
    "Edge",
    "Node",
    "NodeKind",
    "OracleResult",
    "ScopeReport",
    "SystemGraph",
    "analyze",
    "oracle_affected",
    "regression_set",
]

__version__ = "0.1.0"
