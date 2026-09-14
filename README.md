# Vres-OS — 0.2.0-alpha.1

**Controlled-live-test preview. Not production-verified.**

Vres-OS is a new, modular Python/PostgreSQL runtime and Claude Code plugin. The Chairman is the conversational entry point. The runtime preserves task state, documented knowledge, approval-backed procedures and evidence. It draws on AIGO's engineering principles; it does **not** bundle or inherit the validated AIGO runtime/test suite.

Start here: [Windows installation](docs/INSTALL-WINDOWS.md) · [live verification](docs/LIVE-VERIFICATION.md) · [release evidence](docs/RELEASE-VALIDATION.md) · [limitations](docs/KNOWN-LIMITATIONS.md).

## What this preview implements

- PostgreSQL migrations, explicit native-session/task binding and bounded recovery packets.
- Lifecycle hooks for startup, user prompts, compaction, stop/end and protected-validator completion.
- Separate secure first-run console; Windows credential-store writes; no passwords in model prompts.
- Read-only onboarding: fingerprints, project-scoped deduplication, bounded text/CSV/Office/PDF extraction and review queues.
- Knowledge sources, typed semantic relations with additive evidence, findings, approval-backed governance and immutable statements.
- Accepted procedure contracts, correction history, retry-safe baseline registration, candidate records and explicit user decisions.
- Protected Fable/high validator role, observed transcript/model checks, task/artifact fingerprints, stale-PASS rejection.
- Model policy recommendations, advisory telemetry and bounded read-only Codex review execution.
- Optional local embedding jobs with retry/lease protection and a bounded semantic fallback when pgvector is absent.
- Research refresh records tied to an actual reviewed JSON artifact.
- A staged Windows installer, user-scoped personal plugin, matching update path and data-preserving uninstall.
- Dedicated company-authority tools for company-wide source, durable-knowledge and registry publication, shared capability catalog registration, and accepted procedure baselines. These use preview → persisted user approval → exact redacted subject fingerprint → write, and the service layer fails closed when the approval is absent or does not match. Procedure approvals bind the full reusable contract, implementation reference and any initial baseline measurements.
- Host-attested procedure replay evidence. Runtime-classified paired runs are bound to the same input digest, exact baseline/candidate contract fingerprints, a frozen validation context and a host-observed protected-validator result before the Pareto gate can authorize promotion. Caller-reported telemetry cannot enter that path, and the trusted runtime-run/promotion sinks are not exposed through MCP.
- A registered deterministic procedure executor for the code-owned `vres:builtin:json-recipe:v1` implementation family. Its bounded JSON recipe operations are `copy`, `rename`, `set`, `delete`, `pick`, `sort`, `sum` and `count`; the worker is invoked without a shell, enforces input/output/time budgets, validates contracts, hashes canonical input/output and records runtime-owned evidence. The recipe language exposes no arbitrary Python, imports, shell, filesystem or network operation.
- Project-scoped automatic promotion for that registered executor path only: protected contracts must remain identical, baseline and candidate must run on the exact same input, protected validation must attest output equivalence/no protected regression, and the candidate must be Pareto-superior. Deterministic recipes do not invent a stored quality score; host-observed output equivalence supplies the no-regression quality basis for the gate.

These mechanisms have different evidence levels. Local tests execute Python/parsers/subprocesses. GitHub CI also executes the full suite against PostgreSQL 16, including migrations 010–011, company-authority journeys, replay → protected validation → attestation → promotion, and a real bounded-worker baseline/candidate journey whose measurements are produced by the registered executor. Windows PowerShell/credential handling, actual Claude/Codex integration, target-Windows execution of the bounded worker and real embeddings still need their live gates.

## What is deliberately not claimed

**General automatic optimization is still held.** Project-scoped procedures using the registered deterministic JSON executor can now enter the measured replay/attestation/Pareto promotion path. That does not authorize arbitrary Python, shell commands, arbitrary implementation references, LLM-generated executable code, or caller-supplied measurements. Ordinary `procedure_evaluate_candidate` remains non-promoting, and automatic company-wide procedure replacement is separately held pending dedicated company optimization authority.

