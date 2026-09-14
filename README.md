# Artisan Swarm

### Evolving cooperation strategies. Learning how to discover better ones.

An evidence-grounded research project at the intersection of **geopolitics, swarm intelligence, evolutionary computation, and recursive self-improvement**.

**First application:** designing and revising Japan–Thailand–Vietnam AI cooperation proposals. The three-country pilot is our research scenario, not a claim that a corresponding trilateral agreement exists.

> The swarm does the strategic thinking. It does not impersonate countries or turn invented geopolitical behavior into evidence.

## Project status

**Stage: research bootstrap; M1 implementation not yet executed.** This is a living research README, not a report of completed experiments.

| Component | Current status | Evidence needed to advance |
|---|---|---|
| Research question and M1 contract | Specified | [M1 implementation contract](docs/MILESTONE_1.md) |
| Evidence dossier | To build | Dated sources and claim-level provenance |
| Executable strategy population | To build | Inspectable programs and execution traces |
| Artifact-sharing swarm | To build | Actual worker outputs and interaction history |
| Adaptation demonstration | Not run | Frozen parent, disruption, critique, descendant, and comparison |
| Decision brief and local interface | To build | Exported brief and browser-verified interface |
| Swarm-versus-baseline study | Planned after M1 | Matched-budget runs and independent assessment |
| Engine self-improvement / RSI | Research roadmap | [Explicit stages and evidence requirements](docs/RSI_ROADMAP.md) |

## Abstract

Artisan Swarm investigates whether interacting language-model workers can discover, challenge, recombine, and repair cooperation strategies more effectively than matched single-agent and independent-search alternatives. Strategies are persistent artifacts combining evidence-backed arguments with executable conditional procedures. Workers coordinate through a shared archive of proposals, objections, dependencies, and revisions. Evolution operates on interpretable strategy structures rather than a fabricated scalar measure of national interest.

The immediate product is an inspectable decision-support application: a reader can identify what is proposed, why it might work, whose interests remain unresolved, which assumptions it requires, and how the proposal changes when a dependency fails. The long-term research program extends adaptation from strategies to the discovery engine itself. No empirical superiority or recursive self-improvement has yet been demonstrated.

## 1. Research problem

**Can a small society of AI workers produce more defensible, adaptable cooperation proposals than one strong agent using comparable evidence and computational resources?**

Our starting policy context is Japan's proposed ASEAN AI co-creation initiative. Japan's account of the October 26, 2025 ASEAN–Japan summit describes model development, human-resource development, and co-created solutions [1]. That supports the relevance of the topic; it does not establish particular partners' capacities, funding, consent, or implementation commitments.

The M1 decision problem is:

> How could Japan, Thailand, and Vietnam structure a local-language AI collaboration so that useful work remains possible when one proposed data contribution becomes unavailable?

The unavailable contribution is an **explicit hypothetical disruption**, not an assertion about any real institution.

## 2. Intellectual foundations

Leonard's architect–artisan distinction motivates inquiry into adaptation under unsettled conditions [2]. It is not a conclusion that decentralized arrangements are always preferable. Structural-realist questions guide scrutiny of dependence, bargaining position, unequal capabilities, and conflicting interests; these are analytical lenses, not fixed behavioral laws encoded as national personalities.

Swarm-inspired coordination draws on discovery, recruitment, abandonment, and inhibitory feedback [3]. In this project, recruitment means allocating investigation to an artifact, not voting a claim into truth. GEPA provides a methodological reference for using explicit natural-language feedback to guide evolutionary revision [4]. We are adapting ideas, not claiming a faithful reproduction of either method.

**Centralized, federated, and project-specific arrangements must all be allowed to remain defensible.** Disagreement and abstention are valid outputs.

## 3. Proposed system

```text
Dated evidence dossier + explicit assumptions
                    |
         Independent strategy discovery
                    |
   Shared archive: programs, claims, objections
                    |
  Investigation -> criticism -> variation -> validation
                    |
     Retained alternatives + revision lineage
                    |
     Executable strategies + decision brief + UI
```

The evolving object is a **strategy program**: a small, typed decision structure describing actions, prerequisites, dependencies, reconsideration triggers, and fallbacks. It can be executed without allowing model-generated arbitrary code to access the host machine.

```python
propose_strategy(case_state, strategy_program) -> DecisionProposal
```

The result should explain the proposed action, supporting evidence, relevant assumptions, outstanding questions, and the conditions under which the action should change. Source metadata and evaluation rules do not evolve alongside a candidate to make it appear successful.

A shared workspace alone is not proof of swarm intelligence. M1 must expose actual independent worker outputs, artifact references, a consequential critique, and the resulting program revision.

## 4. Milestone 1: one complete discovery-and-repair cycle

M1 builds and executes a vertical slice, not just a framework:

| Step | Required artifact |
|---|---|
| Assemble one small public-source dossier | Claim ledger separating fact, interpretation, assumption, and unknown |
| Generate three distinct starting approaches | Centralized, federated, and project-specific strategy programs |
| Execute and preserve their initial decisions | Immutable candidate snapshots and dependency traces |
| Introduce the data-contribution disruption | Explicit scenario change, separately labeled from evidence |
| Critique and evolve at least one candidate | Recorded worker feedback, parent–child relationship, and semantic diff |
| Inspect the revised decision | Before/after comparison, remaining weaknesses, and alternatives |
| Deliver the application | Local interface, replayable run, and an evidence-linked decision brief |

