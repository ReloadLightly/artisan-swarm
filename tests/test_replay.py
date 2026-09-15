"""Checkpoint, lineage and zero-call replay checks.

The small records in CheckpointTests and FeedbackTests are explicitly
hand-authored unit fixtures. LiveReplayTests uses temporary copies of completed
application research-worker archives, never a fabricated conversation or run.
If no completed archive exists, that integration class is explicitly skipped.
"""
from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from artisan_swarm.archive import file_hash, read, save, semantic_diff
from artisan_swarm.orchestrator import (
    _manifest, _run_live_locked, _validate_critic, _validate_revision,
    replay, scenario_view, verify_engine, verify_hashes,
)
from artisan_swarm.workers import CodexBackend
from tests.test_programs import fixture_case, fixture_dossier, fixture_program

REPO = Path(__file__).resolve().parents[1]
CORE_FILES = ("programs.py", "schemas.py", "evidence.py", "feedback.py")


def fixture_criticism(parent):
    """Hand-authored validator fixture; this is not live model criticism."""
    return {
        "id": "criticism-1", "reviewer_type": "model_judgment",
        "summary": "Unit-test fixture only; no research judgment was generated.",
        "objections": [{"id": "fixture-objection", "candidate_id": parent["id"],
                        "action_id": "discuss", "claim_ids": ["a1"],
                        "issue": "Fixture branch depends on a changed assumption.",
                        "suggested_change": "Exercise a conditional branch in a validator test.",
                        "actionable": True}],
        "disagreements": ["Hand-authored fixture disagreement."],
    }


