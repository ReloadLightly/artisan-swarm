# M1 results and verification

## Outcome

**Engineering cycle completed:** `m1-live-20260915-002`, September 15, 2026, 00:05:02–00:11:18 UTC. Six actual Codex research jobs generated three independent programs, cross-candidate criticism, a model-mediated descendant and a fresh review. Four programs were executed in two states. Offline replay passed with zero new model calls.

**Strategic finding:** the reviewer retained a limited planning repair. This remains a model judgment. The program recommends a new explicit drafting step; it did not produce an evaluation matrix, acquire data, run an evaluation or demonstrate operational resilience. The parent already supported no-data planning.

Read the [decision brief](M1_DECISION_BRIEF.md) and [public manifest](../results/m1/m1-live-20260915-002/manifest.json). The generated [run-local brief](../results/m1/m1-live-20260915-002/decision_brief.md) remains preserved with its original wording.

## Evidence and independent contexts

The [dossier](../data/m1/dossier.json) freezes six principal sources and 16 claims: seven documented facts, one interpretation, three assumptions and five unknowns. Evidence cutoff: **2026-09-14T23:56:51.360466Z**. An official English translation companion accompanies the original Vietnamese strategy account. The [evidence review](../docs/EVIDENCE_REVIEW.md) records precise locators, dates, semantic checks, translations and limitations, including successful MOFA browser access alongside a direct HTTP 403.

Discovery jobs received identical dossiers and initial cases. Only architecture and assigned candidate identity differed. Each ran in a fresh temporary directory/context with tools and project instructions disabled. Later jobs received the archived artifacts appropriate to their role. Development helpers' reports were not used as research-worker outputs.

## Actual revision

Selected parent: [`centralized-v1`](../results/m1/m1-live-20260915-002/candidates/centralized-v1.json). Descendant: [`centralized-v1-r1`](../results/m1/m1-live-20260915-002/candidates/centralized-v1-r1.json). Feedback: objection **O1** in the actual [criticism](../results/m1/m1-live-20260915-002/criticism.json).

The critic found that advisory fallback links were marked inapplicable when their source actions were inactive, while suspension actions remained independently supported. All three candidates had this ambiguity. The allocator only counted objections on blocked or conditional actions; every score was zero, so its frozen lexical tie-break selected the centralized parent. This exposes a recruitment limitation, not an architectural preference derived from evidence.

The revision removed the misleading links and added:

```text
central-no-data-evaluation-design
  when: contribution_available == false
  prerequisite: coordination_authorized == true
  depends_on: central-suspend
  recommendation: draft evaluation requirements without contribution data,
                  model runs, new test datasets or external activity
```

The new recommendation covers language/cultural coverage, baseline questions, threshold-setting procedures, evaluator independence and evidence needed later. It explicitly cannot establish evaluation capacity. The five operational prerequisites remain unknown, and the existing pilot/assessment gates are preserved.

| Program | State | Supported | Conditional | Blocked | Inactive |
|---|---|---:|---:|---:|---:|
| Centralized parent | Initial | 3 | 2 | 0 | 1 |
| Centralized parent | Changed | 3 | 0 | 0 | 3 |
| Federated parent | Initial | 3 | 1 | 0 | 1 |
| Federated parent | Changed | 3 | 0 | 0 | 2 |
| Project-specific parent | Initial | 3 | 1 | 0 | 1 |
| Project-specific parent | Changed | 3 | 0 | 0 | 2 |
| Centralized descendant | Initial | 3 | 2 | 0 | 2 |
| Centralized descendant | Changed | 4 | 0 | 0 | 3 |

Counts are program behavior, not utilities. Inactive contribution-dependent options do not imply their unknown prerequisites were satisfied. The new action is inactive in the initial case and supported only in the changed case with drafting authorization and suspension dependency satisfied.

The preserved [structural diff](../results/m1/m1-live-20260915-002/semantic_diff.json) marks changes to fields, including explanatory text within prerequisites and advisory fallback links. Those flags alone do not establish changed decision logic. The separate [behavior comparison](../results/m1/m1-live-20260915-002/behavior_comparison.json) and the stricter control-signature check establish the new action independently; current validation rejects changes confined to prose, prerequisite reasons or advisory links.

The [fresh review](../results/m1/m1-live-20260915-002/review.json) retained the descendant and called the repair substantive but limited to planning. Its strongest objection is that the parent already preserved evaluation specifications in its prose. The additional action primarily makes that recommendation inspectable. No architecture wins, and no operational resilience or interaction advantage is demonstrated.

## Calls, usage and failures

Application configuration: `codex-cli 0.154.0`, `gpt-6-astra`, medium reasoning, existing ChatGPT sign-in. Development remained Astra Ultra with inherited native helpers. See [runtime details](../docs/RUNTIME.md).

