"""A checkpointed six-job experiment, with replay that cannot invoke a model."""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

from .archive import control_signature, digest, file_hash, now, read, save, semantic_diff
from .evidence import apply_disruption, validate_case, validate_dossier
from .feedback import CONTRACT, CRITIC_SCHEMA, REVIEW_SCHEMA, revision_schema, select_candidate
from .programs import propose_strategy, validate_program
from .schemas import program_schema, validate_json
from .workers import CodexBackend, ROOT, WorkerError

ARCHITECTURES = ("centralized", "federated", "project_specific")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _optional(path, default=None):
    return read(path) if path.exists() else default


def _inputs(run_dir):
    return [read(run_dir / "inputs" / f"{name}.json") for name in ("dossier", "case", "disruption")]


def _attempts(run_dir):
    return [dict(job_id=p.parent.name, **read(p)) for p in sorted((run_dir / "jobs").glob("*/attempt-*.json"))]


def _accounting(run_dir):
    attempts = _attempts(run_dir)
    valid_usages = [a["usage"] for a in attempts if a.get("usage") is not None]
    keys = {k for u in valid_usages for k in u}
    return {"logical_jobs_completed": len(list((run_dir / "jobs").glob("*/output.json"))),
            "cli_invocations": len(attempts), "completed_turns": sum(a.get("completed_turns", 0) for a in attempts),
            "failed_attempts": sum(a["status"] != "valid" for a in attempts),
            "usage": {k: sum(u.get(k, 0) for u in valid_usages) for k in sorted(keys)} if valid_usages else None,
            "attempts_with_unknown_usage": sum(a.get("usage") is None for a in attempts),
            "provider_request_count": None, "provider_retry_count": None, "actual_cost": None}


def verify_hashes(run_dir, manifest):
    for name, expected in manifest.get("artifact_hashes", {}).items():
        path = (run_dir / name).resolve()
        if not path.is_relative_to(run_dir.resolve()):
            raise ValueError("Artifact path escapes run directory")
        if not path.is_file() or file_hash(path) != expected:
            raise ValueError(f"Artifact hash mismatch: {name}")


def verify_engine(manifest):
    for name in ("programs.py", "schemas.py", "evidence.py", "feedback.py"):
        if manifest["code_version"]["source_hashes"].get(name) != file_hash(Path(__file__).parent / name):
            raise ValueError(f"Frozen engine changed: {name}")


def _manifest(run_dir, **updates):
    path = run_dir / "manifest.json"
    manifest = _optional(path, {})
    verify_hashes(run_dir, manifest)
    manifest.update(updates)
    manifest["accounting"] = _accounting(run_dir)
    manifest["updated_at"] = now()
    # Manifest is mutable checkpoint; all inputs, requests, outputs, executions are immutable.
    manifest["artifact_hashes"] = {str(p.relative_to(run_dir)): file_hash(p) for p in sorted(run_dir.rglob("*"))
                                   if p.is_file() and p.name not in {"manifest.json", "replay.json"} and not p.name.endswith(".tmp")}
    save(path, manifest, immutable=False)
    return manifest


def _check_claims(ids, dossier):
    unknown = set(ids) - {c["id"] for c in dossier["claims"]}
    if unknown:
        raise ValueError(f"Unknown claim references: {sorted(unknown)}")


def _validate_critic(value, programs, dossier):
    validate_json(value, CRITIC_SCHEMA)
    if value["id"] != "criticism-1": raise ValueError("Expected criticism-1 ID")
    programs = {p["id"]: p for p in programs}
    seen = set()
    for objection in value["objections"]:
        if objection["id"] in seen: raise ValueError("Duplicate objection ID")
        seen.add(objection["id"])
        p = programs.get(objection["candidate_id"])
        if not p or objection["action_id"] not in {a["id"] for a in p["actions"]}:
            raise ValueError("Objection must reference an archived action")
        if not objection["claim_ids"]: raise ValueError("Objection needs evidence/assumption/unknown claim IDs")
        _check_claims(objection["claim_ids"], dossier)


