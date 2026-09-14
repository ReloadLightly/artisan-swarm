# M1 — Build and execute the first discovery-and-repair cycle

**Status at bootstrap: specified, not implemented or run.**

This document is the implementation assignment for Codex. Execute it end to end, making reasonable implementation decisions without returning a plan in place of working software. Consult `AGENTS.md`, the README, and `docs/SOURCES.md`. The RSI roadmap establishes interfaces and future questions; it is not an instruction to implement later milestones now.

## 1. User-facing outcome

A reader opens a local application and sees three different cooperation strategies for a proposed Japan–Thailand–Vietnam local-language AI collaboration. They can inspect the sources, conditional strategy programs, prerequisites, unknowns, and disagreements. They introduce one explicitly hypothetical change: a proposed data contribution is unavailable. The system identifies affected dependencies, records criticism, produces at least one descendant program through a real model-mediated revision, executes it, and explains what changed and what remains unresolved.

Deliver a source-linked decision brief and a preserved, replayable run. This is the product. A static page, scripted conversation, schema library, or test suite without the live strategy-revision path is not sufficient.

## 2. Scope and evidence

Use one small dossier. Begin with the verified policy anchor in `docs/SOURCES.md`, then retrieve enough public primary material to represent the ASEAN context and Thai and Vietnamese perspectives as well as Japan's. Aim for approximately six useful sources, not an exhaustive literature collection; source coverage matters more than a quota. Use original-language sources when useful and label translations.

For each source record an ID, title, publisher, URL, publication/update date when available, retrieval timestamp, and precise section or paragraph locator. Store short permitted excerpts or original paraphrases with provenance, not full copyrighted books. Keep inaccessible or undated information explicitly identified. Freeze the dossier version for the demonstration.

For every claim record its epistemic type: documented fact, interpretation, assumption, or unknown. Separate the claim's source support from a reviewer's interpretation. An official aspiration is not proof of implementation; silence is not evidence of refusal. If a required capacity, budget, right, or consent cannot be established, represent that as an unresolved prerequisite. Do not manufacture missing data or spend the whole milestone searching for it.

Create a development case and a separately labeled disruption record. The example data-unavailability condition is known to the development team and is NOT a held-out test. Do not attribute it to a real institution. Avoid making a substantive legal determination about data-transfer permissions: unknown permissions remain a question for qualified review.

## 3. Minimal implementation

Prefer Python with a small dependency set, typed records, JSON artifacts, and a lightweight local interface. Use an existing suitable Python environment or a project-local environment; do not download model weights. A small Streamlit app or an equivalently simple server is acceptable. Choose the implementation that makes the core application easy to run and inspect.

Suggested components, not an invitation to build a framework:

- `evidence`: source and claim records, support/contradiction references, explicit unknowns.
- `programs`: typed conditional strategy representation and interpreter.
- `workers`: model backend, independent discovery, criticism, revision, review.
- `archive`: candidate versions, parent IDs, feedback IDs, task history, immutable snapshots.
- `orchestrator`: the finite M1 workflow and checkpoint recovery.
- `reports` / `ui`: decision brief, before/after view, evidence browser, run status.

Implement a simple command-line entry point for live execution, replay, validation, and serving the interface. Add the actual working commands to the README only after they exist and have been tested.

### Executable strategy representation

Each strategy contains a title, substantive rationale, conditional rules, proposed actions, prerequisites, dependencies, evidence/assumption references, reconsideration triggers, and fallbacks. Preserve schema and engine versions.

Use a constrained JSON/AST-like program interpreted by Python. It must contain real conditional logic, not an essay in a Python string. Avoid unrestricted evaluation of generated Python or shell code. A suitable public interface is:

```python
propose_strategy(case_state, strategy_program) -> DecisionProposal
```

Support true, false, and unknown conditions explicitly. Unknown prerequisites cannot silently become satisfied; the output may request clarification or recommend conditional work rather than mark it ready. Distinguish a recommendation to negotiate access from a claim that access exists.

Execute the same program against initial and changed case states. Retain a dependency trace explaining which actions remain supported, become blocked, or need revision. General logic must not special-case one scenario ID to produce the intended answer.

## 4. Actual worker interaction and evolutionary revision

The finite pilot has three independent discovery jobs, a cross-candidate criticism job, a targeted revision job, and a fresh review job. These are logical work units, not a claim about a particular platform's internal number of model calls. Record actual calls and retries where observable.

**Discovery:** produce centralized, federated, and project-specific starting approaches in separate research-worker contexts. Give each the same frozen dossier and case, with only the assigned architectural starting point differing. Do not show other workers' outputs during discovery. These are design alternatives, not simulated national personalities. Permit explicit infeasibility and unresolved commitments.

**Archive and execution:** validate and preserve the initial programs before changing the case. If a generated program has a schema error, retain the invalid output and repair it without silently rewriting its history.

**Criticism and recruitment:** apply the disruption, expose archived programs and their dependency traces to a critic, and record objections tied to specific program elements and evidence/assumption IDs. Select a proposal for further investigation using a transparent rule based on actionable unresolved dependencies, with deterministic tie-breaking. Log which artifact attracted work and why. Do not use an unexplained scalar geopolitical fitness score.

**Variation:** ask a worker to revise the selected program using the recorded feedback. Preserve the parent; create a new candidate ID. Record the semantic change: which branch, prerequisite, commitment, or dependency was altered and what new weakness the change introduces. Recombination may reuse a compatible component of another archived proposal with attribution, but mutation alone is sufficient for the first complete cycle.

