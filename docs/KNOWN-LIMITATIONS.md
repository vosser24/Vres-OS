# Known limitations and release boundaries

Applies to the 0.2.0a1 controlled-live-test preview. Read this before installation.
This is not a production release or a claim that the complete Vres vision is implemented.
A green local release gate does not change the boundaries below.

## Explicitly held functionality

| Capability | Actual preview behavior | What is required before enabling the larger promise |
|---|---|---|
| General automatic procedural optimization | Candidate experiments remain non-promoting when they rely on caller-reported telemetry. A separate replay layer now accepts only runtime-classified paired runs, binds exact input/output digests and contract fingerprints to a frozen protected-validator request, rejects stale/mismatched evidence, and can promote only a current Pareto-superior attested candidate. The runtime-run and promotion sinks are not exposed through MCP. | A bounded runtime-owned production executor that generates the paired measurements from registered procedures; reliable provider/token accounting where token comparison is used; additional fault/concurrency/rollback acceptance. |
| Learned automatic model replacement | Recommendations use registered policies. Recorded telemetry is advisory. | Independently measured comparable runs and a policy-promotion authority, with the same evidence discipline as procedure replay. |
| Arbitrary transparent session replacement | Hooks checkpoint and restore material state around native sessions/compaction. There is no custom terminal host that replaces every Claude context invisibly. | Actual host lifecycle implementation and end-to-end tests. |
| Infinite nested executive hierarchy | Chairman coordinates ordinary subagents; directors return staffing requests rather than recursively spawning unsupported workers. | Supported nested runtime or a separately tested external coordinator. |
| Chaotic company-disk project reconstruction | Mechanical folder ingestion assigns a nominated project. It does not autonomously infer an entire trustworthy company taxonomy. | Project-discovery evaluation and review of ambiguous assignments. |
| Annual unattended market research | Domain due dates and explicit refresh records exist. No annual background scheduler is installed. | A separately authorized scheduler and actual research/validation execution. |
| Automatic best-expert hiring | Roles/skills/capability records aid routing; shared catalog definitions require exact company approval. No benchmark establishes that a generated persona is the world's best expert. | Domain-specific competence evaluations and documented evidence retrieval. |
| Automatic company DB reporting | Vres manages its own memory database. It does not automatically discover or authorize arbitrary reporting databases. | Explicit read-only data-source integration and query validation. |
| Generic recipe execution | Accepted contracts and implementation references can be retrieved. There is no general arbitrary-code procedure runner. The replay evidence sink exists but is intentionally not an MCP capability. | Registered deterministic executors with verified input/output and permissions contracts, bounded process execution, and runtime-owned measurement provenance. |

## Executed and unexecuted target dependencies

Repository CI starts PostgreSQL 16, applies the packaged migrations through the guarded integration fixture,
and runs the full test suite including company-authority and optimization-replay journeys. The authority journey
covers exact-approved global sources, durable knowledge, registry objects, capability definitions and accepted
procedure baselines, including scope provenance and changed-content rejection. The replay journey covers a
reported candidate that cannot self-promote, runtime-classified baseline/candidate runs on the same input,
frozen replay context, an observed Fable validator completion, replay attestation, Pareto assessment and
promotion with retained evidence provenance. That is real PostgreSQL execution on the recorded Linux runner;
it is not Windows acceptance, production-load testing, lock-contention proof, or proof that arbitrary procedure
implementations can yet be executed safely.

The replay integration uses an integration-only runtime-run producer to prove the evidence and promotion state
machine. It is not a production generic executor. Until a bounded registered executor owns that sink, an MCP
caller cannot turn its own metrics into runtime measurements and ordinary candidate evaluation remains
non-promoting.

This audit environment still has not executed the Windows/PowerShell installer, Windows Credential Manager,
live Claude Code plugin/hooks/models, the real MCP SDK transport, live Codex, or a downloaded
SentenceTransformer. Installed-module smoke tests and mocked/scripted boundaries are not substitutes for those
runtimes. See LIVE-VERIFICATION.md for the required target tests.

The wheel is built with the declared build backend prepared in the CI environment and its package contents
checked. Runtime dependencies remain bounded version ranges, not a tested Windows lockfile. The installer
records `resolved-dependencies.txt` and runs `pip check`, but a resolved environment is not a reproducibility
guarantee. Optional embedding dependencies are large and are deliberately not installed by default.

## Security and authority

The local Windows user is a trusted operator. Claude tools, scripts and the memory runtime operate in
that user's security context. The design is not a multi-tenant server, a cryptographic validator identity
system, or protection against a local agent/operator allowed arbitrary shell access to the same files/database.

The validation hook checks a native subagent event, model-family evidence, registered session, frozen
state, reviewed artifact hashes and a structured report. Replay-scoped validation additionally freezes a replay
key and exact baseline/candidate run/contract context. It does not prove every criterion was actually exercised,
that the same OS user could not forge inputs, or that a future executor is safe merely because the evidence
schema exists. High effort is configured rather than cryptographically attested.

