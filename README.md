# Artisan Swarm

### Evolving cooperation strategies. Learning how to discover better ones.

An evidence-grounded research project connecting **geopolitics, swarm intelligence, evolutionary computation, and recursive self-improvement**.

**First application:** proposed Japan–Thailand–Vietnam local-language AI cooperation. This is a research scenario, not an assertion that a trilateral pilot or agreement exists.

## Abstract

Artisan Swarm turns a public-source dossier into executable conditional cooperation proposals, exposes them to criticism, and preserves model-mediated revisions with their evidence and execution traces. Milestone 1 now implements and executes this complete path: six isolated application research jobs generated three architectural alternatives, criticism, a descendant and a fresh review; offline replay reproduced eight executions without model calls.

The reviewer retained a limited planning repair: the centralized descendant adds a guarded action recommending that evaluation requirements be drafted without data. The parent already allowed no-data planning. This demonstration establishes traceable program revision, not operational resilience, architectural superiority, an interaction advantage or recursive engine improvement.

**Read the [decision brief](reports/M1_DECISION_BRIEF.md), [results and checks](reports/M1_RESULTS.md), or [handoff](docs/HANDOFF.md).**

## 1. Research question

**Can interacting AI workers produce more defensible, adaptable cooperation proposals than one strong agent with comparable evidence and computational resources?**

Japan's October 2025 ASEAN–Japan summit account describes a proposed AI co-creation initiative involving model development, skills and co-created solutions [1]. That establishes a policy anchor, not specific partners' consent, funding or capacity. The frozen dossier also represents ASEAN, Thai and Vietnamese institutional perspectives, including Vietnam's August 2026 strategy announcement. Claims describe official statements and reported capabilities within their source scope; they do not establish pilot readiness.

The M1 decision question is: **what remains defensible when an anonymous proposed data contribution becomes unavailable?** This disruption was known during development and is explicitly hypothetical, not a held-out test or a real institutional refusal.

## 2. Foundations

Leonard's architect–artisan distinction motivates adaptation under unsettled conditions [2]. Structural-realist questions guide scrutiny of dependence, bargaining position, unequal capabilities and unresolved interests; they are analytical lenses, not simulated national personalities.

Swarm-inspired discovery, recruitment and inhibitory feedback motivate artifact-based coordination [3]. GEPA motivates explicit natural-language criticism as an input to revision [4]. M1 adapts these ideas rather than reproducing those methods or establishing their effectiveness in policy design. Centralized, federated and project-specific arrangements all remain eligible alternatives.

## 3. Method

```text
Frozen sources + typed claims + scenario assumptions
                       ↓
Three independent discovery contexts → archived strategy programs
                       ↓
Initial execution → hypothetical disruption → changed execution
                       ↓
Cross-candidate criticism → deterministic recruitment → model revision
                       ↓
Fresh review + preserved alternatives → brief + local UI + offline replay
```

Programs use a constrained JSON representation and the Python interface `propose_strategy(case_state, strategy_program)`. Named boolean facts support true, false and unknown conditions. Guards, prerequisites and dependency graphs determine whether an action is supported, conditional, blocked or inactive. Strings never execute as Python or shell code. Supported means recommended under modeled conditions, not that an external action happened.

The dossier distinguishes documented fact, interpretation, assumption and unknown. Data availability and authorization to draft a proposal are scenario assumptions. Real partner consent, local and pooled processing permissions, funding and evaluation capacity remain unknown. A [model semantic spot-check](docs/EVIDENCE_REVIEW.md) is separate from source-ID validation and is not independent expert review.

Application workers use **`gpt-6-astra`, medium reasoning**, through the installed ChatGPT-authenticated Codex CLI. Each receives a fresh, isolated context; discovery jobs do not see one another's outputs. The development session retained **Astra Ultra** with native helpers. Development helpers are not counted as research workers. See [runtime, isolation and accounting](docs/RUNTIME.md).

## 4. Experiment and status

**M1 engineering demonstration: completed on September 15, 2026.** The [implementation contract](docs/MILESTONE_1.md) remains the evaluation boundary.

