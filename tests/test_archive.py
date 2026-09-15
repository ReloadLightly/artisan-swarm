"""Archive tests use hand-authored fixtures, never live research evidence."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from artisan_swarm.archive import canonical, digest, read, save, semantic_diff
from artisan_swarm.programs import propose_strategy
from tests.test_programs import fixture_action, fixture_case, fixture_program


class ArchiveTests(unittest.TestCase):
    def test_digest_is_order_independent_but_content_sensitive(self):
        self.assertEqual(digest({"a": 1, "b": "ภาษาไทย"}), digest({"b": "ภาษาไทย", "a": 1}))
        self.assertNotEqual(digest({"a": True}), digest({"a": None}))
        self.assertEqual(canonical({"text": "Việt Nam"}).decode("utf-8").count("Việt Nam"), 1)

    def test_immutable_snapshot_accepts_identical_recovery_and_rejects_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture" / "parent.json"
            parent = fixture_program()
            save(path, parent)
            original = path.read_bytes()
            save(path, deepcopy(parent))
            changed = deepcopy(parent)
            changed["actions"][0]["prerequisites"] = []
            with self.assertRaisesRegex(ValueError, "Immutable artifact differs"):
                save(path, changed)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(read(path), parent)

    def test_descendant_snapshot_retains_parent_and_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = fixture_program()
            child = deepcopy(parent)
            child.update(id="fixture-descendant", parent_ids=[parent["id"]], feedback_ids=["fixture-criticism"])
            child["actions"][1]["when"] = {"operator": "all", "tests": [{"fact": "available", "equals": False}]}
            save(root / "parent.json", parent)
            before = (root / "parent.json").read_bytes()
            save(root / "descendant.json", child)
            save(root / "diff.json", semantic_diff(parent, child))
            self.assertEqual((root / "parent.json").read_bytes(), before)
            self.assertEqual(read(root / "descendant.json")["parent_ids"], [parent["id"]])
            self.assertEqual(read(root / "descendant.json")["feedback_ids"], ["fixture-criticism"])
            self.assertEqual(read(root / "diff.json")["parent_id"], parent["id"])


class SemanticDiffTests(unittest.TestCase):
    def setUp(self):
        self.parent = fixture_program()
        self.child = deepcopy(self.parent)
        self.child.update(id="fixture-descendant", parent_ids=[self.parent["id"]])

    def test_title_description_and_kind_changes_do_not_prove_control_logic_change(self):
        action = self.child["actions"][0]
        action.update(title="Fixture new title", description="Fixture clearer rationale", kind="negotiation")
        result = semantic_diff(self.parent, self.child)
        self.assertFalse(result["executable_change"])
        self.assertEqual({change["field"] for change in result["changes"]}, {"title", "description", "kind"})
        self.assertTrue(all(not change["executable"] for change in result["changes"]))
        initial = propose_strategy(fixture_case(), self.parent)
        revised = propose_strategy(fixture_case(), self.child)
        self.assertEqual([a["status"] for a in initial["actions"]], [a["status"] for a in revised["actions"]])

    def test_guard_change_is_executable_and_can_change_decision(self):
        self.child["actions"][1]["when"] = {
            "operator": "all", "tests": [{"fact": "available", "equals": False}]}
        result = semantic_diff(self.parent, self.child)
        self.assertTrue(result["executable_change"])
        self.assertEqual(result["changes"][0]["field"], "when")
        initial = propose_strategy(fixture_case(), self.parent)
        revised = propose_strategy(fixture_case(), self.child)
        self.assertEqual(initial["actions"][1]["status"], "supported")
        self.assertEqual(revised["actions"][1]["status"], "inactive")

    def test_prerequisite_dependency_and_fallback_changes_are_recorded(self):
        mutations = {
            "prerequisites": [{"fact": "permission", "equals": True, "reason": "Fixture permission gate"}],
            "depends_on": ["prepare"],
            "fallbacks": [{"action_id": "prepare", "reason": "Fixture conditional fallback"}],
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                child = deepcopy(self.child)
                child["actions"][0][field] = value
                result = semantic_diff(self.parent, child)
                self.assertTrue(result["executable_change"])
                self.assertEqual(len(result["changes"]), 1)
                self.assertEqual(result["changes"][0]["field"], field)
                self.assertEqual(result["changes"][0]["after"], value)

    def test_adding_and_removing_actions_preserves_before_after_details(self):
        removed = self.child["actions"].pop()
        added = fixture_action("new-fixture-work")
        self.child["actions"].append(added)
        result = semantic_diff(self.parent, self.child)
        changes = {entry["action_id"]: entry for entry in result["changes"]}
        self.assertTrue(result["executable_change"])
        self.assertEqual(changes[removed["id"]]["before"], removed)
        self.assertIsNone(changes[removed["id"]]["after"])
        self.assertIsNone(changes[added["id"]]["before"])
        self.assertEqual(changes[added["id"]]["after"], added)

    def test_action_reordering_and_lineage_metadata_are_not_executable_changes(self):
        self.child["actions"].reverse()
        self.child["feedback_ids"] = ["fixture-feedback"]
        self.child["rationale"] = "New fixture summary without changed executable rules."
        result = semantic_diff(self.parent, self.child)
        self.assertEqual(result["changes"], [])
        self.assertFalse(result["executable_change"])

    def test_diff_does_not_mutate_parent_or_descendant(self):
        self.child["actions"][0]["depends_on"] = ["prepare"]
        parent_before, child_before = deepcopy(self.parent), deepcopy(self.child)
        semantic_diff(self.parent, self.child)
        self.assertEqual(self.parent, parent_before)
        self.assertEqual(self.child, child_before)


if __name__ == "__main__":
    unittest.main()