Project-local approvals point to a real persisted user turn and a specific action/subject. Company-authority
writes add an exact redacted subject fingerprint and dedicated `company_<action>` approval type. Changing the
approved company content changes that fingerprint and fails closed. Accepted company-wide procedure approval
binds the reusable procedure contract, implementation reference and any initial baseline metrics to the same
scope provenance stored on the procedure. This is still application-level provenance, not a cryptographic
signature or independent identity system. Conditional/ambiguous assent must not be broadened.

Replay evidence uses `RESTRICT` references from attestations/optimization decisions to the runs and validation
request that justified promotion. This is intended to preserve the evidence chain. Administrators with direct
DB privileges can still modify or delete data by operating outside the cooperative application workflow; Vres
is not a tamper-proof ledger.

Redaction covers common credential patterns, not all possible secrets. Never place real credentials in
chat, source documents, transcripts, test fixtures or Git. PostgreSQL administrators and local users with
filesystem/vault privileges remain able to access data. Vres does not encrypt all database contents itself.
Use infrastructure encryption, access controls and backups appropriate to the deployment.

Project filtering is an application boundary, not PostgreSQL row-level multi-tenant isolation. Knowing a
DB password or having arbitrary local shell access can bypass it. Do not expose this MCP server to strangers.

## Installation, upgrade and recovery

The installer stages versioned virtual environments at their permanent location, verifies imports/plugin
structure, and switches a runtime pointer only after its staging checks. Caught failures attempt to restore
old plugin/runtime/launcher state. None of that has yet run under PowerShell here.

A power loss at the publication boundary leaves a journal for manual recovery. Do not delete the journal
blindly. This preview is not a guaranteed unattended, crash-repairing installer for a novice.
Binary rollback is not database rollback. Back up PostgreSQL and artifact/source files before upgrades.
Older executables must not be forced against an unknown newer schema.

Automatic database provisioning refuses existing role/database names. If interrupted after creating a new
role, an orphan may remain; use new unused names or have an administrator inspect it. Vres must not reset
or delete someone else's role to make a retry convenient. Administrator credentials are discarded rather
than stored; only the dedicated runtime credential goes into the Windows vault.

The primary tested setup target must be a disposable VM and a dedicated database. Do not point the preview
at the user's existing Nexus/Praktiker/ERP production database. Native platform sandboxing and prompt
permissions are separately configured vendor capabilities, not guarantees supplied by Vres.

## Memory, artifacts and concurrency

Only persisted material state survives. Unsaved reasoning, a user instruction lost before a successful
write, or files never included in a review cannot be reconstructed reliably. Session-end hooks are best
effort; do not rely on their short native timeout to save a whole conversation.

Migration/application semantics and the normal integration journeys execute against PostgreSQL 16 in CI.
Real concurrent lock contention, serialization behavior under load, duplicate concurrent promotion attempts and
interrupted transactions still require separate stress/fault testing. No database-wide backup/restore operation
is automated by this preview.

Source paths often reference the original files; ingestion is not an archival backup. Moved/deleted raw
sources can make evidence unavailable. Back up source/artifact storage with the DB. Hashes detect changes;
they do not preserve deleted bytes.

## Ingestion and retrieval

Office/PDF extraction is bounded and isolated in a child process. POSIX resource limits do not constitute
a Windows RAM sandbox; timeout/output/ZIP preflight alone cannot eliminate all parser exhaustion risks.
Use a disposable VM for hostile files. OCR is not automatic. Encrypted/scanned/no-text PDFs go to review.
Legacy `.xls`, unsupported encodings and specialized formats can require conversion.

XLSX formulas use stored cached values; Vres does not recalculate Excel, follow external links, run macros
or interpret drawings. PDF layout, slide diagrams and images may carry meaning not present in extracted text.
Truncation is bounded and must remain visible; a partial extraction is not a whole-document proof.

Cross-run hashing deduplicates source records, but unchanged files can still be reparsed on a new onboarding
run. This is not a fully cached incremental document-processing engine. Files can change during acquisition;
they are flagged rather than silently certified as stable.

Optional vector search requires real model/download/runtime verification. JSON-vector fallback scans a
bounded candidate set, so recall is limited and must not be described as exhaustive. Greek/Greeklish quality
has no real company benchmark yet. Similarity, numeric confidence and repeated model agreement are not
probabilities of truth. Knowledge freshness requires real re-verification, not just resetting a date.

## Licensing and supply chain

Vres source is MIT. Third-party packages/models have their own licenses; the PDF dependency is now pypdf,
not PyMuPDF. This is not a legal clearance of the entire transitive dependency graph. No complete vulnerability
scan, signed installer, Windows code-signing certificate or tested offline dependency mirror is included.
Local SHA-256 manifests prove file consistency relative to the supplied manifest, not publisher authenticity.
