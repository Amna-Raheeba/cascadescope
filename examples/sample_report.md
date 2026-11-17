# CascadeScope report

**System:** clinic

**Change:** memory_edit on mem_guidelines

## Scope

| class | count | nodes |
|---|---|---|
| directly affected (hop 1) | 2 | agent_triage, plan_care |
| reachable (forward closure) | 11 | agent_triage, plan_care, decision_admit, decision_referral, mem_audit_log, tool_alerts, tool_pharmacy, agent_discharge, agent_pharmacist, tool_billing, decision_discharge |
| actually affected | 11 | agent_triage, plan_care, decision_admit, decision_referral, mem_audit_log, tool_alerts, tool_pharmacy, agent_discharge, agent_pharmacist, tool_billing, decision_discharge |
| reachable but unaffected | 0 |  |
| provably unaffected | 10 | agent_intake, config_thresholds, mem_drug_db, mem_patient_history, model_triage, prompt_discharge, prompt_triage, tool_ehr_lookup, tool_lab_api, tool_vitals |

## Numbers

- Blast radius: 0.524
- Max cascade depth: 4
- Overreach (reachable / affected): 1.00

## Greedy regression set

Checks: agent_discharge, agent_triage, decision_admit, plan_care, tool_pharmacy

Coverage of the affected scope: 1.000

## Per-node delta

- agent_triage (hop 1, delta 0.900)
- plan_care (hop 1, delta 0.900)
- decision_admit (hop 2, delta 0.900)
- decision_referral (hop 2, delta 0.720)
- mem_audit_log (hop 2, delta 0.900)
- tool_alerts (hop 2, delta 0.810)
- tool_pharmacy (hop 2, delta 0.810)
- agent_discharge (hop 3, delta 0.720)
- agent_pharmacist (hop 3, delta 0.729)
- tool_billing (hop 3, delta 0.630)
- decision_discharge (hop 4, delta 0.648)