| Launch | CLI invocations | Completed logical jobs / turns | Observed input tokens | Observed output tokens | Actual monetary cost |
|---|---:|---:|---:|---:|---|
| `m1-live-20260915-001` | 2 | 0 / 0 | Unknown | Unknown | Unknown |
| `m1-live-20260915-002` | 6 | 6 / 6 | 99,964 | 11,367 | Unknown |

Cached input tokens reported for the completed run: **0**. The complete work involved **8 CLI invocations**. Exact provider HTTP request/retry counts and usage from failed setup requests remain unknown; six logical jobs are not asserted to equal all internal model requests. Research token accounting excludes development helpers.

The first launch received HTTP 400 `invalid_json_schema`: `uniqueItems` was not permitted in the provider's structured-output schema. Both attempts and prompts are [preserved](../results/m1/m1-live-20260915-001/manifest.json). No valid output existed to reuse. A provider-compatible schema projection removed that keyword only for transmission; the local validator retained uniqueness checks. The second launch completed every job on its first attempt. No API-billed fallback was used.

## Checks actually executed

| Check | Result and scope |
|---|---|
| `PYTHONPATH=src python3 -m unittest discover -s tests -v` | **90 passed**, no skips after the live archive completed |
| `PYTHONPATH=src python3 -m artisan_swarm validate --run-dir results/m1/m1-live-20260915-002` | Dossier/claim/scenario integrity plus complete run replay passed |
| `PYTHONPATH=src python3 -m artisan_swarm replay --run-dir results/m1/m1-live-20260915-002` | Four programs, eight exact execution comparisons, zero model calls |
| `node --check src/artisan_swarm/static/app.js` | Passed |
| `git diff --check` | Passed |
| `bash scripts/set-about.sh` | Description applied and read back successfully |

Tests cover missing sources and invalid references; true/false/unknown conditions; cycles; inactive/blocked dependencies; unavailable contributions and unaffected work; an unrelated water-treatment scenario; no generated-code execution; immutable parents; feedback and lineage identity; corrupted checkpoint rejection; bounded retries and recovery; credential/log exclusion; provider schema projection; and UI/replay model-call prevention. Replay tests operate on temporary copies of actual live artifacts and make backend/process creation fail if attempted.

### Browser → API → artifacts → UI

The interface was checked with **agent-browser 0.37.1 / Chromium** at `http://127.0.0.1:8765`. [Actual browser screenshot](M1_INTERFACE.png); [machine-readable verification record](../results/m1/m1-live-20260915-002/verification.json).

- Page loaded real artifacts, then displayed **4 candidate cards**, `live · completed`, and review `retain`.
- Initial and hypothetical-disruption controls reached `/api/scenario` and rendered their corresponding dependency states without model calls.
- The evidence view displayed **6 HTTP(S) source links and 16 claims**, including locators and provenance. Source retrieval/semantic validation is documented separately; link rendering is not semantic verification.
- The before/after view included `central-no-data-evaluation-design`; the generated decision brief and Markdown endpoint rendered.
- Clicking **Offline replay** returned `passed`, **0** model calls.
- New-live-run dialog cancellation was exercised. The HTTP route's deliberate launch behavior is covered with an injected test backend; the actual six-job model run was launched through the CLI, avoiding a duplicate browser-launched experiment.
- Browser page-error and console-error checks returned no errors. The initial verification used an incorrect selector once; the actual evidence-tab selector was then used successfully. This was a verification-command correction, not an application defect.

## Publication and interpretation boundaries

A development publication audit reviewed public prompts, structured finals, evidence and brief; it found no material factual overclaims, credential patterns, raw session/account fields or full copyrighted documents. All six accepted outputs match preserved raw final artifacts. The audit is a development-model review, separate from the fresh application reviewer. Raw worker wording is preserved, including any limitations; the report clarifies that recommendations are not completed policy work.

The core dossier, schema, interpreter and evaluation contract were fixed during the completed run. Defensive replay checks and interface handling were improved during integration; the manifest records source hashes at run start. The final replay also passed stricter checks on frozen source hashes, lineage identifiers, retention identity and decision-relevant control structure. No saved candidate or review was rewritten to pass them.

**Remaining limits:** one known scenario; same base model across roles; no expert/practitioner assessment; unresolved real prerequisites; allocator all-zero tie; additional drafting recommendation rather than implemented resilience; unknown monetary cost/internal request counts; no matched baseline study or engine self-improvement.

**Next single research milestone:** M2, a fixed-engine comparison against matched single-agent and independent multi-start baselines on fresh cases, with budget accounting and independent/blinded assessment where feasible.