| Component | Actual result | Inspectable evidence |
|---|---|---|
| Public-source dossier | 6 sources; 16 typed claims | [Dossier](data/m1/dossier.json), [source review](docs/EVIDENCE_REVIEW.md) |
| Independent discovery | 3 live starting programs | [Candidates](results/m1/m1-live-20260915-002/candidates/) |
| Criticism and recruitment | 4 model objections; all allocation counts tied at zero | [Criticism](results/m1/m1-live-20260915-002/criticism.json), [selection](results/m1/m1-live-20260915-002/selection.json) |
| Model-mediated revision | 1 preserved descendant, linked to objection O1 | [Revision](results/m1/m1-live-20260915-002/revision.json), [lineage](results/m1/m1-live-20260915-002/lineage.json) |
| Fresh review | Retain; limited planning repair, a model judgment | [Review](results/m1/m1-live-20260915-002/review.json) |
| Execution and replay | 4 programs × 2 states; replay passed with zero calls | [Executions](results/m1/m1-live-20260915-002/executions/), [replay](results/m1/m1-live-20260915-002/replay.json) |
| Local application | Browser-verified scenario, evidence, diff, brief and replay | [UI implementation](src/artisan_swarm/ui.py), [verification report](reports/M1_RESULTS.md) |
| Baselines / RSI | Planned; not demonstrated | [Roadmap](docs/RSI_ROADMAP.md) |

The first launch failed twice because the provider rejected the `uniqueItems` output-schema keyword. Those failures are [preserved](results/m1/m1-live-20260915-001/manifest.json). The provider schema projection was repaired while local uniqueness validation stayed intact. No valid discovery output was discarded.

The [completed run manifest](results/m1/m1-live-20260915-002/manifest.json) records **6 logical jobs, 6 CLI invocations and 6 completed turns**, with **99,964 input tokens and 11,367 output tokens** observed. There were 8 CLI invocations across both launches. The two failed setup attempts have unknown usage. Exact provider request/retry counts and actual monetary cost are unknown; no separately billed API fallback was used.

## 5. Results: concrete before / after

The critic identified a mismatch between inactive contribution-dependent actions and their advisory fallback annotations. The allocator counted objections on blocked or conditional actions; all scores were zero because the objections targeted inactive or supported actions. **Centralized selection therefore came solely from the lexical tie-break**, not a finding that centralization was better.

| Property | Parent `centralized-v1` | Descendant `centralized-v1-r1` |
|---|---|---|
| Response to unavailable data | Independently guarded suspension; evaluation planning mentioned in its prose | Preserves suspension and adds a separately guarded evaluation-requirements drafting action |
| New action's logic | No separate action | `contribution_available == false`; requires `coordination_authorized == true`; depends on `central-suspend` |
| Changed-case supported actions | 3 preparatory recommendations | 4 preparatory recommendations |
| Data-dependent options | Pool design, pilot and assessment inactive | Same three remain inactive |
| Operational unknowns | Consent, both permissions, funding, evaluation capacity | All five remain unknown |

The worker removed misleading fallback links and added `central-no-data-evaluation-design`. Its output is an executable **recommendation to draft** requirements; the system did not author an evaluation matrix, run an assessment or acquire data. The [behavior comparison](results/m1/m1-live-20260915-002/behavior_comparison.json) confirms the additional action independently of descriptive edits in the [structural diff](results/m1/m1-live-20260915-002/semantic_diff.json).

The fresh review calls this substantive but limited to planning. Its strongest objection is that the parent already preserved no-data specifications. The extra supported action is not a utility score or proof of improved geopolitical outcomes. All three parents and their initial decisions remain available.

## 6. Limitations

This is one development case and one repair cycle. Discovery already received the disruption assumption in the shared dossier; there was no held-out challenge. The same base model performed all research roles. The recruitment rule failed to distinguish the actual objections, and a more explicit planning recommendation does not demonstrate useful real-world work or operational resilience.

