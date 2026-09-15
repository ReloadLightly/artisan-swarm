# M1 runtime and provenance

## Development and research separation

The user selected **Codex Astra Ultra** for development; the parent kept that selection and native development helpers inherited it. Helpers implemented evidence, interpreter and UI components; their reports are not application-worker experimental outputs. No attempt was made to equate `xhigh` with Ultra or change the parent session's configuration.

The installed CLI is `codex-cli 0.154.0`. `codex --help`, `codex exec --help`, `codex features list`, `codex login status` and the non-secret model catalogue were inspected. The CLI reported ChatGPT sign-in and listed `gpt-6-astra` with `medium` support (and separate `max`/`ultra` options). No credentials or account session logs were read into the repository.

Official references checked during implementation:

- [Codex models](https://learn.chatgpt.com/docs/models): Ultra combines maximum reasoning with task delegation.
- [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode): ephemeral jobs, structured final output and existing authentication.
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference): reasoning effort, forced login method, project instructions and tool controls.

## Application jobs

Each job starts a new `codex exec` process in a fresh temporary directory, with no repository project instructions or previous worker context. Discovery receives the same frozen dossier and initial case; only assigned architecture and candidate ID differ. The later critic sees the three archived parents and changed-case traces; the reviser sees selected parent and recorded feedback; the reviewer gets a fresh context and the unchanged validation contract.

The explicit application settings are `gpt-6-astra`, `model_reasoning_effort="medium"`, `forced_login_method="chatgpt"`, `--ignore-user-config`, `--ephemeral`, `--sandbox read-only`, `project_doc_max_bytes=0`, and `web_search="disabled"`. Model instructions identify a finite research artifact job and prohibit implementation, delegation, tools and external actions. Shell, apps, plugins, hooks, memories, browsers, image tools and multi-agent features are disabled. API-key environment variables are excluded without inspecting their contents. Research requests never use an API-billed fallback.

Each request preserves the exact prompt, instructions, local output schema, provider-compatible schema and requested settings. The provider's output schema does not accept `uniqueItems`; the wire projection omits that keyword and the unchanged local validator enforces uniqueness. This does not alter the candidate contract or admit invalid references.

Final model outputs are saved before validation. Each failure is retained. A job has at most two CLI attempts, each limited to 420 seconds; a two-second delay separates attempts. Schema-invalid output gets explicit validation feedback and its previous final output in the repair prompt. CLI-internal bounded HTTP retries are distinct from application attempts; their exact count is unknown. Exhaustion stops that run for diagnosis rather than looping. A corrected engine may begin a new versioned run; valid outputs in recoverable runs are reused. A valid final saved just before interruption is recovered without another call.

## What accounting means

`cli_invocations` counts launched CLI jobs/attempts. `completed_turns` and input/cached-input/output tokens come from allowlisted CLI JSONL events. These are observable quantities; they are not assumed to equal the platform's internal number of HTTP/model requests. The CLI's requested model/effort are recorded; its JSONL does not independently echo the resolved model. Exact provider requests, retries and monetary costs remain `null` (unknown). Development-helper usage is separate and not included as research usage.

Raw stdout/stderr remains under ignored `.local/research/`. Only final structured outputs, prompts and selected metadata are public. No raw session/account logs, hidden reasoning, credentials or full source PDFs are published.

## State and replay

Inputs, prompts, outputs, attempts, candidate programs, executions, criticism, lineage and review are immutable snapshots. `manifest.json` is a mutable checkpoint index; existing hashed artifacts must match before its index advances. `replay.json` records the latest deterministic replay and can be refreshed. The public hash manifest detects changes; it is an integrity check, not a cryptographic third-party attestation.

The run records the pre-run Git base and exact source file hashes. Core interpreter, evidence, schemas and fixed feedback contract are checked on resume and replay. Source hashes describe the code at run start even when documentation/interface or defensive handling is subsequently improved. A running process retains its imported code; subsequent fixes must not be misreported as having run earlier.

Replay never constructs a model backend. It validates dossier and references, re-executes all saved programs in both states, compares exact traces, recomputes recruitment and semantic changes, and checks live-output identity and lineage. It does not regenerate a probabilistic model response or re-retrieve the web. The archived structural diff flags changed fields (which can include prose within prerequisites or advisory links); current validation separately compares decision-relevant control signatures, excluding prose and advisory links, so those changes alone cannot establish a revision.

## Local interface

The stdlib HTTP server binds `127.0.0.1` only. GET, page refresh, scenario toggling and offline replay never call models. A deliberate new-live-run control launches a fresh directory and the six-job workflow in a background thread. Local Host, same-origin and CSRF checks protect state-changing requests. Untrusted artifact prose renders as text; only HTTP(S) source links are active. No model credentials reach the browser.

The UI and CLI share the same artifact archive and interpreter. A supported action means a recommendation under scenario conditions, not that a country consented or an external action took place.
