"""Build the three demo systems and the scenario list (data/*.json).

Run: python scripts/build_systems.py
The systems are hand-designed: every node has a transfer function
(the oracle's ground truth) and every edge has an attenuation and a
gate (which change kinds may cross it). The analyzer never sees the
transfer functions — only the gates — so the evaluation measures a
real approximation gap.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SYSTEMS_DIR = HERE / "data" / "systems"
DATA_DIR = HERE / "data"


def node(node_id, kind, label, transfer=None):
    return {"id": node_id, "kind": kind, "label": label,
            "transfer": transfer or {"type": "passthrough"}}


def edge(source, target, edge_type="depends_on", attenuation=1.0, gate=None):
    return {"source": source, "target": target, "edge_type": edge_type,
            "attenuation": attenuation,
            "gate": gate or ["tool_update", "memory_edit", "prompt_change",
                             "model_swap", "config_change"]}


ALL = ["tool_update", "memory_edit", "prompt_change", "model_swap",
       "config_change"]


def clinic():
    nodes = [
        node("model_triage", "model", "Triage LLM",
             {"type": "scale", "factor": 0.9}),
        node("prompt_triage", "prompt", "Triage prompt"),
        node("config_thresholds", "config", "Triage thresholds"),
        node("agent_intake", "agent", "Intake agent"),
        node("tool_vitals", "tool", "Vitals monitor"),
        node("tool_lab_api", "tool", "Lab results API",
             {"type": "scale", "factor": 0.9}),
        node("tool_ehr_lookup", "tool", "EHR lookup",
             {"type": "keyed", "keys": ["allergies", "meds", "history"]}),
        node("mem_patient_history", "memory", "Patient history store",
             {"type": "keyed", "keys": ["allergies", "meds", "history"]}),
        node("mem_guidelines", "memory", "Clinical guidelines store"),
        node("mem_drug_db", "memory", "Drug database",
             {"type": "keyed", "keys": ["dosage", "interactions"]}),
        node("agent_triage", "agent", "Triage agent",
             {"type": "threshold", "threshold": 0.5}),
        node("plan_care", "plan", "Care plan"),
        node("decision_admit", "decision", "Admit decision",
             {"type": "threshold", "threshold": 0.6}),
        node("decision_referral", "decision", "Referral decision",
             {"type": "threshold", "threshold": 0.4}),
        node("tool_pharmacy", "tool", "Pharmacy order tool",
             {"type": "keyed", "keys": ["dosage", "interactions"]}),
        node("agent_pharmacist", "agent", "Pharmacist agent",
             {"type": "keyed", "keys": ["dosage", "interactions"]}),
        node("agent_discharge", "agent", "Discharge agent",
             {"type": "scale", "factor": 0.8}),
        node("decision_discharge", "decision", "Discharge decision",
             {"type": "threshold", "threshold": 0.5}),
        node("tool_billing", "tool", "Billing coder",
             {"type": "scale", "factor": 0.5}),
        node("tool_alerts", "tool", "Alerting tool",
             {"type": "threshold", "threshold": 0.7}),
        node("prompt_discharge", "prompt", "Discharge prompt"),
        node("mem_audit_log", "memory", "Audit log",
             {"type": "absorbing"}),
    ]
    edges = [
        edge("model_triage", "agent_triage", "drives", 0.9, ["model_swap"]),
        edge("prompt_triage", "agent_triage", "drives", 0.9, ["prompt_change"]),
        edge("config_thresholds", "agent_triage", "configures", 0.8,
             ["config_change"]),
        edge("agent_intake", "agent_triage", "hands_off", 1.0),
        edge("tool_vitals", "agent_intake", "feeds", 0.9),
        edge("tool_lab_api", "agent_triage", "feeds", 0.8),
        edge("tool_ehr_lookup", "agent_triage", "feeds", 0.9,
             ),
        edge("mem_patient_history", "tool_ehr_lookup", "read_by", 1.0,
             ["memory_edit"]),
        edge("mem_guidelines", "agent_triage", "read_by", 0.9,
             ["memory_edit"]),
        edge("mem_guidelines", "plan_care", "read_by", 0.9, ["memory_edit"]),
        edge("agent_triage", "plan_care", "writes", 1.0),
        edge("agent_triage", "decision_admit", "feeds", 1.0),
        edge("agent_triage", "tool_alerts", "feeds", 0.9),
        edge("plan_care", "decision_admit", "feeds", 0.9),
        edge("plan_care", "decision_referral", "feeds", 0.8),
        edge("plan_care", "tool_pharmacy", "feeds", 0.9),
        edge("mem_drug_db", "tool_pharmacy", "read_by", 1.0, ["memory_edit"]),
        edge("mem_drug_db", "agent_pharmacist", "read_by", 0.9,
             ["memory_edit"]),
        edge("tool_pharmacy", "agent_pharmacist", "feeds", 0.9,
             ),
        edge("agent_pharmacist", "plan_care", "amends", 0.8),
        edge("decision_admit", "agent_discharge", "gates", 0.8),
        edge("decision_admit", "tool_billing", "feeds", 0.7),
        edge("decision_referral", "agent_discharge", "gates", 0.7),
        edge("agent_discharge", "decision_discharge", "feeds", 0.9),
        edge("prompt_discharge", "agent_discharge", "drives", 0.9,
             ["prompt_change"]),
        edge("decision_discharge", "tool_billing", "feeds", 0.6),
        edge("plan_care", "mem_audit_log", "logged_by", 1.0),
        edge("decision_admit", "mem_audit_log", "logged_by", 1.0),
    ]
    return {"name": "clinic", "nodes": nodes, "edges": edges}


def research():
    nodes = [
        node("model_search", "model", "Search LLM",
             {"type": "scale", "factor": 0.9}),
        node("model_writer", "model", "Writer LLM",
             {"type": "scale", "factor": 0.85}),
        node("prompt_search", "prompt", "Search prompt"),
        node("prompt_writer", "prompt", "Writer prompt"),
        node("config_style", "config", "Citation style config"),
        node("agent_planner", "agent", "Research planner"),
        node("tool_web_search", "tool", "Web search tool",
             {"type": "scale", "factor": 0.9}),
        node("tool_arxiv", "tool", "arXiv lookup tool",
             {"type": "keyed", "keys": ["cs.AI", "cs.LG", "stat.ML"]}),
        node("tool_vector_db", "tool", "Vector DB retrieval",
             {"type": "keyed", "keys": ["embeddings", "chunks"]}),
        node("mem_papers", "memory", "Paper store",
             {"type": "keyed", "keys": ["cs.AI", "cs.LG", "stat.ML"]}),
        node("mem_notes", "memory", "Research notes"),
        node("mem_citations", "memory", "Citation store",
             {"type": "keyed", "keys": ["bibtex", "doi"]}),
        node("agent_searcher", "agent", "Searcher agent",
             {"type": "threshold", "threshold": 0.5}),
        node("plan_outline", "plan", "Report outline"),
        node("agent_writer", "agent", "Writer agent"),
        node("agent_critic", "agent", "Critic agent",
             {"type": "threshold", "threshold": 0.6}),
        node("decision_include", "decision", "Include-paper decision",
             {"type": "threshold", "threshold": 0.4}),
        node("decision_cite", "decision", "Cite decision",
             {"type": "threshold", "threshold": 0.5}),
        node("tool_formatter", "tool", "Formatter tool",
             {"type": "scale", "factor": 0.5}),
        node("mem_audit", "memory", "Audit log", {"type": "absorbing"}),
    ]
    edges = [
        edge("model_search", "agent_searcher", "drives", 0.9, ["model_swap"]),
        edge("model_writer", "agent_writer", "drives", 0.85, ["model_swap"]),
        edge("prompt_search", "agent_searcher", "drives", 0.9,
             ["prompt_change"]),
        edge("prompt_writer", "agent_writer", "drives", 0.9, ["prompt_change"]),
        edge("config_style", "tool_formatter", "configures", 0.8,
             ["config_change"]),
        edge("agent_planner", "agent_searcher", "delegates", 1.0),
        edge("agent_planner", "plan_outline", "writes", 1.0),
        edge("tool_web_search", "agent_searcher", "feeds", 0.9,
             ),
        edge("tool_arxiv", "agent_searcher", "feeds", 0.9,
             ),
        edge("tool_vector_db", "agent_searcher", "feeds", 0.9,
             ),
        edge("mem_papers", "tool_arxiv", "read_by", 1.0, ["memory_edit"]),
        edge("mem_notes", "agent_searcher", "read_by", 0.9, ["memory_edit"]),
        edge("mem_notes", "agent_writer", "read_by", 0.9, ["memory_edit"]),
        edge("agent_searcher", "decision_include", "feeds", 1.0),
        edge("agent_searcher", "plan_outline", "feeds", 0.9),
        edge("decision_include", "agent_writer", "gates", 0.9),
        edge("plan_outline", "agent_writer", "feeds", 1.0),
        edge("agent_writer", "agent_critic", "feeds", 1.0),
        edge("agent_writer", "decision_cite", "feeds", 0.9),
        edge("agent_critic", "agent_writer", "amends", 0.8),
        edge("mem_citations", "decision_cite", "read_by", 1.0,
             ["memory_edit"]),
        edge("decision_cite", "tool_formatter", "feeds", 0.9),
        edge("agent_writer", "tool_formatter", "feeds", 0.8),
        edge("tool_formatter", "mem_audit", "logged_by", 1.0),
        edge("agent_critic", "mem_audit", "logged_by", 1.0),
    ]
    return {"name": "research", "nodes": nodes, "edges": edges}


def phm():
    nodes = [
        node("model_rul", "model", "RUL prediction model",
             {"type": "scale", "factor": 0.9}),
        node("model_anomaly", "model", "Anomaly detection model",
             {"type": "scale", "factor": 0.85}),
        node("prompt_report", "prompt", "Report prompt"),
        node("config_thresholds", "config", "Alert thresholds"),
        node("agent_monitor", "agent", "Monitoring agent"),
        node("tool_vibration", "tool", "Vibration sensor feed",
             {"type": "scale", "factor": 0.9}),
        node("tool_temperature", "tool", "Temperature sensor feed"),
        node("tool_logs", "tool", "System log reader",
             {"type": "keyed", "keys": ["errors", "warnings"]}),
        node("mem_baselines", "memory", "Sensor baselines",
             {"type": "keyed", "keys": ["vibration", "temperature"]}),
        node("mem_failure_modes", "memory", "Failure-mode library",
             {"type": "keyed", "keys": ["bearing", "motor", "pump"]}),
        node("mem_maintenance_history", "memory", "Maintenance history",
             {"type": "keyed", "keys": ["repairs", "replacements"]}),
        node("agent_diagnoser", "agent", "Diagnoser agent",
             {"type": "threshold", "threshold": 0.5}),
        node("plan_maintenance", "plan", "Maintenance plan"),
        node("decision_replace", "decision", "Replace-part decision",
             {"type": "threshold", "threshold": 0.6}),
        node("decision_schedule", "decision", "Schedule decision",
             {"type": "threshold", "threshold": 0.4}),
        node("decision_escalate", "decision", "Escalate decision",
             {"type": "threshold", "threshold": 0.7}),
        node("tool_workorder", "tool", "Work-order tool"),
        node("tool_inventory", "tool", "Spare-parts inventory",
             {"type": "keyed", "keys": ["bearing", "motor", "pump"]}),
        node("tool_dashboard", "tool", "Dashboard renderer",
             {"type": "scale", "factor": 0.5}),
        node("agent_scheduler", "agent", "Scheduler agent",
             {"type": "scale", "factor": 0.8}),
        node("agent_planner", "agent", "Maintenance planner agent"),
        node("agent_reporter", "agent", "Reporter agent"),
        node("tool_alerts", "tool", "Alerting tool",
             {"type": "threshold", "threshold": 0.7}),
        node("mem_audit", "memory", "Audit log", {"type": "absorbing"}),
    ]
    edges = [
        edge("model_rul", "agent_diagnoser", "drives", 0.9, ["model_swap"]),
        edge("model_anomaly", "agent_monitor", "drives", 0.85,
             ["model_swap"]),
        edge("config_thresholds", "agent_monitor", "configures", 0.8,
             ["config_change"]),
        edge("config_thresholds", "decision_escalate", "configures", 0.8,
             ["config_change"]),
        edge("tool_vibration", "agent_monitor", "feeds", 0.9),
        edge("tool_temperature", "agent_monitor", "feeds", 0.9,
             ),
        edge("tool_logs", "agent_monitor", "feeds", 0.9,
             ),
        edge("mem_baselines", "tool_vibration", "read_by", 1.0,
             ["memory_edit"]),
        edge("mem_baselines", "tool_temperature", "read_by", 1.0,
             ["memory_edit"]),
        edge("agent_monitor", "agent_diagnoser", "feeds", 1.0),
        edge("agent_monitor", "decision_escalate", "feeds", 0.9),
        edge("mem_failure_modes", "agent_diagnoser", "read_by", 0.9,
             ["memory_edit"]),
        edge("mem_maintenance_history", "agent_planner", "read_by", 0.9,
             ["memory_edit"]),
        edge("agent_diagnoser", "plan_maintenance", "writes", 1.0),
        edge("agent_diagnoser", "decision_replace", "feeds", 1.0),
        edge("plan_maintenance", "decision_schedule", "feeds", 0.9),
        edge("plan_maintenance", "decision_replace", "feeds", 0.9),
        edge("decision_replace", "tool_workorder", "feeds", 0.9),
        edge("decision_replace", "tool_inventory", "feeds", 0.8),
        edge("mem_failure_modes", "tool_inventory", "read_by", 1.0,
             ["memory_edit"]),
        edge("decision_schedule", "agent_scheduler", "gates", 0.9),
        edge("agent_scheduler", "agent_planner", "feeds", 0.8),
        edge("agent_planner", "plan_maintenance", "amends", 0.9),
        edge("plan_maintenance", "agent_reporter", "feeds", 0.9),
        edge("prompt_report", "agent_reporter", "drives", 0.9,
             ["prompt_change"]),
        edge("agent_reporter", "tool_dashboard", "feeds", 0.8),
        edge("decision_escalate", "tool_alerts", "feeds", 0.9),
        edge("agent_monitor", "tool_alerts", "feeds", 0.9),
        edge("plan_maintenance", "mem_audit", "logged_by", 1.0),
        edge("decision_replace", "mem_audit", "logged_by", 1.0),
    ]
    return {"name": "phm", "nodes": nodes, "edges": edges}


def scenario(sid, system, node_id, kind, severity, description, keys=None):
    return {
        "id": sid,
        "system": system,
        "change": {
            "node_id": node_id,
            "kind": kind,
            "severity": severity,
            "description": description,
            "keys": keys or [],
        },
    }


def scenarios():
    out = []
    # Clinic: 12 scenarios.
    out += [
        scenario("clinic-01", "clinic", "mem_guidelines", "memory_edit",
                 1.0, "Guideline memory updated: sepsis threshold lowered",
                 ["sepsis_threshold"]),
        scenario("clinic-02", "clinic", "mem_patient_history", "memory_edit",
                 1.0, "Patient history edited: allergy added",
                 ["allergies"]),
        scenario("clinic-03", "clinic", "mem_patient_history", "memory_edit",
                 1.0, "Patient history edited: unrelated key changed",
                 ["insurance_id"]),
        scenario("clinic-04", "clinic", "mem_drug_db", "memory_edit",
                 1.0, "Drug DB edited: dosage changed", ["dosage"]),
        scenario("clinic-05", "clinic", "mem_drug_db", "memory_edit",
                 1.0, "Drug DB edited: supplier note changed",
                 ["supplier"]),
        scenario("clinic-06", "clinic", "tool_lab_api", "tool_update",
                 1.0, "Lab API updated: units mg/dL -> mmol/L"),
        scenario("clinic-07", "clinic", "model_triage", "model_swap",
                 0.8, "Triage model swapped to distilled model"),
        scenario("clinic-08", "clinic", "model_triage", "model_swap",
                 0.3, "Triage model swapped, small behaviour delta"),
        scenario("clinic-09", "clinic", "prompt_triage", "prompt_change",
                 1.0, "Triage prompt rewritten"),
        scenario("clinic-10", "clinic", "config_thresholds", "config_change",
                 1.0, "Triage thresholds reconfigured"),
        scenario("clinic-11", "clinic", "mem_guidelines", "memory_edit",
                 0.3, "Guideline memory: minor wording edit",
                 ["sepsis_threshold"]),
        scenario("clinic-12", "clinic", "tool_vitals", "tool_update",
                 1.0, "Vitals monitor firmware updated"),
    ]
    # Research: 12 scenarios.
    out += [
        scenario("research-01", "research", "mem_papers", "memory_edit",
                 1.0, "Paper store edited: cs.AI paper added", ["cs.AI"]),
        scenario("research-02", "research", "mem_papers", "memory_edit",
                 1.0, "Paper store edited: unrelated field changed",
                 ["cs.CV"]),
        scenario("research-03", "research", "mem_citations", "memory_edit",
                 1.0, "Citation store edited: DOI corrected", ["doi"]),
        scenario("research-04", "research", "mem_notes", "memory_edit",
                 1.0, "Research notes edited"),
        scenario("research-05", "research", "tool_arxiv", "tool_update",
                 1.0, "arXiv tool updated: new API version"),
        scenario("research-06", "research", "tool_vector_db", "tool_update",
                 1.0, "Vector DB re-indexed with new embeddings",
                 ["embeddings"]),
        scenario("research-07", "research", "model_writer", "model_swap",
                 0.8, "Writer model swapped"),
        scenario("research-08", "research", "model_search", "model_swap",
                 0.3, "Search model swapped, small behaviour delta"),
        scenario("research-09", "research", "prompt_writer", "prompt_change",
                 1.0, "Writer prompt rewritten"),
        scenario("research-10", "research", "config_style", "config_change",
                 1.0, "Citation style reconfigured"),
        scenario("research-11", "research", "tool_web_search", "tool_update",
                 1.0, "Web search tool updated"),
        scenario("research-12", "research", "mem_notes", "memory_edit",
                 0.3, "Research notes: minor edit"),
    ]
    # PHM: 12 scenarios.
    out += [
        scenario("phm-01", "phm", "mem_baselines", "memory_edit",
                 1.0, "Sensor baselines recalibrated: vibration",
                 ["vibration"]),
        scenario("phm-02", "phm", "mem_baselines", "memory_edit",
                 1.0, "Sensor baselines edited: unrelated key",
                 ["humidity"]),
        scenario("phm-03", "phm", "mem_failure_modes", "memory_edit",
                 1.0, "Failure-mode library: bearing mode updated",
                 ["bearing"]),
        scenario("phm-04", "phm", "mem_maintenance_history", "memory_edit",
                 1.0, "Maintenance history: repair record added",
                 ["repairs"]),
        scenario("phm-05", "phm", "tool_vibration", "tool_update",
                 1.0, "Vibration feed updated: sampling rate doubled"),
        scenario("phm-06", "phm", "tool_logs", "tool_update",
                 1.0, "Log reader updated"),
        scenario("phm-07", "phm", "model_rul", "model_swap",
                 0.8, "RUL model swapped to a retrained version"),
        scenario("phm-08", "phm", "model_anomaly", "model_swap",
                 0.3, "Anomaly model swapped, small behaviour delta"),
        scenario("phm-09", "phm", "prompt_report", "prompt_change",
                 1.0, "Report prompt rewritten"),
        scenario("phm-10", "phm", "config_thresholds", "config_change",
                 1.0, "Alert thresholds reconfigured"),
        scenario("phm-11", "phm", "mem_failure_modes", "memory_edit",
                 0.3, "Failure-mode library: minor note edit",
                 ["bearing"]),
        scenario("phm-12", "phm", "tool_temperature", "tool_update",
                 1.0, "Temperature feed updated"),
    ]
    return out


def main():
    SYSTEMS_DIR.mkdir(parents=True, exist_ok=True)
    for system in (clinic(), research(), phm()):
        path = SYSTEMS_DIR / (system["name"] + ".json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(system, handle, indent=2)
            handle.write("\n")
        print("wrote " + str(path) + " (%d nodes, %d edges)"
              % (len(system["nodes"]), len(system["edges"])))
    with open(DATA_DIR / "scenarios.json", "w", encoding="utf-8") as handle:
        json.dump({"scenarios": scenarios()}, handle, indent=2)
        handle.write("\n")
    print("wrote scenarios.json (36 scenarios)")


if __name__ == "__main__":
    main()
