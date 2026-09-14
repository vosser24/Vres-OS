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

These mechanisms have different evidence levels. Local tests execute Python/parsers/subprocesses. GitHub CI now also executes the full test suite against PostgreSQL 16, including migration 010 and the company-authority journey. Windows PowerShell/credential handling, actual Claude/Codex integration and real embeddings still need the live runbook.

## What is deliberately not claimed

**Automatic optimization is held.** A pure Pareto gate exists, but agent-reported runtime/tokens and `independent=true` are not trustworthy paired replay. This preview will not silently promote candidates or alter model policy on those assertions.

**Company-wide authority is explicit, not ambient.** Ordinary project tools still default to the current project and reject global writes. Dedicated `company_*` tools can publish approved sources, knowledge, registry objects, capability definitions and accepted procedure baselines only after an exact-subject approval. Existing global seeds remain readable.

**Continuity is checkpoint recovery, not magical memory.** Persisted state survives; unsaved reasoning does not. Native Claude compaction is supported by hooks, but Vres does not own transparent arbitrary context rollover. Several unfinished tasks require explicit disambiguation when a new session has no binding.

**Review evidence is host-observed, not cryptographic attestation.** A local user/process with the same credentials and arbitrary execution can bypass cooperative workflow controls. Native tools are not an OS security boundary.

**Procedures are registered recipes, not a general verified executable compiler.** The Chairman must inspect and execute the accepted implementation/contract. Automatic conversion of every conversation into trusted Python is not implemented.

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
          ├─ Protected validator / artifact fingerprints
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