**Company-wide authority is explicit, not ambient.** Ordinary project tools still default to the current project and reject global writes. Dedicated `company_*` tools can publish approved sources, knowledge, registry objects, capability definitions and accepted procedure baselines only after an exact-subject approval. Existing global seeds remain readable. A company-wide procedure may be read or executed through an eligible registered implementation, but the automatic candidate/promotion path rejects global scope until a dedicated company optimization authority is defined and tested.

**Continuity is checkpoint recovery, not magical memory.** Persisted state survives; unsaved reasoning does not. Native Claude compaction is supported by hooks, but Vres does not own transparent arbitrary context rollover. Several unfinished tasks require explicit disambiguation when a new session has no binding.

**Review evidence is host-observed, not cryptographic attestation.** A local user/process with the same credentials and arbitrary execution can bypass cooperative workflow controls. Native tools are not an OS security boundary. Replay attestations improve application provenance; they do not create a cryptographic root of trust.

**Registered recipes are not a general verified executable compiler.** Vres can execute the bounded code-owned JSON recipe family described above, but it does not treat arbitrary procedure text, Python, shell, external programs or generated code as trusted executable recipes. New executor families require explicit code registration plus their own input/output, permission and validation contracts.

## Windows preview installation

Use a disposable project, a dedicated PostgreSQL test database and a Windows snapshot/backup. Extract the complete release source ZIP, then run in a separate PowerShell window:

```powershell
cd C:\Install\Vres-OS
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Optional flags: `-WithEmbeddings`, `-WithCodex`, `-UseRemotePostgres`. Embeddings are **off by default** so installation does not silently download a large model runtime.

The installer requires current Claude Code (preview compatibility floor: 2.1.246), Python 3.12 or 3.13, and Git. It prompts before installing missing dependencies. It stages a versioned runtime under `%LOCALAPPDATA%\VresOS\releases`, validates it, and selects it through `active-install.json`. It installs the personal plugin at `%USERPROFILE%\.claude\skills\vres-os` (or the equivalent under `CLAUDE_CONFIG_DIR`). It does not rewrite unrelated settings or delete marketplaces.

In a **new** terminal:

```powershell
cd C:\Projects\Vres-Live-Test
claude
```

Say `start vres`. Enter database credentials only in the separate local setup console. Native vendor authentication remains with Claude/Codex.

## Architecture and ownership

```text
User ↔ Chairman
          ├─ Directors / temporary capabilities
          ├─ PostgreSQL: tasks, sessions, findings, procedures, approvals
          ├─ Sources / bounded ingestion / retrieval / optional embeddings
          ├─ Protected validator / artifact fingerprints / replay attestations
          ├─ Registered deterministic procedure worker / runtime evidence
          └─ Native execution adapters: Claude tools, read-only Codex
```

One source of truth per responsibility: versioned code, tests and engineering documents live in Git; operational state and semantic indexes live in PostgreSQL; credentials live in the OS vault. File references do not replace backing up the files themselves.

## Validation and release

```powershell
python -m pip install ".[full,dev]"
python scripts\release_gate.py --output C:\VresEvidence\static
```

The gate runs tests, compiles Python, checks plugin frontmatter/tool references, audits migration file ordering and provenance, builds a wheel offline from the prepared build environment, verifies packaged bytes, and imports installed wheel modules outside the source checkout. The local gate itself is **not** a substitute for running SQL or PowerShell. The repository CI adds a PostgreSQL 16 service and runs the full suite with the opt-in integration guard enabled before running the local release gate.

The released evidence bundle contains actual logs, JUnit results, coverage data, dependency inventory and a per-file validation ledger. The source ZIP and Git bundle are exported from one final commit; checksums and a machine-readable release manifest identify them. Historical conversation test counts are not release evidence.

## Development rule

Outcome → evidence → smallest change → regression test → review → commit → restore/export verification. Do not add a feature to compensate for a broken boundary. Do not call a stored assertion a measurement. Do not call a working tree a release.
