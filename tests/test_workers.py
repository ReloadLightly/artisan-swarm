"""Mocked CLI fixtures only: these tests make zero live research/model calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from artisan_swarm import workers
from artisan_swarm.archive import read
from artisan_swarm.schemas import validate_json


FIXTURE_SCHEMA = {
    "type": "object",
    "properties": {"outcome": {"type": "string", "enum": ["fixture_valid"]}},
    "required": ["outcome"],
    "additionalProperties": False,
}
FIXTURE_OUTPUT = {"outcome": "fixture_valid"}
PRIVATE_SENTINEL = "UNIT_TEST_PRIVATE_ACCOUNT_SENTINEL_NOT_A_REAL_SECRET"


def validate_fixture(output):
    validate_json(output, FIXTURE_SCHEMA)


class EventSummaryTests(unittest.TestCase):
    def test_only_allowlisted_accounting_leaves_raw_events(self):
        events = [
            {"type": "thread.started", "thread_id": PRIVATE_SENTINEL, "account": PRIVATE_SENTINEL},
            {"type": "item.completed", "item": {"type": "reasoning", "text": PRIVATE_SENTINEL}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": PRIVATE_SENTINEL}},
            {"type": "turn.completed", "usage": {
                "input_tokens": 17, "cached_input_tokens": 4, "output_tokens": 3,
                "account_id": PRIVATE_SENTINEL, "access_token": PRIVATE_SENTINEL,
                "billing": {"private": PRIVATE_SENTINEL}, "unknown_measure": 99}},
            {"type": "turn.completed", "usage": {"input_tokens": 5, "output_tokens": 2}},
            {"type": "error", "message": PRIVATE_SENTINEL},
        ]
        result = workers.summarize_events("\n".join(json.dumps(e) for e in events))
        self.assertEqual(result["usage"], {"input_tokens": 22, "cached_input_tokens": 4, "output_tokens": 5})
        self.assertEqual(result["completed_turns"], 2)
        self.assertEqual(result["error_events"], 1)
        self.assertEqual(result["tool_item_types"], [])
        self.assertNotIn(PRIVATE_SENTINEL, json.dumps(result))
        self.assertIsNone(result["provider_request_count"])
        self.assertIsNone(result["provider_retry_count"])

    def test_absent_usage_is_unknown_and_invalid_token_types_are_not_counted(self):
        self.assertIsNone(workers.summarize_events("not JSON\n")["usage"])
        result = workers.summarize_events(json.dumps({"type": "turn.completed", "usage": {
            "input_tokens": True, "cached_input_tokens": "8", "output_tokens": 4.5}}))
        self.assertEqual(result["usage"], {})

    def test_unexpected_tool_use_is_visible_without_exporting_tool_contents(self):
        result = workers.summarize_events(json.dumps({"type": "item.completed", "item": {
            "type": "command_execution", "command": PRIVATE_SENTINEL, "output": PRIVATE_SENTINEL}}))
        self.assertEqual(result["tool_item_types"], ["command_execution"])
        self.assertNotIn(PRIVATE_SENTINEL, json.dumps(result))

    def test_non_object_events_and_items_do_not_crash_accounting(self):
        events = ["null", "[]", '"fixture"', "42", '{"type":"item.completed","item":null}',
                  '{"type":"item.completed","item":[]}']
        result = workers.summarize_events("\n".join(events))
        self.assertEqual(result["completed_turns"], 0)
        self.assertIsNone(result["usage"])


class CommandTests(unittest.TestCase):
    def test_provider_projection_preserves_local_uniqueness_contract(self):
        schema = {"type": "object", "properties": {"refs": {
            "type": "array", "items": {"type": "string"}, "uniqueItems": True}},
            "required": ["refs"], "additionalProperties": False}
        original = deepcopy(schema)
        projected = workers.wire_schema(schema)
        self.assertEqual(schema, original)
        self.assertNotIn("uniqueItems", projected["properties"]["refs"])
        self.assertEqual(projected["properties"]["refs"]["items"], {"type": "string"})
        validate_json({"refs": ["fixture-a", "fixture-a"]}, projected)
        with self.assertRaisesRegex(ValueError, "unique|duplicate"):
            validate_json({"refs": ["fixture-a", "fixture-a"]}, schema)

    def test_command_is_fresh_isolated_explicit_model_and_existing_auth(self):
        workspace = Path("/tmp/fixture-isolated-worker")
        args = workers.command(workspace, workspace / "schema.json", workspace / "final.json")
        self.assertEqual(args[:2], ["codex", "exec"])
        self.assertNotIn("resume", args)
        for option in ("--ephemeral", "--ignore-user-config", "--skip-git-repo-check", "--json"):
            self.assertIn(option, args)
        self.assertEqual(args[args.index("--model") + 1], "gpt-6-astra")
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
        self.assertEqual(args[args.index("--cd") + 1], str(workspace))
        configs = [args[i + 1] for i, value in enumerate(args[:-1]) if value == "-c"]
        for config in ('model_reasoning_effort="medium"', 'forced_login_method="chatgpt"',
                       'approval_policy="never"', 'project_doc_max_bytes=0', 'web_search="disabled"'):
            self.assertIn(config, configs)
        self.assertIn('model_instructions_file=' + json.dumps(str(workspace / "worker-instructions.txt")), configs)
        disabled = {args[i + 1] for i, value in enumerate(args[:-1]) if value == "--disable"}
        self.assertTrue({"shell_tool", "unified_exec", "multi_agent", "multi_agent_v2", "apps", "plugins",
                         "hooks", "memories", "browser_use", "computer_use", "image_generation"} <= disabled)
        self.assertEqual(args[-1], "-")


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="artisan-mocked-worker-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run_dir = self.root / "results" / "fixture-run"
        self.root_patch = patch.object(workers, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.sleep_patch = patch.object(workers.time, "sleep")
        self.sleep_patch.start()
        self.addCleanup(self.sleep_patch.stop)
        self.backend = workers.CodexBackend(self.run_dir)

    def response(self, output=FIXTURE_OUTPUT, *, returncode=0, events=None, stderr=""):
        """Write a fabricated final only inside the test's isolated temp directory."""
        def run(args, **kwargs):
            output_path = Path(args[args.index("--output-last-message") + 1])
            if output is not None:
                output_path.write_text(output if isinstance(output, str) else json.dumps(output))
            stdout = events if events is not None else json.dumps({"type": "turn.completed", "usage": {
                "input_tokens": 10, "output_tokens": 5}})
            return subprocess.CompletedProcess(args, returncode, stdout, stderr)
        return run

    def generate(self, validator=validate_fixture):
        return self.backend.generate("fixture-job", "unit_test_fixture", "Hand-authored test fixture prompt.",
                                     FIXTURE_SCHEMA, validator)

    def public_text(self):
        return "\n".join(path.read_text() for path in self.run_dir.rglob("*.json"))

    def test_api_key_fallbacks_removed_and_private_logs_stay_out_of_archive(self):
        events = "\n".join([json.dumps({"type": "thread.started", "thread_id": PRIVATE_SENTINEL}),
                            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10}})])
        fake = self.response(events=events, stderr=PRIVATE_SENTINEL)
        def inspect_invocation(args, **kwargs):
            self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
            self.assertNotIn("CODEX_API_KEY", kwargs["env"])
            self.assertEqual(kwargs["env"]["ARTISAN_TEST_PRESERVED_ENV"], "fixture")
            self.assertEqual(Path(kwargs["cwd"]), Path(args[args.index("--cd") + 1]))
            self.assertNotEqual(Path(kwargs["cwd"]), workers.ROOT)
            self.assertTrue((Path(kwargs["cwd"]) / "worker-instructions.txt").exists())
            return fake(args, **kwargs)
        with patch.dict(os.environ, {"OPENAI_API_KEY": PRIVATE_SENTINEL, "CODEX_API_KEY": PRIVATE_SENTINEL,
                                     "ARTISAN_TEST_PRESERVED_ENV": "fixture"}), \
                patch.object(workers.subprocess, "run", side_effect=inspect_invocation) as run:
            self.assertEqual(self.generate(), FIXTURE_OUTPUT)
        self.assertEqual(run.call_count, 1)
        self.assertNotIn(PRIVATE_SENTINEL, self.public_text())
        self.assertIn(PRIVATE_SENTINEL, (self.backend.private_dir / "fixture-job-1.events.jsonl").read_text())
        self.assertIn(PRIVATE_SENTINEL, (self.backend.private_dir / "fixture-job-1.stderr.log").read_text())
        self.assertIsNone(self.backend.settings["cost"])
        self.assertEqual(self.backend.settings["authentication"], "existing_chatgpt_sign_in")

    def test_schema_failure_retries_with_feedback_and_preserves_both_outputs(self):
        invalid = {"outcome": "fixture_invalid"}
        responses = iter([self.response(invalid), self.response()])
        prompts, working_dirs = [], []
        def run(args, **kwargs):
            prompts.append(kwargs["input"])
            working_dirs.append(kwargs["cwd"])
            return next(responses)(args, **kwargs)
        with patch.object(workers.subprocess, "run", side_effect=run):
            self.assertEqual(self.generate(), FIXTURE_OUTPUT)
        job = self.run_dir / "jobs" / "fixture-job"
        self.assertEqual(read(job / "raw-output-1.json"), invalid)
        self.assertEqual(read(job / "raw-output-2.json"), FIXTURE_OUTPUT)
        self.assertEqual(read(job / "attempt-1.json")["status"], "failed")
        self.assertEqual(read(job / "attempt-2.json")["status"], "valid")
        self.assertIn("Validation feedback", prompts[1])
        self.assertIn("fixture_invalid", prompts[1])
        self.assertNotEqual(working_dirs[0], working_dirs[1])

    def test_non_json_final_is_preserved_before_format_repair(self):
        responses = iter([self.response("HAND-AUTHORED INVALID JSON FIXTURE"), self.response()])
        with patch.object(workers.subprocess, "run", side_effect=lambda a, **kw: next(responses)(a, **kw)):
            self.generate()
        job = self.run_dir / "jobs" / "fixture-job"
        self.assertEqual(read(job / "raw-output-1.json"), {"invalid_final_text": "HAND-AUTHORED INVALID JSON FIXTURE"})
        self.assertEqual(read(job / "output.json"), FIXTURE_OUTPUT)

    def test_saved_valid_output_recovers_with_no_new_call_and_is_revalidated(self):
        with patch.object(workers.subprocess, "run", side_effect=self.response()):
            self.generate()
        job = self.run_dir / "jobs" / "fixture-job"
        previous = {path.name: path.read_bytes() for path in job.glob("*.json")}
        validated = []
        def validator(output):
            validated.append(deepcopy(output))
            validate_fixture(output)
        recovered = workers.CodexBackend(self.run_dir)
        with patch.object(workers.subprocess, "run", side_effect=AssertionError("Replay/recovery must not call model")):
            result = recovered.generate("fixture-job", "unit_test_fixture", "Hand-authored test fixture prompt.",
                                        FIXTURE_SCHEMA, validator)
        self.assertEqual(result, FIXTURE_OUTPUT)
        self.assertEqual(validated, [FIXTURE_OUTPUT])
        self.assertEqual(previous, {path.name: path.read_bytes() for path in job.glob("*.json")})

    def test_interrupted_final_snapshot_recovers_valid_raw_output_without_new_call(self):
        original_save = workers.save
        def crash_before_final_snapshot(path, value, **kwargs):
            if path.name == "output.json":
                raise RuntimeError("Unit-test simulated interruption before final snapshot")
            return original_save(path, value, **kwargs)
        with patch.object(workers.subprocess, "run", side_effect=self.response()), \
                patch.object(workers, "save", side_effect=crash_before_final_snapshot), \
                self.assertRaisesRegex(RuntimeError, "simulated interruption"):
            self.generate()
        job = self.run_dir / "jobs" / "fixture-job"
        self.assertFalse((job / "output.json").exists())
        self.assertEqual(read(job / "attempt-1.json")["status"], "valid")
        self.assertEqual(read(job / "raw-output-1.json"), FIXTURE_OUTPUT)
        with patch.object(workers.subprocess, "run", side_effect=AssertionError("Valid raw artifact should recover")):
            self.assertEqual(self.generate(), FIXTURE_OUTPUT)
        self.assertEqual(read(job / "output.json"), FIXTURE_OUTPUT)
        self.assertFalse((job / "attempt-2.json").exists())

    def test_restart_after_failed_attempt_resumes_missing_attempt_with_feedback(self):
        invalid = {"outcome": "fixture_invalid"}
        with patch.object(workers.subprocess, "run", side_effect=self.response(invalid)), \
                patch.object(workers.time, "sleep", side_effect=RuntimeError("Unit-test interrupted retry")), \
                self.assertRaisesRegex(RuntimeError, "interrupted retry"):
            self.generate()
        job = self.run_dir / "jobs" / "fixture-job"
        failed_before = (job / "raw-output-1.json").read_bytes()
        def resume(args, **kwargs):
            self.assertIn("Validation feedback", kwargs["input"])
            self.assertIn("fixture_invalid", kwargs["input"])
            return self.response()(args, **kwargs)
        with patch.object(workers.subprocess, "run", side_effect=resume) as run:
            self.assertEqual(self.generate(), FIXTURE_OUTPUT)
        self.assertEqual(run.call_count, 1)
        self.assertEqual((job / "raw-output-1.json").read_bytes(), failed_before)
        self.assertEqual(read(job / "attempt-1.json")["status"], "failed")
        self.assertEqual(read(job / "attempt-2.json")["status"], "valid")

    def test_cli_start_failure_does_not_fall_back_or_export_exception_details(self):
        with patch.object(workers.subprocess, "run", side_effect=FileNotFoundError(PRIVATE_SENTINEL)) as run, \
                self.assertRaisesRegex(workers.WorkerError, "FileNotFoundError") as caught:
            self.generate()
        self.assertEqual(run.call_count, 1)
        self.assertNotIn(PRIVATE_SENTINEL, str(caught.exception))
        self.assertNotIn(PRIVATE_SENTINEL, self.public_text())

    def test_changing_completed_request_cannot_overwrite_history(self):
        with patch.object(workers.subprocess, "run", side_effect=self.response()):
            self.generate()
        with patch.object(workers.subprocess, "run", side_effect=AssertionError("Must reject before a call")), \
                self.assertRaisesRegex(ValueError, "Immutable artifact differs"):
            self.backend.generate("fixture-job", "unit_test_fixture", "Different fixture prompt.",
                                  FIXTURE_SCHEMA, validate_fixture)

    def test_repeated_cli_failure_is_bounded_without_api_fallback_or_log_leakage(self):
        with patch.object(workers.subprocess, "run", side_effect=self.response(
                None, returncode=9, events=json.dumps({"type": "error", "message": PRIVATE_SENTINEL}),
                stderr=PRIVATE_SENTINEL)) as run, self.assertRaises(workers.WorkerError):
            self.generate()
        self.assertEqual(run.call_count, workers.MAX_ATTEMPTS)
        self.assertTrue(all(call.args[0][:2] == ["codex", "exec"] for call in run.call_args_list))
        job = self.run_dir / "jobs" / "fixture-job"
        self.assertEqual(len(list(job.glob("attempt-*.json"))), workers.MAX_ATTEMPTS)
        self.assertFalse((job / "output.json").exists())
        self.assertNotIn(PRIVATE_SENTINEL, self.public_text())
        with patch.object(workers.subprocess, "run", side_effect=AssertionError("Attempt budget exhausted")), \
                self.assertRaises(workers.WorkerError):
            self.generate()

    def test_tool_using_worker_is_excluded_despite_valid_final(self):
        events = json.dumps({"type": "item.completed", "item": {"type": "command_execution",
                                                                 "command": PRIVATE_SENTINEL}})
        with patch.object(workers.subprocess, "run", side_effect=self.response(events=events)), \
                self.assertRaisesRegex(workers.WorkerError, "unexpectedly used tools"):
            self.generate()
        job = self.run_dir / "jobs" / "fixture-job"
        self.assertFalse((job / "output.json").exists())
        self.assertEqual(read(job / "attempt-1.json")["tool_item_types"], ["command_execution"])
        self.assertNotIn(PRIVATE_SENTINEL, self.public_text())

    def test_timeout_bytes_are_kept_private_and_followed_by_bounded_retry(self):
        responses = iter([subprocess.TimeoutExpired("codex", 420, output=PRIVATE_SENTINEL.encode(),
                                                    stderr=PRIVATE_SENTINEL.encode()), self.response()])
        def run(args, **kwargs):
            response = next(responses)
            if isinstance(response, Exception):
                raise response
            return response(args, **kwargs)
        with patch.object(workers.subprocess, "run", side_effect=run) as mocked:
            self.assertEqual(self.generate(), FIXTURE_OUTPUT)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(read(self.run_dir / "jobs" / "fixture-job" / "attempt-1.json")["exit_code"], -1)
        self.assertNotIn(PRIVATE_SENTINEL, self.public_text())


if __name__ == "__main__":
    unittest.main()
