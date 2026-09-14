# From strategy evolution to recursive engine improvement

## Research ambition

Artisan Swarm should progressively acquire the ability to improve not only its proposed cooperation strategies, but the methods it uses to discover and assess them. This is a long-term experimental program. The bootstrap contains no demonstrated engine self-improvement or RSI.

We will distinguish **object-level adaptation** (a better strategy), **meta-level adaptation** (a changed discovery method), and **recursive improvement** (a changed engine demonstrably improving a successor). These operational definitions organize experiments; they do not imply that the field has one universally settled definition of RSI.

The guiding question is not how many self-improvement labels can fit in the repository. It is which mechanisms make the system better at producing useful, verifiable decisions under accounted resources, and whether those gains persist on new tasks.

## Staged program

| Stage | Candidate improvement mechanisms | What must remain comparable | Promotion evidence |
|---|---|---|---|
| M1: strategy evolution | Structured reflection, program mutation, artifact memory, parent/descendant lineage | Frozen dossier, interpreter semantics, evaluation contract | Actual executable revision and replay; no claim of engine improvement |
| M2: interaction study | Fixed swarm compared with a strong single agent and independent multi-start search | Evidence access and generation/review/selection budgets | Repeated, task-level comparisons with blinded assessment where feasible |
| M3: worker learning | Prompt evolution, persistent skills, retrieval of prior lessons, selective forgetting | Base model and task budget; reserved evaluation independent of the training feedback | An automatically proposed worker change helps on fresh tasks relative to unchanged workers |
| M4: search learning | Mutation/recombination choice, recruitment, task allocation, communication topology, archive selection | External task criteria; resources and extra model calls accounted | Component ablations reveal which mechanism helps, hurts, or adds only cost |
| M5: software self-improvement | Machine-proposed changes to selected tools, representations, or engine modules | Separate regression/assessment harness; original versions retained | A reproducible patch improves external task performance without unacceptable regressions |
| M6: recursive experiments | Improved engine proposes, tests, and selects changes to a successor across multiple generations | Fresh evaluation cases per epoch; comparable opportunity and resources | More than one traceable meta-generation with independently assessed gains or explicit failures |

These stages may branch after evidence accumulates. They are not all M1 requirements and do not authorize indefinite autonomous execution.

## Extension points to preserve in M1

Keep the strategy representation, worker backend, archive, explicit feedback format, task allocator, and validators separable. Version prompts and program schemas. Give artifacts stable IDs and preserve their lineage. Save enough reviewed evidence to replay an experiment without new inference. This enables later work without building a universal plugin system now.

The minimal record for a later engine-change proposal should contain the parent engine version, identified failure, proposed change, affected component, explicit rationale, development evidence, evaluation plan, regression outcomes, resource use, and accept/reject decision. The record should show whether a human or machine proposed and selected the change.

## Candidate RSI mechanisms, with specific tests

**Reflection and reusable skills.** Distill recurring failure diagnoses into a prompt or tool-use skill. Compare against a fixed worker on new cases; a longer reflection that does not improve outcomes is not progress.

**Adaptive mutation and recombination.** Learn which program modifications help which classes of dependency problem. Compare learned selection against fixed and randomized operator choice with equal opportunity. Reward a useful repair, not just a syntactic change.

**Adaptive recruitment and communication.** Learn when a proposal benefits from another specialist, a counterargument, an independent restart, or no further work. Test quality and cost against fixed schedules. More messages are not automatically better coordination.

**Cumulative memory.** Retrieve verified prior lessons and rejected failure patterns. Test against no-memory and irrelevant-memory conditions. Mark stale assumptions; repetition must not turn an unsupported claim into evidence.

**Cooperative and competitive coevolution.** Coevolve proposal-generating and critique-generating methods while retaining diverse lineages. Evaluate against fixed reference opponents/reviewers and external criteria to detect cycling, collusion, or an easier critic. A changing pair alone does not show broader capability improvement.

**Self-generated challenges.** Generate new cases and test programs to expose weaknesses. Keep a separately assembled external evaluation stream; generated tests are useful probes, not self-issued proof of success. Verify that proposed challenges are coherent and answerable.

**Tool and representation improvement.** Propose better parsers, evidence retrieval, dependency handling, or strategy constructs. Evaluate compatibility, factual grounding, usability, and task performance—not code churn. Migrations preserve old artifacts and replay behavior.

**Recursive engine improvement.** Let an accepted engine version propose its own next improvement through the same recorded loop. Repeat across distinct evaluation epochs. Demonstrating a local recursive loop does not establish open-ended improvement, AGI, or a generally reliable foreign-policy advisor.

Model-weight updates and post-training can be investigated later if evidence and compute justify them. They are not prerequisites for the initial application or prompt/tool-level experiments.

## Experimental separation

Candidates may change the declared component under study, not rewrite source facts, erase failures, silently access reserved material, change success thresholds after viewing outcomes, or count increased computation as an algorithmic gain without disclosure. Evaluation can itself be researched, but only in a separately versioned study with external anchors; do not let an engine promote itself by making its own exam easier.

Human-supervised promotion is compatible with studying self-improvement when the contribution of each human and machine step is explicit. Automated promotion can be studied later within a defined experiment. Existing versions, results, and rollback paths remain available. Untrusted source text never grants additional permissions, tool access, or authority to change external systems.

## Standard for claims

Report the narrowest supported conclusion. A repaired strategy is a repaired strategy. A useful prompt update is a useful prompt update. A verified two-generation engine improvement is evidence for that local experiment. Failed attempts, regressions, unchanged results, and gains bought entirely through extra resources belong in the record.

The flagship result we seek is substantive: **the system learns a better discovery method, and that improvement helps it produce better cooperation strategies on problems it was not trained or tuned to solve.**