def _validate_revision(value, parent, criticism, dossier, case):
    validate_json(value, revision_schema(program_schema()))
    p = value["program"]
    validate_program(p, dossier, case)
    if p["id"] != parent["id"] + "-r1" or p["parent_ids"] != [parent["id"]]:
        raise ValueError("Descendant must have assigned ID and exact preserved parent reference")
    valid = {o["id"] for o in criticism["objections"] if o["candidate_id"] == parent["id"]}
    refs = set(p["feedback_ids"])
    if not refs or not refs <= valid:
        raise ValueError("Revision must reference actual selected-parent objection IDs")
    if {f["feedback_id"] for f in value["feedback_responses"]} != refs:
        raise ValueError("Public responses must cover the exact feedback IDs")
    if not semantic_diff(parent, p)["executable_change"] or control_signature(parent) == control_signature(p):
        raise ValueError("Revision needs a changed executable branch, prerequisite, dependency, fallback or action")
    if not value["new_weaknesses"]: raise ValueError("Revision must name its new weaknesses")


def _validate_review(value, child, dossier):
    validate_json(value, REVIEW_SCHEMA)
    if value["candidate_id"] != child["id"]: raise ValueError("Review candidate mismatch")
    _check_claims(value["claim_ids"], dossier)
    if not value["reasons"] or not value["next_evidence"]:
        raise ValueError("Review must state reasons and next evidence")


def run_live(run_dir: Path, data_dir: Path | None = None, backend=None) -> dict:
    """Launch/resume only when explicitly called; reuse every valid saved job."""
    run_dir = Path(run_dir).resolve()
    data_dir = Path(data_dir or ROOT / "data" / "m1")
    run_dir.mkdir(parents=True, exist_ok=True)
    import fcntl
    # Lock state remains local, not a research artifact; prevents simultaneous resumes.
    lock_dir = ROOT / ".local" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    with (lock_dir / (digest(str(run_dir)) + ".lock")).open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("This run is already active") from None
        return _run_live_locked(run_dir, data_dir, backend)


