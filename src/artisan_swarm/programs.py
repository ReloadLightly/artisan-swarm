"""Constrained, versioned strategy programs with three-valued dependencies.

Programs only compare named external case facts to booleans. Their strings are
explanatory data; no generated code, paths, imports, or external actions execute.
A supported action means its modeled prerequisites pass, not that a real-world
institution has consented or that the action has been carried out.
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict

from .evidence import validate_case, validate_dossier
from .schemas import ENGINE_VERSION, program_schema, validate_json

Truth = Literal["true", "false", "unknown"]
Status = Literal["supported", "blocked", "conditional", "inactive"]


class DecisionProposal(TypedDict):
    program_id: str
    case_id: str
    engine_version: str
    actions: list[dict[str, Any]]
    summary: dict[str, list[str]]


def _structure(program: dict[str, Any], case: dict[str, Any]) -> list[str]:
    """Check a closed expression language and return dependency order."""
    validate_json(program, program_schema())
    if not isinstance(case, dict) or not isinstance(case.get("facts"), dict):
        raise ValueError("case.facts: expected object")
    if not isinstance(case.get("id"), str) or not case["id"]:
        raise ValueError("case.id: expected nonempty string")
    for fact, value in case["facts"].items():
        if not isinstance(fact, str) or not fact or not (value is None or isinstance(value, bool)):
            raise ValueError("case.facts: expected named true, false, or null values")
    actions = {action["id"]: action for action in program["actions"]}
    if len(actions) != len(program["actions"]):
        raise ValueError("program.actions: duplicate action IDs")
    if program["id"] in program["parent_ids"]:
        raise ValueError("program.parent_ids: program cannot be its own parent")
    for action in program["actions"]:
        aid = action["id"]
        for block, tests in (("when.tests", action["when"]["tests"]),
                             ("prerequisites", action["prerequisites"])):
            names = [test["fact"] for test in tests]
            if len(set(names)) != len(names):
                raise ValueError(f"action {aid}.{block}: duplicate fact tests")
            for name in names:
                if name not in case["facts"]:
                    raise ValueError(f"action {aid}.{block}: invalid fact reference {name}")
        for reference in action["depends_on"]:
            if reference not in actions:
                raise ValueError(f"action {aid}: invalid dependency reference {reference}")
        for fallback in action["fallbacks"]:
            if fallback["action_id"] not in actions or fallback["action_id"] == aid:
                raise ValueError(f"action {aid}: invalid fallback reference {fallback['action_id']}")
    order: list[str] = []
    visiting: list[str] = []
    done: set[str] = set()

    def visit(aid: str) -> None:
        if aid in visiting:
            cycle = visiting[visiting.index(aid):] + [aid]
            raise ValueError("dependency cycle: " + " -> ".join(cycle))
        if aid in done:
            return
        visiting.append(aid)
        for dependency in actions[aid]["depends_on"]:
            visit(dependency)
        visiting.pop()
        done.add(aid)
        order.append(aid)

    for aid in actions:
        visit(aid)
    return order


def validate_program(program: dict[str, Any], dossier: dict[str, Any],
                     case: dict[str, Any]) -> None:
    """Validate schema, typed evidence, external fact refs, and dependencies.

    Archive-level parent and feedback existence is checked by the orchestrator;
    this validator has no authority to change the dossier or candidate program.
    """
    validate_dossier(dossier)
    validate_case(case, dossier)
    _structure(program, case)
    claims = {claim["id"]: claim for claim in dossier["claims"]}
    records = [("program", program)] + [(f"action {a['id']}", a) for a in program["actions"]]
    cited = set()
    for where, record in records:
        for key, allowed in (("evidence_refs", {"documented_fact", "interpretation"}),
                             ("assumption_refs", {"assumption", "unknown"})):
            for reference in record[key]:
                if reference not in claims:
                    raise ValueError(f"{where}.{key}: invalid claim reference {reference}")
                if claims[reference]["type"] not in allowed:
                    raise ValueError(f"{where}.{key}: wrong epistemic type for {reference}")
                cited.add(reference)
    if not cited:
        raise ValueError("program: at least one evidence or assumption reference required")


def _test(test: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    actual = case["facts"][test["fact"]]
    value: Truth = "unknown" if actual is None else "true" if actual is test["equals"] else "false"
    result = {"fact": test["fact"], "expected": test["equals"], "actual": actual,
              "value": value, "claim_refs": list(case.get("fact_claims", {}).get(test["fact"], []))}
    if "reason" in test:
        result["reason"] = test["reason"]
    return result


def _combine(values: list[Truth], operator: str) -> Truth:
    # Empty guards deliberately mean unconditional for either spelling.
    if not values:
        return "true"
    if operator == "all":
        return "false" if "false" in values else "unknown" if "unknown" in values else "true"
    return "true" if "true" in values else "unknown" if "unknown" in values else "false"


def propose_strategy(case_state: dict[str, Any], strategy_program: dict[str, Any]) -> DecisionProposal:
    """Execute fixed case facts through a strategy and return an inspectable trace.

    A false guard makes an action inactive. A false prerequisite, blocked
    dependency, or inactive dependency blocks an enabled action. An unknown
    guard/prerequisite or conditional dependency keeps it conditional. Only
    an enabled action with all prerequisites/dependencies satisfied is supported.
    Prerequisites express case facts, not results of executing preceding actions.
    All statuses are modeled recommendations; this function performs no actions.
    """
    order = _structure(strategy_program, case_state)
    actions = {action["id"]: action for action in strategy_program["actions"]}
    decisions: dict[str, dict[str, Any]] = {}
    for aid in order:
        action = actions[aid]
        tests = [_test(test, case_state) for test in action["when"]["tests"]]
        condition = _combine([test["value"] for test in tests], action["when"]["operator"])
        prerequisites = [_test(test, case_state) for test in action["prerequisites"]]
        dependencies = [{"action_id": dep, "status": decisions[dep]["status"]}
                        for dep in action["depends_on"]]
        reasons = []
        if condition == "false":
            status: Status = "inactive"
            reasons.append("Action guard is false in this case.")
        else:
            failed = [item for item in prerequisites if item["value"] == "false"]
            unknown = [item for item in prerequisites if item["value"] == "unknown"]
            failed_dependencies = [item for item in dependencies if item["status"] in {"blocked", "inactive"}]
            pending_dependencies = [item for item in dependencies if item["status"] == "conditional"]
            if failed or failed_dependencies:
                status = "blocked"
            elif condition == "unknown" or unknown or pending_dependencies:
                status = "conditional"
            else:
                status = "supported"
            if condition == "unknown":
                reasons.append("Action guard is unknown; clarification is required.")
            for item in failed:
                reasons.append(f"Prerequisite {item['fact']} expected {str(item['expected']).lower()}, "
                               f"observed {str(item['actual']).lower()}: {item['reason']}")
            for item in unknown:
                reasons.append(f"Prerequisite {item['fact']} is unknown: {item['reason']}")
            for item in failed_dependencies + pending_dependencies:
                reasons.append(f"Dependency {item['action_id']} is {item['status']}.")
            if status == "supported":
                reasons.append("All modeled guards, prerequisites, and dependencies are satisfied.")
        decisions[aid] = {
            "id": aid, "title": action["title"], "kind": action["kind"],
            "status": status, "reasons": reasons,
            "condition": {"operator": action["when"]["operator"], "value": condition, "tests": tests},
            "prerequisites": prerequisites, "dependencies": dependencies,
            "evidence_refs": list(action["evidence_refs"]), "assumption_refs": list(action["assumption_refs"]),
            "reconsideration_triggers": list(action["reconsideration_triggers"]), "fallbacks": [],
        }
    # Fallbacks are references for inspection. They do not bypass any condition
    # or imply that the target action was executed; its own status is preserved.
    for aid, decision in decisions.items():
        decision["fallbacks"] = [dict(fallback, status=decisions[fallback["action_id"]]["status"],
                                      applicable=decision["status"] in {"blocked", "conditional"})
                                 for fallback in actions[aid]["fallbacks"]]
    ordered_decisions = [decisions[action["id"]] for action in strategy_program["actions"]]
    summary = {status: [a["id"] for a in ordered_decisions if a["status"] == status]
               for status in ("supported", "blocked", "conditional", "inactive")}
    return {"program_id": strategy_program["id"], "case_id": case_state["id"],
            "engine_version": ENGINE_VERSION, "actions": ordered_decisions, "summary": summary}