The evidence audit and fresh review are model judgments. Permissions need qualified review; partner preferences, cost-sharing, resources and evaluation arrangements remain unresolved. There are no behavioral probabilities, fabricated national utilities, stakeholder commitments or expert endorsements. A fixed-engine baseline study is required before claiming that interaction helps. M1 does not modify the discovery engine recursively.

## 7. Reproducibility

Requires Python **3.10+**; the application and tests have no third-party Python dependencies. Run from the repository root in the existing WSL workspace.

```bash
# Inspect the actual preserved run at http://127.0.0.1:8765
PYTHONPATH=src python3 -m artisan_swarm serve --run-dir results/m1/m1-live-20260915-002 --port 8765

# Offline replay: zero new model calls; no authentication or web access needed
PYTHONPATH=src python3 -m artisan_swarm replay --run-dir results/m1/m1-live-20260915-002

# Evidence integrity and complete-run validation
PYTHONPATH=src python3 -m artisan_swarm validate --run-dir results/m1/m1-live-20260915-002

# Tests, including replay of the actual archive with model/process calls forbidden
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

To deliberately start another live run, use an unused directory (or the UI's **New live run** control):

```bash
PYTHONPATH=src python3 -m artisan_swarm live --run-dir results/m1/my-new-run
```

Live execution requires the supported Codex CLI and existing ChatGPT sign-in. The same command resumes missing work in that directory; valid outputs are reused. Opening, refreshing or changing the UI scenario never calls a model. The offline replay and new-live-run controls are separate.

**Executed checks:** 90 tests passed, JavaScript syntax passed, dossier validation passed, eight execution comparisons passed, and browser checks covered page loading, source/claim display, both scenarios, before/after view, review, brief download, cancellation and offline replay without console/page errors. Details and qualifications are in [M1 results](reports/M1_RESULTS.md).

Public artifacts preserve prompts, final outputs, hashes, provenance, attempts and lineage. Raw CLI account/session events stay local and ignored. No credentials, full copyrighted PDFs, license changes or model-weight downloads are included. The versioned GitHub [About description](docs/REPOSITORY_ABOUT.txt) was applied and verified with `bash scripts/set-about.sh`.

## 8. Roadmap

| Stage | Object of improvement | Required evidence |
|---|---|---|
| M1 — completed | Conditional strategy programs | This live revision, review, execution and replay |
| **M2 — next** | Fixed-engine interaction effect | Matched single-agent and independent-search baselines; fresh cases and accounted resources |
| M3 | Worker prompts and reusable skills | Gains on reserved tasks versus unchanged workers |
| M4 | Search organization, recruitment and memory | Component ablations and accounted resource use |
| M5 | Selected engine code and tools | Machine-proposed patches, regression checks, external assessment and rollback |
| M6 | Recursive engine improvement | Multiple verified generations and fresh evaluations |

The backend, representation, archive, feedback, allocator and validators remain separate extension points. Later stages are research questions, not implemented capabilities. See [RSI boundaries](docs/RSI_ROADMAP.md).

## References

1. Japan MOFA. [The 28th ASEAN–Japan Summit](https://www.mofa.go.jp/a_o/rp/pageite_000001_00004.html), October 26, 2025. Complete M1 policy references, including ASEAN, NECTEC and Vietnam Government News, are in the [frozen dossier](data/m1/dossier.json).
2. Mark Leonard. *Surviving Chaos: Geopolitics When the Rules Fail*. [Author book-talk overview](https://quincyinst.org/events/book-talk-surviving-chaos-geopolitics-when-the-rules-fail/), June 3, 2026. Motivation from the overview; the full book was not reviewed.
3. Reina et al. [A Design Pattern for Decentralised Decision Making](https://doi.org/10.1371/journal.pone.0140950). *PLOS ONE* (2015).
4. Agrawal et al. [GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/abs/2507.19457), 2025; revised February 2026.

[Bootstrap source notes](docs/SOURCES.md) · [Agent instructions](AGENTS.md) · [Runtime and provenance](docs/RUNTIME.md)