def fixture_revision(parent):
    """Hand-authored structural test mutation, never an application descendant."""
    child = deepcopy(parent)
    child.update(id=parent["id"] + "-r1", parent_ids=[parent["id"]],
                 feedback_ids=["fixture-objection"])
    child["actions"][0]["when"] = {
        "operator": "all", "tests": [{"fact": "available", "equals": False}]}
    return {"program": child, "change_summary": "Unit-test guard mutation only.",
            "feedback_responses": [{"feedback_id": "fixture-objection", "response": "Fixture response."}],
            "new_weaknesses": ["Fixture branch applies to a narrower state."]}


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="artisan-checkpoint-test-")
        self.addCleanup(self.temporary.cleanup)
        self.run_dir = Path(self.temporary.name) / "fixture-checkpoint"
        self.run_dir.mkdir()
        save(self.run_dir / "inputs" / "case.json", {"fixture": True, "state": "initial"})
        _manifest(self.run_dir, mode="fixture", status="partial")

    def test_append_only_save_preserves_parent_bytes(self):
        path = self.run_dir / "fixture-parent.json"
        parent = fixture_program()
        save(path, parent)
        original = path.read_bytes()
        save(path, deepcopy(parent))
        self.assertEqual(path.read_bytes(), original)
        changed = deepcopy(parent)
        changed["rationale"] = "Altered fixture parent."
        with self.assertRaisesRegex(ValueError, "Immutable artifact differs"):
            save(path, changed)
        self.assertEqual(path.read_bytes(), original)

    def test_manifest_update_cannot_bless_checkpoint_corruption(self):
        before = (self.run_dir / "manifest.json").read_bytes()
        save(self.run_dir / "inputs" / "case.json", {"fixture": True, "state": "corrupted"}, immutable=False)
        with self.assertRaisesRegex(ValueError, "Artifact hash mismatch: inputs/case.json"):
            _manifest(self.run_dir, status="running")
        self.assertEqual((self.run_dir / "manifest.json").read_bytes(), before)

    def test_missing_checkpoint_artifact_is_rejected(self):
        manifest = read(self.run_dir / "manifest.json")
        (self.run_dir / "inputs" / "case.json").unlink()
        with self.assertRaisesRegex(ValueError, "Artifact hash mismatch"):
            verify_hashes(self.run_dir, manifest)

    def test_checkpoint_paths_cannot_escape_archive(self):
        outside = Path(self.temporary.name) / "outside.json"
        save(outside, {"fixture": True})
        manifest = {"artifact_hashes": {"../outside.json": file_hash(outside)}}
        with self.assertRaisesRegex(ValueError, "escapes run directory"):
            verify_hashes(self.run_dir, manifest)

    def test_input_tampering_is_detected_before_resume_or_model_construction(self):
        before = (self.run_dir / "manifest.json").read_bytes()
        save(self.run_dir / "inputs" / "case.json", {"fixture": True, "state": "corrupted"}, immutable=False)
        with patch.object(CodexBackend, "__init__", side_effect=AssertionError("No model construction allowed")) as backend, \
                patch("subprocess.run", side_effect=AssertionError("No process allowed")) as process:
            with self.assertRaisesRegex(ValueError, "Artifact hash mismatch"):
                _run_live_locked(self.run_dir, self.run_dir / "unused-inputs", None)
            backend.assert_not_called()
            process.assert_not_called()
        self.assertEqual((self.run_dir / "manifest.json").read_bytes(), before)

    def test_fixture_backend_cannot_be_labeled_live(self):
        class HandAuthoredFixtureBackend:
            def generate(self, *args, **kwargs):
                raise AssertionError("Fixture backend must not run")
        with self.assertRaisesRegex(ValueError, "Custom backends are not live research"):
            _run_live_locked(self.run_dir, self.run_dir / "unused-inputs", HandAuthoredFixtureBackend())
        self.assertEqual(read(self.run_dir / "manifest.json")["mode"], "fixture")

    def test_frozen_engine_hashes_are_checked_without_modifying_source(self):
        hashes = {name: file_hash(REPO / "src" / "artisan_swarm" / name) for name in CORE_FILES}
        manifest = {"code_version": {"source_hashes": hashes}}
        verify_engine(manifest)
        for name in CORE_FILES:
            with self.subTest(name=name):
                altered = deepcopy(manifest)
                altered["code_version"]["source_hashes"][name] = "0" * 64
                with self.assertRaisesRegex(ValueError, f"Frozen engine changed: {name}"):
                    verify_engine(altered)


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.parent = fixture_program()
        self.criticism = fixture_criticism(self.parent)
        self.revision = fixture_revision(self.parent)

    def validate_revision(self):
        _validate_revision(self.revision, self.parent, self.criticism, fixture_dossier(), fixture_case())

    def test_valid_feedback_to_revision_references_preserve_parent(self):
        original = deepcopy(self.parent)
        _validate_critic(self.criticism, [self.parent], fixture_dossier())
        self.validate_revision()
        self.assertEqual(self.parent, original)
        self.assertNotEqual(self.revision["program"]["id"], self.parent["id"])
        self.assertEqual(self.revision["program"]["parent_ids"], [self.parent["id"]])

    def test_feedback_must_reference_an_archived_action(self):
        self.criticism["objections"][0]["action_id"] = "missing-action"
        with self.assertRaisesRegex(ValueError, "archived action"):
            _validate_critic(self.criticism, [self.parent], fixture_dossier())

    def test_feedback_ids_cannot_be_fabricated_or_belong_to_another_parent(self):
        for mutation in ("fabricated", "other-parent"):
            with self.subTest(mutation=mutation):
                criticism = deepcopy(self.criticism)
                if mutation == "fabricated":
                    criticism["objections"] = []
                else:
                    criticism["objections"][0]["candidate_id"] = "other-parent"
                with self.assertRaisesRegex(ValueError, "selected-parent objection IDs"):
                    _validate_revision(self.revision, self.parent, criticism, fixture_dossier(), fixture_case())

    def test_revision_requires_feedback_and_matching_public_response_ids(self):
        for changes, expected in (
            ("no-refs", "selected-parent objection IDs"),
            ("wrong-response", "exact feedback IDs"),
        ):
            with self.subTest(changes=changes):
                revision = deepcopy(self.revision)
                if changes == "no-refs":
                    revision["program"]["feedback_ids"] = []
                else:
                    revision["feedback_responses"][0]["feedback_id"] = "unrelated-feedback"
                with self.assertRaisesRegex(ValueError, expected):
                    _validate_revision(revision, self.parent, self.criticism, fixture_dossier(), fixture_case())

    def test_reason_and_advisory_fallback_only_edits_are_not_control_revisions(self):
        for mutation in ("prerequisite-reason", "fallback"):
            with self.subTest(mutation=mutation):
                revision = deepcopy(self.revision)
                revision["program"]["actions"] = deepcopy(self.parent["actions"])
                action = revision["program"]["actions"][0]
                if mutation == "prerequisite-reason":
                    action["prerequisites"][0]["reason"] = "Different explanatory wording"
                else:
                    target = revision["program"]["actions"][1]["id"]
                    action["fallbacks"] = [{"action_id": target, "reason": "Advisory reference only"}]
                with self.assertRaisesRegex(ValueError, "changed executable"):
                    _validate_revision(revision, self.parent, self.criticism, fixture_dossier(), fixture_case())

    def test_revision_cannot_rewrite_assigned_parent_or_child_identity(self):
        for key, value in (("parent_ids", ["different-parent"]), ("id", "unrelated-child")):
            with self.subTest(key=key):
                revision = deepcopy(self.revision)
                revision["program"][key] = value
                with self.assertRaisesRegex(ValueError, "assigned ID and exact preserved parent"):
                    _validate_revision(revision, self.parent, self.criticism, fixture_dossier(), fixture_case())

    def test_kind_only_or_prose_only_change_is_not_executable_revision(self):
        for field, value in (("kind", "evaluation"), ("description", "Different fixture wording")):
            with self.subTest(field=field):
                revision = deepcopy(self.revision)
                revision["program"]["actions"] = deepcopy(self.parent["actions"])
                revision["program"]["actions"][0][field] = value
                self.assertFalse(semantic_diff(self.parent, revision["program"])["executable_change"])
                with self.assertRaisesRegex(ValueError, "changed executable"):
                    _validate_revision(revision, self.parent, self.criticism, fixture_dossier(), fixture_case())