**Review and retention:** a fresh context checks the descendant against the unchanged dossier, changed case, and validation contract. It must not receive instructions to approve it. Retain or reject with explicit reasons and preserve alternatives. Do not force the proposal toward decentralization or a prewritten workstream-separation solution. A justified reduction of scope or suspension may be the appropriate recommendation.

The system must demonstrate a real worker-produced, executable revision. Whether that revision constitutes a substantive improvement is a separate, qualified finding. A rejected descendant can still demonstrate the mechanism; it does not demonstrate successful strategic repair. Report that distinction prominently.

### Backend and runtime

Use the installed, officially supported Codex CLI with the user's existing sign-in where feasible. Inspect `codex --help`, `codex exec --help`, and official references before relying on flags. Structured-output support is useful when available. Do not read or export credential files. Do not silently create an API-billed fallback.

Keep the **development session on Astra Ultra as requested**. Application research jobs should use an explicit, recorded configuration; the proposed M1 worker default is `gpt-6-astra` with supported medium reasoning, separate from the Ultra build session. Validate support locally, report the selected configuration, and never silently substitute another model. Do not assume that the builder's Ultra subagents are automatically application experiment workers.

Implement the research backend as finite artifact-generation jobs, not recursively nested copies of the M1 development task. Worker prompts explicitly prohibit implementing the repo, spawning further research jobs, editing evidence, or executing external actions. Give them only the task inputs needed; use read-only or isolated working directories and prevent accidental inheritance of this implementation assignment. Parallel execution is not required: independent contexts can run sequentially.

Provide an offline replay of the actual saved outputs that performs zero new model calls. Hand-authored test fixtures are acceptable for unit tests but must be labeled as fixtures; never relabel them as a live swarm run. Preserve existing valid output on retries and resume only missing work. Recover ordinary transient/formatting errors with a small documented retry policy, not an unlimited loop.

If a real external blocker prevents live calls, finish the runnable implementation, tests, and honestly labeled fixture/replay view, then record the exact blocker and one continuation command. Do not fabricate a live outcome or mark M1 complete.

## 5. Decision brief and interface

The brief should be readable as a short decision memo, not a log dump. Include the decision question, evidence cutoff, three alternatives, recommendation or qualified non-recommendation, causal rationale, unresolved interests and dependencies, resource requirements where supported, adaptation triggers, strongest objection, and the next evidence to obtain. Explicitly distinguish actual costs from unknowns or scenario assumptions.

The UI must display the actual run artifacts: candidate cards, evidence links, a program/dependency view, the scenario change, the parent/descendant semantic diff, and the review outcome. Provide distinct controls for replay and a new live run; opening or refreshing the app must not incur model calls. Clearly show live, replay, fixture, partial, or blocked status. Bind the local server to localhost by default and keep model credentials out of client-side code.

Check the page with available browser tools when possible: it loads, the scenario interaction works, the source links and before/after view render, and there are no obvious console errors. If browser tooling is unavailable, report the alternative smoke check and do not claim browser verification or invent a screenshot.

## 6. Checks, records, and definition of done

Test the behaviors that establish a meaningful cycle: schema validation; missing source IDs; invalid program references; three-valued prerequisites; dependency-cycle handling; unavailable contributions; unaffected work not being needlessly blocked; preserved parent versions; feedback-to-revision references; no arbitrary code execution; replay without model calls; and accidental live-call prevention in UI/replay. Include a test outside the one named scenario to catch hardcoding.

Source-ID validation is only referential integrity. Include a small documented semantic spot-check of important claims against retrieved text, labeled with reviewer type. Do not call that independent expert validation when performed by a model.

For the live run record input and program hashes, code/engine version, parent IDs, worker roles, prompts, final structured outputs, explicit feedback summaries, model settings, timestamps, known usage, attempts, failures, and outcome. Export a reviewed public research manifest; raw CLI account/session logs stay local. Record unknown costs as unknown, not free or zero.

Required deliverables (equivalent paths are acceptable if the README links them clearly):

| Deliverable | Suggested location |
|---|---|
| Runnable implementation and tested entry point | `src/artisan_swarm/`, `pyproject.toml` |
| Dossier, claim ledger, case, disruption | `data/m1/` |
| Three parents, descendant, and lineage | `results/m1/<run_id>/` |
| Reviewed live-run manifest and replay inputs | `results/m1/<run_id>/manifest.json` |
| Decision brief with source references | `reports/M1_DECISION_BRIEF.md` |
| Before/after and unresolved findings | `reports/M1_RESULTS.md` |
| Local interface and run instructions | Actual app path documented in README |
| Tests and evidence of checks performed | `tests/`, results report |
| Updated scientific README and handoff | `README.md`, `docs/HANDOFF.md` |

M1 is complete only when the application-level live cycle and its replay have run, outputs are inspectable, relevant tests pass, and the documentation accurately represents the result. Separately state whether the descendant passed review or achieved a useful repair. Do not perform a broad baseline tournament, long search, or engine self-modification campaign in this milestone.

## 7. Publication and final handoff

Apply the versioned GitHub About description with `bash scripts/set-about.sh` when authenticated CLI access is available. The helper changes description only; a metadata permission failure must not derail implementation.

Inspect `git status` and staged diffs, exclude secrets/private logs/large source documents, stage only relevant files, and commit the finished work. Preserve any existing license. Push non-destructively to the expected branch. Fetch and compare local HEAD with the actual remote branch SHA; report a push failure honestly rather than claiming publication.

Update the README status and results tables from real artifacts, preserving its scientific structure. Finish with: what was implemented; the concrete strategy change; where to read the brief; the exact app/replay commands; live job/call counts and known costs; checks run; remaining limitations; local and remote commit SHAs; and the next single research milestone. Do not end after scaffolding or a list of future tasks.
