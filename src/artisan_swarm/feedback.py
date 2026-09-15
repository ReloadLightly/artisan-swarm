"""Fixed feedback, recruitment and review contract; outside program mutation."""
from __future__ import annotations

CONTRACT = {
    "version": "m1-evaluation-1",
    "criteria": [
        "References resolve to the frozen dossier; factual assertions match source scope and locators.",
        "Unknown consent, resources and permissions never become satisfied by prose or a branch change.",
        "Executable prerequisites and dependencies match the stated action, including negotiation versus implementation.",
        "Changed-case decisions respond to the unavailable contribution and explain unaffected work.",
        "Revision answers identified criticism; preserve parent and alternatives, and state new weaknesses.",
        "Retain or reject with concise reasons. A scope reduction or suspension can be defensible.",
        "Software checks do not establish feasibility. Reviews are model judgments, not expert validation.",
    ],
    "selection_rule": "Count distinct blocked or conditional action IDs with actionable critic objections; descending count, then lexicographic candidate ID. No geopolitical score.",
    "development_case": True,
    "held_out": False,
}


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def array(items):
    return {"type": "array", "items": items}


STR = {"type": "string"}
STRINGS = array(STR)
BOOL = {"type": "boolean"}
CRITIC_SCHEMA = obj({
    "id": STR, "reviewer_type": {"enum": ["model_judgment"], "type": "string"},
    "summary": STR,
    "objections": array(obj({"id": STR, "candidate_id": STR, "action_id": STR,
                             "claim_ids": STRINGS, "issue": STR, "suggested_change": STR,
                             "actionable": BOOL})),
    "disagreements": STRINGS,
})
REVIEW_SCHEMA = obj({
    "id": STR, "candidate_id": STR, "reviewer_type": {"enum": ["model_judgment"], "type": "string"},
    "outcome": {"type": "string", "enum": ["retain", "reject"]}, "substantive_repair": BOOL,
    "recommendation": STR, "reasons": STRINGS, "strongest_objection": STR,
    "unresolved_interests": STRINGS, "resource_requirements": STRINGS, "next_evidence": STRINGS,
    "claim_ids": STRINGS,
})


def revision_schema(program_schema):
    return obj({"program": program_schema, "change_summary": STR,
                "feedback_responses": array(obj({"feedback_id": STR, "response": STR})),
                "new_weaknesses": STRINGS})


def select_candidate(programs, executions, criticism):
    rows = []
    for p in programs:
        unresolved = {a["id"] for a in executions[p["id"]]["actions"] if a["status"] in {"blocked", "conditional"}}
        objections = [o for o in criticism["objections"] if o["candidate_id"] == p["id"] and o["actionable"] and o["action_id"] in unresolved]
        actions = sorted({o["action_id"] for o in objections})
        rows.append({"candidate_id": p["id"], "actionable_unresolved_action_ids": actions,
                     "count": len(actions), "feedback_ids": [o["id"] for o in objections]})
    rows.sort(key=lambda row: (-row["count"], row["candidate_id"]))
    return {"selected_id": rows[0]["candidate_id"], "rule": CONTRACT["selection_rule"],
            "ranking": rows, "feedback_ids": rows[0]["feedback_ids"],
            "reason": f"{rows[0]['count']} distinct unresolved actions attracted actionable criticism; lexical tie-break if needed."}