def completed_live_archive():
    """Discover saved completed live outputs; never manufacture a substitute."""
    for path in sorted((REPO / "results" / "m1").glob("*/manifest.json"), reverse=True):
        manifest = read(path)
        if manifest.get("mode") == "live" and manifest.get("status") == "completed":
            return path.parent
    return None


class LiveReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = completed_live_archive()
        if cls.archive is None:
            raise unittest.SkipTest("No completed live archive yet; replay integration awaits real worker outputs.")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="artisan-live-replay-test-")
        self.addCleanup(self.temporary.cleanup)
        self.run_dir = Path(self.temporary.name) / self.archive.name
        shutil.copytree(self.archive, self.run_dir)
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for target in ("artisan_swarm.workers.CodexBackend.__init__",
                       "artisan_swarm.workers.CodexBackend.generate", "subprocess.run", "subprocess.Popen"):
            self.guards.enter_context(patch(target, side_effect=AssertionError(f"Replay attempted forbidden call: {target}")))

    def replace_copied_artifact_and_refresh_digest(self, name, value):
        """Probe semantic checks after digests pass, exclusively in a temp copy.

        Rehashing is deliberate test corruption: it must not allow mismatched
        lineage or worker identity through the independent semantic checks.
        The real archived files and their manifest are never changed.
        """
        path = self.run_dir / name
        save(path, value, immutable=False)
        manifest = read(self.run_dir / "manifest.json")
        manifest["artifact_hashes"][name] = file_hash(path)
        save(self.run_dir / "manifest.json", manifest, immutable=False)

    def test_actual_archive_replays_with_zero_model_or_process_calls(self):
        before = {p.relative_to(self.run_dir): p.read_bytes() for p in self.run_dir.rglob("*")
                  if p.is_file() and p.name != "replay.json"}
        result = replay(self.run_dir)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["mode"], "replay")
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["programs"], 4)
        self.assertEqual(result["executions_compared"], 8)
        for name, original in before.items():
            self.assertEqual((self.run_dir / name).read_bytes(), original, str(name))

    def test_initial_and_changed_scenario_controls_make_zero_model_calls(self):
        for changed in (False, True):
            with self.subTest(changed=changed):
                result = scenario_view(self.run_dir, changed)
                self.assertEqual(result["model_calls"], 0)
                self.assertEqual(result["changed"], changed)
                phase = "changed" if changed else "initial"
                for candidate_id, execution in result["executions"].items():
                    self.assertEqual(execution, read(self.run_dir / "executions" / phase / f"{candidate_id}.json"))

    def test_actual_input_tampering_prevents_replay_and_resume(self):
        path = self.run_dir / "inputs" / "case.json"
        value = read(path)
        value["description"] += " Deliberate temporary test corruption."
        save(path, value, immutable=False)
        with self.assertRaisesRegex(ValueError, "Artifact hash mismatch"):
            replay(self.run_dir)
        with self.assertRaisesRegex(ValueError, "Artifact hash mismatch"):
            _run_live_locked(self.run_dir, self.run_dir / "unused-inputs", None)

    def test_discovery_snapshot_matches_actual_worker_output(self):
        name = "jobs/discover-centralized/output.json"
        value = read(self.run_dir / name)
        value["rationale"] += " Deliberate temporary test corruption."
        self.replace_copied_artifact_and_refresh_digest(name, value)
        with self.assertRaisesRegex(ValueError, "live discovery output"):
            replay(self.run_dir)

    def test_lineage_identifiers_match_actual_selected_parent_and_descendant(self):
        original = read(self.run_dir / "lineage.json")
        for key in ("parent_id", "child_id"):
            with self.subTest(key=key):
                value = deepcopy(original)
                value[key] = "wrong-artifact-id"
                self.replace_copied_artifact_and_refresh_digest("lineage.json", value)
                with self.assertRaisesRegex(ValueError, "Lineage mismatch"):
                    replay(self.run_dir)
        self.replace_copied_artifact_and_refresh_digest("lineage.json", original)

    def test_lineage_feedback_and_parent_hash_are_cross_checked(self):
        original = read(self.run_dir / "lineage.json")
        for key, invalid in (("feedback_ids", ["fabricated-feedback"]), ("parent_hash", "0" * 64)):
            with self.subTest(key=key):
                value = deepcopy(original)
                value[key] = invalid
                self.replace_copied_artifact_and_refresh_digest("lineage.json", value)
                with self.assertRaisesRegex(ValueError, "Lineage mismatch"):
                    replay(self.run_dir)
        self.replace_copied_artifact_and_refresh_digest("lineage.json", original)

    def test_review_must_match_saved_fresh_worker_output(self):
        name = "jobs/review/output.json"
        value = read(self.run_dir / name)
        value["recommendation"] += " Deliberate temporary test corruption."
        self.replace_copied_artifact_and_refresh_digest(name, value)
        with self.assertRaisesRegex(ValueError, "Saved worker output mismatch: review"):
            replay(self.run_dir)


if __name__ == "__main__":
    unittest.main()