def _run_live_locked(run_dir, data_dir, backend):
    existing = _optional(run_dir / "manifest.json", {})
    verify_hashes(run_dir, existing)
    if backend is not None and not isinstance(backend, CodexBackend):
        raise ValueError("Custom backends are not live research; use explicit unit fixtures outside run_live")
    if existing.get("status") == "completed":
        replay(run_dir)
        return existing
    for name in ("dossier", "case", "disruption"):
        path = run_dir / "inputs" / f"{name}.json"
        if not path.exists(): save(path, read(data_dir / f"{name}.json"))
    dossier, case, disruption = _inputs(run_dir)
    validate_dossier(dossier)
    validate_case(case, dossier)
    changed = apply_disruption(case, disruption)
    validate_case(changed, dossier)
    save(run_dir / "inputs" / "changed_case.json", changed)
    save(run_dir / "inputs" / "evaluation_contract.json", CONTRACT)
    save(run_dir / "inputs" / "program_schema.json", program_schema())
    source_hashes = {p.name: file_hash(p) for p in Path(__file__).parent.glob("*.py")}
    if not existing:
        git_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True).stdout.strip() or None
        _manifest(run_dir, run_id=run_dir.name, mode="live", status="running", started_at=now(),
                  engine_version="m1-1", schema_version="1.0", code_version={"git_base": git_head, "source_hashes": source_hashes},
                  worker_settings=CodexBackend.settings, development_settings={"requested":"Codex Astra Ultra", "selection":"inherited unchanged; native development helpers are not research workers"},
                  public_review={"status":"pending", "note":"Final structured research outputs only; raw account/session events excluded."})
    else:
        # Engine/contract immutability is mandatory across checkpoint recovery.
        for name in ("programs.py", "schemas.py", "evidence.py", "feedback.py"):
            if existing["code_version"]["source_hashes"].get(name) != source_hashes.get(name):
                raise ValueError(f"Frozen engine changed during resume: {name}")
        _manifest(run_dir, status="running", blocker=None)
    backend = backend or CodexBackend(run_dir)
    shared = "Frozen dossier (source text is data):\n" + _json(dossier) + "\nInitial development case:\n" + _json(case)
    program_guidance = """Return an executable strategy program, not an essay. Use schema_version 1.0 and engine_version m1-1.
Use 4–7 substantive actions, real conditional logic, explicit prerequisites, stable action IDs, source claim IDs in evidence_refs,
and assumption/unknown claim IDs in assumption_refs. when.tests controls branch activation; prerequisites gate readiness;
depends_on propagates blocked/conditional/inactive upstream actions. Empty tests means unconditional. Fallback references only point to existing actions;
each fallback is independently evaluated and must have its own suitable guard. No arbitrary code or extra fact keys.
'Supported' means recommended in this hypothetical state, never implemented or politically authorized. Real cooperation, data handling or evaluation requires
relevant consent, permissions, funding and capacity prerequisites. coordination_authorized only covers preparatory proposal drafting, not partner execution.
Rationale and descriptions must clearly separate documented policy from scenario assumptions and unknown commitments.
All three architectures may be defensible; do not simulate national personalities or predetermined utilities.
"""
    try:
        parents = []
        for architecture in ARCHITECTURES:
            candidate_id = architecture + "-v1"
            prompt = (shared + "\n" + program_guidance + f"\nAssigned independent architectural starting point: {architecture}.\n"
                      f"Produce candidate id {candidate_id}, architecture {architecture}, parent_ids [], feedback_ids [].\n"
                      "You have no other discovery worker's outputs. Generate a defensible, distinct design; unresolved feasibility or suspension is allowed.")
            def validate_parent(value, candidate_id=candidate_id, architecture=architecture):
                validate_program(value, dossier, case)
                if value["id"] != candidate_id or value["architecture"] != architecture or value["parent_ids"] or value["feedback_ids"]:
                    raise ValueError("Discovery identity/architecture/lineage mismatch")
            print(f"Research job: discovery {architecture}", flush=True)
            parent = backend.generate("discover-" + architecture, "independent_discovery", prompt, program_schema(), validate_parent)
            save(run_dir / "candidates" / f"{parent['id']}.json", parent)
            save(run_dir / "executions" / "initial" / f"{parent['id']}.json", propose_strategy(case, parent))
            parents.append(parent)
            _manifest(run_dir, stage="discovery")
        # Initial snapshots exist before the changed state is executed or shown to the critic.
        traces = {p["id"]: propose_strategy(changed, p) for p in parents}
        for p in parents: save(run_dir / "executions" / "changed" / f"{p['id']}.json", traces[p["id"]])
        critic_prompt = shared + "\nDisruption (hypothetical, not held out):\n" + _json(disruption)
        critic_prompt += "\nChanged case:\n" + _json(changed) + "\nArchived parents:\n" + _json(parents) + "\nChanged executions:\n" + _json(traces)
        critic_prompt += "\nUnchanged evaluation contract:\n" + _json(CONTRACT)
        critic_prompt += "\nProduce cross-candidate criticism id criticism-1, reviewer_type model_judgment. Tie each objection to an exact candidate/action ID and claim IDs. Identify actionable unresolved dependencies, overclaimed consent and the strongest architectural disagreements. Criticism need not prefer any architecture."
        print("Research job: cross-candidate criticism", flush=True)
        criticism = backend.generate("critic", "cross_candidate_critic", critic_prompt, CRITIC_SCHEMA,
                                    lambda v: _validate_critic(v, parents, dossier))
        save(run_dir / "criticism.json", criticism)
        selection = select_candidate(parents, traces, criticism)
        save(run_dir / "selection.json", selection)
        _manifest(run_dir, stage="revision", selected_id=selection["selected_id"])
        parent = next(p for p in parents if p["id"] == selection["selected_id"])
        revision_prompt = shared + "\n" + program_guidance
        revision_prompt += "\nChanged case:\n" + _json(changed) + "\nHypothetical disruption:\n" + _json(disruption)
        revision_prompt += "\nSelected immutable parent:\n" + _json(parent) + "\nExecution:\n" + _json(traces[parent["id"]])
        revision_prompt += "\nActual cross-candidate feedback:\n" + _json(criticism) + "\nRecruitment record:\n" + _json(selection)
        revision_prompt += "\nUnchanged evaluation contract:\n" + _json(CONTRACT)
        revision_prompt += (f"\nRevise selected parent into id {parent['id']}-r1, parent_ids [{json.dumps(parent['id'])}]. "
                            "Use actual objection IDs in program.feedback_ids and feedback_responses. Make a substantive executable change and explain new weaknesses. "
                            "You may reduce scope or suspend; no preferred architecture or prewritten repair is required. Do not weaken unknown prerequisites, evidence or contract. "
                            "Do not simply paraphrase. Return program, change_summary, feedback_responses, new_weaknesses.")
        print("Research job: targeted program revision", flush=True)
        revision = backend.generate("revise", "targeted_revision", revision_prompt, revision_schema(program_schema()),
                                    lambda v: _validate_revision(v, parent, criticism, dossier, case))
        save(run_dir / "revision.json", revision)
        child = revision["program"]
        save(run_dir / "candidates" / f"{child['id']}.json", child)
        for phase, state in (("initial", case), ("changed", changed)):
            save(run_dir / "executions" / phase / f"{child['id']}.json", propose_strategy(state, child))
        diff = semantic_diff(parent, child)
        save(run_dir / "semantic_diff.json", diff)
        save(run_dir / "lineage.json", {"parent_id": parent["id"], "child_id": child["id"],
             "parent_hash": digest(parent), "child_hash": digest(child), "feedback_ids": child["feedback_ids"],
             "selection_rule": selection["rule"], "operator": "model_mediated_mutation"})
        _manifest(run_dir, stage="review")
        review_prompt = ("Fresh independent review context. Return reviewer_type model_judgment; inspect, do not rubber-stamp.\n"
                         "Frozen dossier:\n" + _json(dossier) + "\nChanged case:\n" + _json(changed) +
                         "\nFixed validation contract:\n" + _json(CONTRACT) + "\nParent:\n" + _json(parent) +
                         "\nCriticism:\n" + _json(criticism) + "\nDescendant and public rationale:\n" + _json(revision) +
                         "\nComputed semantic diff:\n" + _json(diff) + "\nDescendant execution:\n" + _json(propose_strategy(changed, child)) +
                         "\nReturn id review-1, candidate_id " + child["id"] +
                         ". Retain or reject with explicit reasons; independently decide whether this is substantive repair. "
                         "Name unresolved interests, resource requirements (amounts unknown unless evidenced), strongest objection and next evidence. "
                         "Check narrative actions against actual executable gates. Reference claim IDs for material claims. Reject if necessary; successful repair is not required.")
        print("Research job: fresh review", flush=True)
        review = backend.generate("review", "fresh_reviewer", review_prompt, REVIEW_SCHEMA,
                                  lambda v: _validate_review(v, child, dossier))
        save(run_dir / "review.json", review)
        retention = {"descendant": child["id"], "outcome": review["outcome"], "reviewer_type": "model_judgment",
                     "alternatives_preserved": [p["id"] for p in parents], "substantive_repair": review["substantive_repair"]}
        save(run_dir / "retention.json", retention)
        from .reports import decision_brief
        brief = decision_brief(build_view(run_dir))
        brief_path = run_dir / "decision_brief.md"
        if brief_path.exists() and brief_path.read_text() != brief: raise ValueError("Immutable brief changed")
        brief_path.write_text(brief)
        _manifest(run_dir, status="completed", stage="completed", finished_at=now(), outcome=retention,
                  mechanism_complete=True, strategic_repair=review["substantive_repair"], blocker=None)
        replay(run_dir)
        return read(run_dir / "manifest.json")
    except (ValueError, WorkerError, OSError) as error:
        _manifest(run_dir, status="blocked" if isinstance(error, WorkerError) else "partial", blocker=str(error))
        raise


