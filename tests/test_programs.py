"""Hand-authored unit-test fixtures; never application research-worker outputs."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from artisan_swarm.programs import propose_strategy, validate_program
from artisan_swarm.schemas import ENGINE_VERSION, SCHEMA_VERSION, program_schema, validate_json


def fixture_dossier():
    return {"sources": [{"id": "s1", "title": "Unit test source", "publisher": "Fixture",
                         "url": "https://example.org/fixture", "publication_date": None,
                         "retrieved_at": "2026-09-15T00:00:00Z", "locator": "Fixture paragraph 1"}],
            "claims": [{"id": "c1", "type": "documented_fact", "text": "Fixture evidence only",
                        "source_ids": ["s1"], "locator": "Fixture paragraph 1"},
                       {"id": "a1", "type": "assumption", "text": "Unit test assumptions",
                        "source_ids": [], "locator": "Unit-test scenario definition"},
                       {"id": "u1", "type": "unknown", "text": "Permission is unknown",
                        "source_ids": [], "locator": "Unit-test missing information"}]}


def fixture_case():
    return {"id": "fixture-initial", "title": "Unit test case", "description": "Not research evidence",
            "facts": {"available": True, "permission": None, "authorized": True},
            "fact_claims": {"available": ["a1"], "permission": ["u1"], "authorized": ["a1"]}}


def fixture_action(aid, *, depends_on=None, prerequisites=None, when=None):
    return {"id": aid, "title": f"Fixture {aid}", "description": "Hand-authored unit-test fixture",
            "kind": "preparation", "when": when or {"operator": "all", "tests": []},
            "prerequisites": prerequisites or [], "depends_on": depends_on or [],
            "evidence_refs": ["c1"], "assumption_refs": ["a1"],
            "reconsideration_triggers": ["Fixture input changes"], "fallbacks": []}


def fixture_program():
    return {"schema_version": SCHEMA_VERSION, "engine_version": ENGINE_VERSION,
            "id": "fixture-parent", "title": "Unit test strategy", "architecture": "centralized",
            "rationale": "Hand-authored fixture, not a worker strategy or experiment result.",
            "parent_ids": [], "feedback_ids": [], "evidence_refs": ["c1"], "assumption_refs": ["a1", "u1"],
            "actions": [fixture_action("discuss", prerequisites=[
                {"fact": "authorized", "equals": True, "reason": "Discussion is authorized in fixture"}]),
                fixture_action("prepare", prerequisites=[
                    {"fact": "available", "equals": True, "reason": "Needs fixture contribution"}]),
                fixture_action("process", depends_on=["prepare"], prerequisites=[
                    {"fact": "permission", "equals": True, "reason": "Needs confirmed permission"}]),
                fixture_action("evaluate", depends_on=["process"])]}


class ProgramTests(unittest.TestCase):
    def setUp(self):
        self.case = fixture_case()
        self.dossier = fixture_dossier()
        self.program = fixture_program()

    def statuses(self, case=None, program=None):
        result = propose_strategy(case or self.case, program or self.program)
        return {a["id"]: a["status"] for a in result["actions"]}

    def test_valid_schema_and_program(self):
        validate_json(self.program, program_schema())
        validate_program(self.program, self.dossier, self.case)

    def test_wrong_schema_or_engine_version_rejected(self):
        for key in ("schema_version", "engine_version"):
            with self.subTest(key=key):
                invalid = deepcopy(self.program)
                invalid[key] = "future-unimplemented"
                with self.assertRaises(ValueError):
                    validate_program(invalid, self.dossier, self.case)

    def test_artifact_identifiers_cannot_contain_paths(self):
        for key, invalid in (("id", "../escaped"), ("id", "/absolute"),
                             ("parent_ids", ["../../parent"]), ("feedback_ids", ["bad/id"])):
            with self.subTest(key=key, invalid=invalid):
                program = deepcopy(self.program)
                program[key] = invalid
                with self.assertRaises(ValueError):
                    validate_program(program, self.dossier, self.case)

    def test_unknown_prerequisite_never_ready(self):
        self.assertEqual(self.statuses(), {"discuss": "supported", "prepare": "supported",
                                          "process": "conditional", "evaluate": "conditional"})
        self.case["facts"]["permission"] = False
        self.assertEqual(self.statuses()["process"], "blocked")
        self.case["facts"]["permission"] = True
        self.assertEqual(self.statuses()["process"], "supported")

    def test_unavailable_contribution_blocks_dependents_not_unrelated_work(self):
        self.case["facts"]["available"] = False
        self.assertEqual(self.statuses(), {"discuss": "supported", "prepare": "blocked",
                                          "process": "blocked", "evaluate": "blocked"})
        trace = propose_strategy(self.case, self.program)
        blocked = next(a for a in trace["actions"] if a["id"] == "prepare")
        self.assertEqual(blocked["prerequisites"][0]["actual"], False)
        self.assertEqual(blocked["prerequisites"][0]["claim_refs"], ["a1"])

    def test_guard_all_and_any_three_valued_truth_tables(self):
        action = self.program["actions"][0]
        action["prerequisites"] = []
        action["when"]["tests"] = [{"fact": "available", "equals": True},
                                   {"fact": "permission", "equals": True}]
        for operator, a, b, expected in [
            ("all", True, None, "conditional"), ("all", False, None, "inactive"),
            ("all", True, True, "supported"), ("any", True, None, "supported"),
            ("any", False, None, "conditional"), ("any", False, False, "inactive"),
        ]:
            with self.subTest(operator=operator, a=a, b=b):
                action["when"]["operator"] = operator
                self.case["facts"].update(available=a, permission=b)
                self.assertEqual(self.statuses()["discuss"], expected)

    def test_false_equality_branch_and_inactive_dependency(self):
        self.program["actions"][1]["when"] = {
            "operator": "all", "tests": [{"fact": "available", "equals": False}]}
        self.assertEqual(self.statuses()["prepare"], "inactive")
        self.assertEqual(self.statuses()["process"], "blocked")
        self.case["facts"]["available"] = False
        self.program["actions"][1]["prerequisites"] = []
        self.assertEqual(self.statuses()["prepare"], "supported")

    def test_empty_guard_is_unconditional(self):
        self.program["actions"][0]["when"]["operator"] = "any"
        self.assertEqual(self.statuses()["discuss"], "supported")

    def test_dependency_order_does_not_depend_on_list_order(self):
        expected = self.statuses()
        self.program["actions"].reverse()
        self.assertEqual(self.statuses(), expected)

    def test_cycle_is_rejected_with_trace(self):
        self.program["actions"][1]["depends_on"] = ["evaluate"]
        with self.assertRaisesRegex(ValueError, "dependency cycle:.*prepare"):
            propose_strategy(self.case, self.program)

    def test_invalid_dependencies_fallbacks_and_facts(self):
        for mutation in ("dependency", "fallback", "fact"):
            with self.subTest(mutation=mutation):
                candidate = deepcopy(self.program)
                if mutation == "dependency":
                    candidate["actions"][0]["depends_on"] = ["missing"]
                elif mutation == "fallback":
                    candidate["actions"][0]["fallbacks"] = [{"action_id": "missing", "reason": "fixture"}]
                else:
                    candidate["actions"][0]["prerequisites"][0]["fact"] = "missing"
                with self.assertRaises(ValueError):
                    validate_program(candidate, self.dossier, self.case)

    def test_invalid_claim_and_wrong_epistemic_type(self):
        for reference in ("nonexistent", "u1", "a1"):
            with self.subTest(reference=reference):
                self.program["evidence_refs"] = [reference]
                with self.assertRaises(ValueError):
                    validate_program(self.program, self.dossier, self.case)

    def test_duplicate_action_ids_and_fact_tests_rejected(self):
        self.program["actions"].append(deepcopy(self.program["actions"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate action"):
            propose_strategy(self.case, self.program)
        self.program["actions"].pop()
        self.program["actions"][0]["prerequisites"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate fact"):
            propose_strategy(self.case, self.program)

    def test_fallback_does_not_bypass_target_prerequisites(self):
        self.program["actions"][1]["fallbacks"] = [{"action_id": "process", "reason": "Fixture fallback"}]
        self.case["facts"]["available"] = False
        trace = propose_strategy(self.case, self.program)
        fallback = trace["actions"][1]["fallbacks"][0]
        self.assertTrue(fallback["applicable"])
        self.assertEqual(fallback["status"], "blocked")

    def test_different_scenario_names_and_fact_keys_are_generic(self):
        self.case["id"] = "fixture-water-treatment"
        self.case["facts"] = {"pump_operational": False, "permit_confirmed": None, "meeting_allowed": True}
        mapping = {"available": "pump_operational", "permission": "permit_confirmed", "authorized": "meeting_allowed"}
        self.case["fact_claims"] = {mapping[k]: v for k, v in self.case["fact_claims"].items()}
        for action in self.program["actions"]:
            for test in action["prerequisites"]:
                test["fact"] = mapping[test["fact"]]
        validate_program(self.program, self.dossier, self.case)
        self.assertEqual(self.statuses(), {"discuss": "supported", "prepare": "blocked",
                                          "process": "blocked", "evaluate": "blocked"})

    def test_execution_does_not_mutate_parent_or_case(self):
        original_program, original_case = deepcopy(self.program), deepcopy(self.case)
        propose_strategy(self.case, self.program)
        self.assertEqual(self.program, original_program)
        self.assertEqual(self.case, original_case)

    def test_arbitrary_code_fields_rejected_and_strings_are_inert(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "should-not-exist"
            self.program["rationale"] = f"__import__('pathlib').Path({str(marker)!r}).touch()"
            validate_program(self.program, self.dossier, self.case)
            propose_strategy(self.case, self.program)
            self.assertFalse(marker.exists())
            self.program["python"] = self.program["rationale"]
            with self.assertRaisesRegex(ValueError, "unexpected keys"):
                propose_strategy(self.case, self.program)

    def test_strict_booleans_and_no_expression_language(self):
        self.program["actions"][0]["prerequisites"][0]["equals"] = 1
        with self.assertRaises(ValueError):
            propose_strategy(self.case, self.program)
        self.program["actions"][0]["prerequisites"][0]["equals"] = True
        self.program["actions"][0]["when"]["expression"] = "available or True"
        with self.assertRaises(ValueError):
            propose_strategy(self.case, self.program)

    def test_generic_validator_rejects_unsupported_schema_keyword(self):
        with self.assertRaisesRegex(ValueError, "unsupported schema keywords"):
            validate_json({}, {"type": "object", "oneOf": []})

    def test_generic_validator_checks_required_null_arrays_and_enum(self):
        schema = {"type": "object", "properties": {
            "outcome": {"type": "string", "enum": ["retain", "reject"]},
            "usage": {"type": ["integer", "null"]}},
            "required": ["outcome", "usage"], "additionalProperties": False}
        validate_json({"outcome": "retain", "usage": None}, schema)
        for invalid in ({"outcome": "retain"}, {"outcome": "approve", "usage": 1},
                        {"outcome": "retain", "usage": True}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_json(invalid, schema)


if __name__ == "__main__":
    unittest.main()
