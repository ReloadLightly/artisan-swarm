# M1 handoff

## Delivered

M1's live application cycle completed, its actual outputs replayed, 90 tests passed, and the localhost interface was browser-verified. The fresh model reviewer retained a limited planning repair. The descendant recommends a separately guarded no-data evaluation-requirements drafting step; no evaluation matrix or operational pilot was produced. All original alternatives remain preserved.

- [Decision brief](../reports/M1_DECISION_BRIEF.md)
- [Results, exact checks and limitations](../reports/M1_RESULTS.md)
- [Reviewed run manifest](../results/m1/m1-live-20260915-002/manifest.json)
- [Before/after behavior](../results/m1/m1-live-20260915-002/behavior_comparison.json)
- [Runtime and worker isolation](RUNTIME.md)
- [Evidence review](EVIDENCE_REVIEW.md)
- [Preserved failed setup](../results/m1/m1-live-20260915-001/manifest.json)

## Open and replay

From `/home/roland/actir/artisan-swarm`:

```bash
PYTHONPATH=src python3 -m artisan_swarm serve --run-dir results/m1/m1-live-20260915-002 --port 8765
```

Open **http://127.0.0.1:8765**. Page loads, refreshes and scenario changes do not call models. The interface has distinct offline replay and deliberate new-live-run controls.

```bash
PYTHONPATH=src python3 -m artisan_swarm replay --run-dir results/m1/m1-live-20260915-002
PYTHONPATH=src python3 -m artisan_swarm validate --run-dir results/m1/m1-live-20260915-002
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

No third-party Python dependencies, model downloads or authentication are needed for replay/UI. A deliberately new live run requires the installed supported Codex CLI and existing ChatGPT sign-in:

```bash
PYTHONPATH=src python3 -m artisan_swarm live --run-dir results/m1/my-new-run
```

Reuse that run directory to resume missing work. Do not reuse the failed schema-setup directory to overwrite its history. The completed directory opens/replays existing output without another model cycle.

## Accounting

Successful run: six jobs, six CLI invocations, six completed turns; 99,964 observed input and 11,367 output tokens, zero reported cached input tokens. The first setup launch added two failed CLI invocations with unknown usage. Provider-internal request/retry counts and actual monetary costs remain unknown. Development helpers are separate from application research jobs.

## Repository verification

The About description was applied and read back with the versioned helper. Publication uses the existing `main` branch and preserves prior history; no license change was made. The final delivery message reports the verified full local and remote commit SHAs. Recheck the current checkout independently with:

```bash
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
git ls-remote origin refs/heads/main
git status --short
```

The run manifest records the pre-run Git base and exact source hashes. Runtime evolution and the final verification are described in the results report.

## Next

M2: compare the fixed engine with matched single-agent and independent multi-start baselines on fresh cases. The all-zero recruitment tie and modest planning change are reasons to test the interaction effect, not evidence that it already helps.