def build_view(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    inputs = run_dir / "inputs"
    candidates = [read(p) for p in sorted((run_dir / "candidates").glob("*.json"))]
    view = {"run_dir": str(run_dir), "manifest": _optional(run_dir / "manifest.json", {"status":"partial","mode":"live"}),
            "dossier": _optional(inputs / "dossier.json", {}), "case": _optional(inputs / "case.json", {}),
            "disruption": _optional(inputs / "disruption.json", {}), "candidates": candidates,
            "executions": {phase: {p.stem: read(p) for p in sorted((run_dir / "executions" / phase).glob("*.json"))} for phase in ("initial", "changed")}}
    for name in ("criticism", "selection", "revision", "semantic_diff", "review", "lineage", "retention", "replay"):
        view[name] = _optional(run_dir / f"{name}.json", {})
    view["brief"] = (run_dir / "decision_brief.md").read_text() if (run_dir / "decision_brief.md").exists() else "Decision brief pending completion of the live cycle."
    return view


def scenario_view(run_dir: Path, changed: bool) -> dict:
    dossier, case, disruption = _inputs(Path(run_dir))
    state = apply_disruption(case, disruption) if changed else case
    executions = {}
    for path in sorted((Path(run_dir) / "candidates").glob("*.json")):
        p = read(path)
        validate_program(p, dossier, state)
        executions[p["id"]] = propose_strategy(state, p)
    return {"case": state, "changed": changed, "executions": executions, "model_calls": 0}


def replay(run_dir: Path) -> dict:
    """Revalidate saved model outputs, rerun interpreter and compare all executions.

    No backend object is constructed. This verifies provenance/behavior, not model
    reproducibility or external feasibility. Inputs use saved snapshots, not live web.
    """
    run_dir = Path(run_dir)
    manifest = read(run_dir / "manifest.json")
    verify_hashes(run_dir, manifest)
    verify_engine(manifest)
    dossier, case, disruption = _inputs(run_dir)
    validate_dossier(dossier)
    validate_case(case, dossier)
    if read(run_dir / "inputs" / "evaluation_contract.json") != CONTRACT:
        raise ValueError("Evaluation contract differs from frozen version")
    if read(run_dir / "inputs" / "program_schema.json") != program_schema():
        raise ValueError("Program schema differs from frozen version")
    changed = apply_disruption(case, disruption)
    if changed != read(run_dir / "inputs" / "changed_case.json"): raise ValueError("Changed case mismatch")
    programs = [read(p) for p in sorted((run_dir / "candidates").glob("*.json"))]
    executions = {"initial": {}, "changed": {}}
    for program in programs:
        validate_program(program, dossier, case)
        for phase, state in (("initial", case), ("changed", changed)):
            actual = propose_strategy(state, program)
            if actual != read(run_dir / "executions" / phase / f"{program['id']}.json"):
                raise ValueError(f"Replay differs for {phase}/{program['id']}")
            executions[phase][program["id"]] = actual
    parents = [p for p in programs if not p["parent_ids"]]
    if len(parents) != 3 or {p["architecture"] for p in parents} != set(ARCHITECTURES):
        raise ValueError("Replay requires all three archived discovery parents")
    for parent in parents:
        if parent != read(run_dir / "jobs" / ("discover-" + parent["architecture"]) / "output.json"):
            raise ValueError("Archived program differs from live discovery output")
    criticism = read(run_dir / "criticism.json")
    _validate_critic(criticism, parents, dossier)
    selection = select_candidate(parents, executions["changed"], criticism)
    if selection != read(run_dir / "selection.json"): raise ValueError("Recruitment replay mismatch")
    parent = next(p for p in parents if p["id"] == selection["selected_id"])
    revision = read(run_dir / "revision.json")
    _validate_revision(revision, parent, criticism, dossier, case)
    child = revision["program"]
    if child != read(run_dir / "candidates" / f"{child['id']}.json"): raise ValueError("Descendant snapshot mismatch")
    if semantic_diff(parent, child) != read(run_dir / "semantic_diff.json"): raise ValueError("Semantic diff mismatch")
    lineage = read(run_dir / "lineage.json")
    if (lineage["parent_id"] != parent["id"] or lineage["child_id"] != child["id"]
            or lineage["parent_hash"] != digest(parent) or lineage["child_hash"] != digest(child)
            or lineage["feedback_ids"] != child["feedback_ids"]):
        raise ValueError("Lineage mismatch")
    review = read(run_dir / "review.json")
    _validate_review(review, child, dossier)
    retention = read(run_dir / "retention.json")
    expected_retention = {"descendant": child["id"], "outcome": review["outcome"], "reviewer_type": "model_judgment",
                          "alternatives_preserved": [architecture + "-v1" for architecture in ARCHITECTURES],
                          "substantive_repair": review["substantive_repair"]}
    if retention != expected_retention or manifest.get("outcome") != retention:
        raise ValueError("Retention outcome differs from saved review")
    for job, value in (("critic", criticism), ("revise", revision), ("review", review)):
        if value != read(run_dir / "jobs" / job / "output.json"): raise ValueError(f"Saved worker output mismatch: {job}")
    result = {"mode": "replay", "status": "passed", "replayed_at": now(), "model_calls": 0,
              "programs": len(programs), "executions_compared": len(programs)*2,
              "checks": ["artifact hashes", "frozen evidence and contract", "program schema/references", "three distinct architectures",
                         "initial and changed execution equality", "worker-output identity", "recruitment selection", "parent lineage",
                         "feedback references", "executable semantic diff", "fresh review reference"],
              "note": "Deterministic software replay of actual saved research-worker outputs; no new inference or independent political validation."}
    save(run_dir / "replay.json", result, immutable=False)
    return result
