"""Hand-authored integrity fixtures, not semantic verification or live outputs."""
from copy import deepcopy
import unittest

from artisan_swarm.evidence import apply_disruption, validate_case, validate_dossier
from tests.test_programs import fixture_case, fixture_dossier


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.dossier = fixture_dossier()
        self.case = fixture_case()

    def test_valid_dossier_and_case(self):
        validate_dossier(self.dossier)
        validate_case(self.case, self.dossier)

    def test_missing_source_rejected(self):
        self.dossier["claims"][0]["source_ids"] = ["missing-source"]
        with self.assertRaisesRegex(ValueError, "missing references"):
            validate_dossier(self.dossier)

    def test_no_source_for_fact_and_missing_locator_rejected(self):
        self.dossier["claims"][0]["source_ids"] = []
        with self.assertRaisesRegex(ValueError, "require a source"):
            validate_dossier(self.dossier)
        self.dossier = fixture_dossier()
        self.dossier["claims"][0]["locator"] = ""
        with self.assertRaisesRegex(ValueError, "locator"):
            validate_dossier(self.dossier)

    def test_unknown_and_assumption_remain_valid_without_sources(self):
        self.assertEqual(self.dossier["claims"][1]["source_ids"], [])
        self.assertEqual(self.dossier["claims"][2]["source_ids"], [])
        validate_dossier(self.dossier)

    def test_source_date_must_explicitly_be_unknown_and_retrieval_zoned(self):
        del self.dossier["sources"][0]["publication_date"]
        with self.assertRaisesRegex(ValueError, "publication_date"):
            validate_dossier(self.dossier)
        self.dossier = fixture_dossier()
        self.dossier["sources"][0]["retrieved_at"] = "2026-09-15T00:00:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            validate_dossier(self.dossier)

    def test_unsupported_epistemic_type_rejected(self):
        self.dossier["claims"][0]["type"] = "proven_political_truth"
        with self.assertRaisesRegex(ValueError, "epistemic type"):
            validate_dossier(self.dossier)

    def test_duplicate_claim_source_ids_rejected(self):
        for key in ("sources", "claims"):
            with self.subTest(key=key):
                dossier = fixture_dossier()
                dossier[key].append(deepcopy(dossier[key][0]))
                with self.assertRaisesRegex(ValueError, "duplicate ID"):
                    validate_dossier(dossier)

    def test_reference_mapping_required_for_every_fact(self):
        del self.case["fact_claims"]["available"]
        with self.assertRaisesRegex(ValueError, "mapping per case fact"):
            validate_case(self.case, self.dossier)

    def test_missing_claim_and_empty_claim_mapping_rejected(self):
        for references in (["missing-claim"], []):
            with self.subTest(references=references):
                self.case["fact_claims"]["available"] = references
                with self.assertRaises(ValueError):
                    validate_case(self.case, self.dossier)

    def test_unknown_claim_cannot_establish_consent(self):
        self.case["facts"]["permission"] = True
        with self.assertRaisesRegex(ValueError, "unknown claim"):
            validate_case(self.case, self.dossier)

    def test_non_boolean_fact_rejected(self):
        self.case["facts"]["available"] = "true"
        with self.assertRaisesRegex(ValueError, "true, false, or null"):
            validate_case(self.case, self.dossier)

    def test_source_url_must_be_http_and_is_never_executed(self):
        self.dossier["sources"][0]["url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValueError, "HTTP"):
            validate_dossier(self.dossier)

    def test_contradiction_references_checked(self):
        self.dossier["claims"][0]["contradicts_claim_ids"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "missing references"):
            validate_dossier(self.dossier)

    def test_disruption_is_explicit_hypothetical_and_preserves_initial_case(self):
        original = deepcopy(self.case)
        disruption = {"id": "fixture-disruption", "label": "hypothetical", "description": "Unit-test change",
                      "changes": {"available": False}, "fact_claims": {"available": ["changed-assumption"]}}
        changed = apply_disruption(self.case, disruption)
        self.assertFalse(changed["facts"]["available"])
        self.assertIsNone(changed["facts"]["permission"])
        self.assertEqual(self.case, original)
        self.assertEqual(changed["fact_claims"]["available"], ["changed-assumption"])
        self.assertEqual(self.case["fact_claims"]["available"], ["a1"])
        self.assertEqual(changed["applied_disruption"]["label"], "hypothetical")
        disruption["label"] = "actual"
        with self.assertRaisesRegex(ValueError, "hypothetical"):
            apply_disruption(self.case, disruption)

    def test_disruption_cannot_add_undeclared_facts_or_expressions(self):
        for changes in ({"invented_consent": True}, {"available": "__import__('os')"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                apply_disruption(self.case, {"id": "fixture-change", "label": "hypothetical",
                                             "description": "Fixture", "changes": changes,
                                             "fact_claims": {key: ["a1"] for key in changes}})

    def test_changed_fact_requires_separate_provenance_mapping(self):
        disruption = {"id": "fixture-change", "label": "hypothetical", "description": "Fixture",
                      "changes": {"available": False}, "fact_claims": {"permission": ["a1"]}}
        with self.assertRaisesRegex(ValueError, "mapping per changed fact"):
            apply_disruption(self.case, disruption)


if __name__ == "__main__":
    unittest.main()