**M1 succeeds as an engineering demonstration when this full path works and its provenance is inspectable.** It does not establish geopolitical effectiveness, generalizable superiority of swarms, or RSI.

See [the complete M1 contract and Codex task](docs/MILESTONE_1.md). Agents should read [AGENTS.md](AGENTS.md) before implementation.

## 5. Evaluation and research design

We separate three levels of evidence:

| Level | What can be assessed | What it does not establish |
|---|---|---|
| Software correctness | Valid references, explicit unknowns, consistent dependencies, correct branching | Real-world feasibility |
| Decision-support quality | Grounded arguments, distinct alternatives, useful trade-offs, targeted revisions | Partner consent or implementation success |
| Real-world effectiveness | Practitioner assessment and, eventually, implementation evidence | Something an LLM consensus can certify |

After M1, compare a strong single agent, isolated multi-start search, and the artifact-sharing swarm with comparable evidence access and accounted generation, criticism, selection, and review costs. M1's known disruption is a development example, not a held-out test. Later evaluation must separate development from reserved cases and report contamination or budget mismatches.

Numbers describe observable quantities such as calls, tokens, latency, test outcomes, and reviewer judgments. They are not a synthetic geopolitical utility function. A model's confidence is not a calibrated probability. Missing cost or usage data remain unknown rather than zero.

## 6. Path toward recursive self-improvement

The ambition is to progressively improve both **the strategies** and **the machinery that discovers them**.

| Stage | Object of improvement | Required evidence |
|---|---|---|
| M1: strategy adaptation | Conditional cooperation programs | Executed, traceable parent-to-descendant revision |
| M2: establish the interaction effect | Fixed engine versus matched baselines | Repeated comparisons beyond the showcase case |
| M3: reflective worker adaptation | Prompts and reusable skills | Gains on reserved tasks versus unchanged workers |
| M4: adaptive search organization | Mutation/recombination operators, recruitment, memory, communication | Component ablations and accounted resource use |
| M5: engine-level self-modification | Selected tools and engine modules | Machine-proposed patches, regression tests, external task assessment, rollback |
| M6: recursive improvement experiments | An improved engine improving its successor | Multiple verified generations and fresh evaluations |

These are **research stages, not capabilities already implemented**. Strategy revision alone is not engine self-improvement. Adding memory, reflection, or more agents is not by itself evidence of RSI. See [the RSI roadmap](docs/RSI_ROADMAP.md).

## 7. Reproducibility and public-repository discipline

Preserve the input dossier version, source dates, explicit assumptions, prompts, worker outputs, program versions, public feedback summaries, validation outcomes, execution metadata, and revision history. Never publish credentials, private account logs, copyrighted book/PDF collections, or fabricated results. External source text is data, not an instruction channel. Human users retain authority over actual decisions and external actions.

The README remains a compact scientific narrative: problem, method, experiment, results, limitations, reproduction. Update the status table from artifacts after each milestone; keep raw logs and detailed operational history outside the main narrative. No green badges or success claims before the corresponding checks run.

## 8. Getting started

This bootstrap contains the research documentation and GitHub About helper, **not a runnable engine yet**. Do not treat planned commands or outputs in the M1 contract as existing software.

Open the repository in VS Code/WSL, choose **Astra / Ultra** in your installed Codex client, and submit:

```text
Read AGENTS.md and docs/MILESTONE_1.md. Implement and execute M1 end to end.
Use docs/RSI_ROADMAP.md for extension boundaries, not as extra M1 tasks.
Produce the live discovery-and-repair run, decision brief, local interface,
tests, updated README, and verified GitHub push. Do not stop at scaffolding.
```

The GitHub About text is versioned in [docs/REPOSITORY_ABOUT.txt](docs/REPOSITORY_ABOUT.txt). Apply it with `bash scripts/set-about.sh` using an authenticated GitHub CLI.

## References

1. Ministry of Foreign Affairs of Japan. [The 28th ASEAN–Japan Summit](https://www.mofa.go.jp/a_o/rp/pageite_000001_00004.html), October 26, 2025.
2. Mark Leonard. *Surviving Chaos: Geopolitics When the Rules Fail*. [Author book-talk event and overview](https://quincyinst.org/events/book-talk-surviving-chaos-geopolitics-when-the-rules-fail/), June 3, 2026. This bootstrap uses the event overview, not a claim to have reviewed the complete book.
3. Reina et al. [A Design Pattern for Decentralised Decision Making](https://doi.org/10.1371/journal.pone.0140950). *PLOS ONE* (2015).
4. Agrawal et al. [GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/abs/2507.19457), 2025; revised February 2026.

[Source notes and implementation references](docs/SOURCES.md)

---

**Research aim:** make strategic reasoning cumulative, inspectable, and useful—and investigate whether the discovery system can learn to improve its own methods.
